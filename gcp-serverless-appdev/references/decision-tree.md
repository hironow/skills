# Service Decision Trees

技術選択で迷った時に参照するフローチャート。
詳細な仕様は対応する `infrastructure-*.md` を Read して確認する。

## 1. Data Store Selection

```
What kind of data?
|
+--> Document / JSON-like?
|     |
|     +--> Real-time sync needed?
|     |     +--> Yes: Firestore (Client SDK, onSnapshot)
|     |     +--> No: Firestore (Admin SDK)
|     |
|     +--> Strict schema + distributed tx needed?
|           +--> Yes: Cloud Spanner [Extension]
|           +--> No: Firestore
|
+--> Graph / relationship traversal?
|     +--> Neo4j AuraDB [Extension]
|
+--> Vector / semantic search?
|     |
|     +--> Scale: < 100K vectors?
|     |     +--> Firestore Vector Search (find_nearest)
|     |
|     +--> Scale: > 100K vectors?
|           +--> Qdrant Cloud [Extension]
|
+--> Full-text search (Japanese)?
|     +--> Elastic Cloud [Extension]
|
+--> Binary / file storage?
      +--> Cloud Storage (via Firebase Storage)
```

Legend:
- [Extension]: Optional, not required for initial release
- Firestore: Core data store for most use cases
- Cloud Spanner: Only when Firestore's 500 doc/tx limit or schema flexibility is insufficient

## 2. Async Processing Selection

```
Processing pattern?
|
+--> 1:1 delivery (explicit target)?
|     |
|     +--> Need rate control / scheduling?
|     |     +--> Yes: Cloud Tasks
|     |
|     +--> Simple async fire-and-forget?
|           +--> Cloud Tasks (simpler) or Pub/Sub push
|
+--> 1:N fan-out (multiple consumers)?
|     +--> Cloud Pub/Sub
|
+--> GCP service event reaction?
|     |
|     +--> Firestore write / Storage upload / Audit Log?
|           +--> Eventarc -> Cloud Run or Cloud Functions
|
+--> Scheduled / cron?
|     +--> Cloud Scheduler -> Cloud Tasks or Pub/Sub or Cloud Run Jobs
|
+--> Pull-based consumer (high volume)?
      +--> Pub/Sub pull + Cloud Run Worker Pools [optional]
```

Key rules:
- Cloud Tasks: "確実に 1 回は成功させたい" 1:1 処理
- Pub/Sub: "複数の consumer に知らせたい" fan-out
- Eventarc: "GCP サービスの変更に反応したい"
- 全て at-least-once なので handler は冪等に実装

## 3. Compute Selection

```
Workload type?
|
+--> HTTP endpoint (API, Web)?
|     +--> Cloud Run Services
|
+--> Event trigger (Firestore change, Auth event)?
|     +--> Cloud Functions (Cloud Run functions)
|
+--> Batch / run-to-completion?
|     |
|     +--> Duration < 1 hour?
|     |     +--> Cloud Run Jobs
|     |
|     +--> Duration 1-168 hours?
|           +--> Cloud Run Jobs (>24h は Preview)
|
+--> Pull-based continuous consumer?
|     +--> Cloud Run Worker Pools
|
+--> Stateful / complex networking?
      +--> GKE (rare, escalate decision)
```

## 4. Client Access Pattern

```
Who accesses Firestore?
|
+--> Frontend (browser/mobile)?
|     |
|     +--> Read-heavy + real-time needed?
|     |     +--> Direct access via Client SDK + Security Rules
|     |     |    (onSnapshot for real-time, offline support)
|     |
|     +--> Write + business logic?
|           +--> Backend API -> Admin SDK
|           |    (Security Rules: allow write: if false)
|
+--> Backend only?
|     +--> Admin SDK (bypasses Security Rules)
|
+--> Both?
      +--> Pattern A: Client reads via SDK, writes via Backend API
      +--> Pattern B: All access via Backend API (simpler security model)
```

## 5. Authentication Flow

```
Who is the caller?
|
+--> End user (browser / mobile)?
|     |
|     +--> Frontend: Firebase Auth SDK (sign-in UI)
|     +--> Backend: Verify Firebase ID Token
|     |    Authorization: Bearer {idToken}
|     |    firebase_admin.auth.verify_id_token(token)
|
+--> GCP service (Cloud Tasks, Scheduler, Pub/Sub)?
|     +--> OIDC Token verification
|     |    Cloud Run: --no-allow-unauthenticated + IAM roles/run.invoker
|
+--> CI/CD (GitHub Actions)?
|     +--> Workload Identity Federation (no long-lived keys)
|
+--> Service-to-service (Cloud Run -> Cloud Run)?
      +--> OIDC Token
      |    metadata server -> ID token -> Authorization header
```

## 6. Environment & Secrets

```
What kind of secret/config?
|
+--> Runtime secret (API key, DSN, project config)?
|     +--> dotenvx (SSOT for runtime secrets)
|     |    .env (encrypted, committed)
|     |    .env.keys (encryption key, gitignored)
|
+--> Build-time secret (CI/CD)?
|     +--> GitHub Actions secrets or Secret Manager
|
+--> GCP service account key?
|     +--> DO NOT create long-lived keys
|     +--> Use Workload Identity Federation
|
+--> Feature flag / maintenance mode?
      +--> Firebase Remote Config
```

## 7. Database Query Capability Check

Firestore で実現可能かの確認フロー:

```
Query requirement?
|
+--> Equality filter (==)?
|     +--> Unlimited fields -> OK
|
+--> Inequality / range filter?
|     +--> Up to 10 fields -> OK (composite index needed)
|     +--> > 10 fields -> Consider restructuring data model
|
+--> Full-text search (Japanese)?
|     +--> Firestore: Not supported natively
|     +--> Use Elastic Cloud [Extension]
|
+--> Array contains?
|     +--> 1 per query -> OK
|
+--> in / not-in?
|     +--> in: max 30 values -> OK
|     +--> not-in: max 10 values -> OK
|
+--> Aggregation (count, sum, avg)?
|     +--> Standard: Server-side aggregation -> OK
|     +--> Enterprise: Pipeline operations (180+ features) -> Enhanced
|
+--> Complex JOIN-like query?
|     +--> Firestore: No native JOIN
|     +--> Option 1: Denormalize data
|     +--> Option 2: Multiple queries + client-side join
|     +--> Option 3: Cloud Spanner [Extension]
|
+--> Vector similarity search?
|     +--> find_nearest (max 2048 dims, max 1000 results) -> OK
|
+--> Geo proximity search?
      +--> lat/lng range query (recommended) -> OK
      +--> Geohash (legacy) -> OK but less efficient
```
