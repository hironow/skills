# Project Scaffold Guide

Initial setup procedure for a new GCP application project.

## 1. Monorepo Structure

```
project-root/
├── backend/
│   ├── src/
│   │   ├── __init__.py
│   │   ├── main.py           # FastAPI app entry point
│   │   ├── dependencies.py   # Shared dependencies (Firestore client, auth)
│   │   ├── routers/          # API route modules
│   │   └── services/         # Business logic
│   ├── tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   └── e2e/
│   ├── Dockerfile
│   ├── pyproject.toml
│   └── justfile
├── frontend/
│   ├── src/
│   │   ├── app/              # Next.js App Router
│   │   ├── components/
│   │   ├── lib/
│   │   │   ├── firebase.ts   # Firebase client init
│   │   │   └── api.ts        # Backend API client
│   │   └── hooks/
│   ├── Dockerfile
│   ├── package.json
│   ├── next.config.js
│   └── tsconfig.json
├── emulator/
│   ├── firebase/
│   │   ├── Dockerfile
│   │   ├── firebase.json
│   │   ├── firestore.rules
│   │   ├── firestore.indexes.json
│   │   └── storage.rules
│   ├── docker-compose.yaml
│   ├── justfile
│   └── .env.local.example
├── .github/
│   └── workflows/
│       ├── test.yaml
│       └── deploy.yaml
├── .env.keys              # dotenvx encryption keys (gitignore)
├── .env                   # dotenvx encrypted env vars
├── justfile               # Root task runner
├── firestore.rules        # Production Firestore rules
└── firebase.json          # Production Firebase config
```

## 2. Backend Scaffold

### pyproject.toml

```toml
[project]
name = "my-backend"
version = "0.1.0"
requires-python = ">=3.13"
dependencies = [
    "fastapi>=0.115",
    "uvicorn[standard]>=0.34",
    "firebase-admin>=6.6",
    "google-cloud-tasks>=2.16",
    "google-cloud-pubsub>=2.23",
    "structlog>=24.4",
    "sentry-sdk[fastapi]>=2.19",
]

[dependency-groups]
dev = [
    "pytest>=8.3",
    "httpx>=0.28",       # FastAPI TestClient
    "ruff>=0.8",
    "ty>=0.0.77",
]

[tool.ruff.lint]
select = [
    "FAST", "C90", "NPY", "PD", "B", "A", "DTZ", "T20",
    "N", "I", "E", "F", "PLE", "PLR", "UP", "FURB", "RUF",
]
extend-ignore = ["E501", "RUF002", "RUF003"]
```

### Dockerfile (Backend)

```dockerfile
# ---- Build stage ----
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS builder
WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev
COPY . .
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# ---- Production stage ----
FROM python:3.13-slim-bookworm
WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/src /app/src
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
EXPOSE 8080
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

### main.py (pseudocode)

```python
import sentry_sdk
import structlog
from fastapi import FastAPI

# Sentry initialization
sentry_sdk.init(dsn=settings.sentry_dsn, environment=settings.environment)

# Structured logging
structlog.configure(processors=[structlog.processors.JSONRenderer()])

app = FastAPI()

@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}

# Mount routers
app.include_router(users_router, prefix="/api/v1/users")
```

## 3. Frontend Scaffold

### Dockerfile (Frontend)

```dockerfile
# ---- Dependencies ----
FROM node:22-alpine AS deps
WORKDIR /app
COPY package.json pnpm-lock.yaml ./
RUN corepack enable && pnpm install --frozen-lockfile

# ---- Build ----
FROM deps AS builder
COPY . .
RUN pnpm build

# ---- Production ----
FROM node:22-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public
EXPOSE 3000
CMD ["node", "server.js"]
```

### Firebase Client Init (pseudocode)

```typescript
// lib/firebase.ts
import { initializeApp } from "firebase/app";
import { getAuth, connectAuthEmulator } from "firebase/auth";
import { getFirestore, connectFirestoreEmulator } from "firebase/firestore";

const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const db = getFirestore(app);

