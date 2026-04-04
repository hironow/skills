# 11. GCP Service Alternatives & Selection Rationale

本ドキュメントは、GCP 内で同一カテゴリに複数のサービス選択肢が存在する場合に、
なぜ特定のサービスを選定したのかを対比構造で記録する。
Section 1〜10 の選定結果の「Why not」を補完する。

> **2026-03 時点の GCP サービス体系に基づく。**

## 11.1 Compute: Cloud Run vs GKE vs Cloud Functions

### 11.1.1 Cloud Run Resource Types (2025〜)

Cloud Run は現在 **3 つのリソースタイプ** を提供する。

| Resource Type | Model | Endpoint | Scaling | Use Case |
|---------------|-------|----------|---------|----------|
| **Services** | Request-driven | HTTPS endpoint (自動付与) | Request-based autoscaling, scale-to-zero | API server, Web frontend, Webhook |
| **Jobs** | Run-to-completion | なし | 並列 task (最大 10,000) | Batch processing, DB migration, scheduled script |
| **Worker Pools** | Continuous background | なし (HTTP endpoint 不要) | Manual / CREMA (外部メトリクスベース) | Pull-based consumer (Pub/Sub pull, Kafka, RabbitMQ) |

#### Worker Pools の特徴

| Property | Detail |
|----------|--------|
| Pricing | Services 比で CPU/Memory 最大 **40% 安い** |
| Autoscaling | CREMA (Cloud Run External Metrics Autoscaling) による外部メトリクスベース scaling |
| CREMA sources | Pub/Sub queue depth, Kafka consumer lag, Prometheus metrics, GitHub Runner |
| GPU support | 対応 (autoscale 不可、instance 稼働中は常時課金) |
| Min instances | Manual: 最低 1 instance / **CREMA: scale-to-zero 可能** |

