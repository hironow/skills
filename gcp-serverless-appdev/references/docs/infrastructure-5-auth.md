# 5. Authentication / Authorization / Secrets

## 5.1 User Authentication: Firebase Authentication

**Service**: [Firebase Authentication](https://firebase.google.com/docs/auth)

Managed identity platform。Google / Apple / Email-Password 等の identity provider を
統合し、JWT (ID Token) ベースの認証を提供する。
Client SDK が token lifecycle (refresh, expiry) を自動管理し、
Backend は Admin SDK で token を verify する。

### 5.1.1 Key Characteristics

| Property | Detail |
|----------|--------|
| Token Format | JWT (RS256) |
| Token Lifetime | 1 hour (auto-refresh by client SDK) |
| Identity Providers | Configurable (Google, Apple, Email, etc.) |
| User Management | Firebase Console / Admin SDK |
| Multi-tenancy | Project-level isolation |

### 5.1.2 Authentication Flow

```
Client App
  |
  +--> Firebase Auth SDK (sign-in with provider)
  |
  +--> Receive ID Token (JWT)
  |
  +--> Send ID Token in Authorization header to Backend
  |
Backend (Cloud Run)
  |
  +--> Verify ID Token via Firebase Admin SDK
  |
  +--> Extract uid, claims from verified token
```

## 5.2 Backend Authorization

### 5.2.1 Service-to-Service Authentication

GCP service 間の通信 (Cloud Tasks -> Cloud Run, Cloud Scheduler -> Cloud Run,
Cloud Functions -> Cloud Run) は OIDC token による service account 認証を使用する。
Cloud Run の `--ingress` 設定 (`all` / `internal` / `internal-and-cloud-load-balancing`)
で ingress を制御する。

### 5.2.2 Firestore Security Rules

Client SDK からの直接アクセスに対し、declarative rule で制御:

- `request.auth != null` : 認証済みユーザーのみ
- `request.auth.uid == resource.data.uid` : 本人のデータのみ
- Collection / document level で read/write を個別制御

## 5.3 Secret Management: Google Cloud Secret Manager

**Service**: [Google Cloud Secret Manager](https://cloud.google.com/secret-manager)

Versioned secret storage。API key, credential 等の sensitive value を
GCP IAM で access control し、application code から programmatic に取得する。

Cloud Build / Cloud Run から `roles/secretmanager.secretAccessor` で参照する。

### 5.3.1 Key Characteristics

| Property | Detail |
|----------|--------|
| Versioning | Automatic (create, access, destroy per version) |
| Access Control | IAM-based per-secret |
| Rotation | Manual or automated via Cloud Functions |
| Audit | Cloud Audit Logs |
| Replication | Automatic or user-managed |

## 5.4 CI/CD Authentication: Workload Identity Federation

**Service**: [Workload Identity Federation](https://cloud.google.com/iam/docs/workload-identity-federation)

External identity provider (GitHub OIDC) の token を GCP IAM の short-lived credential に
exchange する仕組み。Service account key file を GitHub Secrets に保存する必要がなく、
key rotation / leak risk を排除する。

### 5.4.1 Authentication Flow

```
GitHub Actions Runner
  |
  +--> Request OIDC token from GitHub
  |
  +--> Present OIDC token to GCP Security Token Service
  |
  +--> Receive short-lived GCP access token
  |
  +--> Use access token for GCP API calls
```

### 5.4.2 Required Resources

| Resource | Purpose |
|----------|---------|
| Workload Identity Pool | GitHub token の validation context |
| Workload Identity Provider | GitHub OIDC issuer mapping |
| Service Account | `github-actions@{project}.iam.gserviceaccount.com` |

### 5.4.3 Service Account Roles

| Role | Purpose |
|------|---------|
| `roles/artifactregistry.writer` | Container image / package の push |
| `roles/cloudbuild.builds.editor` | Cloud Build job execution |
| `roles/storage.objectCreator` | Build artifact upload |
| `roles/storage.admin` | Storage bucket management |
| `roles/iam.serviceAccountUser` | Cloud Run deploy 時の SA impersonation |
| `roles/secretmanager.secretAccessor` | Build 時の secret 参照 |

## 5.5 Secret Management: Single Source of Truth Policy

Runtime secret の正本 (SSOT) を以下の通り定める。
二系統 (dotenvx / Secret Manager) の責務境界を明確にし、
事故時の更新手順・監査経路を一本化する。

### 5.5.1 SSOT Matrix

| 機密種別 | 正本 (SSOT) | 理由 |
|----------|------------|------|
| CI/CD 認証 (GCP OIDC) | GitHub Secrets | CI runner のみが参照。GCP 外 |
| dotenvx 復号キー | GitHub Secrets | Build-time injection。CI 以外から参照しない |
| Runtime API Keys (LLM, TTS, etc.) | **dotenvx** | Deploy 時に container に注入。Secret Manager 不要 |
| Firebase Config (public) | **dotenvx** | Non-sensitive。Client bundle に含まれる |
| GCP Service Account Key | **なし (使用禁止)** | Workload Identity Federation で代替 |
| Cloud Build 専用 secret | **Secret Manager** | Cloud Build native integration 必須の場合のみ |

### 5.5.2 運用ルール

| Rule | Detail |
|------|--------|
| 正本は常に 1 箇所 | 同一 secret を dotenvx と Secret Manager の両方に保存しない |
| 更新手順 | dotenvx: `dotenvx set KEY=VALUE -f .env.{env}` -> commit -> deploy |
| 監査 | dotenvx: git history で変更追跡 / Secret Manager: Cloud Audit Logs |
| Rotation | API key rotation 時は dotenvx の該当 .env.{env} を更新し再 deploy |

### 5.5.3 Secret Manager の使用条件

Secret Manager は以下の場合にのみ使用する:

1. Cloud Build が build 時に参照する secret (dotenvx key 自体の復号等)
2. Cloud Run の環境変数ではなく volume mount で secret を渡す必要がある場合
3. Application code から dynamic に secret を取得する必要がある場合 (rotation without redeploy)

上記以外の runtime secret は dotenvx を正本とする。

## 5.6 Firebase Project Isolation

Environment ごとに独立した Firebase / GCP project を使用し、
data / config / IAM を完全に分離する。

| Environment | Firebase Project | Purpose |
|-------------|-----------------|---------|
| Development | `{name}-dev` | Integration / staging |
| Production | `{name}-prd` | Live service |
