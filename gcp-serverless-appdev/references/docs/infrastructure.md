# Infrastructure Selection

This set of documents records the infrastructure selection results required to release the service.

**Cloud Provider**: Google Cloud Platform (GCP)
**Primary Region**: `asia-northeast1` (Tokyo)

## Architecture Overview

### Core (Initial Release Required)

```
+--------------------+       +--------------------+       +------------------+
|   Frontend         |       |   Backend          |       | Cloud Functions  |
|   (Cloud Run)      |<----->|   (Cloud Run)      |       | (Event Trigger)  |
+--------------------+       +----+------+--------+       +--------+---------+
         |                        |      |                          |
         v                        v      v                          v
+--------------------+   +--------+--+  +----------+     +---------+--------+
|   Firebase Auth    |   | Firestore |  | Cloud    |     | Firebase Auth    |
|                    |   |           |  | Storage  |     | Events / Audit   |
+--------------------+   +-----+-----+  +----------+     +------------------+
                               |
                    +----------+----------+
                    |          |          |
              +-----v----+ +--v-------+ +v-----------+
              |Cloud Tasks| | Pub/Sub  | | Eventarc   |
              +-----+-----+ +----------+ +------------+
                    |
              +-----v-------+
              | Scheduler   |
              +-------------+
```

### Extension (Optional - GraphRAG/RAG etc.)

```
+--------+  +--------+  +--------+  +----------+
|Spanner |  | Neo4j  |  | Qdrant |  | Elastic  |
|(PG)    |  |(Graph) |  |(Vector)|  | (Search) |
+--------+  +--------+  +--------+  +----------+
```

Legend:
- Frontend: Web UI application
- Backend: API server / business logic
- Cloud Functions: Lightweight event-driven processing (Go/Python)
- Firebase Auth: Identity provider
- Firestore: Document database (NoSQL)
- Cloud Storage: Object storage
- Cloud Tasks: Async task queue (at-least-once delivery)
- Pub/Sub: Message broker (fan-out capable)
- Eventarc: GCP service event router
- Scheduler: Cron-based scheduled execution
- Spanner (PG): Distributed relational database [Extension]
- Neo4j (Graph): Graph database for relationship traversal [Extension]
- Qdrant (Vector): Vector similarity search engine [Extension]
- Elastic (Search): Full-text search and analytics engine [Extension]

## Document Index

| # | Document | Scope |
|---|----------|-------|
| 1 | [infrastructure-1-compute.md](infrastructure-1-compute.md) | Compute / Container / Hosting |
| 2 | [infrastructure-2-data.md](infrastructure-2-data.md) | Data Persistence / Object Storage / Search |
| 3 | [infrastructure-3-async.md](infrastructure-3-async.md) | Async Processing / Event-Driven / Scheduling |
| 4 | [infrastructure-4-cicd.md](infrastructure-4-cicd.md) | CI/CD Pipeline / Container Registry / Deployment |
| 5 | [infrastructure-5-auth.md](infrastructure-5-auth.md) | Authentication / Authorization / Secrets |
| 6 | [infrastructure-6-observability.md](infrastructure-6-observability.md) | Monitoring / Error Tracking / Logging |
| 7 | [infrastructure-7-ops.md](infrastructure-7-ops.md) | Local Dev / Task Runner / Deploy / Scaling |
| 8 | [infrastructure-8-incident.md](infrastructure-8-incident.md) | Incident Response / Rollback / Maintenance / Backup |
| 9 | [infrastructure-9-network.md](infrastructure-9-network.md) | Network / Ingress / Boundary Defense / TLS |
| 10 | [infrastructure-10-app-constraints.md](infrastructure-10-app-constraints.md) | App Development Constraints (Backend / Frontend / Mobile) |
| 11 | [infrastructure-11-gcp-alternatives.md](infrastructure-11-gcp-alternatives.md) | GCP Service Alternatives & Selection Rationale |

## Region Strategy

Standardize all resources on `asia-northeast1` (Tokyo).

