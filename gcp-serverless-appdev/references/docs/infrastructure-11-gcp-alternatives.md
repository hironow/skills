# 11. GCP Service Alternatives & Selection Rationale

This document records, in a side-by-side form, why a particular service was
selected when GCP offers several options in the same category.
It complements the "Why not" behind the selections made in Sections 1 through 10.

> **Based on the GCP service lineup as of 2026-03.**

## 11.1 Compute: Cloud Run vs GKE vs Cloud Functions

### 11.1.1 Cloud Run Resource Types (2025 onward)

Cloud Run currently offers **three resource types**.

| Resource Type | Model | Endpoint | Scaling | Use Case |
|---------------|-------|----------|---------|----------|
| **Services** | Request-driven | HTTPS endpoint (assigned automatically) | Request-based autoscaling, scale-to-zero | API server, Web frontend, Webhook |
| **Jobs** | Run-to-completion | None | Parallel tasks (up to 10,000) | Batch processing, DB migration, scheduled script |
| **Worker Pools** | Continuous background | None (no HTTP endpoint needed) | Manual / CREMA (external-metric based) | Pull-based consumer (Pub/Sub pull, Kafka, RabbitMQ) |

#### Characteristics of Worker Pools

| Property | Detail |
|----------|--------|
| Pricing | CPU/memory up to **40% cheaper** than Services |
| Autoscaling | External-metric based scaling through CREMA (Cloud Run External Metrics Autoscaling) |
| CREMA sources | Pub/Sub queue depth, Kafka consumer lag, Prometheus metrics, GitHub Runner |
| GPU support | Supported (no autoscale; billed continuously while the instance runs) |
| Min instances | Manual: at least 1 instance / **CREMA: scale-to-zero possible** |

