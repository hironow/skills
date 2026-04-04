# 7. Development Operations / Local Environment

## 7.1 Local Emulator Suite

Local development では、GCP service を emulator で再現し、
cloud 環境への依存なしに開発・テストを行う。

### 7.1.1 Firebase Emulator Suite

Firebase CLI が提供する統合 emulator。Single process で複数サービスを起動し、
Web UI (port 4000) で状態を確認できる。

| Service | Port | Emulated Feature |
|---------|------|------------------|
| Auth | 9099 | User sign-up/sign-in, ID token issue |
| Firestore | 8080 | Document CRUD, security rules evaluation |
| Storage | 9199 | Object upload/download |
| Pub/Sub | 8085 | Topic publish/subscribe |
| Eventarc | 9299 | Event routing |
| Cloud Tasks | 9499 | Task enqueue/dispatch |
| Emulator UI | 4000 | Web-based management console |

### 7.1.2 Docker Compose Stack

Firebase Emulator 以外のデータストアは Docker Compose で起動する。

| Service | Image | Ports |
|---------|-------|-------|
| Cloud Spanner | `gcr.io/cloud-spanner-emulator/emulator` | 9010, 9020 |
| pgAdapter | `gcr.io/cloud-spanner-pg-adapter/pgadapter` | 5432 |
| Neo4j | `neo4j:5-community` | 7474, 7687 |
| Qdrant | `qdrant/qdrant:latest` | 6333, 6334 |
| Elasticsearch | `elasticsearch:8+` | 9200 |
| pgvector | `pgvector/pgvector:pg18` | 55432 |

### 7.1.3 Data Persistence

Emulator data は volume mount で永続化し、再起動後も保持する。
Firebase Emulator は `--export-on-exit` / `--import` flag で
data directory の export/import を行う。

## 7.2 Task Runner

開発コマンドを task runner で統一し、個人差を排除する。

### 7.2.1 Primary: justfile

| Command | Purpose |
|---------|---------|
| `just dev` | Backend dev server 起動 (hot-reload) |
| `just test` | Unit test 実行 |
| `just test-e2e` | E2E test 実行 |
| `just lint` | Linter 実行 (ruff check + mypy) |
| `just fmt` | Formatter 実行 (ruff format) |
| `just build` | Docker image build |
| `just push` | Artifact Registry へ push |
| `just deploy` | Cloud Run へ deploy |

### 7.2.2 Supplementary: mise.toml

Tool version management + task definition。
環境変数 (`GOOGLE_CLOUD_PROJECT`, `GOOGLE_CLOUD_LOCATION` 等) を一元管理し、
task 内で参照する。

## 7.3 Code Generation Pipeline

API client と型定義を source of truth から自動生成し、手動同期のズレを防ぐ。

| Source | Target | Tool |
|--------|--------|------|
| FastAPI (Python) -> OpenAPI spec | Go / Swift / Dart client | OpenAPI Generator (Docker) |
| Pydantic model (Python) | TypeScript type definitions | pydantic-to-typescript |

CI で生成結果の差分を検証し、未反映の変更を検出する。

## 7.4 Deploy Procedure

### 7.4.1 Cloud Run Deploy

```
1. Docker image build (multi-stage)
2. Artifact Registry へ push
3. gcloud run deploy --image={image}:{tag} \
     --region={region} \
     --memory={memory} \
     --cpu={cpu} \
     --concurrency={concurrency} \
     --timeout={timeout} \
     --min-instances={min} \
     --max-instances={max}
```

### 7.4.2 Cloud Run Service Parameters

| Parameter | Development | Production |
|-----------|-------------|------------|
| Memory | 1024 MiB | 1024 MiB |
| CPU | 1 | 1 |
| Concurrency | 80 | 80 |
| Timeout | 300s | 300s |
| Min Instances | 0 | 0-1 |
| Max Instances | 1 | 10 |

### 7.4.3 Firebase Deploy

```
firebase deploy --only firestore:rules    # Security rules
firebase deploy --only firestore:indexes  # Composite indexes
firebase deploy --only storage            # Storage rules
firebase deploy --only remoteconfig       # Remote Config
```

### 7.4.4 Cloud Functions Deploy

```
gcloud functions deploy {function_name} \
  --gen1 \
  --runtime={runtime} \
  --trigger-event={event} \
  --region={region}
```

## 7.5 Health Check

Cloud Run service の liveness を確認する endpoint。
Load balancer と Cloud Scheduler からの定期確認にも使用する。

| Item | Value |
|------|-------|
| Endpoint | `GET /health` |
| Expected Response | 200 OK |
| Usage | Cloud Run startup probe, external monitoring |

## 7.6 Scaling Configuration

### 7.6.1 Cloud Run Auto-Scaling

Cloud Run は request 数に応じて instance を自動 scale する。

```
0 requests --> 0 instances (scale-to-zero)
  |
  +--> Request arrives --> Cold start (new instance)
  |
  +--> Concurrency limit reached --> Scale out (new instance)
  |
  +--> Requests drop --> Scale in (idle instances removed)
```

**Cold Start 対策**:
- `--min-instances=1` で warm instance を常駐させる (production)
- Container image size を最小化 (multi-stage build)
- Application の startup time を短縮
