# 1. Compute / Container / Hosting

## 1.1 Application Runtime: Cloud Run

**Service**: [Google Cloud Run](https://cloud.google.com/run)

Fully-managed serverless container platform。HTTP request-driven auto-scaling (including scale-to-zero) を提供する。
VM / Kubernetes cluster の管理は不要。OCI-compatible container image を deploy するだけで、
TLS termination, load balancing, revision management を platform 側が担う。

### 1.1.1 Frontend Service

| Item | Value |
|------|-------|
| Runtime | Node.js (LTS) |
| Framework | Next.js (standalone output mode) |
| Port | 3000 |
| Scaling | Request-based, scale-to-zero |
| Memory | 512 MiB |
| CPU | 1 |

### 1.1.2 Backend Service

| Item | Value |
|------|-------|
| Runtime | Python 3.13+ |
| Framework | FastAPI + uvicorn |
| Port | 8080 |
| Scaling | Request-based, scale-to-zero |
| Memory | 1024 MiB |
| CPU | 1 |
| Concurrency | 80 |
| Timeout | 300s |
| Health Check | `GET /health` |

## 1.2 Event-Driven Functions: Cloud Functions

**Service**: [Google Cloud Functions](https://cloud.google.com/functions)

Single-purpose な event-driven function を deploy する serverless platform。
Cloud Run と異なり、HTTP request 以外に Firebase Auth event, Firestore trigger,
Pub/Sub message 等の GCP event を直接 trigger として受け取れる。

Cloud Run が「long-running な HTTP service」に適するのに対し、
Cloud Functions は「特定 event に反応する短い処理」に適する。

### 1.2.1 Key Characteristics

| Property | Detail |
|----------|--------|
| Runtime | Go 1.21+ / Python 3.13+ |
| Generation | Gen 1 (Firebase event triggers) / Gen 2 (Eventarc-based) |
| Trigger Types | Firebase Auth events, Firestore changes, Pub/Sub, HTTP |
| Max Timeout | 540s (Gen 1), 3600s (Gen 2, HTTP/callable), 540s (Gen 2, event-driven) |
| Scaling | Automatic, configurable max instances |

### 1.2.2 Usage Pattern

Firebase Auth の `user.create` event に反応して初期データを作成する等、
GCP service event に対する lightweight な処理に使用する。

## 1.3 Container Build Strategy

Multi-stage Docker build を採用し、build dependencies を final image から排除する。

### 1.3.1 Backend Image

```
Stage 1 (builder): uv による dependency resolution + install
Stage 2 (runtime): Python slim image + application code のみ
```

- Base builder: `ghcr.io/astral-sh/uv:python3.13-bookworm-slim`
- Base runtime: `python:3.13-slim-bookworm`
- Platform: `linux/amd64`

### 1.3.2 Frontend Image

```
Stage 1 (deps): pnpm install (lockfile-based)
Stage 2 (builder): next build (standalone output)
Stage 3 (runner): Node.js alpine + standalone output のみ
```

- Base: `node:lts-alpine`
- Platform: `linux/amd64`

## 1.4 Container Registry: Artifact Registry

**Service**: [Google Cloud Artifact Registry](https://cloud.google.com/artifact-registry)

GCP-native な multi-format registry。Docker container image に加え、
Python / npm / Maven 等の language package も hosting できる。
IAM による fine-grained access control と vulnerability scanning を提供する。

### 1.4.1 Docker Repository

| Item | Value |
|------|-------|
| Location | `us-central1` |
| Format | Docker |
| Naming | `us-central1-docker.pkg.dev/{project}/{repository}/{image}:{tag}` |

### 1.4.2 Python Package Repository

| Item | Value |
|------|-------|
| Location | `asia-northeast1` |
| Format | Python |
| Naming | `asia-northeast1-python.pkg.dev/{project}/{repository}/` |
| Usage | 共有ライブラリを private package として publish し、他プロジェクトから `uv add` で利用 |

## 1.5 Local Development

Firebase Emulator Suite + Docker Compose による local emulation。
Cloud Run 自体は container を local で `docker run` することで再現する。
