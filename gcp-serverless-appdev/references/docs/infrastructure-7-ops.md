# 7. Development Operations / Local Environment

## 7.1 Local Emulator Suite

In local development, GCP services are reproduced with emulators so that
development and testing run without depending on the cloud environment.

### 7.1.1 Firebase Emulator Suite

An integrated emulator provided by the Firebase CLI. It starts several services in a
single process, and the state can be inspected in the Web UI (port 4000).

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

Data stores other than the Firebase Emulator are started with Docker Compose.

| Service | Image | Ports |
|---------|-------|-------|
| Cloud Spanner | `gcr.io/cloud-spanner-emulator/emulator` | 9010, 9020 |
| pgAdapter | `gcr.io/cloud-spanner-pg-adapter/pgadapter` | 5432 |
| Neo4j | `neo4j:5-community` | 7474, 7687 |
| Qdrant | `qdrant/qdrant:latest` | 6333, 6334 |
| Elasticsearch | `elasticsearch:8+` | 9200 |
| pgvector | `pgvector/pgvector:pg18` | 55432 |

### 7.1.3 Data Persistence

Emulator data is persisted through a volume mount and retained across restarts.
The Firebase Emulator exports and imports its data directory with the
`--export-on-exit` / `--import` flags.

## 7.2 Task Runner

Development commands are unified in a task runner to remove per-person differences.

### 7.2.1 Primary: justfile

| Command | Purpose |
|---------|---------|
| `just dev` | Start the backend dev server (hot-reload) |
| `just test` | Run unit tests |
| `just test-e2e` | Run E2E tests |
| `just lint` | Run the linter (ruff check + ty check) |
| `just fmt` | Run the formatter (ruff format) |
| `just build` | Docker image build |
| `just push` | Push to Artifact Registry |
| `just deploy` | Deploy to Cloud Run |

### 7.2.2 Supplementary: mise.toml

Tool version management plus task definitions.
Environment variables (`GOOGLE_CLOUD_PROJECT`, `GOOGLE_CLOUD_LOCATION`, and so on)
are managed in one place and referenced from tasks.

## 7.3 Code Generation Pipeline

API clients and type definitions are generated automatically from the source of
truth, which prevents drift caused by manual synchronization.

| Source | Target | Tool |
|--------|--------|------|
| FastAPI (Python) -> OpenAPI spec | Go / Swift / Dart client | OpenAPI Generator (Docker) |
| Pydantic model (Python) | TypeScript type definitions | pydantic-to-typescript |

CI verifies the diff of the generated output and detects changes that have not
been applied.

## 7.4 Deploy Procedure

### 7.4.1 Cloud Run Deploy

```
1. Docker image build (multi-stage)
2. Push to Artifact Registry
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

An endpoint that checks the liveness of a Cloud Run service.
It is also used for periodic checks from the load balancer and Cloud Scheduler.

| Item | Value |
|------|-------|
| Endpoint | `GET /health` |
| Expected Response | 200 OK |
| Usage | Cloud Run startup probe, external monitoring |

## 7.6 Scaling Configuration

### 7.6.1 Cloud Run Auto-Scaling

Cloud Run scales instances automatically according to the number of requests.

```
0 requests --> 0 instances (scale-to-zero)
  |
  +--> Request arrives --> Cold start (new instance)
  |
  +--> Concurrency limit reached --> Scale out (new instance)
  |
  +--> Requests drop --> Scale in (idle instances removed)
```

**Cold start countermeasures**:
- Keep a warm instance resident with `--min-instances=1` (production)
- Minimize the container image size (multi-stage build)
- Shorten the application startup time
