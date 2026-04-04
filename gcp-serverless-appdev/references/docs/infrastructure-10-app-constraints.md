# 10. Infrastructure Constraints on Application Development

本ドキュメントは、インフラ選定 (Section 1〜9) がアプリケーション開発に課す制約を列挙する。
Backend / Frontend / Mobile の各レイヤーで遵守すべき事項を定める。

## 10.1 Cross-Cutting Constraints (全レイヤー共通)

### 10.1.1 Idempotency (冪等性)

Cloud Tasks, Pub/Sub, Eventarc は全て **at-least-once delivery** である。
同一リクエストが複数回到達する可能性があるため、
副作用を持つ処理は冪等に実装しなければならない。

| Pattern | Detail |
|---------|--------|
| Idempotency Key | Request に一意な ID を含め、処理済みなら skip |
| Upsert | INSERT OR UPDATE で重複 write を吸収 |
| Firestore Transaction | `runTransaction` 内で状態を確認してから write |

### 10.1.2 Stateless Execution

Cloud Run instance は request 間で状態を保持しない前提で設計する。

| Constraint | Rationale |
|------------|-----------|
| In-memory state は request 間で共有不可 | Scale-to-zero / scale-out で instance が入れ替わる |
| File system への永続 write 不可 | Container file system は ephemeral |
| Session state は外部ストアに保持 | Firestore / Cloud Storage を使用 |

### 10.1.3 Request Timeout

Cloud Run の request timeout (default 300s) 内に response を返す必要がある。
長時間処理は Cloud Tasks に enqueue して非同期化する。

### 10.1.4 Cold Start Awareness

Scale-to-zero 構成の場合、初回 request で cold start が発生する。
Application の起動時間 (import, initialization) を最小化する設計が必要。

| Mitigation | Detail |
|------------|--------|
| Lazy initialization | Heavy な resource (ML model, DB pool) は初回アクセス時に初期化 |
| Image size 最小化 | Multi-stage build, 不要な依存の排除 |
| Min instances = 1 (production) | Cold start 回避 (cost trade-off) |

### 10.1.5 Environment Isolation

dev / prd は独立した GCP project であり、Firestore / Storage / Auth のデータは完全分離。
Application code は環境を `APP_ENV` 等の環境変数で判定し、
環境固有の値はハードコードしない。

## 10.2 Backend Constraints

### 10.2.1 Container Requirements

