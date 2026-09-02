---
name: gcp-serverless-tf
description: >
  Generate and maintain Terraform/OpenTofu configurations for GCP serverless
  architectures (Cloud Run, Firestore, Cloud Tasks, Pub/Sub, Cloud Functions,
  Eventarc, Cloud Scheduler, Artifact Registry, Secret Manager).
  Use for any Terraform or OpenTofu work on those services — initial .tf
  generation, updating .tf after application code changes, and the
  Terraform-vs-OpenTofu choice — including Japanese requests such as
  "tfファイル作って" or "インフラをコード化".
---

# GCP Serverless Terraform/OpenTofu Skill

GCP サーバーレスアーキテクチャの Terraform/OpenTofu 構成を生成・保守する。
`gcp-serverless-appdev` スキルで定義されたアーキテクチャ（Cloud Run, Firestore,
Cloud Tasks, Pub/Sub 等）に対応する `.tf` ファイルを生成し、
アプリケーションコードの変更に追従して `.tf` を更新する。

## Two Modes

### Mode 1: Init (初期生成)

プロジェクトに `.tf` ファイルがまだ存在しない場合。
ユーザーのアプリケーションコード（Dockerfile, main.py, docker-compose.yaml 等）を
読み取り、使用している GCP サービスを特定して、対応する `.tf` ファイル群を生成する。

### Mode 2: Diff (差分更新)

既存の `.tf` ファイルがある場合。
アプリケーションコードの変更（git diff や新規ファイル）を読み取り、
インフラに影響する変更を特定して `.tf` の差分を提案・適用する。

## Workflow

### Step 1: ユーザーの意図を確認

以下を確認する（不明なら質問する）:

1. **Terraform or OpenTofu?** — どちらを使うか。構文はほぼ同一だが、
   `required_providers` の registry URL と state encryption が異なる
2. **State backend** — GCS バケット or ローカル or Terraform Cloud
3. **環境構成** — ディレクトリ分離（推奨）or workspaces

### Step 2: アプリケーション構成を読み取る

以下のファイルを Read してインフラ要件を抽出する:

- `docker-compose.yaml` — 使用しているエミュレータからサービスを推定
- `Dockerfile` — Cloud Run のコンテナ設定
- `pyproject.toml` / `package.json` — GCP SDK 依存から使用サービスを特定
- `main.py` / アプリケーションコード — エンドポイント、Cloud Tasks/Pub/Sub 呼び出し
- `firestore.rules` — Firestore の存在確認
- `firebase.json` — Firebase プロジェクト設定
- `.github/workflows/` — CI/CD 設定

### Step 3: リソースマッピング

検出したサービスを Terraform リソースにマッピングする。
詳細は `references/resource-map.md` を Read して確認。

主要なマッピング:

| GCP Service | Terraform Resource | Module |
|---|---|---|
| Cloud Run Service | `google_cloud_run_v2_service` | `modules/cloud-run/` |
| Cloud Run Job | `google_cloud_run_v2_job` | `modules/cloud-run/` |
| Firestore | `google_firestore_database` | `modules/firestore/` |
| Cloud Tasks Queue | `google_cloud_tasks_queue` | `modules/async/` |
| Pub/Sub Topic | `google_pubsub_topic` | `modules/async/` |
| Pub/Sub Subscription | `google_pubsub_subscription` | `modules/async/` |
| Cloud Functions | `google_cloudfunctions2_function` | `modules/functions/` |
| Eventarc Trigger | `google_eventarc_trigger` | `modules/async/` |
| Cloud Scheduler | `google_cloud_scheduler_job` | `modules/async/` |
| Artifact Registry | `google_artifact_registry_repository` | `modules/registry/` |
| Secret Manager | `google_secret_manager_secret` | `modules/secrets/` |
| Service Account | `google_service_account` | `modules/iam/` |
| IAM Binding | `google_project_iam_member` | `modules/iam/` |

### Step 4: ディレクトリ構造を生成

Google Cloud 公式ベストプラクティスに従った構造:

