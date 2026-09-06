# 3. Async Processing / Event-Driven / Scheduling

## 3.1 Task Queue: Cloud Tasks

**Service**: [Google Cloud Tasks](https://cloud.google.com/tasks)

A managed task queue based on HTTP callbacks.
When a task is enqueued, it is delivered to the specified HTTP endpoint with at-least-once delivery.
It has automatic retry with exponential backoff, and within the `task_ttl` window (31 days by default)
it keeps retrying until the target endpoint returns success (2xx).

It suits work that "must succeed at least once, but has to return a response immediately".

### 3.1.1 Key Characteristics

| Property | Detail |
|----------|--------|
| Delivery Guarantee | At-least-once (duplicate execution is possible) |
| Retry | Automatic exponential backoff |
| Task TTL | 31 days by default. Once the TTL is exceeded the task is deleted, dispatched or not |
| Max Attempts | Configurable. Retries stop as soon as either `max_attempts` **or** `max_retry_duration` is reached, whichever comes first |
| Target | HTTP/HTTPS endpoint (Cloud Run service URL) |
| Rate Limiting | Queue-level dispatch rate control |
| Scheduling | Task-level delay (future execution, up to 30 days ahead) |
| Deduplication | Idempotency control through the task name + `tombstone_ttl` (v2 GA: up to 24 hours; v2beta3: configurable, default 1 hour) |
| Max Task Size | 1 MiB (HTTP request body) |

> **Ref**: [Cloud Tasks Queue Configuration](https://cloud.google.com/tasks/docs/configuring-queues),
> [googleapis/queue.proto](https://github.com/googleapis/googleapis/blob/master/google/cloud/tasks/v2beta3/queue.proto)

### 3.1.2 Usage Pattern

```
Client Request --> Backend (Cloud Run)
                    |
                    +--> Enqueue to Cloud Tasks (immediate response to client)
                              |
                              +--> Cloud Tasks calls Backend endpoint (async)
                                      |
                                      +--> Success (2xx): task complete
                                      +--> Failure: retry with backoff (within task_ttl)
                                      +--> task_ttl (31d) expired: task deleted
```

### 3.1.3 Task Lifecycle & Terminal Failure Handling

A Cloud Tasks task is deleted under the following conditions:

1. **`task_ttl` exceeded** (31 days by default): deleted regardless of dispatch state
2. **`max_attempts` reached or `max_retry_duration` exceeded**: retries stop as soon as either one is reached, and the task is deleted once `task_ttl` is reached

Unlike Cloud Pub/Sub, it has no native Dead-Letter Queue (DLQ), so to make sure every task
completes, implement the terminal-handling design below.

#### Retry Configuration

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| task_ttl | 31d (default) | Maximum lifetime of a task |
| Max Attempts | 10 | Enough recovery headroom for transient failures |
| Max Retry Duration | 604800s (7d) | Retry for 7 days even during a long outage |
| Min Backoff | 10s | Prevents retries that come too quickly |
| Max Backoff | 600s | Limits resource consumption during a long outage |
| Max Doublings | 5 | How fast the backoff reaches its ceiling |

#### Failure Detection & Recovery

```
Task Handler (Cloud Run)
  |
  +--> try: execute business logic
  |
  +--> except: (transient error)
  |      +--> return 5xx (Cloud Tasks retries automatically)
  |
  +--> except: (permanent error / retry exhaustion detected)
         |
         +--> 1. Record the failed task in a failure collection in Firestore
         |       (task payload, error detail, timestamp, retry count)
         |
         +--> 2. Increment a Cloud Monitoring custom metric
         |
         +--> 3. Alerting (Sentry / Cloud Monitoring -> notification)
         |
         +--> return 2xx (remove the task from the queue to prevent a backlog)
```

#### Reprocessing Procedure

1. Fetch the failed task from the failure collection in Firestore
2. Fix the root cause
3. Re-enqueue to Cloud Tasks manually or with a script
4. Update the failure record to resolved

#### Notification Conditions

| Condition | Notification |
|-----------|-------------|
| A task reaches retry exhaustion | Sentry alert (immediate) |
| N or more unprocessed records accumulate in the failure collection | Cloud Monitoring alert (daily) |

## 3.2 Message Broker: Cloud Pub/Sub

**Service**: [Google Cloud Pub/Sub](https://cloud.google.com/pubsub)

A globally-distributed message broker. With the publisher-subscriber pattern, it fully decouples
message producers from consumers.
It guarantees at-least-once delivery and retains a message until the subscriber acknowledges it.

Difference from Cloud Tasks: Pub/Sub supports fan-out (1 message -> N subscribers) and has richer
messaging primitives such as message filtering, ordering, and dead-letter queues.
Cloud Tasks, by contrast, is specialized for point-to-point delivery where 1 task = 1 target.

### 3.2.1 Key Characteristics

| Property | Detail |
|----------|--------|
| Delivery Guarantee | At-least-once (push/pull subscription) |
| Fan-out | 1 topic -> N subscriptions |
| Message Retention | Default 7 days (configurable up to 31 days) |
| Ordering | Optional (ordering key) |
| Dead-letter | Configurable dead-letter topic |
| Max Message Size | 10 MiB |
| Filtering | Attribute-based message filtering per subscription |

## 3.3 Event Router: Eventarc

**Service**: [Google Cloud Eventarc](https://cloud.google.com/eventarc)

It declaratively routes events emitted by GCP services to targets such as Cloud Run and Workflows.
You can build a processing pipeline triggered by Firestore document changes,
Cloud Storage object uploads, Cloud Audit Log events, and so on.

Difference from Pub/Sub: Eventarc is a declarative layer specialized for routing GCP service events,
and internally it uses Pub/Sub as its transport. Unlike Pub/Sub, where application code publishes
explicitly, Eventarc captures GCP service events automatically.

### 3.3.1 Key Characteristics

| Property | Detail |
|----------|--------|
| Event Source | GCP services (Firestore, Storage, Audit Log, etc.) |
| Target | Cloud Run, Workflows, Cloud Functions |
| Transport | Pub/Sub (internal) |
| Event Format | CloudEvents v1.0 |
| Filtering | Event type, resource path, etc. |

### 3.3.2 Usage Example

```
Firestore document write
    --> Eventarc trigger (filter: specific collection)
        --> Cloud Run endpoint (process the change)
```

## 3.4 Scheduled Execution: Cloud Scheduler

**Service**: [Google Cloud Scheduler](https://cloud.google.com/scheduler)

A fully-managed cron service. With schedule definitions in unix-cron format, it runs jobs
periodically against an HTTP endpoint, a Pub/Sub topic, or App Engine.

### 3.4.1 Key Characteristics

| Property | Detail |
|----------|--------|
| Schedule Format | unix-cron (5-field) |
| Target Types | HTTP, Pub/Sub, App Engine |
| Timezone | Configurable (e.g., `Asia/Tokyo`) |
| Retry | Configurable retry policy |
| Auth | OIDC token / OAuth token for authenticated endpoints |

## 3.5 Service Selection Guide

| Use Case | Service |
|----------|---------|
| Async processing that must complete (1:1) | Cloud Tasks |
| Event fan-out (1:N) | Cloud Pub/Sub |
| Reacting to GCP service events | Eventarc |
| Scheduled execution (cron) | Cloud Scheduler |
| Periodic publish to a Pub/Sub topic | Cloud Scheduler -> Pub/Sub |

## 3.6 Local Emulation

| Service | Emulator | Port |
|---------|----------|------|
| Cloud Tasks | Firebase Emulator | 9499 |
| Pub/Sub | Firebase Emulator | 9399 |
| Eventarc | Firebase Emulator | 9299 |