> **Ref**: [Cloud Run Overview](https://docs.cloud.google.com/run/docs/overview/what-is-cloud-run),
> [Worker Pools](https://docs.cloud.google.com/run/docs/deploy-worker-pools),
> [CREMA Autoscaling](https://docs.cloud.google.com/run/docs/configuring/workerpools/crema-autoscaling)

### 11.1.2 Cloud Run vs GKE

| Aspect | Cloud Run | GKE (Google Kubernetes Engine) |
|--------|-----------|-------------------------------|
| Management | Fully managed (infrastructure invisible) | Cluster management required (K8s knowledge needed even in Autopilot mode) |
| Scaling | Request-based autoscale, scale-to-zero | Pod autoscaler (HPA/VPA), node autoscaler |
| Stateful workload | Not possible (stateless only) | Possible (PersistentVolume, StatefulSet) |
| Networking | Simplified (automatic HTTPS, automatic load balancing) | Full control (Ingress, Service Mesh, Network Policy) |
| Cost model | Per-request / per-instance-second | Cluster fee + node fee (always running) |
| Cold start | Yes (with a scale-to-zero configuration) | No (nodes always running) |
| GPU | Supported through Worker Pools | Full GPU support (scheduling, time-sharing) |
| Custom runtime | Container image (any language) | Container image (any language) + sidecar pattern |
| Min cost | 0 (scale-to-zero) | Control plane fee (from $74.40/month) |

**Selection: Cloud Run**

| Rationale |
|-----------|
| Cloud Run Services is the best fit for a stateless API server / web frontend |
| Cost optimization through scale-to-zero (when traffic is low in the early phase) |
| No infrastructure management (no K8s operational knowledge required) |
| A pull-based consumer can be handled with Worker Pools |
| Batch processing can be handled with Jobs |

**When GKE should be considered**:
- Stateful workload (DB on K8s, ML training with checkpoint)
- A complex Service Mesh / Network Policy is required
- The sidecar pattern with multi-container pods is mandatory
- Always-on, high-throughput workloads (cold start unacceptable)

### 11.1.3 Cloud Run Services vs Cloud Functions (Cloud Run functions)

> **Note**: Since August 2024, Cloud Functions (2nd gen) has been renamed
> **Cloud Run functions** and internally runs on Cloud Run. Billing has also been
> unified with Cloud Run.

| Aspect | Cloud Run Services | Cloud Run functions (formerly Cloud Functions) |
|--------|--------------------|------------------------------------------|
| Deploy unit | Container image | Source code (per function) |
| Runtime | Any (Docker image) | Limited (Node.js, Python, Go, Java, .NET, Ruby, PHP) |
| Trigger | HTTP request | HTTP + Eventarc event triggers |
| Concurrency | Configurable (up to 1000) | 1 instance = 1 concurrent request (default) |
| Startup | Container startup | Function framework startup |
| Build | Your own Dockerfile | Source-based build (automatic) |

**Selection: Cloud Run Services (primary) + Cloud Functions (supplementary)**

| Component | Service | Rationale |
|-----------|---------|-----------|
| Backend API | Cloud Run Services | Multiple endpoints, concurrency control, custom container |
| Frontend (Next.js) | Cloud Run Services | Custom Node.js runtime, standalone build |
| Event handler (lightweight) | Cloud Functions | Eventarc trigger, single function, simplicity of source deploy |

## 11.2 Database: Firestore vs Cloud SQL vs Cloud Spanner

### 11.2.1 Three-Way Comparison

| Aspect | Firestore | Cloud SQL | Cloud Spanner |
|--------|-----------|-----------|---------------|
| Model | Document (NoSQL) | Relational (SQL) | Relational (SQL) + horizontal scale |
| Schema | Flexible (schema-less) | Strict (DDL) | Strict (DDL) |
| Consistency | Strong (all queries) | Strong (single instance) | External consistency (global) |
| Scaling | Automatic (serverless) | Vertical (instance size) | Horizontal (add nodes) |
| Max size | Several TB (recommended) | Several TB (depends on instance) | PB scale |
| Serverless | Fully serverless | Instance management required | Serverless mode available |
| Client SDK | Firebase SDK (real-time sync) | None | None |
| Offline support | Yes (Client SDK) | None | None |
| Real-time listener | `onSnapshot` | None (polling required) | None (Change Streams are limited) |
| Security Rules | Yes (controls direct client access) | None (server-side only) | None (server-side only) |
| Transaction | Max 500 docs/tx | Full ACID | Full ACID (distributed) |
| Min cost | 0 (free tier available) | Cost of an always-running instance | Node cost or the serverless minimum |

### 11.2.2 Selection: Firestore (Core)

| Rationale |
|-----------|
| Real-time sync through the Client SDK (no need to implement WebSocket/SSE/polling yourself) |
| Offline persistence (works on Mobile/Web even when the network drops) |
| Direct client access control through Security Rules (reads/writes that can bypass the backend) |
| Fully serverless (no instance management, equivalent to scale-to-zero) |
| Native integration with Firebase Auth |
| Flexible schema (an advantage for rapid iteration in early development) |

**When Cloud SQL should be considered**:
- Migrating an existing RDB schema / ORM
- Complex JOINs are frequently required
- The PostgreSQL / MySQL ecosystem (extensions, tooling) is mandatory
- The application is server-side only (no client SDK needed)

**When Cloud Spanner should be considered** (already selected as an Extension):
- Large-scale workloads that need horizontal scale
- Strong consistency across regions is required
- A strict schema plus distributed ACID transactions are mandatory

## 11.3 Async: Cloud Tasks vs Cloud Pub/Sub

### 11.3.1 Difference in Design Philosophy

| Aspect | Cloud Tasks | Cloud Pub/Sub |
|--------|-------------|---------------|
| Invocation model | **Explicit** (the publisher specifies the endpoint) | **Implicit** (the publisher does not know the subscribers) |
| Delivery pattern | **1:1** (point-to-point) | **1:N** (fan-out, 1 topic -> N subscriptions) |
| Pull subscription | None | Yes |
| Push subscription | HTTP callback (the only delivery method) | HTTP push / pull / BigQuery / Cloud Storage |
| Scheduled delivery | Yes (future execution, up to 30 days ahead) | None |
| Rate limiting | Queue-level dispatch rate control (max 500 qps/queue) | Client-side flow control |
| Deduplication | Task name + tombstone_ttl | None (implement it on the subscriber side) |
| Message ordering | Best-effort | Guaranteed through an ordering key |
| Dead-letter | None (implement it yourself) | A DLQ topic can be configured |
| Max message size | 1 MiB | 10 MiB |
| Max retention | task_ttl 31 days (default) | 31 days (configurable) |

### 11.3.2 Choosing Between Them

```
+-------------------------------------------+
|          Async Processing Decision         |
+-------------------------------------------+
     |
     +--> 1:1 delivery?
     |     |
     |     +--> Yes: need rate control / scheduling?
     |     |          |
     |     |          +--> Yes: Cloud Tasks
     |     |          +--> No:  Cloud Tasks (simpler) or Pub/Sub push
     |     |
     |     +--> No (1:N fan-out): Cloud Pub/Sub
     |
     +--> Pull-based consumer?
     |     |
     |     +--> Yes: Cloud Pub/Sub + Cloud Run Worker Pools
     |
     +--> GCP service event reaction?
           |
           +--> Eventarc (internal: Pub/Sub transport)
```

Legend:
- 1:1 delivery: one-to-one delivery
- 1:N fan-out: one-to-many delivery
- Rate control: control of the flow rate
- Pull-based consumer: a consumer that pulls messages
- GCP service event reaction: reacting to GCP service events

### 11.3.3 Pattern for Using Cloud Tasks and Pub/Sub Together

This infrastructure uses Cloud Tasks and Pub/Sub **together**.

| Pattern | Service | Example |
|---------|---------|---------|
| Asynchronous 1:1 processing (guaranteed completion) | Cloud Tasks | Sending email, external API calls, heavy computation |
| Event fan-out (1:N) | Pub/Sub | User creation -> notification + analytics + audit |
| GCP event trigger | Eventarc (Pub/Sub) | Firestore write -> processing pipeline |
| Pull-based consumer | Pub/Sub + Worker Pools | Batch processing of a large volume of messages |
| Scheduled execution | Cloud Scheduler -> Cloud Tasks or Pub/Sub | Daily report, cleanup job |

## 11.4 Compute Mode: Cloud Run Services vs Jobs vs Worker Pools

### 11.4.1 Three-Way Comparison

| Aspect | Services | Jobs | Worker Pools |
|--------|----------|------|-------------|
| Trigger | HTTP request | Manual / Schedule / Workflow | Autonomous (pull-based) |
| Endpoint | HTTPS URL (assigned automatically) | None | None |
| Duration | Request timeout (max 3600s) | Max 168 hours (7 days; >24h is Preview) | Unlimited (continuous) |
| Scaling | Request-based autoscale | Specify the number of parallel tasks (max 10,000) | Manual / CREMA |
| Scale-to-zero | Possible | N/A (ends when execution completes) | CREMA: possible / Manual: not possible (min 1) |
| Concurrency | Configurable (max 1000/instance) | 1 task = 1 instance | Defined by the application |
| Cost | Per-request or per-instance | Billed by execution time | Billed by instance runtime (-40% vs Services) |
| Retry | Implemented by the application | Task-level retry | Implemented by the application |

### 11.4.2 Selection Mapping

| Workload | Resource Type | Rationale |
|----------|--------------|-----------|
| Backend API server | Services | HTTP endpoint, request-based scaling |
| Frontend (Next.js SSR) | Services | HTTP endpoint, concurrency |
| Cloud Tasks callback | Services | Receiving the HTTP callback |
| Pub/Sub push handler | Services | HTTP push endpoint |
| DB migration | Jobs | Run-to-completion, retry on failure |
| Scheduled batch script | Jobs | Cloud Scheduler trigger, completion semantics |
| Pub/Sub pull consumer | Worker Pools | Pull-based, continuous processing, cost efficiency |
| Kafka consumer | Worker Pools | Pull-based, CREMA autoscaling |

> Adopting Worker Pools is **optional** at this point.
> Pub/Sub can be handled with a push subscription plus Cloud Run Services.
> Introduce Worker Pools if a switch to pull-based becomes necessary.

## 11.5 Event-Driven: Eventarc vs Pub/Sub Direct vs Cloud Tasks

| Aspect | Eventarc | Pub/Sub (direct) | Cloud Tasks |
|--------|----------|-------------------|-------------|
| Event source | GCP service events (Firestore, Storage, Audit Log) | Published from application code | Enqueued from application code |
| Configuration | Declarative (trigger definition) | Create topic + subscription | Create queue + task |
| Transport | Pub/Sub (internal) | Pub/Sub native | HTTP callback |
| Format | CloudEvents v1.0 | Free-form (attribute + data) | HTTP request body |
| Use case | Reacting to changes in GCP services | Event notification between applications | 1:1 asynchronous processing that must complete reliably |

**Selection: all three used together**

| Trigger Source | Service |
|----------------|---------|
| Firestore document change | Eventarc -> Cloud Run / Cloud Functions |
| Cloud Storage object upload | Eventarc -> Cloud Run / Cloud Functions |
| Application-generated event (fan-out) | Pub/Sub |
| Application-generated task (1:1, guaranteed completion) | Cloud Tasks |

## 11.6 Database Extensions: Managed vs Self-Hosted

This compares the options available on GCP for Extension tier data stores.

### 11.6.1 Graph Database

| Aspect | Neo4j AuraDB (managed) | Neo4j on GKE (self-hosted) | Dgraph |
|--------|----------------------|---------------------------|--------|
| Management | Fully managed | Cluster operation required | Self-hosted or Dgraph Cloud |
| Backup | Automatic daily snapshot | Manual (`neo4j-admin dump`) | Manual or managed |
| Scaling | Plan upgrade | Add nodes (manual) | Sharding |
| Cost | Subscription | GKE node + storage | Subscription or infrastructure cost |

**Selection: Neo4j AuraDB** — it minimizes the operational load so effort stays
on core development.

### 11.6.2 Vector Search Engine

| Aspect | Qdrant Cloud (managed) | Qdrant on GKE | Firestore Vector Search | Vertex AI Vector Search |
|--------|----------------------|---------------|------------------------|------------------------|
| Management | Fully managed | Self-hosted | Serverless (built into Firestore) | Fully managed |
| Max dimensions | 65536 | Same as left | 2048 | No limit |
| Scale | Sharding + replication | Manual | Firestore auto-scale | Automatic |
| Filtering | Payload filter (feature-rich) | Same as left | Combined with Firestore filters | Metadata filter |
| Cost | Subscription | GKE cost | Billed by Firestore reads | Billed by index + query |

**Selection: Qdrant Cloud (large scale) / Firestore Vector Search (small to medium scale)**

- Small to medium scale (tens of thousands to hundreds of thousands of vectors): Firestore native vector search is sufficient
- Large scale (millions and above): migrate to Qdrant Cloud

### 11.6.3 Full-Text Search

| Aspect | Elastic Cloud (managed) | Elasticsearch on GKE | Cloud Firestore (Enterprise Pipeline) |
|--------|------------------------|---------------------|--------------------------------------|
| Management | Fully managed | Cluster operation required | Serverless (built into Firestore) |
| Japanese morphological analysis | Kuromoji analyzer | Same as left | Not supported (regex only) |
| Aggregation | Full aggregation | Same as left | Limited |
| Scale | Managed sharding | Manual sharding | Firestore auto-scale |

**Selection: Elastic Cloud** — when Japanese full-text search is required.
Firestore Enterprise Pipeline operations support regex, but not morphological analysis.

## 11.7 Selection Summary

| Category | Selected | Not Selected | Key Differentiator |
|----------|----------|--------------|--------------------|
| Compute (primary) | Cloud Run Services | GKE | Serverless, scale-to-zero, no operations |
| Compute (event) | Cloud Functions | — | Eventarc trigger, source deploy |
| Compute (batch) | Cloud Run Jobs | — | Run-to-completion, max 24h |
| Compute (pull consumer) | Cloud Run Worker Pools (optional) | GKE | Managed, -40% cost, CREMA |
| Database (primary) | Firestore | Cloud SQL | Client SDK, real-time sync, serverless |
| Database (relational) | Cloud Spanner [Extension] | Cloud SQL | Horizontal scale, distributed ACID |
| Async (1:1) | Cloud Tasks | — | Explicit invocation, rate control, scheduling |
| Async (1:N) | Pub/Sub | — | Fan-out, DLQ, pull subscription |
| Async (GCP event) | Eventarc | — | Declarative, CloudEvents |
| Graph DB | Neo4j AuraDB [Extension] | Self-hosted | Managed, auto backup |
| Vector search | Qdrant Cloud [Extension] | Vertex AI Vector Search | Performance, filtering, cost |
| Full-text search | Elastic Cloud [Extension] | Firestore Pipeline | Japanese morphological analysis, aggregation |