> **Ref**: [Cloud Run Overview](https://docs.cloud.google.com/run/docs/overview/what-is-cloud-run),
> [Worker Pools](https://docs.cloud.google.com/run/docs/deploy-worker-pools),
> [CREMA Autoscaling](https://docs.cloud.google.com/run/docs/configuring/workerpools/crema-autoscaling)

### 11.1.2 Cloud Run vs GKE

| Aspect | Cloud Run | GKE (Google Kubernetes Engine) |
|--------|-----------|-------------------------------|
| Management | Fully managed (infrastructure 不可視) | Cluster 管理が必要 (Autopilot mode でも K8s の知識要) |
| Scaling | Request-based autoscale, scale-to-zero | Pod autoscaler (HPA/VPA), node autoscaler |
| Stateful workload | 不可 (stateless only) | 可能 (PersistentVolume, StatefulSet) |
| Networking | Simplified (自動 HTTPS, 自動 load balancing) | Full control (Ingress, Service Mesh, Network Policy) |
| Cost model | Per-request / per-instance-second | Cluster fee + node fee (常時稼働) |
| Cold start | あり (scale-to-zero 構成時) | なし (node 常時起動) |
| GPU | Worker Pools で対応 | Full GPU support (scheduling, time-sharing) |
| Custom runtime | Container image (任意言語) | Container image (任意言語) + sidecar pattern |
| Min cost | 0 (scale-to-zero) | Control plane fee ($74.40/month〜) |

**選定: Cloud Run**

| Rationale |
|-----------|
| Stateless な API server / Web frontend には Cloud Run Services が最適 |
| Scale-to-zero による cost 最適化 (初期フェーズで traffic が少ない場合) |
| Infrastructure 管理不要 (K8s の運用知識が不要) |
| Pull-based consumer は Worker Pools で対応可能 |
| Batch 処理は Jobs で対応可能 |

**GKE を検討すべきケース**:
- Stateful workload (DB on K8s, ML training with checkpoint)
- 複雑な Service Mesh / Network Policy が必要
- Multi-container pod の sidecar pattern が必須
- 常時稼働で高 throughput のワークロード (cold start 不可)

### 11.1.3 Cloud Run Services vs Cloud Functions (Cloud Run functions)

> **Note**: 2024 年 8 月以降、Cloud Functions (2nd gen) は **Cloud Run functions** に改称され、
> 内部的には Cloud Run 上で稼働する。課金体系も Cloud Run に統一された。

| Aspect | Cloud Run Services | Cloud Run functions (旧 Cloud Functions) |
|--------|--------------------|------------------------------------------|
| Deploy unit | Container image | Source code (関数単位) |
| Runtime | 任意 (Docker image) | 限定 (Node.js, Python, Go, Java, .NET, Ruby, PHP) |
| Trigger | HTTP request | HTTP + Eventarc event triggers |
| Concurrency | 設定可能 (最大 1000) | 1 instance = 1 concurrent request (default) |
| Startup | Container 起動 | Function framework 起動 |
| Build | 自前 Dockerfile | Source-based build (自動) |

**選定: Cloud Run Services (主) + Cloud Functions (補助)**

| Component | Service | Rationale |
|-----------|---------|-----------|
| Backend API | Cloud Run Services | 複数 endpoint、concurrency 制御、custom container |
| Frontend (Next.js) | Cloud Run Services | Custom Node.js runtime、standalone build |
| Event handler (軽量) | Cloud Functions | Eventarc trigger、単一関数、source deploy の簡便性 |

## 11.2 Database: Firestore vs Cloud SQL vs Cloud Spanner

### 11.2.1 三者比較

| Aspect | Firestore | Cloud SQL | Cloud Spanner |
|--------|-----------|-----------|---------------|
| Model | Document (NoSQL) | Relational (SQL) | Relational (SQL) + 水平スケール |
| Schema | Flexible (schema-less) | Strict (DDL) | Strict (DDL) |
| Consistency | Strong (全クエリ) | Strong (single instance) | External consistency (global) |
| Scaling | 自動 (serverless) | Vertical (instance size) | Horizontal (node 追加) |
| Max size | 数 TB (推奨) | 数 TB (instance 依存) | PB 級 |
| Serverless | 完全 serverless | Instance 管理必要 | Serverless mode あり |
| Client SDK | Firebase SDK (real-time sync) | なし | なし |
| Offline support | あり (Client SDK) | なし | なし |
| Real-time listener | `onSnapshot` | なし (Polling 必要) | なし (Change Streams は限定的) |
| Security Rules | あり (client 直接アクセス制御) | なし (server 経由のみ) | なし (server 経由のみ) |
| Transaction | Max 500 docs/tx | Full ACID | Full ACID (distributed) |
| Min cost | 0 (無料枠あり) | Instance 常時稼働費 | Node 費 or serverless 最低費 |

### 11.2.2 選定: Firestore (Core)

| Rationale |
|-----------|
| Client SDK による real-time sync (WebSocket/SSE/Polling の自前実装が不要) |
| Offline persistence (Mobile/Web で network 切断時も動作) |
| Security Rules による client 直接アクセス制御 (Backend bypass が可能な read/write) |
| 完全 serverless (instance 管理不要、scale-to-zero 相当) |
| Firebase Auth との native 統合 |
| Flexible schema (初期開発での rapid iteration に有利) |

**Cloud SQL を検討すべきケース**:
- 既存の RDB schema / ORM を移行する場合
- Complex JOIN が頻繁に必要
- PostgreSQL / MySQL の ecosystem (extension, tooling) が必須
- Application が server-side only (client SDK 不要)

**Cloud Spanner を検討すべきケース** (Extension として選定済み):
- 水平スケールが必要な大規模 workload
- Cross-region での strong consistency が必要
- Strict schema + distributed ACID transaction が必須

## 11.3 Async: Cloud Tasks vs Cloud Pub/Sub

### 11.3.1 設計思想の違い

| Aspect | Cloud Tasks | Cloud Pub/Sub |
|--------|-------------|---------------|
| Invocation model | **Explicit** (publisher が endpoint を指定) | **Implicit** (publisher は subscriber を知らない) |
| Delivery pattern | **1:1** (point-to-point) | **1:N** (fan-out, 1 topic -> N subscriptions) |
| Pull subscription | なし | あり |
| Push subscription | HTTP callback (唯一の配信方法) | HTTP push / pull / BigQuery / Cloud Storage |
| Scheduled delivery | あり (future execution, 最大 30 日先) | なし |
| Rate limiting | Queue-level dispatch rate control (max 500 qps/queue) | Client-side flow control |
| Deduplication | Task name + tombstone_ttl | なし (subscriber 側で実装) |
| Message ordering | Best-effort | Ordering key による保証 |
| Dead-letter | なし (自前実装) | DLQ topic 設定可能 |
| Max message size | 1 MiB | 10 MiB |
| Max retention | task_ttl 31 日 (default) | 31 日 (configurable) |

### 11.3.2 使い分け

```
+-------------------------------------------+
|          Async Processing Decision         |
+-------------------------------------------+
     |
     +--> 1:1 delivery?
     |     |
     |     +--> Yes: need rate control / scheduling?
     |     |          |
     |     |          +--> Yes: Cloud Tasks
     |     |          +--> No:  Cloud Tasks (simpler) or Pub/Sub push
     |     |
     |     +--> No (1:N fan-out): Cloud Pub/Sub
     |
     +--> Pull-based consumer?
     |     |
     |     +--> Yes: Cloud Pub/Sub + Cloud Run Worker Pools
     |
     +--> GCP service event reaction?
           |
           +--> Eventarc (internal: Pub/Sub transport)
```

Legend / 凡例:
- 1:1 delivery: 1 対 1 配信
- 1:N fan-out: 1 対多配信
- Rate control: 流量制御
- Pull-based consumer: Pull 型消費者
- GCP service event reaction: GCP サービスイベントへの反応

### 11.3.3 Cloud Tasks + Pub/Sub 併用パターン

本インフラでは Cloud Tasks と Pub/Sub を**併用**する。

| Pattern | Service | Example |
|---------|---------|---------|
| 非同期 1:1 処理 (確実完了) | Cloud Tasks | Email 送信、外部 API call、重い計算 |
| Event fan-out (1:N) | Pub/Sub | User 作成 -> notification + analytics + audit |
| GCP event trigger | Eventarc (Pub/Sub) | Firestore write -> processing pipeline |
| Pull-based consumer | Pub/Sub + Worker Pools | 大量メッセージの batch processing |
| Scheduled execution | Cloud Scheduler -> Cloud Tasks or Pub/Sub | Daily report, cleanup job |

## 11.4 Compute Mode: Cloud Run Services vs Jobs vs Worker Pools

### 11.4.1 三者比較

| Aspect | Services | Jobs | Worker Pools |
|--------|----------|------|-------------|
| Trigger | HTTP request | Manual / Schedule / Workflow | 自律 (pull-based) |
| Endpoint | HTTPS URL (自動付与) | なし | なし |
| Duration | Request timeout (max 3600s) | Max 168 hours (7 days, >24h は Preview) | 無制限 (continuous) |
| Scaling | Request-based autoscale | 並列 task 数指定 (max 10,000) | Manual / CREMA |
| Scale-to-zero | 可能 | N/A (実行完了で終了) | CREMA: 可能 / Manual: 不可 (min 1) |
| Concurrency | 設定可能 (max 1000/instance) | 1 task = 1 instance | Application 定義 |
| Cost | Per-request or per-instance | 実行時間課金 | Instance 稼働時間課金 (Services 比 -40%) |
| Retry | Application 実装 | Task-level retry | Application 実装 |

### 11.4.2 選定マッピング

| Workload | Resource Type | Rationale |
|----------|--------------|-----------|
| Backend API server | Services | HTTP endpoint、request-based scaling |
| Frontend (Next.js SSR) | Services | HTTP endpoint、concurrency |
| Cloud Tasks callback | Services | HTTP callback 受信 |
| Pub/Sub push handler | Services | HTTP push endpoint |
| DB migration | Jobs | Run-to-completion、retry on failure |
| Scheduled batch script | Jobs | Cloud Scheduler trigger、completion semantics |
| Pub/Sub pull consumer | Worker Pools | Pull-based、continuous processing、cost 効率 |
| Kafka consumer | Worker Pools | Pull-based、CREMA autoscaling |

> 現時点では Worker Pools の採用は **optional**。
> Pub/Sub は push subscription + Cloud Run Services で対応可能。
> Pull-based に切り替える必要が生じた場合に Worker Pools を導入する。

## 11.5 Event-Driven: Eventarc vs Pub/Sub Direct vs Cloud Tasks

| Aspect | Eventarc | Pub/Sub (direct) | Cloud Tasks |
|--------|----------|-------------------|-------------|
| Event source | GCP service events (Firestore, Storage, Audit Log) | Application code から publish | Application code から enqueue |
| Configuration | Declarative (trigger 定義) | Topic + Subscription 作成 | Queue + Task 作成 |
| Transport | Pub/Sub (internal) | Pub/Sub native | HTTP callback |
| Format | CloudEvents v1.0 | 自由 (attribute + data) | HTTP request body |
| Use case | GCP サービス変更への反応 | アプリケーション間の event 通知 | 確実に完了させる 1:1 非同期処理 |

**選定: 三者併用**

| Trigger Source | Service |
|----------------|---------|
| Firestore document 変更 | Eventarc -> Cloud Run / Cloud Functions |
| Cloud Storage object upload | Eventarc -> Cloud Run / Cloud Functions |
| Application-generated event (fan-out) | Pub/Sub |
| Application-generated task (1:1, 確実完了) | Cloud Tasks |

## 11.6 Database Extensions: Managed vs Self-Hosted

Extension tier のデータストアについて、GCP 上での選択肢を比較する。

### 11.6.1 Graph Database

| Aspect | Neo4j AuraDB (managed) | Neo4j on GKE (self-hosted) | Dgraph |
|--------|----------------------|---------------------------|--------|
| Management | Fully managed | Cluster 運用必要 | Self-hosted or Dgraph Cloud |
| Backup | 自動 daily snapshot | 手動 (`neo4j-admin dump`) | 手動 or managed |
| Scaling | Plan upgrade | Node 追加 (手動) | Sharding |
| Cost | Subscription | GKE node + storage | Subscription or infra費 |

**選定: Neo4j AuraDB** — 運用負荷を最小化し、本業の開発に集中する。

### 11.6.2 Vector Search Engine

| Aspect | Qdrant Cloud (managed) | Qdrant on GKE | Firestore Vector Search | Vertex AI Vector Search |
|--------|----------------------|---------------|------------------------|------------------------|
| Management | Fully managed | Self-hosted | Serverless (Firestore 組み込み) | Fully managed |
| Max dimensions | 65536 | 同左 | 2048 | 制限なし |
| Scale | Sharding + replication | 手動 | Firestore の auto-scale | 自動 |
| Filtering | Payload filter (高機能) | 同左 | Firestore filter と組み合わせ | Metadata filter |
| Cost | Subscription | GKE 費 | Firestore read 課金 | Index + query 課金 |

**選定: Qdrant Cloud (大規模) / Firestore Vector Search (小〜中規模)**

- 小〜中規模 (数万〜数十万 vectors): Firestore native vector search で十分
- 大規模 (数百万〜): Qdrant Cloud に移行

### 11.6.3 Full-Text Search

| Aspect | Elastic Cloud (managed) | Elasticsearch on GKE | Cloud Firestore (Enterprise Pipeline) |
|--------|------------------------|---------------------|--------------------------------------|
| Management | Fully managed | Cluster 運用必要 | Serverless (Firestore 組み込み) |
| 日本語形態素解析 | Kuromoji analyzer | 同左 | 未対応 (regex のみ) |
| Aggregation | Full aggregation | 同左 | 限定的 |
| Scale | Managed sharding | 手動 sharding | Firestore auto-scale |

**選定: Elastic Cloud** — 日本語全文検索が必要な場合。Firestore Enterprise の Pipeline operations は regex 対応だが、形態素解析は未サポート。

## 11.7 Selection Summary

| Category | Selected | Not Selected | Key Differentiator |
|----------|----------|--------------|--------------------|
| Compute (primary) | Cloud Run Services | GKE | Serverless, scale-to-zero, 運用不要 |
| Compute (event) | Cloud Functions | — | Eventarc trigger, source deploy |
| Compute (batch) | Cloud Run Jobs | — | Run-to-completion, max 24h |
| Compute (pull consumer) | Cloud Run Worker Pools (optional) | GKE | Managed, -40% cost, CREMA |
| Database (primary) | Firestore | Cloud SQL | Client SDK, real-time sync, serverless |
| Database (relational) | Cloud Spanner [Extension] | Cloud SQL | Horizontal scale, distributed ACID |
| Async (1:1) | Cloud Tasks | — | Explicit invocation, rate control, scheduling |
| Async (1:N) | Pub/Sub | — | Fan-out, DLQ, pull subscription |
| Async (GCP event) | Eventarc | — | Declarative, CloudEvents |
| Graph DB | Neo4j AuraDB [Extension] | Self-hosted | Managed, auto backup |
| Vector search | Qdrant Cloud [Extension] | Vertex AI Vector Search | Performance, filtering, cost |
| Full-text search | Elastic Cloud [Extension] | Firestore Pipeline | 日本語形態素解析, aggregation |