// Emulator connection (dev only)
if (process.env.NODE_ENV === "development") {
  connectAuthEmulator(auth, "http://localhost:9099");
  connectFirestoreEmulator(db, "localhost", 8080);
}
```

## 4. Emulator Setup

### docker-compose.yaml

```yaml
services:
  firebase-emulator:
    build:
      context: ./firebase
      dockerfile: Dockerfile
    volumes:
      - ./firebase/firebase.json:/firebase/firebase.json:ro
      - ./firebase/firestore.rules:/firebase/firestore.rules:ro
      - ./firebase/firestore.indexes.json:/firebase/firestore.indexes.json:ro
      - ./firebase/storage.rules:/firebase/storage.rules:ro
      - ./firebase/data:/firebase/data
    ports:
      - "${AUTH_PORT:-9099}:9099"
      - "${FIRESTORE_PORT:-8080}:8080"
      - "${PUBSUB_PORT:-8085}:8085"
      - "${STORAGE_PORT:-9199}:9199"
      - "${EVENTARC_PORT:-9299}:9299"
      - "${TASKS_PORT:-9499}:9499"
      - "${FIREBASE_UI_PORT:-4000}:4000"
    environment:
      - FIREBASE_PROJECT_ID=${FIREBASE_PROJECT_ID:-test-project}
    command: >
      sh -c "
        if [ -d /firebase/data/firestore_export ]; then
          firebase emulators:start --project=$${FIREBASE_PROJECT_ID} --import=/firebase/data --export-on-exit=/firebase/data;
        else
          firebase emulators:start --project=$${FIREBASE_PROJECT_ID} --export-on-exit=/firebase/data;
        fi
      "
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:4000"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 60s
```

### Emulator Ports

| Service | Port |
|---------|------|
| Auth | 9099 |
| Firestore | 8080 |
| Pub/Sub | 8085 |
| Storage | 9199 |
| Eventarc | 9299 |
| Cloud Tasks | 9499 |
| Emulator UI | 4000 |

## 5. Root justfile

```just
default: help

help:
    @just --list --unsorted

# Start all emulators
emulator-up:
    cd emulator && docker compose up -d

# Stop emulators
emulator-down:
    cd emulator && docker compose down

# Backend: run dev server
backend-dev:
    cd backend && uv run uvicorn src.main:app --reload --port 8080

# Backend: run tests
backend-test:
    cd backend && uv run pytest

# Backend: lint + type check
backend-lint:
    cd backend && uv run ruff check . && uv run ty check

# Frontend: run dev server
frontend-dev:
    cd frontend && pnpm dev

# Frontend: build
frontend-build:
    cd frontend && pnpm build

# Deploy backend to Cloud Run
deploy-backend env='staging':
    gcloud run deploy backend \
      --source backend/ \
      --region asia-northeast1 \
      --platform managed
```

## 6. Firestore Security Rules (template)

```
rules_version = '2';

service cloud.firestore {
  match /databases/{database}/documents {
    // Helper: check if user is authenticated
    function isSignedIn() {
      return request.auth != null;
    }

    // Helper: check if user owns the resource
    function isOwner(userId) {
      return isSignedIn() && request.auth.uid == userId;
    }

    // User profile: owner read, server write only
    match /users/{userId} {
      allow read: if isOwner(userId);
      allow write: if false;  // Backend API via Admin SDK only
    }

    // Public collection: authenticated read, server write only
    match /public/{docId} {
      allow read: if isSignedIn();
      allow write: if false;
    }
  }
}
```

## 7. GitHub Actions (test workflow)

```yaml
name: Test
on:
  pull_request:
    branches: [main]

concurrency:
  group: test-${{ github.head_ref }}
  cancel-in-progress: true

jobs:
  backend-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
      - run: uv sync --frozen
        working-directory: backend
      - run: uv run ruff check .
        working-directory: backend
      - run: uv run ty check
        working-directory: backend
      - run: uv run pytest
        working-directory: backend

  frontend-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 22
          cache: pnpm
          cache-dependency-path: frontend/pnpm-lock.yaml
      - run: pnpm install --frozen-lockfile
        working-directory: frontend
      - run: pnpm lint
        working-directory: frontend
      - run: pnpm test
        working-directory: frontend
```

## 8. Environment Management (dotenvx)

```bash
# Initialize dotenvx
dotenvx ext genkey > .env.keys

# Encrypt environment variables
dotenvx set FIREBASE_PROJECT_ID my-project
dotenvx set SENTRY_DSN https://xxx@sentry.io/xxx

# Decrypt at runtime
dotenvx run -- uvicorn src.main:app

# .env.keys is gitignored, .env (encrypted) is committed
```
