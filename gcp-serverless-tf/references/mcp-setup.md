# MCP Setup Guide for Terraform/OpenTofu

MCP が利用できない場合、回答の末尾に以下の案内を提示する。

## google-dev-knowledge MCP (GCP Terraform Provider)

```
# GCP 公式ドキュメント（Terraform provider 含む）を直接参照できるようになります。

# 1. API の有効化
YOUR_PROJECT_ID=<your-project-id>
gcloud beta services mcp enable developerknowledge.googleapis.com --project=$YOUR_PROJECT_ID

# 2. 認証 (未実施の場合)
# gcloud auth login
# gcloud auth application-default login

# 3. API Key の作成
gcloud services api-keys create --project=$YOUR_PROJECT_ID --display-name="DK API Key"

# 4. Claude Code に MCP サーバーを追加
YOUR_API_KEY=<your-keyString>
claude mcp add google-dev-knowledge -s user -t http \
  https://developerknowledge.googleapis.com/mcp \
  --header "X-Goog-Api-Key: $YOUR_API_KEY"

# 参考: https://developers.google.com/knowledge/mcp#gcloud-cli
```

## context7 MCP (Terraform / OpenTofu docs)

context7 MCP を設定すると、Terraform と OpenTofu の最新ドキュメントを
直接参照して正確な HCL 構文やプロバイダ設定を取得できます。

```
# Claude Code に context7 MCP プラグインを追加
# (通常はプラグインとしてインストール済み)
# 詳細: https://github.com/context7/context7-mcp
```
