# 10. Infrastructure Constraints on Application Development

This document lists the constraints that the infrastructure choices (Sections 1
through 9) impose on application development.
It defines what must be observed at each of the Backend, Frontend, and Mobile layers.

## 10.1 Cross-Cutting Constraints (Common to All Layers)

### 10.1.1 Idempotency

Cloud Tasks, Pub/Sub, and Eventarc all provide **at-least-once delivery**.
The same request may arrive more than once, so any processing that has side
effects must be implemented idempotently.

| Pattern | Detail |
|---------|--------|
| Idempotency Key | Include a unique ID in the request and skip it if already processed |
| Upsert | Absorb duplicate writes with INSERT OR UPDATE |
| Firestore Transaction | Check the state inside `runTransaction` before writing |

### 10.1.2 Stateless Execution

Design on the assumption that a Cloud Run instance keeps no state between requests.

| Constraint | Rationale |
|------------|-----------|
| In-memory state cannot be shared between requests | Instances are swapped out by scale-to-zero / scale-out |
| No durable writes to the file system | The container file system is ephemeral |
| Keep session state in an external store | Use Firestore / Cloud Storage |

### 10.1.3 Request Timeout

A response must be returned within the Cloud Run request timeout (default 300s).
Long-running processing is enqueued to Cloud Tasks and handled asynchronously.

### 10.1.4 Cold Start Awareness

With a scale-to-zero configuration, the first request incurs a cold start.
The design must minimize application startup time (imports, initialization).

| Mitigation | Detail |
|------------|--------|
| Lazy initialization | Initialize heavy resources (ML model, DB pool) on first access |
| Minimize image size | Multi-stage build, drop unnecessary dependencies |
| Min instances = 1 (production) | Avoids cold start (cost trade-off) |

### 10.1.5 Environment Isolation

dev and prd are independent GCP projects, and Firestore / Storage / Auth data is
fully separated.
Application code determines the environment from an environment variable such as
`APP_ENV`, and never hardcodes environment-specific values.

## 10.2 Backend Constraints

### 10.2.1 Container Requirements

