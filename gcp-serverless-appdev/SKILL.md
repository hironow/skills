---
name: gcp-serverless-appdev
description: >
  GCP serverless application development guide covering Cloud Run, Firestore,
  Cloud Tasks, Pub/Sub, Firebase Auth, Cloud Functions, Eventarc, and Cloud Scheduler:
  service selection, implementation patterns, and gcloud-based deployment.
  Use when the user is designing or writing the application side — mentions "GCPで開発",
  "Cloud Runで", "Firestoreに", "新しいGCPプロジェクト", scaffolding a GCP app, choosing
  between Cloud Tasks and Pub/Sub, Firestore data modeling, Firebase Auth integration,
  deploying a service with gcloud, or comparing GCP services with AWS/Azure equivalents,
  including cross-cloud migration discussions.
  Not for Terraform/OpenTofu — any .tf, `tofu`, "tfファイル", or "インフラをコード化"
  request is gcp-serverless-tf.
---

# GCP Serverless Application Development Guide

This skill supports application development on GCP serverless services, based on the
bundled infrastructure selection documents (`references/docs/`).

## Knowledge Base

The details of the infrastructure selection are collected in the documents below.
Read them whenever an implementation decision is unclear — GCP service specifications
and limits are easy to get wrong from general knowledge alone, so it matters to confirm
them against the bundled documents.

| Doc | File | Content |
|-----|------|---------|
| Index | `references/docs/infrastructure.md` | Overall structure, service list, environment strategy |
| Compute | `references/docs/infrastructure-1-compute.md` | Cloud Run, Cloud Functions, Docker build |
| Data | `references/docs/infrastructure-2-data.md` | Firestore, Spanner, Neo4j, Qdrant, ES, Storage |
| Async | `references/docs/infrastructure-3-async.md` | Cloud Tasks, Pub/Sub, Eventarc, Scheduler |
| CI/CD | `references/docs/infrastructure-4-cicd.md` | GitHub Actions, Cloud Build, Artifact Registry |
| Auth | `references/docs/infrastructure-5-auth.md` | Firebase Auth, WIF, Secret Manager |
| Observability | `references/docs/infrastructure-6-observability.md` | Sentry, structlog, Cloud Monitoring |
| Ops | `references/docs/infrastructure-7-ops.md` | Local dev, emulators, deploy, scaling |
| Incident | `references/docs/infrastructure-8-incident.md` | Rollback, maintenance, backup, recovery |
| Network | `references/docs/infrastructure-9-network.md` | Ingress, TLS, CORS, DDoS, VPC |
| App Constraints | `references/docs/infrastructure-10-app-constraints.md` | Backend/Frontend/Mobile development constraints |
| Alternatives | `references/docs/infrastructure-11-gcp-alternatives.md` | Comparison between GCP services and selection rationale |

## Core Principles

1. **Region**: all services fixed to `asia-northeast1` (Tokyo)
2. **Tier**: separate Core (required for the initial release) from Extension (optional)
3. **Idempotency**: delivery is at-least-once, so implement every async handler idempotently
4. **Stateless**: Cloud Run is stateless — design without in-memory state
5. **Serverless first**: prefer Cloud Run over GKE
6. **Managed first**: prefer managed services over self-hosted ones

## Phase Guide

### Phase 1: Project Scaffold

When starting a new project, read `references/scaffold.md` to check the project
structure and the setup procedure.

Main scaffold targets:
- **monorepo structure**: `backend/` + `frontend/` + `emulator/`
- **Backend**: Python (FastAPI + uvicorn), dependencies managed with uv, multi-stage Dockerfile
- **Frontend**: Next.js (standalone), multi-stage Dockerfile
- **Emulator**: Firebase Emulator Suite started via docker-compose.yaml
- **Task runner**: tasks defined in a justfile
- **CI/CD**: GitHub Actions workflow
- **Firestore**: security rules + indexes
- **Environment**: encrypted management with dotenvx

### Phase 2: Feature Development

When implementing a feature, decide in this order:

1. **Data model design**: which data store to use?
   - Read `references/decision-tree.md` to check the selection flow
   - Firestore (Core) / Spanner, Neo4j, Qdrant, ES (Extension)