| Constraint | Value | Ref |
|------------|-------|-----|
| Listen port | 8080 | Cloud Run default |
| Health check | `GET /health` -> 200 | [Section 7.5](infrastructure-7-ops.md#75-health-check) |
| Startup time | < 10s recommended | Cold start budget |
| Memory limit | 1024 MiB | [Section 1.1.2](infrastructure-1-compute.md#112-backend-service) |
| Concurrency | 80 requests/instance | [Section 1.1.2](infrastructure-1-compute.md#112-backend-service) |
| Stateless | In-memory state 不可 | [Section 10.1.2](#1012-stateless-execution) |

### 10.2.2 Authentication Handling

| Caller | Verification Method |
|--------|-------------------|
| End-user (Frontend/Mobile) | `Authorization: Bearer {Firebase ID Token}` -> Firebase Admin SDK で verify |
| GCP service (Tasks/Scheduler/Eventarc) | `Authorization: Bearer {OIDC Token}` -> IAM が自動検証 (`--no-allow-unauthenticated`) |
| Internal service (Backend -> Backend) | Service account OIDC token |

Backend は caller 種別に応じて token type を判別する必要がある。

### 10.2.3 Firestore Data Model Constraints

Firestore は内部的に Cloud Spanner をストレージ基盤として使用しており、
全クエリで strong consistency を保証する。
過去の「inequality filter は 1 field のみ」制限は撤廃済み。

| Constraint | Detail |
|------------|--------|
| Consistency | **Strong consistency (全クエリ)** |
| Max document size | 1 MiB |
| Max write rate (single document) | 1 write/sec |
| Max transaction size | 500 documents |
| Inequality / range filter | **複数フィールド対応** (最大 10 フィールド) |
| Array membership | `array-contains` / `array-contains-any` は 1 query に 1 つ |
| `in` | 最大 30 disjunction values |
| `not-in` | 最大 **10** values |
| `OR` query | Supported |
| Composite index (Standard) | Multi-field query には明示的な index 定義が必要 |
| Pipeline operations (Enterprise) | Array unnest, aggregation, regex, chained stages が可能 |
| Geo query | lat/lng 直接 range query (推奨) または Geohash。クライアント側での距離フィルタリングが必要 |
| Vector search (KNN) | `find_nearest` API。最大 2048 次元、最大 1000 件。Vector index の作成が必要 |

> Firestore editions の詳細は [infrastructure-2-data.md Section 2.1.1](infrastructure-2-data.md#211-editions) を参照。
> Geo query / Vector search の詳細は [infrastructure-2-data.md Section 2.1.3](infrastructure-2-data.md#213-query-capabilities) を参照。

### 10.2.4 Cloud Tasks Callback Endpoint

Cloud Tasks から呼ばれる endpoint は以下を満たす必要がある:

| Constraint | Detail |
|------------|--------|
| 成功: 2xx 返却 | 2xx 以外は retry される |
| 冪等性 | At-least-once のため同一 task が複数回到達しうる |
| Timeout | Cloud Tasks の dispatch deadline 内に完了 (default 10 min, max 30 min) |
| Poison message 処理 | Permanent error は 2xx で返しつつ failure を記録 ([Section 3.1.3](infrastructure-3-async.md#313-task-lifecycle--terminal-failure-handling)) |
| Authentication | OIDC token (service account) で認証 |

### 10.2.5 Structured Logging

Cloud Logging との統合のため、stdout に JSON structured log を出力する。

| Field | Purpose |
|-------|---------|
| `severity` | Cloud Logging の severity mapping (INFO, WARNING, ERROR) |
| `message` | Human-readable message |
| `logging.googleapis.com/trace` | Request trace ID (Cloud Run header から取得) |

### 10.2.6 Async Processing Pattern

```
[Sync path]
  Client -> Backend -> immediate response (< 300s)

[Async path]
  Client -> Backend -> enqueue Cloud Tasks -> 202 Accepted
                          |
                          +--> Cloud Tasks -> Backend callback endpoint (async)
```

Response time が 数秒を超える処理は async path を使用する。

## 10.3 Frontend Constraints (Web)

### 10.3.1 Build & Deploy

| Constraint | Detail |
|------------|--------|
| Output mode | Next.js standalone (`output: 'standalone'`) |
| Container runtime | Cloud Run (port 3000) |
| Static assets | Next.js `_next/static` (self-served from Cloud Run) |
| Image optimization | `next/image` の loader 設定 (Cloud Run 上で動作) |

### 10.3.2 Authentication

| Constraint | Detail |
|------------|--------|
| Firebase Auth SDK | Client-side sign-in (Google, Apple, Email 等) |
| ID Token 取得 | `getIdToken()` で取得し、Backend への request に `Authorization: Bearer` で付与 |
| Token refresh | Firebase SDK が自動で refresh (1 hour expiry) |
| Auth state listener | `onAuthStateChanged` で session 状態を reactive に管理 |

### 10.3.3 Firestore Direct Access & Real-time Sync

Client SDK から Firestore に直接 read/write する場合、Security Rules の制約を受ける。
一方で、**WebSocket / SSE / Polling を自前実装することなく** real-time sync が得られる。

| Constraint | Detail |
|------------|--------|
| Firebase Client SDK 必須 | Real-time listener (`onSnapshot`) は Firebase SDK でのみ利用可能。REST API では不可 |
| 認証必須 | `request.auth != null` が前提 |
| Own data only | `request.auth.uid == resource.data.uid` パターンが基本 |
| Write validation | Security Rules で field type / value を検証 |
| Listener cost | Active listener は document read として課金。大量 listener はコスト注意 |
| Offline persistence | SDK が offline cache を保持。offline write は online 復帰時に自動 sync。conflict は last-write-wins |

| Benefit | Detail |
|---------|--------|
| Real-time push (zero infra) | サーバー側の変更が `onSnapshot` で自動通知。WebSocket server 不要 |
| Optimistic UI | Write はローカルキャッシュに即反映。server 確認は非同期 |
| Automatic reconnection | Network 切断後の再接続と差分同期を SDK が自動処理 |

> 詳細は [infrastructure-2-data.md Section 2.1.5](infrastructure-2-data.md#215-real-time-synchronization) を参照。

### 10.3.4 Cloud Storage Upload

| Constraint | Detail |
|------------|--------|
| Firebase Storage SDK | Client-side upload with resumable upload support |
| Security Rules | Upload 可能なユーザー / ファイルサイズ / content type を制限 |
| CORS | Bucket に CORS 設定が必要 ([Section 9.4.2](infrastructure-9-network.md#942-cloud-storage-cors)) |

### 10.3.5 Environment Variables

| Prefix | Exposure |
|--------|----------|
| `NEXT_PUBLIC_*` | Client bundle に含まれる (public) |
| それ以外 | Server-side only (SSR / API routes) |

Sensitive value は `NEXT_PUBLIC_` prefix を付けない。
Firebase config (apiKey, authDomain 等) は public で問題ない。

## 10.4 Mobile Constraints (iOS / Android)

### 10.4.1 Authentication

| Constraint | Detail |
|------------|--------|
| Firebase Auth SDK | Native SDK (iOS: FirebaseAuth, Android: firebase-auth) |
| ID Token | `getIDToken()` で取得し Backend に送信 |
| Token refresh | SDK が自動管理 |
| Biometric auth | Firebase Auth とは独立。local authentication framework で実装 |

### 10.4.2 Firestore Real-time Sync & Offline Support

Mobile SDK は real-time listener (`onSnapshot`) と offline persistence をデフォルトで有効化する。
WebSocket / SSE / Polling の実装なしで、サーバー側の変更がリアルタイムに端末に反映される。

| Benefit | Detail |
|---------|--------|
| Real-time push | `onSnapshot` でサーバー変更を自動受信。Push infra 不要 |
| Offline read | Cache からの read が可能 (network 不要) |
| Offline write | Local に queue され、online 復帰時に自動 sync |
| Optimistic UI | Write は即座にローカル反映 |

| Constraint | Detail |
|------------|--------|
| Firebase Client SDK 必須 | Real-time listener は Firebase SDK でのみ利用可能 |
| Conflict resolution | Last-write-wins (server timestamp が優先) |
| Cache size | Default 100 MiB (configurable) |
| Listener cost | Active listener は document read として課金 |

Offline write の pending 状態をユーザーに明示する UI 設計が必要。

### 10.4.3 API Client Generation

Backend の OpenAPI spec から Mobile 用の API client を自動生成する。

| Platform | Generator | Output |
|----------|-----------|--------|
| iOS | OpenAPI Generator (Swift5) | Swift Codable models + URLSession client |
| Android | OpenAPI Generator (Kotlin) | Kotlin data classes + Retrofit client |

生成コードを手動編集しない。Backend の spec 変更時に再生成する。

### 10.4.4 Push Notification (Optional)

| Service | Detail |
|---------|--------|
| Firebase Cloud Messaging (FCM) | Cross-platform push notification |
| Token management | Device token を Firestore に保存し、Backend から FCM API で送信 |

### 10.4.5 Binary Size & Startup

| Constraint | Detail |
|------------|--------|
| Firebase SDK size | iOS: ~10 MiB, Android: ~5 MiB (Auth + Firestore + Storage) |
| Lazy initialization | FirebaseApp.configure() を app startup で 1 回のみ |
| Network dependency | 初回起動時に Firebase Auth / Firestore への接続が必要 |

## 10.5 Constraints Summary Matrix

| Constraint | Backend | Frontend | Mobile |
|------------|---------|----------|--------|
| Stateless execution | Required | Required (Cloud Run) | N/A |
| Idempotency | Required (Tasks/Pub/Sub callback) | N/A | N/A |
| Firebase Auth token verification | Required | N/A (SDK handles) | N/A (SDK handles) |
| Firebase Auth token acquisition | N/A | Required | Required |
| Firestore Security Rules | Bypass (Admin SDK) | Subject to rules | Subject to rules |
| Firestore real-time sync | N/A (write side) | `onSnapshot` (Firebase SDK 必須) | `onSnapshot` (Firebase SDK 必須) |
| Firestore offline support | N/A | Optional | Default enabled |
| Health check endpoint | Required | Required | N/A |
| Structured logging (JSON) | Required | Recommended | N/A |
| Container port | 8080 | 3000 | N/A |
| Cold start optimization | Required | Required | N/A |
| API client generation | Source (OpenAPI spec) | Consumer (TypeScript) | Consumer (Swift/Kotlin) |
| CORS handling | Server-side config | N/A | N/A |
| dotenvx | Build-time injection | Build-time injection | N/A (native config) |
