# Implementation Patterns

GCP サービスを使った実装パターン集。全て言語非依存の pseudocode であり、
実際のプロジェクトの言語 (Python, Go, Rust, Swift, Kotlin, TypeScript 等) に合わせて具体化すること。

## Table of Contents

1. [Firebase Auth Token Verification](#1-firebase-auth-token-verification)
2. [Firestore CRUD via Admin SDK](#2-firestore-crud-via-admin-sdk)
3. [Firestore Real-time Listener](#3-firestore-real-time-listener)
4. [Firestore Security Rules Patterns](#4-firestore-security-rules-patterns)
5. [Cloud Tasks Enqueue](#5-cloud-tasks-enqueue)
6. [Cloud Tasks Callback Handler](#6-cloud-tasks-callback-handler)
7. [Pub/Sub Publish](#7-pubsub-publish)
8. [Pub/Sub Push Handler](#8-pubsub-push-handler)
9. [Eventarc Firestore Trigger](#9-eventarc-firestore-trigger)
10. [Cloud Scheduler Job](#10-cloud-scheduler-job)
11. [Structured Logging](#11-structured-logging)
12. [Health Check](#12-health-check)
13. [Firestore Vector Search](#13-firestore-vector-search)
14. [Firestore Geo Query](#14-firestore-geo-query)

---

## 1. Firebase Auth Token Verification

Backend で Firebase ID Token を検証する。

```
FUNCTION verify_firebase_token(request) -> UserInfo:
    auth_header = request.headers["Authorization"]
    IF auth_header IS EMPTY OR NOT starts_with("Bearer "):
        RETURN Error(401, "Missing token")

    token = auth_header.split("Bearer ")[1]
    decoded = FirebaseAuth.verify_id_token(token)
    // decoded contains: { uid, email, name, ... }
    RETURN decoded

// Usage: middleware / dependency injection
ENDPOINT GET /me (user = verify_firebase_token(request)):
    RETURN { uid: user.uid }
```

## 2. Firestore CRUD via Admin SDK

Backend から Firestore にアクセスする (server-side, Admin SDK)。

```
db = Firestore.client()

// --- Create ---
FUNCTION create_item(user_id, data) -> document_id:
    doc_ref = db.collection("users").doc(user_id).collection("items").doc()
    doc_ref.set({ ...data, created_at: SERVER_TIMESTAMP })
    RETURN doc_ref.id

// --- Read ---
FUNCTION get_item(user_id, item_id) -> Item | null:
    doc = db.collection("users").doc(user_id).collection("items").doc(item_id).get()
    RETURN doc.exists ? doc.to_dict() : null

// --- Query (multiple inequality filters) ---
FUNCTION query_items(user_id, min_price, max_date) -> List[Item]:
    query = db.collection("users").doc(user_id).collection("items")
        .where("price", ">=", min_price)
        .where("created_at", "<=", max_date)
        .order_by("price")
        .limit(50)
    RETURN query.get()

// --- Transaction (max 500 docs) ---
FUNCTION transfer(from_id, to_id, amount):
    db.run_transaction(FUNCTION(tx):
        from_ref = db.collection("accounts").doc(from_id)
        to_ref   = db.collection("accounts").doc(to_id)
        from_doc = tx.get(from_ref)
        to_doc   = tx.get(to_ref)
        tx.update(from_ref, { balance: from_doc.balance - amount })
        tx.update(to_ref,   { balance: to_doc.balance + amount })
    )
```

## 3. Firestore Real-time Listener

Client (Web/iOS/Android) から Firestore の変更をリアルタイムに受信する (Client SDK)。
WebSocket / SSE / Polling の自前実装は不要。

```
// Client-side: framework hook or callback pattern
FUNCTION use_items(user_id) -> { items, loading }:
    items = []
    loading = true

    query = db.collection("users", user_id, "items")
        .where("status", "==", "active")
        .order_by("created_at", "desc")

    unsubscribe = query.onSnapshot(FUNCTION(snapshot):
        items = snapshot.docs.map(doc => { id: doc.id, ...doc.data() })
        loading = false
    )

    // Cleanup: call unsubscribe() when component unmounts / scope ends
    RETURN { items, loading, unsubscribe }
```

**Constraint**: Firebase Client SDK (Web/iOS/Android) が必要。
Server-side rendering ではリアルタイム listener は使用不可。

## 4. Firestore Security Rules Patterns

```
rules_version = '2';

service cloud.firestore {
  match /databases/{database}/documents {
    // Auth check helper
    function isSignedIn() {
      return request.auth != null;
    }

    // Owner check helper
    function isOwner(userId) {
      return isSignedIn() && request.auth.uid == userId;
    }

    // Pattern A: Owner-only read, server-only write
    match /users/{userId} {
      allow read: if isOwner(userId);
      allow write: if false;
    }

    // Pattern B: Authenticated read, owner write with validation
    match /posts/{postId} {
      allow read: if isSignedIn();
      allow create: if isSignedIn()
        && request.resource.data.author_uid == request.auth.uid
        && request.resource.data.keys().hasAll(["title", "body", "author_uid"]);
      allow update: if isSignedIn()
        && resource.data.author_uid == request.auth.uid;
      allow delete: if false;
    }

    // Pattern C: Public read, no write (server-managed)
    match /public/{docId} {
      allow read: if true;
      allow write: if false;
    }
  }
}
```

## 5. Cloud Tasks Enqueue

非同期処理を Cloud Tasks にエンキューする。

```
tasks_client = CloudTasks.client()

FUNCTION enqueue_task(
    queue_name,
    handler_url,
    payload,         // JSON-serializable data
    delay_seconds=0,
    task_id=null     // Deduplication key (optional)
) -> task_name:

    parent = "projects/{PROJECT_ID}/locations/asia-northeast1/queues/{queue_name}"

    task = {
        http_request: {
            method: POST,
            url: handler_url,
            headers: { "Content-Type": "application/json" },
            body: JSON.encode(payload),
            oidc_token: { service_account_email: SA_EMAIL },
        }
    }

    IF task_id IS NOT null:
        task.name = "{parent}/tasks/{task_id}"

    IF delay_seconds > 0:
        task.schedule_time = NOW() + delay_seconds

    response = tasks_client.create_task(parent, task)
    RETURN response.name
```

## 6. Cloud Tasks Callback Handler

Cloud Tasks からの HTTP callback を処理する。**冪等性が必須**。

```
ENDPOINT POST /tasks/process-order (request):
    // Cloud Tasks callback handler - MUST be idempotent
    payload = request.json()
    order_id = payload.order_id

    // 1. Idempotency check
    order = get_order(order_id)
    IF order AND order.processed:
        RETURN 200 { status: "already_processed" }

    // 2. Process (business logic)
    TRY:
        result = process_order(order_id)
    CATCH PermanentError:
        // Permanent failure: return 2xx to stop retries, log for investigation
        log.error("permanent_failure", order_id)
        mark_order_failed(order_id)
        RETURN 200 { status: "permanent_failure" }
    CATCH TemporaryError:
        // Temporary failure: return 5xx to trigger retry
        RETURN 503 { status: "temporary_failure" }

    // 3. Mark as processed (idempotency flag)
    mark_order_processed(order_id, result)
    RETURN 200 { status: "processed" }
```

**Key rules**:
- 2xx response = task complete (no retry)
- 4xx/5xx response = retry with exponential backoff
- Permanent error → return 2xx + log failure
- task_ttl default 31 days, max_attempts OR max_retry_duration のいずれかで retry 停止

## 7. Pub/Sub Publish

1:N fan-out でイベントを配信する。

```
publisher = PubSub.publisher_client()

FUNCTION publish_event(topic_name, event_type, data) -> message_id:
    topic_path = "projects/{PROJECT_ID}/topics/{topic_name}"
    message = JSON.encode(data)

    message_id = publisher.publish(
        topic_path,
        data: message,
        attributes: { event_type: event_type }  // for subscription filtering
    )
    RETURN message_id
```

## 8. Pub/Sub Push Handler

Pub/Sub push subscription からのメッセージを処理する。

```
ENDPOINT POST /pubsub/user-events (request):
    // Pub/Sub push handler - MUST be idempotent
    envelope = request.json()
    message = envelope.message

    // Decode payload
    data = JSON.decode(BASE64.decode(message.data))
    message_id = message.messageId  // Dedup key

    // Idempotency check
    IF is_already_processed(message_id):
        RETURN 200 { status: "duplicate" }

    // Process based on event type (attribute filtering)
    event_type = message.attributes.event_type

    SWITCH event_type:
        CASE "user.created": handle_user_created(data)
        CASE "user.updated": handle_user_updated(data)
        DEFAULT: log.warning("unknown_event_type", event_type)

    mark_processed(message_id)
    RETURN 200 { status: "ok" }
```

## 9. Eventarc Firestore Trigger

Firestore document の変更に反応する Cloud Function。

```
// Cloud Functions (Gen 2 / Cloud Run functions)
FUNCTION on_document_created(cloud_event):
    // Triggered by Firestore document creation via Eventarc
    data = cloud_event.data

    doc_path = data.value.name     // Full document path
    fields   = data.value.fields   // Document fields

    // Process (e.g., send notification, update aggregate)
    process_new_document(doc_path, fields)
```

## 10. Cloud Scheduler Job

定期実行ジョブの設定。

```bash
# Create a scheduler job that calls Cloud Run service
gcloud scheduler jobs create http daily-cleanup \
  --location=asia-northeast1 \
  --schedule="0 3 * * *" \
  --time-zone="Asia/Tokyo" \
  --uri="https://backend-xxx.run.app/tasks/daily-cleanup" \
  --http-method=POST \
  --oidc-service-account-email=scheduler-sa@project.iam.gserviceaccount.com
```

## 11. Structured Logging

Cloud Logging と統合する構造化ログパターン。

```
// Configure structured JSON logging
logger = StructuredLogger.configure({
    format: JSON,
    fields: [log_level, timestamp_iso, context_vars]
})

// Usage
logger.info("order_processed", { order_id: "123", amount: 500 })
// Output: {"event":"order_processed","order_id":"123","amount":500,"level":"info","timestamp":"..."}
```

## 12. Health Check

Cloud Run health check endpoint。

```
ENDPOINT GET /health:
    RETURN 200 { status: "ok" }
```

Cloud Run startup probe:
```bash
gcloud run deploy backend \
  --startup-cpu-boost \
  --startup-probe-path=/health \
  --startup-probe-initial-delay=0s \
  --startup-probe-timeout=3s \
  --startup-probe-period=10s
```

## 13. Firestore Vector Search

Embedding vector を使った semantic search。

```
// Store embedding
FUNCTION store_with_embedding(doc_data, embedding):
    // embedding: list of floats, max 2048 dimensions
    doc_ref = db.collection("documents").doc()
    doc_ref.set({ ...doc_data, embedding: Vector(embedding) })

// Search by vector similarity
FUNCTION vector_search(query_embedding, limit=10) -> List[Document]:
    results = db.collection("documents").find_nearest(
        vector_field: "embedding",
        query_vector: Vector(query_embedding),
        distance_measure: COSINE,
        limit: limit
    )
    RETURN results.get()
```

**Requires**: Vector index の作成
```bash
gcloud firestore indexes composite create \
  --collection-group=documents \
  --query-scope=COLLECTION \
  --field-config=vector-config='{"dimension":768,"flat":{}}',field-path=embedding
```

## 14. Firestore Geo Query

地理的な近傍検索 (lat/lng 直接 range query 推奨)。

```
// Recommended: direct lat/lng range query
FUNCTION find_nearby(lat, lng, radius_km) -> List[Place]:
    // Approximate bounding box
    lat_delta = radius_km / 111.0
    lng_delta = radius_km / (111.0 * cos(radians(lat)))

    results = db.collection("places")
        .where("latitude", ">=", lat - lat_delta)
        .where("latitude", "<=", lat + lat_delta)
        .where("longitude", ">=", lng - lng_delta)
        .where("longitude", "<=", lng + lng_delta)
        .get()

    // Client-side distance filtering for precision
    RETURN results.filter(doc =>
        haversine_distance(lat, lng, doc.latitude, doc.longitude) <= radius_km
    )
```