2. **Sync vs async**: should this processing return synchronously or be pushed to an async path?
   - An immediate response is required -> synchronous processing in a Cloud Run Service
   - 1:1 processing that must reliably complete -> Cloud Tasks
   - 1:N fan-out -> Pub/Sub
   - GCP service event -> Eventarc

3. **Direct from client vs through the server**: does the client access Firestore directly?
   - Read-heavy + real-time -> Firestore onSnapshot (Client SDK)
   - Write + business logic -> through the Backend API

4. **Implementation pattern**: read `references/patterns.md` to check the pseudocode

### Phase 3: Deploy & Operations

Procedure for deployment and operations:

1. **Container build**: multi-stage Docker build -> push to Artifact Registry
2. **Cloud Run deploy**: `gcloud run deploy` with revision-based rollback
3. **Firestore deploy**: `firebase deploy` for security rules + indexes
4. **Monitoring setup**: Sentry + Cloud Logging + Cloud Monitoring SLI/SLO
5. **Incident response**: the flow of rollback -> investigate -> fix -> verify

### Phase 4: Architecture Decisions

When a technology choice is unclear:
- Read `references/docs/infrastructure-11-gcp-alternatives.md` to check the comparison structure
- Cloud Run vs GKE -> almost always Cloud Run. Consider GKE only for stateful workloads
- Firestore vs Cloud SQL -> Firestore if the Client SDK or real-time is required
- Cloud Tasks vs Pub/Sub -> Tasks for explicit 1:1, Pub/Sub for 1:N fan-out
- Services vs Jobs vs Worker Pools -> Services for an HTTP endpoint, Jobs for batch, Worker Pools for a pull consumer

## How to Use References

Read the reference files as needed. There is no need to read all of them at once.

| Situation | Read this |
|-----------|-----------|
| Creating a new project | `references/scaffold.md` |
| Technology choice / architecture decision | `references/decision-tree.md` |
| Concrete implementation method | `references/patterns.md` |
| Checking detailed constraints / specifications | the matching `references/docs/infrastructure-*.md` |

## Using the google-dev-knowledge MCP

GCP services are updated frequently, so the information in the bundled documents may be
out of date. If the `google-dev-knowledge` MCP server is available, it can supplement
them with the latest information from the official documentation. The division of roles
is that the bundled documents provide the policy and the structure, while the MCP
provides the latest specifications and numbers.

**Flow when the MCP is available:**
1. Read the bundled documents to check the policy and patterns
2. For the main services included in the answer, search the latest official documentation with `mcp__google-dev-knowledge__search_documents` (at least once)
3. Fetch the relevant documents from the search results with `mcp__google-dev-knowledge__get_documents` and check the details
4. If the bundled documents and the official documentation differ, the official documentation wins

Situations where searching with the MCP is especially effective:
- When mentioning a service quota / limit / pricing
- When stating API parameters or default values
- When explaining a new feature (Worker Pools, Firestore Pipeline, etc.)
- When comparing concrete specs in a cross-cloud comparison

**When the MCP is not available:**
Work from the bundled documents only. However, present the setup guidance in
`references/mcp-setup.md` at the end of the answer, so that the user can also consult
the latest official documentation from then on.

## Cross-Cloud Comparison

When asked for a comparison with other clouds:

| GCP Service | AWS Equivalent | Azure Equivalent |
|-------------|---------------|-----------------|
| Cloud Run | ECS Fargate / App Runner | Container Apps |
| Firestore | DynamoDB | Cosmos DB |
| Cloud Tasks | SQS (FIFO) | Queue Storage |
| Pub/Sub | SNS + SQS | Service Bus |
| Cloud Functions | Lambda | Functions |
| Firebase Auth | Cognito | Azure AD B2C |
| Cloud Spanner | Aurora (global) | Cosmos DB (relational) |
| Eventarc | EventBridge | Event Grid |
| Cloud Scheduler | EventBridge Scheduler | Logic Apps |
| Secret Manager | Secrets Manager | Key Vault |
| Artifact Registry | ECR | Container Registry |

When comparing, explain "why this GCP service was chosen" based on
`references/docs/infrastructure-11-gcp-alternatives.md`.
