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

このスキルはバンドルされたインフラ選定ドキュメント (`references/docs/`) に基づき、
GCP サーバーレスサービスを使ったアプリケーション開発を支援する。

## Knowledge Base

インフラ選定の詳細は以下のドキュメントにまとまっている。
実装判断に迷った場合はこれらを Read して確認する — GCP サービスの仕様や制約は
一般知識だけでは不正確になりがちなため、バンドルドキュメントで裏付けを取ることが重要。

| Doc | File | Content |
|-----|------|---------|
| Index | `references/docs/infrastructure.md` | 全体構成、サービス一覧、環境戦略 |
| Compute | `references/docs/infrastructure-1-compute.md` | Cloud Run, Cloud Functions, Docker build |
| Data | `references/docs/infrastructure-2-data.md` | Firestore, Spanner, Neo4j, Qdrant, ES, Storage |
| Async | `references/docs/infrastructure-3-async.md` | Cloud Tasks, Pub/Sub, Eventarc, Scheduler |
| CI/CD | `references/docs/infrastructure-4-cicd.md` | GitHub Actions, Cloud Build, Artifact Registry |
| Auth | `references/docs/infrastructure-5-auth.md` | Firebase Auth, WIF, Secret Manager |
| Observability | `references/docs/infrastructure-6-observability.md` | Sentry, structlog, Cloud Monitoring |
| Ops | `references/docs/infrastructure-7-ops.md` | Local dev, emulators, deploy, scaling |
| Incident | `references/docs/infrastructure-8-incident.md` | Rollback, maintenance, backup, recovery |
| Network | `references/docs/infrastructure-9-network.md` | Ingress, TLS, CORS, DDoS, VPC |
| App Constraints | `references/docs/infrastructure-10-app-constraints.md` | Backend/Frontend/Mobile 開発制約 |
| Alternatives | `references/docs/infrastructure-11-gcp-alternatives.md` | GCP サービス間の対比・選定理由 |

## Core Principles

1. **Region**: 全サービス `asia-northeast1` (Tokyo) 固定
2. **Tier**: Core (初期リリース必須) と Extension (オプション) を分離
3. **Idempotency**: at-least-once delivery のため、全ての async handler は冪等に実装
4. **Stateless**: Cloud Run は stateless — in-memory state を持たない設計
5. **Serverless first**: GKE よりも Cloud Run を優先
6. **Managed first**: self-hosted よりも managed service を優先

## Phase Guide

### Phase 1: Project Scaffold

新規プロジェクトを立ち上げる場合、`references/scaffold.md` を Read して
プロジェクト構造とセットアップ手順を確認する。

主要な scaffold 対象:
- **monorepo 構造**: `backend/` + `frontend/` + `emulator/`
- **Backend**: Python (FastAPI + uvicorn), uv で依存管理, multi-stage Dockerfile
- **Frontend**: Next.js (standalone), multi-stage Dockerfile
- **Emulator**: Firebase Emulator Suite を docker-compose.yaml で起動
- **Task runner**: justfile でタスク定義
- **CI/CD**: GitHub Actions workflow
- **Firestore**: security rules + indexes
- **Environment**: dotenvx で暗号化管理

### Phase 2: Feature Development

機能を実装する場合、以下の順序で判断する:

1. **データモデル設計**: どのデータストアを使うか？
   - `references/decision-tree.md` を Read して選定フローを確認
   - Firestore (Core) / Spanner, Neo4j, Qdrant, ES (Extension)

2. **同期 vs 非同期**: この処理は同期で返すか、非同期に流すか？
   - 即座にレスポンスが必要 → Cloud Run Service で同期処理
   - 確実に完了させたい 1:1 処理 → Cloud Tasks
   - 1:N fan-out → Pub/Sub
   - GCP service event → Eventarc

3. **Client 直接 vs Server 経由**: クライアントから直接 Firestore にアクセスするか？
   - Read-heavy + real-time → Firestore onSnapshot (Client SDK)
   - Write + business logic → Backend API 経由

4. **実装パターン**: `references/patterns.md` を Read して pseudocode を確認

### Phase 3: Deploy & Operations

デプロイ・運用時の手順:

1. **Container build**: multi-stage Docker build → Artifact Registry push
2. **Cloud Run deploy**: `gcloud run deploy` with revision-based rollback
3. **Firestore deploy**: security rules + indexes を `firebase deploy`
4. **Monitoring setup**: Sentry + Cloud Logging + Cloud Monitoring SLI/SLO
5. **Incident response**: rollback → investigate → fix → verify の流れ

### Phase 4: Architecture Decisions

技術選択で迷った場合:
- `references/docs/infrastructure-11-gcp-alternatives.md` を Read して対比構造を確認
- Cloud Run vs GKE → ほぼ Cloud Run。Stateful workload のみ GKE 検討
- Firestore vs Cloud SQL → Client SDK/real-time 必要なら Firestore
- Cloud Tasks vs Pub/Sub → 1:1 explicit なら Tasks、1:N fan-out なら Pub/Sub
- Services vs Jobs vs Worker Pools → HTTP endpoint なら Services、batch なら Jobs、pull consumer なら Worker Pools

## How to Use References

参照ファイルは必要に応じて Read する。全てを一度に読む必要はない。

| Situation | Read this |
|-----------|-----------|
| 新規プロジェクト作成 | `references/scaffold.md` |
| 技術選択・アーキテクチャ判断 | `references/decision-tree.md` |
| 具体的な実装方法 | `references/patterns.md` |
| 詳細な制約・仕様確認 | 対応する `references/docs/infrastructure-*.md` |

## google-dev-knowledge MCP との併用

GCP サービスは頻繁にアップデートされるため、バンドルドキュメントの情報が古くなっている可能性がある。
`google-dev-knowledge` MCP サーバーが利用可能であれば、公式ドキュメントで最新情報を補完できる。
バンドルドキュメントが方針と構造を、MCP が最新の仕様と数値を提供するという役割分担になる。

**MCP 利用可能時のフロー:**
1. バンドルドキュメントを Read して方針・パターンを確認
2. 回答に含まれる主要サービスについて `mcp__google-dev-knowledge__search_documents` で最新の公式ドキュメントを検索（最低1回）
3. 検索結果から関連ドキュメントを `mcp__google-dev-knowledge__get_documents` で取得して詳細確認
4. バンドルドキュメントの情報と公式ドキュメントに差異があれば、公式ドキュメントを優先

MCP での検索が特に有効な場面:
- サービスの quota / limit / pricing に言及する時
- API パラメータやデフォルト値を記載する時
- 新機能 (Worker Pools, Firestore Pipeline 等) について説明する時
- クロスクラウド比較で具体的なスペックを比較する時

**MCP が利用できない場合:**
バンドルドキュメントのみで対応する。ただし、回答の末尾に `references/mcp-setup.md` の
セットアップ案内を提示して、次回以降は最新の公式ドキュメントも参照できるようにユーザーを誘導する。

## Cross-Cloud Comparison

他クラウドとの比較を求められた場合:

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

比較時は「なぜ GCP のこのサービスを選んだのか」を
`references/docs/infrastructure-11-gcp-alternatives.md` に基づいて説明する。
