# 2. Data Persistence / Object Storage / Search

> Sections 2.1 and 2.6 are **Core** (required for the initial release).
> Sections 2.2 through 2.5 are **Extension** (add them as needed).
> For backup / RPO / RTO, see [infrastructure-8-incident.md Section 8.6](infrastructure-8-incident.md#86-backup--recovery).

## 2.1 Document Database: Cloud Firestore

**Service**: [Google Cloud Firestore](https://cloud.google.com/firestore)

A serverless document-oriented database. Internally it uses Cloud Spanner as its storage layer,
and it guarantees strong consistency for every query (eventual consistency is the old behavior).
It offers push notification to clients through real-time listeners, and offline persistence.
Following the policy of staying in a Japanese region, it is placed in `asia-northeast1` (Tokyo).

Firestore has a hierarchy of collection > document > subcollection.

> **Ref**: [Firestore Editions](https://firebase.google.com/docs/firestore/editions),
> [Firestore Pipeline Operations](https://firebase.blog/posts/2026/01/firestore-enterprise-pipeline-operations/)

### 2.1.1 Editions

Firestore comes in 2 editions: **Standard** and **Enterprise**.

| Aspect | Standard | Enterprise |
|--------|----------|-----------|
| Query engine | Core operations | Core + **Pipeline operations** (180+ stages/operators) |
| Indexing | Single-field: automatic / Composite: must be declared explicitly | **Optional indexing** (queries work without an index) |
| Pipeline operations | Not available | Array unnest, aggregation, regex, chained stages |
| MongoDB compatibility | None | MongoDB compatibility API supported (3.6 to 8.0) |
| Query Explain | **Yes** (basic analysis) | **Yes** (advanced analysis including analyze mode) |
| VPC Service Controls | No | Yes |
| CMEK | **Yes** | Yes |
| Pricing | Read/Write/Delete billed separately | Write + Delete billed together, based on data chunks |

**Edition selection policy**: start with Standard, and move to Enterprise once Pipeline operations
or optional indexing become necessary. Existing queries remain compatible.

### 2.1.2 Key Characteristics

| Property | Detail |
|----------|--------|
| Consistency | **Strong consistency (all queries)** |
| Internal Engine | Cloud Spanner based |
| Region | `asia-northeast1` (single-region) |
| Transactions | ACID across multiple documents (max 500 docs/tx) |
| Max Document Size | 1 MiB |
| Offline Support | Client SDK provides offline persistence and automatic sync |

### 2.1.3 Query Capabilities

| Capability | Standard | Enterprise |
|------------|----------|-----------|
| Equality filter | Unlimited fields | Same |
| Inequality / range filter | **Multiple fields supported** (up to 10 fields) | Same |
| `array-contains` / `array-contains-any` | One per query | Same |
| `in` | Up to 30 disjunction values | Same |
| `not-in` | Up to **10** values | Same |
| `OR` query | Supported | Same |
| Order by | Depends on the composite index definition | Optional indexing |
| Aggregation (count, sum, avg) | Supported (server-side) | Enhanced (Pipeline) |
| Array unnest | Not available | **Available with Pipeline operations** |
| Regex matching | Not available | **Available with Pipeline operations** |
| Chained transformations | Not available | **Available with Pipeline operations** |
| **Geo query** | Geohash-based range query | Same |
| **Vector search (KNN)** | `find_nearest` (up to 2048 dimensions) | Same |

> **Note**: the old restriction "inequality filter on one field only" has been removed.
> Range / inequality filters can now be applied to up to 10 fields.

#### Geo Query

Firestore has no GIS-specific operators, but geographic search can be done in two ways.

**Approach A: Geohash (the traditional approach)**

| Property | Detail |
|----------|--------|
| Encoding | Geohash (encodes latitude and longitude into a string) |
| Query method | Range query on the geohash prefix (bounding box) |
| Precision | Controlled by the geohash length (longer means a narrower area) |
| Limitation | Because it is bounding-box based, distance filtering on the client is required. Extra reads occur. |

**Approach B: multi-field range query (recommended, since 2024-03)**

| Property | Detail |
|----------|--------|
| Query method | Direct range query on the `latitude` / `longitude` fields |
| Precision | Any bounding box can be specified |
| Advantage | About **5.4x** better read efficiency than geohash |
| Requirement | Multiple inequality filter support (GA in 2024-03) |

> **Recommendation**: use approach B (direct lat/lng range query) for new implementations.
> Keep geohash only for compatibility with existing implementations.
>
> **Ref**: [Firestore Geo queries](https://firebase.google.com/docs/firestore/solutions/geoqueries)

#### Vector Search (KNN)

Firestore stores embedding vectors in document fields and natively supports
K-Nearest Neighbor (KNN) search through the `find_nearest` API.
It covers the basic use cases of semantic search and recommendation.

| Property | Detail |
|----------|--------|
| API | `find_nearest` (Client SDK / Admin SDK) |
| Max dimensions | 2048 |
| Max results | 1000 |
| Distance measures | Euclidean, Cosine, Dot product |
| Pre-filtering | Can be combined with normal Firestore filters |
| Index | A vector index must be created (`gcloud firestore indexes composite create`) |
| Integration | Integration with LangChain and LlamaIndex is supported |

> **Ref**: [Firestore Vector search](https://firebase.google.com/docs/firestore/vector-search)

**Choosing between this and Qdrant**: Firestore vector search suits small to medium
embedding search. For large vector workloads (millions or more), advanced filtering, or when
HNSW tuning is required, use [Qdrant (Section 2.4)](#24-extension-vector-search-engine-qdrant).

### 2.1.4 Indexing

**Standard edition**:
- Single-field indexes are created automatically
- Multi-field (composite) indexes are declared in `firestore.indexes.json` and applied with
  `firebase deploy --only firestore:indexes`

**Enterprise edition**:
- Indexes are not created by default (optional indexing model)
- Developers create only the indexes they need, based on Query Explain / Query Insights
- Queries run even without an index (with a performance trade-off on large collections)

### 2.1.5 Real-time Synchronization

With the real-time listener (`onSnapshot`) built into the client SDK, Firestore Native Mode can
push server-side data changes to clients immediately,
**without implementing WebSocket, polling, or SSE yourself**.

```
Client A: write document
    |
    v
Firestore (server)
    |
    +--> Client B: onSnapshot callback fires (automatic, sub-second)
    +--> Client C: onSnapshot callback fires (automatic, sub-second)
```

#### Benefits

| Benefit | Detail |
|---------|--------|
| Real-time push (zero infra) | No need to build a WebSocket server or a Pub/Sub -> Push path |
| Offline-first | The client SDK keeps a local cache, so reads work while offline. It syncs automatically when back online. |
| Optimistic UI | Writes are applied to the local cache immediately, so the UI updates at once (server confirmation is asynchronous) |
| Unified across platforms | The same real-time API on Web / iOS / Android / Flutter |
| Automatic reconnection | The SDK handles reconnection after a network drop and the delta sync automatically |

#### Constraints

| Constraint | Detail |
|------------|--------|
| Firebase Client SDK required | Real-time listeners are available only through the Firebase SDK (`firebase/firestore`). They cannot be used from the REST API or the Admin SDK |
| Security Rules apply | Access from the client SDK goes through Security Rules. Writes made through the backend are also delivered to listeners |
| Listener cost | Active listeners are billed as document reads. Watch the cost when there are many listeners |
| Fan-out limit | There is a practical limit on the number of concurrent listeners on a single document (tens of thousands of connections per document) |
| Query listener | A listener on a collection query is notified only of changes that match the query conditions |

#### Architecture Implication

Because Firestore has real-time listeners, the following architecture patterns are possible:

```
[Pattern A: Direct sync (recommended for simple state)]
  Client SDK --> Firestore <-- Client SDK
  (no backend involvement for read/write + real-time sync)

[Pattern B: Backend-mediated write + client real-time read]
  Client --> Backend (Cloud Run) --> Firestore write
                                        |
  Client <-- onSnapshot listener -------+
  (the backend writes via its business logic; the client is updated at once by the listener)
```

With pattern B, the backend can perform validation and transformation while still delivering
real-time updates to clients without a WebSocket server.

### 2.1.6 Security Rules

Firestore Security Rules declaratively define field-level access control
for direct access from the client SDK.
Access from the backend (Admin SDK) bypasses Security Rules.

---

## Extension (Optional)

Introduce the data stores below when GraphRAG, RAG, or advanced search requirements come up.
They are not needed for the initial release.

## 2.2 [Extension] Distributed Relational Database: Cloud Spanner

**Service**: [Google Cloud Spanner](https://cloud.google.com/spanner)

A globally-distributed, strongly-consistent relational database.
It combines horizontal scaling with ACID transactions.
It offers a PostgreSQL-compatible dialect, so existing PostgreSQL client libraries and ORMs can connect.

Choosing between this and Firestore: Firestore is a flexible-schema document store, well suited to
rapid prototyping and direct client access.
Use Spanner when you need a strict schema, complex queries, or cross-row transactions.

### 2.2.1 Key Characteristics

| Property | Detail |
|----------|--------|
| Consistency | External consistency (linearizability) |
| Dialect | PostgreSQL-compatible (via pgAdapter) |
| Scaling | Horizontal (adding nodes raises throughput) |
| Transactions | Fully ACID, distributed |
| Schema | Strongly typed, DDL-managed |
| Interleaving | Parent-child table co-location for performance |

### 2.2.2 pgAdapter

A proxy for accessing Cloud Spanner over the PostgreSQL wire protocol.
Standard PostgreSQL drivers (asyncpg, psycopg2, and so on) can be used as they are.

| Item | Value |
|------|-------|
| Port | 5432 (standard PostgreSQL port) |
| Mode | Auto-configure with emulator / production project |

### 2.2.3 Local Emulation

Use the Cloud Spanner Emulator (`gcr.io/cloud-spanner-emulator/emulator`).
Connect from a PostgreSQL client through pgAdapter.

## 2.3 [Extension] Graph Database: Neo4j

**Service**: [Neo4j](https://neo4j.com/)

A graph database based on the property graph model.
For data with a graph structure made of nodes and relationships, it runs
traversal and pattern matching through the Cypher query language.

Exploring relationships between entities (N-hop traversal, shortest path, community detection,
and so on) is orders of magnitude faster than a recursive JOIN in an RDB.

### 2.3.1 Key Characteristics

| Property | Detail |
|----------|--------|
| Model | Property Graph (Nodes + Relationships + Properties) |
| Query Language | Cypher |
| Protocols | Bolt (7687), HTTP (7474) |

### 2.3.2 Hosting Strategy

| Environment | Hosting | Detail |
|-------------|---------|--------|
| Local | Docker Compose | `neo4j:5-community` (self-hosted) |
| Production | **Neo4j AuraDB** (managed) | A fully-managed service from Neo4j. It runs on GCP, and backup / scaling / patching are automated |

## 2.4 [Extension] Vector Search Engine: Qdrant

**Service**: [Qdrant](https://qdrant.tech/)

A high-performance vector similarity search engine.
It provides nearest neighbor search over embedding vectors and acts as the retrieval layer for
semantic search, recommendation, and RAG (Retrieval-Augmented Generation).

### 2.4.1 Key Characteristics

| Property | Detail |
|----------|--------|
| Index Type | HNSW (Hierarchical Navigable Small World) |
| Distance Metrics | Cosine, Euclidean, Dot product |
| Filtering | Payload-based filtering with vector search |
| API | REST (6333), gRPC (6334) |
| Scalability | Sharding + replication (cluster mode) |

### 2.4.2 Hosting Strategy

| Environment | Hosting | Detail |
|-------------|---------|--------|
| Local | Docker Compose | `qdrant/qdrant:latest` (self-hosted) |
| Production | **Qdrant Cloud** (managed) | A fully-managed service from Qdrant. It can be deployed on GCP. Backup, scaling, and monitoring are automated |

### 2.4.3 Alternative: pgvector

pgvector, which provides vector search as a PostgreSQL extension, is another option.
It can integrate vector search inside the same PostgreSQL ecosystem as Cloud Spanner (pgAdapter),
but its throughput at large scale is lower than a dedicated engine (Qdrant).

| Item | Value |
|------|-------|
| Image | `pgvector/pgvector:pg18` |
| Port | 55432 |
| Usage | Small-scale vector search, or when the vectors do not need to live in Spanner (a standalone PostgreSQL with pgvector is enough) |

## 2.5 [Extension] Full-Text Search Engine: Elasticsearch

**Service**: [Elasticsearch](https://www.elastic.co/elasticsearch/)

A distributed full-text search and analytics engine.
It provides fast full-text search through an inverted index, and analytical queries through aggregations.
It supports morphological analysis (analyzers) for many languages, including Japanese.

### 2.5.1 Key Characteristics

| Property | Detail |
|----------|--------|
| Engine | Apache Lucene-based inverted index |
| API | REST (9200) |
| Scaling | Cluster mode (sharding + replication) |
| Analysis | Built-in analyzers + custom analyzer pipeline |

### 2.5.2 Hosting Strategy

| Environment | Hosting | Detail |
|-------------|---------|--------|
| Local | Docker Compose | `elasticsearch:8+` (self-hosted, single-node) |
| Production | **Elastic Cloud** (managed) | A fully-managed service from Elastic. It can be deployed on GCP. Cross-cluster replication, snapshots, and monitoring are automated |

## 2.6 Object Storage: Cloud Storage (via Firebase Storage)

**Service**: [Google Cloud Storage](https://cloud.google.com/storage) (Firebase Storage interface)

Exabyte-scale object storage.
Clients can upload and download directly through the Firebase SDK wrapper.
Access control can be applied with Firebase Security Rules.
The backend operates on it directly with the Google Cloud Storage client library.

### 2.6.1 Key Characteristics

| Property | Detail |
|----------|--------|
| Storage Class | Standard (frequently accessed data) |
| Access Control | Firebase Security Rules (client) / IAM (backend) |
| CORS | Explicit configuration required for browser-origin requests |
| Lifecycle | Object lifecycle policies can delete objects or change their class automatically |
| Max Object Size | 5 TiB |

### 2.6.2 Bucket Naming Convention

```
{project-id}.firebasestorage.app
```

## 2.7 Data Store Selection Guide

| Use Case | Service | Tier | Rationale |
|----------|---------|------|-----------|
| User profile, session, flexible schema | Firestore | Core | Direct client SDK access, real-time sync |
| File / media storage | Cloud Storage | Core | Object storage at scale |
| Strict schema, complex query, distributed tx | Cloud Spanner | Extension | ACID + horizontal scale |
| Entity relationship traversal | Neo4j | Extension | Graph traversal performance |
| Semantic similarity search (embedding) | Qdrant | Extension | HNSW-based ANN search |
| Full-text search, analytics | Elasticsearch | Extension | Inverted index + aggregation |

## 2.8 Local Emulation

| Service | Emulator | Port |
|---------|----------|------|
| Firestore | Firebase Emulator | 8080 |
| Cloud Storage | Firebase Emulator | 9199 |
| Cloud Spanner | Spanner Emulator + pgAdapter | 9010 (gRPC), 5432 (PG) |
| Neo4j | Docker (neo4j:5-community) | 7474, 7687 |
| Qdrant | Docker (qdrant/qdrant) | 6333, 6334 |
| Elasticsearch | Docker (elasticsearch:8+) | 9200 |
| pgvector | Docker (pgvector/pgvector:pg18) | 55432 |