| Constraint | Value | Ref |
|------------|-------|-----|
| Listen port | 8080 | Cloud Run default |
| Health check | `GET /health` -> 200 | [Section 7.5](infrastructure-7-ops.md#75-health-check) |
| Startup time | < 10s recommended | Cold start budget |
| Memory limit | 1024 MiB | [Section 1.1.2](infrastructure-1-compute.md#112-backend-service) |
| Concurrency | 80 requests/instance | [Section 1.1.2](infrastructure-1-compute.md#112-backend-service) |
| Stateless | No in-memory state | [Section 10.1.2](#1012-stateless-execution) |

### 10.2.2 Authentication Handling

| Caller | Verification Method |
|--------|-------------------|
| End-user (Frontend/Mobile) | `Authorization: Bearer {Firebase ID Token}` -> verify with the Firebase Admin SDK |
| GCP service (Tasks/Scheduler/Eventarc) | `Authorization: Bearer {OIDC Token}` -> verified automatically by IAM (`--no-allow-unauthenticated`) |
| Internal service (Backend -> Backend) | Service account OIDC token |

The backend must determine the token type according to the kind of caller.

### 10.2.3 Firestore Data Model Constraints

Firestore internally uses Cloud Spanner as its storage foundation and guarantees
strong consistency for every query.
The former restriction that an inequality filter could apply to only one field
has been removed.

| Constraint | Detail |
|------------|--------|
| Consistency | **Strong consistency (all queries)** |
| Max document size | 1 MiB |
| Max write rate (single document) | 1 write/sec |
| Max transaction size | 500 documents |
| Inequality / range filter | **Multiple fields supported** (up to 10 fields) |
| Array membership | One `array-contains` / `array-contains-any` per query |
| `in` | Up to 30 disjunction values |
| `not-in` | Up to **10** values |
| `OR` query | Supported |
| Composite index (Standard) | A multi-field query needs an explicit index definition |
| Pipeline operations (Enterprise) | Array unnest, aggregation, regex, and chained stages are available |
| Geo query | Direct range query on lat/lng (recommended) or Geohash. Distance filtering must be done on the client side |
| Vector search (KNN) | `find_nearest` API. Up to 2048 dimensions, up to 1000 results. A vector index must be created |

> For details of Firestore editions, see [infrastructure-2-data.md Section 2.1.1](infrastructure-2-data.md#211-editions).
> For details of geo query and vector search, see [infrastructure-2-data.md Section 2.1.3](infrastructure-2-data.md#213-query-capabilities).

### 10.2.4 Cloud Tasks Callback Endpoint

An endpoint called by Cloud Tasks must satisfy the following:

| Constraint | Detail |
|------------|--------|
| Success: return 2xx | Anything other than 2xx is retried |
| Idempotency | Delivery is at-least-once, so the same task may arrive more than once |
| Timeout | Complete within the Cloud Tasks dispatch deadline (default 10 min, max 30 min) |
| Poison message handling | Return 2xx for a permanent error while recording the failure ([Section 3.1.3](infrastructure-3-async.md#313-task-lifecycle--terminal-failure-handling)) |
| Authentication | Authenticate with an OIDC token (service account) |

### 10.2.5 Structured Logging

For integration with Cloud Logging, emit JSON structured logs to stdout.

| Field | Purpose |
|-------|---------|
| `severity` | Maps to Cloud Logging severity (INFO, WARNING, ERROR) |
| `message` | Human-readable message |
| `logging.googleapis.com/trace` | Request trace ID (taken from the Cloud Run header) |

### 10.2.6 Async Processing Pattern

```
[Sync path]
  Client -> Backend -> immediate response (< 300s)

[Async path]
  Client -> Backend -> enqueue Cloud Tasks -> 202 Accepted
                          |
                          +--> Cloud Tasks -> Backend callback endpoint (async)
```

Processing whose response time exceeds a few seconds uses the async path.

## 10.3 Frontend Constraints (Web)

### 10.3.1 Build & Deploy

| Constraint | Detail |
|------------|--------|
| Output mode | Next.js standalone (`output: 'standalone'`) |
| Container runtime | Cloud Run (port 3000) |
| Static assets | Next.js `_next/static` (self-served from Cloud Run) |
| Image optimization | `next/image` loader configuration (runs on Cloud Run) |

### 10.3.2 Authentication

| Constraint | Detail |
|------------|--------|
| Firebase Auth SDK | Client-side sign-in (Google, Apple, Email, and so on) |
| ID token acquisition | Obtain it with `getIdToken()` and attach it to backend requests as `Authorization: Bearer` |
| Token refresh | The Firebase SDK refreshes automatically (1 hour expiry) |
| Auth state listener | Manage session state reactively with `onAuthStateChanged` |

### 10.3.3 Firestore Direct Access & Real-time Sync

Reading and writing Firestore directly from the client SDK is subject to the
constraints of Security Rules.
In return, real-time sync is obtained **without implementing WebSocket / SSE /
polling yourself**.

| Constraint | Detail |
|------------|--------|
| Firebase Client SDK required | The real-time listener (`onSnapshot`) is available only through the Firebase SDK, not through the REST API |
| Authentication required | `request.auth != null` is a precondition |
| Own data only | The `request.auth.uid == resource.data.uid` pattern is the baseline |
| Write validation | Validate field type and value in Security Rules |
| Listener cost | An active listener is billed as a document read. Watch the cost of large numbers of listeners |
| Offline persistence | The SDK keeps an offline cache. Offline writes sync automatically once back online. Conflicts are last-write-wins |

| Benefit | Detail |
|---------|--------|
| Real-time push (zero infra) | Server-side changes are notified automatically through `onSnapshot`. No WebSocket server needed |
| Optimistic UI | Writes are reflected in the local cache immediately; server confirmation is asynchronous |
| Automatic reconnection | The SDK handles reconnection after a network drop and the delta sync automatically |

> For details, see [infrastructure-2-data.md Section 2.1.5](infrastructure-2-data.md#215-real-time-synchronization).

### 10.3.4 Cloud Storage Upload

| Constraint | Detail |
|------------|--------|
| Firebase Storage SDK | Client-side upload with resumable upload support |
| Security Rules | Restrict which users may upload, plus file size and content type |
| CORS | The bucket needs CORS configuration ([Section 9.4.2](infrastructure-9-network.md#942-cloud-storage-cors)) |

### 10.3.5 Environment Variables

| Prefix | Exposure |
|--------|----------|
| `NEXT_PUBLIC_*` | Included in the client bundle (public) |
| Anything else | Server-side only (SSR / API routes) |

Do not give a sensitive value the `NEXT_PUBLIC_` prefix.
Firebase config (apiKey, authDomain, and so on) is fine to expose publicly.

## 10.4 Mobile Constraints (iOS / Android)

### 10.4.1 Authentication

| Constraint | Detail |
|------------|--------|
| Firebase Auth SDK | Native SDK (iOS: FirebaseAuth, Android: firebase-auth) |
| ID Token | Obtain it with `getIDToken()` and send it to the backend |
| Token refresh | Managed automatically by the SDK |
| Biometric auth | Independent of Firebase Auth. Implemented with the local authentication framework |

### 10.4.2 Firestore Real-time Sync & Offline Support

The mobile SDK enables the real-time listener (`onSnapshot`) and offline
persistence by default.
Server-side changes reach the device in real time with no WebSocket / SSE /
polling implementation.

| Benefit | Detail |
|---------|--------|
| Real-time push | Receive server changes automatically with `onSnapshot`. No push infrastructure needed |
| Offline read | Reads can be served from the cache (no network needed) |
| Offline write | Queued locally and synced automatically once back online |
| Optimistic UI | Writes are reflected locally right away |

| Constraint | Detail |
|------------|--------|
| Firebase Client SDK required | The real-time listener is available only through the Firebase SDK |
| Conflict resolution | Last-write-wins (the server timestamp takes precedence) |
| Cache size | Default 100 MiB (configurable) |
| Listener cost | An active listener is billed as a document read |

The UI design must make the pending state of offline writes visible to the user.

### 10.4.3 API Client Generation

Generate the mobile API client automatically from the backend OpenAPI spec.

| Platform | Generator | Output |
|----------|-----------|--------|
| iOS | OpenAPI Generator (Swift5) | Swift Codable models + URLSession client |
| Android | OpenAPI Generator (Kotlin) | Kotlin data classes + Retrofit client |

Do not edit the generated code by hand. Regenerate it when the backend spec changes.

### 10.4.4 Push Notification (Optional)

| Service | Detail |
|---------|--------|
| Firebase Cloud Messaging (FCM) | Cross-platform push notification |
| Token management | Store the device token in Firestore and send from the backend through the FCM API |

### 10.4.5 Binary Size & Startup

| Constraint | Detail |
|------------|--------|
| Firebase SDK size | iOS: ~10 MiB, Android: ~5 MiB (Auth + Firestore + Storage) |
| Lazy initialization | Call FirebaseApp.configure() exactly once at app startup |
| Network dependency | The first launch requires a connection to Firebase Auth / Firestore |

## 10.5 Constraints Summary Matrix

| Constraint | Backend | Frontend | Mobile |
|------------|---------|----------|--------|
| Stateless execution | Required | Required (Cloud Run) | N/A |
| Idempotency | Required (Tasks/Pub/Sub callback) | N/A | N/A |
| Firebase Auth token verification | Required | N/A (SDK handles) | N/A (SDK handles) |
| Firebase Auth token acquisition | N/A | Required | Required |
| Firestore Security Rules | Bypass (Admin SDK) | Subject to rules | Subject to rules |
| Firestore real-time sync | N/A (write side) | `onSnapshot` (Firebase SDK required) | `onSnapshot` (Firebase SDK required) |
| Firestore offline support | N/A | Optional | Default enabled |
| Health check endpoint | Required | Required | N/A |
| Structured logging (JSON) | Required | Recommended | N/A |
| Container port | 8080 | 3000 | N/A |
| Cold start optimization | Required | Required | N/A |
| API client generation | Source (OpenAPI spec) | Consumer (TypeScript) | Consumer (Swift/Kotlin) |
| CORS handling | Server-side config | N/A | N/A |
| dotenvx | Build-time injection | Build-time injection | N/A (native config) |
