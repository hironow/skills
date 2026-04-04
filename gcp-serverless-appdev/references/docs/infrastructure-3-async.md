# 3. Async Processing / Event-Driven / Scheduling

## 3.1 Task Queue: Cloud Tasks

**Service**: [Google Cloud Tasks](https://cloud.google.com/tasks)

HTTP callback 方式の managed task queue。
Task を enqueue すると、指定した HTTP endpoint に対して at-least-once delivery で配信する。
Automatic retry with exponential backoff を備え、`task_ttl` (デフォルト 31 日) の期間内は
target endpoint が成功 (2xx) を返すまで再試行を継続する。

「確実に一度は成功させたいが、即座にレスポンスを返す必要がある」処理に適する。

### 3.1.1 Key Characteristics

| Property | Detail |
|----------|--------|
| Delivery Guarantee | At-least-once (重複実行の可能性あり) |
| Retry | Automatic exponential backoff |
| Task TTL | デフォルト 31 日。TTL 超過で dispatch 有無に関わらず task 削除 |
| Max Attempts | 設定可能。`max_attempts` **または** `max_retry_duration` のいずれかに先に到達した時点で retry 停止 |
| Target | HTTP/HTTPS endpoint (Cloud Run service URL) |
| Rate Limiting | Queue-level dispatch rate control |
| Scheduling | Task-level delay (future execution, 最大 30 日先) |
| Deduplication | Task name + `tombstone_ttl` による冪等性制御 (v2 GA: 最大 24 時間、v2beta3: 設定可能 default 1 時間) |
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
                                      +--> Failure: retry with backoff (task_ttl 内)
                                      +--> task_ttl (31d) expired: task deleted
```

### 3.1.3 Task Lifecycle & Terminal Failure Handling

Cloud Tasks の task は以下の条件で削除される:

1. **`task_ttl` 超過** (デフォルト 31 日): dispatch 状態に関わらず削除
2. **`max_attempts` 到達 または `max_retry_duration` 超過**: いずれか先に到達した時点で retry 停止、その後 `task_ttl` 到達で削除

Cloud Pub/Sub と異なり native Dead-Letter Queue (DLQ) を持たないため、
確実に全 task を完了させるには、以下の終端処理設計を実装する。

#### Retry Configuration

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| task_ttl | 31d (default) | Task の最大生存期間 |
| Max Attempts | 10 | 一時障害の十分な回復猶予 |
| Max Retry Duration | 604800s (7d) | 長期障害でも 7 日間は retry |
| Min Backoff | 10s | 短すぎる retry の抑止 |
| Max Backoff | 600s | 長時間障害時のリソース消費抑制 |
| Max Doublings | 5 | Backoff 上限への到達速度 |

#### Failure Detection & Recovery

```
Task Handler (Cloud Run)
  |
  +--> try: execute business logic
  |
  +--> except: (transient error)
  |      +--> return 5xx (Cloud Tasks が自動 retry)
  |
  +--> except: (permanent error / retry exhaustion detected)
         |
         +--> 1. Failed task を Firestore の failure collection に記録
         |       (task payload, error detail, timestamp, retry count)
         |
         +--> 2. Cloud Monitoring custom metric を increment
         |
         +--> 3. Alerting (Sentry / Cloud Monitoring -> notification)
         |
         +--> return 2xx (task を queue から除去し、滞留を防止)
```

#### 再処理手順

1. Firestore の failure collection から failed task を取得
2. Root cause を修正
3. 手動または script で Cloud Tasks に再 enqueue
4. Failure record を resolved に更新

#### 通知条件

| Condition | Notification |
|-----------|-------------|
| Task が retry exhaustion に到達 | Sentry alert (immediate) |
| Failure collection に未処理 record が N 件以上滞留 | Cloud Monitoring alert (daily) |

## 3.2 Message Broker: Cloud Pub/Sub

**Service**: [Google Cloud Pub/Sub](https://cloud.google.com/pubsub)

Globally-distributed message broker。Publisher-Subscriber pattern で、
message producer と consumer を完全に decouple する。
At-least-once delivery を保証し、subscriber 側が ack するまで message を保持する。

Cloud Tasks との違い: Pub/Sub は fan-out (1 message -> N subscribers) をサポートし、
message filtering, ordering, dead-letter queue 等のより豊富な messaging primitive を持つ。
一方 Cloud Tasks は 1 task = 1 target の point-to-point delivery に特化する。

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

GCP service が emit する event を declarative に Cloud Run / Workflows 等の target に routing する。
Firestore document の変更、Cloud Storage object の upload、Cloud Audit Log の event 等を
trigger として、processing pipeline を構築できる。

Pub/Sub との違い: Eventarc は GCP service event の routing に特化した declarative layer であり、
内部的には Pub/Sub を transport として利用する。Application code から明示的に publish する Pub/Sub と異なり、
GCP service の event を自動的に capture する。

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

Fully-managed cron service。unix-cron format のスケジュール定義で、
HTTP endpoint / Pub/Sub topic / App Engine に対して定期実行を行う。

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
| 必ず完了させたい非同期処理 (1:1) | Cloud Tasks |
| イベントの fan-out (1:N) | Cloud Pub/Sub |
| GCP サービスイベントへの反応 | Eventarc |
| 定期実行 (cron) | Cloud Scheduler |
| Pub/Sub topic への定期 publish | Cloud Scheduler -> Pub/Sub |

## 3.6 Local Emulation

| Service | Emulator | Port |
|---------|----------|------|
| Cloud Tasks | Firebase Emulator | 9499 |
| Pub/Sub | Firebase Emulator | 9399 |
| Eventarc | Firebase Emulator | 9299 |
