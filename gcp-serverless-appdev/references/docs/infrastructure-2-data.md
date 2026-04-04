# 2. Data Persistence / Object Storage / Search

> Section 2.1, 2.6 は **Core** (初期リリース必須)。
> Section 2.2〜2.5 は **Extension** (必要に応じて追加)。
> Backup / RPO / RTO は [infrastructure-8-incident.md Section 8.6](infrastructure-8-incident.md#86-backup--recovery) を参照。

## 2.1 Document Database: Cloud Firestore

**Service**: [Google Cloud Firestore](https://cloud.google.com/firestore)

Serverless な document-oriented database。内部的に Cloud Spanner をストレージ基盤として使用しており、
全てのクエリで strong consistency を保証する（結果整合性は過去の仕様）。
Real-time listener によるクライアントへの push 通知、offline persistence を提供する。
日本リージョン固定方針に基づき `asia-northeast1` (Tokyo) に配置する。

Firestore は「コレクション > ドキュメント > サブコレクション」の階層構造を持つ。

> **Ref**: [Firestore Editions](https://firebase.google.com/docs/firestore/editions),
> [Firestore Pipeline Operations](https://firebase.blog/posts/2026/01/firestore-enterprise-pipeline-operations/)

### 2.1.1 Editions

Firestore は **Standard** と **Enterprise** の 2 edition を提供する。

| Aspect | Standard | Enterprise |
|--------|----------|-----------|
| Query engine | Core operations | Core + **Pipeline operations** (180+ stages/operators) |
| Indexing | Single-field: 自動 / Composite: 明示定義必須 | **Optional indexing** (index なしでもクエリ可能) |
| Pipeline operations | 不可 | Array unnest, aggregation, regex, chained stages |
| MongoDB 互換 | なし | MongoDB compatibility API サポート (3.6〜8.0) |
| Query Explain | **あり** (基本分析) | **あり** (analyze mode 含む高度な分析) |
| VPC Service Controls | なし | あり |
| CMEK | **あり** | あり |
| Pricing | Read/Write/Delete 個別課金 | Write + Delete 統合課金、data chunk ベース |

**Edition 選定方針**: 初期は Standard で開始し、Pipeline operations や optional indexing が
必要になった段階で Enterprise に移行する。既存クエリは互換性が維持される。

### 2.1.2 Key Characteristics

| Property | Detail |
|----------|--------|
| Consistency | **Strong consistency (全クエリ)** |
| Internal Engine | Cloud Spanner ベース |
| Region | `asia-northeast1` (single-region) |
| Transactions | ACID across multiple documents (max 500 docs/tx) |
| Max Document Size | 1 MiB |
| Offline Support | Client SDK provides offline persistence and automatic sync |

### 2.1.3 Query Capabilities

| Capability | Standard | Enterprise |
|------------|----------|-----------|
| Equality filter | Unlimited fields | Same |
| Inequality / range filter | **複数フィールドに対応** (最大 10 フィールド) | Same |
| `array-contains` / `array-contains-any` | 1 query に 1 つ | Same |
| `in` | 最大 30 disjunction values | Same |
| `not-in` | 最大 **10** values | Same |
| `OR` query | Supported | Same |
| Order by | Composite index 定義に依存 | Optional indexing |
| Aggregation (count, sum, avg) | Supported (server-side) | Enhanced (Pipeline) |
| Array unnest | 不可 | **Pipeline operations で可能** |
| Regex matching | 不可 | **Pipeline operations で可能** |
| Chained transformations | 不可 | **Pipeline operations で可能** |
| **Geo query** | Geohash ベースの range query | Same |
| **Vector search (KNN)** | `find_nearest` (最大 2048 次元) | Same |

> **Note**: 過去の制限「inequality filter は 1 field のみ」は撤廃済み。
> 現在は最大 10 フィールドに対して range / inequality filter を適用可能。

#### Geo Query

Firestore は GIS 専用演算子を持たないが、2 つの方式で地理検索を実現できる。

**方式 A: Geohash (従来方式)**

| Property | Detail |
|----------|--------|
| Encoding | Geohash (緯度・経度を文字列にエンコード) |
| Query method | Geohash prefix による range query (bounding box) |
| Precision | Geohash 文字数で制御 (長いほど狭い範囲) |
| Limitation | Bounding box ベースのため、クライアント側の距離フィルタリングが必要。余分な read が発生する |

**方式 B: 複数フィールド range query (推奨、2024-03〜)**

| Property | Detail |
|----------|--------|
| Query method | `latitude` / `longitude` field に対する直接 range query |
| Precision | 任意の bounding box を指定可能 |
| Advantage | Geohash 比で約 **5.4 倍** read 効率が良い |
| Requirement | Multiple inequality filter 対応 (2024-03 GA) |

> **推奨**: 新規実装では方式 B (lat/lng 直接 range query) を使用する。
> Geohash は既存実装の互換性維持のみ。
>
> **Ref**: [Firestore Geo queries](https://firebase.google.com/docs/firestore/solutions/geoqueries)

#### Vector Search (KNN)

Firestore は document field に embedding vector を格納し、
`find_nearest` API による K-Nearest Neighbor (KNN) 検索を native にサポートする。
Semantic search や recommendation の基本的なユースケースに対応できる。

| Property | Detail |
|----------|--------|
| API | `find_nearest` (Client SDK / Admin SDK) |
| Max dimensions | 2048 |
| Max results | 1000 |
| Distance measures | Euclidean, Cosine, Dot product |
| Pre-filtering | 通常の Firestore filter と組み合わせ可能 |
| Index | Vector index の作成が必要 (`gcloud firestore indexes composite create`) |
| Integration | LangChain, LlamaIndex との統合をサポート |

> **Ref**: [Firestore Vector search](https://firebase.google.com/docs/firestore/vector-search)

**Qdrant との使い分け**: Firestore vector search は小〜中規模の embedding 検索に適する。
大規模 (数百万〜) の vector workload、高度な filtering、HNSW チューニングが必要な場合は
[Qdrant (Section 2.4)](#24-extension-vector-search-engine-qdrant) を使用する。

### 2.1.4 Indexing

**Standard edition**:
- Single-field index は自動作成される
- Multi-field (composite) index は `firestore.indexes.json` で宣言管理し、
  `firebase deploy --only firestore:indexes` で適用

**Enterprise edition**:
- Index はデフォルトで作成されない (optional indexing model)
- 開発者が Query Explain / Query Insights を基に必要な index のみを作成
- Index なしでもクエリは実行可能 (大規模コレクションでは性能トレードオフ)

### 2.1.5 Real-time Synchronization

Firestore Native Mode は、client SDK に組み込まれた real-time listener (`onSnapshot`) により、
**WebSocket / Polling / SSE を自前で実装することなく**、サーバー側のデータ変更を
クライアントに即座に push 通知できる。

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
| Real-time push (zero infra) | WebSocket server / Pub/Sub -> Push の構築が不要 |
| Offline-first | Client SDK がローカルキャッシュを保持し、offline 時も read 可能。online 復帰時に自動 sync |
| Optimistic UI | Write はローカルキャッシュに即反映され、UI が即座に更新される (server 確認は非同期) |
| Multi-platform 統一 | Web / iOS / Android / Flutter で同一の real-time API |
| Automatic reconnection | Network 切断後の再接続と差分同期を SDK が自動処理 |

#### Constraints

| Constraint | Detail |
|------------|--------|
| Firebase Client SDK 必須 | Real-time listener は Firebase SDK (`firebase/firestore`) でのみ利用可能。REST API / Admin SDK からは利用不可 |
| Security Rules 適用 | Client SDK からのアクセスは Security Rules を経由する。Backend 経由の write も listener に通知される |
| Listener cost | Active listener は document read として課金される。大量の listener は cost に注意 |
| Fan-out limit | 単一 document への同時 listener 数に実質的な上限がある (数万 connections/document) |
| Query listener | Collection query に対する listener は query 条件に一致する変更のみ通知する |

#### Architecture Implication

Firestore real-time listener の存在により、以下のアーキテクチャパターンが成立する:

```
[Pattern A: Direct sync (recommended for simple state)]
  Client SDK --> Firestore <-- Client SDK
  (no backend involvement for read/write + real-time sync)

[Pattern B: Backend-mediated write + client real-time read]
  Client --> Backend (Cloud Run) --> Firestore write
                                        |
  Client <-- onSnapshot listener -------+
  (backend が business logic を経由して write, client は listener で即座に反映を受け取る)
```

Pattern B により、Backend で validation / transformation を行いつつ、
client には WebSocket server なしで real-time update を配信できる。

### 2.1.6 Security Rules

Firestore Security Rules により、client SDK からの直接アクセスに対して
field-level の access control を宣言的に定義する。
Backend (Admin SDK) からのアクセスは Security Rules を bypass する。

---

## Extension (Optional)

以下のデータストアは GraphRAG / RAG / 高度な検索要件が発生した場合に導入する。
初期リリースには不要。

## 2.2 [Extension] Distributed Relational Database: Cloud Spanner

**Service**: [Google Cloud Spanner](https://cloud.google.com/spanner)

Globally-distributed, strongly-consistent relational database。
水平スケーリングと ACID transaction を両立する。
PostgreSQL 互換 dialect を提供し、既存の PostgreSQL client library / ORM から接続可能。

Firestore との使い分け: Firestore は flexible schema の document store であり、
rapid prototyping やクライアント直接アクセスに適する。
Spanner は strict schema, complex query, cross-row transaction が必要な場合に使用する。

### 2.2.1 Key Characteristics

| Property | Detail |
|----------|--------|
| Consistency | External consistency (linearizability) |
| Dialect | PostgreSQL-compatible (via pgAdapter) |
| Scaling | Horizontal (node 追加で throughput 向上) |
| Transactions | Fully ACID, distributed |
| Schema | Strongly typed, DDL-managed |
| Interleaving | Parent-child table co-location for performance |

### 2.2.2 pgAdapter

Cloud Spanner に PostgreSQL wire protocol でアクセスするための proxy。
Standard PostgreSQL driver (asyncpg, psycopg2 等) をそのまま使用できる。

| Item | Value |
|------|-------|
| Port | 5432 (standard PostgreSQL port) |
| Mode | Auto-configure with emulator / production project |

### 2.2.3 Local Emulation

Cloud Spanner Emulator (`gcr.io/cloud-spanner-emulator/emulator`) を使用。
pgAdapter 経由で PostgreSQL client から接続する。

## 2.3 [Extension] Graph Database: Neo4j

**Service**: [Neo4j](https://neo4j.com/)

Property graph model の graph database。
Node と Relationship で構成されるグラフ構造のデータに対して、
Cypher query language による traversal / pattern matching を実行する。

Entity 間の関係性探索（N-hop traversal, shortest path, community detection 等）が
RDB の recursive JOIN より桁違いに高速。

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
| Production | **Neo4j AuraDB** (managed) | Neo4j 社提供の fully-managed service。GCP 上で稼働し、backup / scaling / patching が自動化される |

## 2.4 [Extension] Vector Search Engine: Qdrant

**Service**: [Qdrant](https://qdrant.tech/)

High-performance な vector similarity search engine。
Embedding vector に対する nearest neighbor search を提供し、
semantic search, recommendation, RAG (Retrieval-Augmented Generation) の retrieval 層として機能する。

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
| Production | **Qdrant Cloud** (managed) | Qdrant 社提供の fully-managed service。GCP 上に deploy 可能。Backup, scaling, monitoring が自動化される |

### 2.4.3 Alternative: pgvector

PostgreSQL extension として vector search を提供する pgvector も選択肢。
Cloud Spanner (pgAdapter) と同じ PostgreSQL ecosystem 内で vector search を統合できるが、
専用 engine (Qdrant) と比較して large-scale での throughput は劣る。

| Item | Value |
|------|-------|
| Image | `pgvector/pgvector:pg18` |
| Port | 55432 |
| Usage | Small-scale vector search / Spanner 統合が不要な場合 |

## 2.5 [Extension] Full-Text Search Engine: Elasticsearch

**Service**: [Elasticsearch](https://www.elastic.co/elasticsearch/)

Distributed full-text search and analytics engine。
Inverted index による高速な全文検索と、aggregation による分析クエリを提供する。
日本語を含む多言語の形態素解析 (analyzer) をサポートする。

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
| Production | **Elastic Cloud** (managed) | Elastic 社提供の fully-managed service。GCP 上に deploy 可能。Cross-cluster replication, snapshot, monitoring が自動化される |

## 2.6 Object Storage: Cloud Storage (via Firebase Storage)

**Service**: [Google Cloud Storage](https://cloud.google.com/storage) (Firebase Storage interface)

Exabyte-scale の object storage。
Firebase SDK wrapper を通じてクライアントから直接 upload/download が可能。
Firebase Security Rules によるアクセス制御を適用できる。
Backend からは Google Cloud Storage client library で直接操作する。

### 2.6.1 Key Characteristics

| Property | Detail |
|----------|--------|
| Storage Class | Standard (frequently accessed data) |
| Access Control | Firebase Security Rules (client) / IAM (backend) |
| CORS | Explicit configuration required for browser-origin requests |
| Lifecycle | Object lifecycle policies で自動削除・class 変更が可能 |
| Max Object Size | 5 TiB |

### 2.6.2 Bucket Naming Convention

```
{project-id}.firebasestorage.app
```

## 2.7 Data Store Selection Guide

| Use Case | Service | Tier | Rationale |
|----------|---------|------|-----------|
| User profile, session, flexible schema | Firestore | Core | Client SDK 直接アクセス、real-time sync |
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
