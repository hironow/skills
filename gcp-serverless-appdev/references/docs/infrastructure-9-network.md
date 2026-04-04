# 9. Network / Ingress / Boundary Defense / TLS

## 9.1 Public Ingress: Cloud Run Default Domain

Cloud Run service は deploy 時に自動で `*.run.app` domain と
Google-managed TLS 証明書が付与される。

### 9.1.1 Default Domain

```
https://{service-identifier}.run.app
```

> **Note**: URL 形式は non-deterministic であり、予測不可。
> Deploy 後に `gcloud run services describe` で取得する。

| Item | Detail |
|------|--------|
| TLS | Google-managed (自動更新、設定不要) |
| Certificate Authority | Google Trust Services or Let's Encrypt |
| Protocol | HTTPS only (HTTP -> HTTPS redirect) |

### 9.1.2 Custom Domain (Optional)

独自ドメインを使用する場合は Cloud Run domain mapping または
external HTTP(S) Load Balancer を前段に配置する。

| Method | Use Case |
|--------|----------|
| Cloud Run domain mapping | 単純なカスタムドメイン割当 |
| External HTTP(S) LB | CDN, WAF, multi-region routing が必要な場合 |

Custom domain 使用時は DNS に CNAME / A record を設定し、
Google-managed certificate の provisioning を待つ (最大 24 時間)。

## 9.2 Ingress Control

### 9.2.1 Cloud Run Ingress Setting

Cloud Run の `--ingress` flag で、service に到達できるトラフィックを制限する。

| Setting | 許可範囲 | Use Case |
|---------|---------|----------|
| `all` | Internet + internal | Frontend (public-facing) |
| `internal` | VPC + GCP services only | Internal API (Cloud Tasks/Scheduler callback) |
| `internal-and-cloud-load-balancing` | VPC + GCP services + LB | LB 経由の public service |

### 9.2.2 推奨構成

| Service | Ingress | Rationale |
|---------|---------|-----------|
| Frontend (Cloud Run) | `all` | End-user が直接アクセス |
| Backend (Cloud Run) | `all` | Frontend + client app からアクセス |
| Internal callback endpoint | `internal` | Cloud Tasks / Scheduler からのみ |

Backend を `internal` に制限する場合は、Frontend から Backend への通信を
同一 VPC 内の serverless VPC connector 経由にする必要がある。
初期構成では `all` + Firebase Auth token 検証で boundary を確保する。

## 9.3 Service-to-Service Authentication

### 9.3.1 GCP Service -> Cloud Run

Cloud Tasks, Cloud Scheduler, Eventarc が Cloud Run endpoint を呼び出す際は、
service account に紐づく OIDC token を自動付与する。
Cloud Run 側で `--no-allow-unauthenticated` を設定すると、
有効な OIDC token を持たない request を reject する。

```
Cloud Tasks / Scheduler
  |
  +--> OIDC token (service account) を Authorization header に付与
  |
Cloud Run (--no-allow-unauthenticated)
  |
  +--> IAM が OIDC token を検証
  +--> roles/run.invoker を持つ SA のみ許可
```

### 9.3.2 Backend -> External API

Backend から外部 API (LLM provider, TTS 等) への egress は
Cloud Run の default egress (public internet) を使用する。

| Item | Detail |
|------|--------|
| Egress | Public internet (default) |
| Authentication | API key / OAuth token (Secret Manager / dotenvx) |
| Rate Limiting | Application-level (外部 API の quota に準拠) |

## 9.4 CORS Policy

Frontend と Backend が異なる origin の場合、Backend に CORS header を設定する。
Cloud Storage bucket への browser-origin request にも CORS 設定が必要。

### 9.4.1 Backend CORS

FastAPI middleware で `allow_origins`, `allow_methods`, `allow_headers` を設定する。

### 9.4.2 Cloud Storage CORS

`cors.json` を作成し `gsutil cors set cors.json gs://{bucket}` で適用する。

| Item | Detail |
|------|--------|
| Allowed Origins | Frontend domain (dev/prd) |
| Allowed Methods | GET (download) |
| Max Age | 3600s |

## 9.5 DDoS Protection

Cloud Run は Google Front End (GFE) を経由するため、
Layer 3/4 の DDoS protection は GCP infrastructure が自動提供する。

Layer 7 (application-level) の protection が必要な場合は
Cloud Armor を External HTTP(S) Load Balancer と組み合わせる。

| Tier | Protection | Configuration |
|------|-----------|---------------|
| Default (GFE) | L3/L4 DDoS mitigation | Automatic, no config required |
| Cloud Armor (Optional) | L7 WAF, rate limiting, geo-blocking | Requires External LB |

## 9.6 Firewall / VPC (Optional)

Cloud Run はデフォルトで VPC 外で動作する。
VPC 内のリソース (Cloud SQL, Memorystore 等) にアクセスする場合は
**Direct VPC egress** (推奨) または Serverless VPC Access connector を設定する。

| Method | Status | Throughput | Cost |
|--------|--------|-----------|------|
| **Direct VPC egress** | GA (推奨) | Connector 比 ~2x | Idle cost なし |
| Serverless VPC Access connector | GA (legacy) | Standard | Connector instance 常時課金 |

初期構成では VPC は不要。Extension tier のデータストアを
GCE / GKE 上で self-host する場合に VPC 設計が必要になる。

## 9.7 Network Summary

```
Internet
  |
  +--> [Cloud Run: Frontend] --ingress=all, HTTPS (Google-managed TLS)
  |         |
  |         +--> [Cloud Run: Backend] --ingress=all, Firebase Auth token
  |                   |
  |                   +--> [Firestore] (IAM, Admin SDK)
  |                   +--> [Cloud Storage] (IAM)
  |                   +--> [Cloud Tasks] (IAM) --> callback to Cloud Run (OIDC)
  |                   +--> [External API] (API key, egress via public internet)
  |
  +--> [Cloud Tasks / Scheduler / Eventarc]
           |
           +--> [Cloud Run: Backend] --no-allow-unauthenticated (OIDC)
```

Legend:
- Internet: End-user access
- Cloud Run: Frontend: Public-facing web application
- Cloud Run: Backend: API server (authenticated)
- Firestore / Cloud Storage: Data layer (IAM-protected)
- Cloud Tasks / Scheduler / Eventarc: Async triggers (OIDC-authenticated)
- External API: Third-party services (API key)