| Resource | Region | Rationale |
|----------|--------|-----------|
| Cloud Run | `asia-northeast1` | Primary compute region |
| Cloud Functions | `asia-northeast1` | Co-located with compute |
| Firestore | `asia-northeast1` | Data locality (policy of fixing to the Japan region) |
| Cloud Spanner [Extension] | `asia-northeast1` | Co-located with compute |
| Artifact Registry (Docker) | `asia-northeast1` | Co-located with compute |
| Artifact Registry (Python) | `asia-northeast1` | Private package registry |
| Cloud Tasks | `asia-northeast1` | Co-located with Cloud Run |
| Cloud Scheduler | `asia-northeast1` | Co-located with Cloud Run |
| Cloud Storage | `asia-northeast1` | Data locality |

## Environment Strategy

| Environment | Branch | GCP Project | Purpose |
|-------------|--------|-------------|---------|
| Local | - | Emulator Suite | Developer workstation |
| Development | `develop` | `{project}-dev` | Integration verification |
| Production | `main` | `{project}-prd` | Live service |

## GCP Services Summary

### Core (Initial Release Required)

| Category | Service | Section |
|----------|---------|---------|
| Compute | Cloud Run | [1.1](infrastructure-1-compute.md#11-application-runtime-cloud-run) |
| Compute | Cloud Functions | [1.2](infrastructure-1-compute.md#12-event-driven-functions-cloud-functions) |
| Data (Document) | Cloud Firestore | [2.1](infrastructure-2-data.md#21-document-database-cloud-firestore) |
| Data (Object) | Cloud Storage | [2.6](infrastructure-2-data.md#26-object-storage-cloud-storage-via-firebase-storage) |
| Async | Cloud Tasks | [3.1](infrastructure-3-async.md#31-task-queue-cloud-tasks) |
| Async | Cloud Pub/Sub | [3.2](infrastructure-3-async.md#32-message-broker-cloud-pubsub) |
| Async | Eventarc | [3.3](infrastructure-3-async.md#33-event-router-eventarc) |
| Async | Cloud Scheduler | [3.4](infrastructure-3-async.md#34-scheduled-execution-cloud-scheduler) |
| CI/CD | GitHub Actions | [4.1](infrastructure-4-cicd.md#41-cicd-platform-github-actions) |
| CI/CD | Cloud Build | [4.2](infrastructure-4-cicd.md#42-container-build-cloud-build) |
| Registry | Artifact Registry | [4.3](infrastructure-4-cicd.md#43-container--package-registry-artifact-registry) |
| Auth | Firebase Authentication | [5.1](infrastructure-5-auth.md#51-user-authentication-firebase-authentication) |
| Secrets | Secret Manager | [5.3](infrastructure-5-auth.md#53-secret-management-google-cloud-secret-manager) |
| Network | Cloud Run ingress / IAM | [9.1](infrastructure-9-network.md#91-public-ingress-cloud-run-default-domain), [9.2](infrastructure-9-network.md#92-ingress-control) |
| Monitoring | Cloud Logging / Monitoring | [6.2](infrastructure-6-observability.md#62-logging-cloud-logging--structlog), [6.3](infrastructure-6-observability.md#63-metrics--alerting-cloud-monitoring) |
| Monitoring | Sentry | [6.1](infrastructure-6-observability.md#61-error-tracking-sentry) |

### Extension (Optional)

| Category | Service | Section | Use Case |
|----------|---------|---------|----------|
| Data (Relational) | Cloud Spanner | [2.2](infrastructure-2-data.md#22-extension-distributed-relational-database-cloud-spanner) | Strict schema, distributed tx |
| Data (Graph) | Neo4j (AuraDB managed) | [2.3](infrastructure-2-data.md#23-extension-graph-database-neo4j) | Entity relationship traversal |
| Data (Vector) | Qdrant (Qdrant Cloud managed) | [2.4](infrastructure-2-data.md#24-extension-vector-search-engine-qdrant) | Semantic search, RAG retrieval |
| Data (Full-text) | Elasticsearch (Elastic Cloud managed) | [2.5](infrastructure-2-data.md#25-extension-full-text-search-engine-elasticsearch) | Full-text search, analytics |
