# 1. Compute / Container / Hosting

## 1.1 Application Runtime: Cloud Run

**Service**: [Google Cloud Run](https://cloud.google.com/run)

A fully-managed serverless container platform. It provides HTTP request-driven auto-scaling (including scale-to-zero).
There is no need to manage VMs or Kubernetes clusters. You only deploy an OCI-compatible container image, and
the platform handles TLS termination, load balancing, and revision management.

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

A serverless platform for deploying single-purpose, event-driven functions.
Unlike Cloud Run, it can take GCP events such as Firebase Auth events, Firestore triggers,
and Pub/Sub messages directly as triggers, not only HTTP requests.

Where Cloud Run suits a "long-running HTTP service",
Cloud Functions suits "short processing that reacts to a specific event".

### 1.2.1 Key Characteristics

| Property | Detail |
|----------|--------|
| Runtime | Go 1.21+ / Python 3.13+ |
| Generation | Gen 1 (Firebase event triggers) / Gen 2 (Eventarc-based) |
| Trigger Types | Firebase Auth events, Firestore changes, Pub/Sub, HTTP |
| Max Timeout | 540s (Gen 1), 3600s (Gen 2, HTTP/callable), 540s (Gen 2, event-driven) |
| Scaling | Automatic, configurable max instances |

### 1.2.2 Usage Pattern

Use it for lightweight processing in response to GCP service events, such as
creating initial data in reaction to the Firebase Auth `user.create` event.

## 1.3 Container Build Strategy

Adopt a multi-stage Docker build and keep build dependencies out of the final image.

### 1.3.1 Backend Image

```
Stage 1 (builder): dependency resolution + install with uv
Stage 2 (runtime): Python slim image + application code only
```

- Base builder: `ghcr.io/astral-sh/uv:python3.13-bookworm-slim`
- Base runtime: `python:3.13-slim-bookworm`
- Platform: `linux/amd64`

### 1.3.2 Frontend Image

```
Stage 1 (deps): pnpm install (lockfile-based)
Stage 2 (builder): next build (standalone output)
Stage 3 (runner): Node.js alpine + standalone output only
```

- Base: `node:lts-alpine`
- Platform: `linux/amd64`

## 1.4 Container Registry: Artifact Registry

**Service**: [Google Cloud Artifact Registry](https://cloud.google.com/artifact-registry)

A GCP-native multi-format registry. In addition to Docker container images, it can also
host language packages such as Python, npm, and Maven.
It provides fine-grained access control through IAM, plus vulnerability scanning.

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
| Usage | Publish shared libraries as private packages and consume them from other projects with `uv add` |

## 1.5 Local Development

Local emulation with the Firebase Emulator Suite + Docker Compose.
Cloud Run itself is reproduced by running the container locally with `docker run`.