```
terraform/                    # or infra/
├── modules/
│   ├── cloud-run/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   ├── firestore/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   ├── async/                # Cloud Tasks, Pub/Sub, Eventarc, Scheduler
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   ├── registry/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   ├── secrets/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   └── iam/
│       ├── main.tf
│       ├── variables.tf
│       └── outputs.tf
├── environments/
│   ├── dev/
│   │   ├── main.tf           # module 呼び出し + dev 固有値
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   ├── backend.tf        # state backend 設定
│   │   └── terraform.tfvars  # dev 環境変数
│   ├── staging/
│   │   └── ...
│   └── prod/
│       └── ...
└── versions.tf               # provider version constraints (共通)
```

### Step 5: MCP で最新仕様を確認

`.tf` ファイルを書く前に、MCP で最新のリソース仕様を確認する。
GCP のリソース属性（特に Cloud Run v2, Firestore のパラメータ）は
頻繁に変わるため、一般知識だけでは不正確になりやすい。

**利用可能な MCP:**

1. **google-dev-knowledge** — GCP Terraform provider の最新ドキュメント
   ```
   mcp__google-dev-knowledge__search_documents
   → "terraform google_cloud_run_v2_service configuration"
   → "terraform google_firestore_database resource"
   ```

2. **context7** — Terraform/OpenTofu の最新構文。`resolve-library-id` で "hashicorp/terraform" / "opentofu" を解決し、`query-docs` で "module structure best practices" / "provider version constraints" を引く。

**MCP 利用フロー:**
1. 生成するリソースごとに `google-dev-knowledge` で最新の属性を検索
2. 記法に迷ったら `context7` で Terraform/OpenTofu の最新構文を確認
3. バンドルの `references/resource-map.md` と MCP の情報が異なる場合は MCP を優先

**MCP が利用できない場合:**
バンドルの references のみで対応するが、回答の末尾に
`references/mcp-setup.md` のセットアップ案内を提示する。

### Step 6: .tf ファイルを生成

`references/resource-map.md` を Read してリソース定義のテンプレートを確認し、
MCP で最新仕様を裏付けた上で `.tf` ファイルを生成する。

**生成時の原則:**

1. **Terraform と OpenTofu の互換性**: 基本的に HCL は共通。
   差異がある場合はコメントで明記する
2. **Region 固定**: `asia-northeast1` をデフォルトにする
   （`gcp-serverless-appdev` の Core Principle に準拠）
3. **変数化**: ハードコードしない。project_id, region, environment は変数にする
4. **API 有効化**: 各モジュールで `google_project_service` を含め、
   `enable_apis` 変数で制御可能にする
5. **最小権限 IAM**: サービスアカウントには必要最小限のロールのみ付与
6. **命名規則**: リソース名はアンダースコア区切り、
   唯一のリソースは `main` と命名

## Diff Mode の詳細

既存の `.tf` がある場合の更新フロー:

1. **変更を検出**: `git diff` またはユーザーが指定したファイルの変更を読む
2. **インフラ影響を判定**: 以下の変更パターンを検出する
   - 新しい GCP SDK import → 新リソースが必要
   - 新しいエンドポイント → Cloud Run の環境変数やサービス設定
   - 新しい Cloud Tasks / Pub/Sub 呼び出し → キュー/トピック追加
   - Dockerfile の変更 → Artifact Registry やビルド設定
   - 環境変数の追加 → Secret Manager or Cloud Run env vars
3. **差分 .tf を提案**: 追加・変更が必要な `.tf` ファイルの差分を提示
4. **`terraform plan` 推奨**: 変更適用前に `terraform plan` で確認するよう促す

## References

| Situation | Read this |
|---|---|
| リソース定義テンプレート | `references/resource-map.md` |
| MCP セットアップ案内 | `references/mcp-setup.md` |

## Terraform vs OpenTofu

| 項目 | Terraform | OpenTofu |
|---|---|---|
| Provider registry | `registry.terraform.io` | `registry.opentofu.org` |
| State encryption | Terraform Cloud のみ | ネイティブ対応 |
| License | BSL 1.1 | MPL 2.0 (OSS) |
| HCL 互換性 | 基準 | ほぼ完全互換 |
| `required_providers` | `source = "hashicorp/google"` | 同左 (fallback あり) |

実用上、`.tf` ファイルの内容はほぼ同一。`versions.tf` の書き方だけ注意する。
