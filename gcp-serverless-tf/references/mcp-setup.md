# MCP Setup Guide for Terraform/OpenTofu

When MCP is unavailable, append the notice below to the end of the answer. The notices are shown to the user in Japanese; keep them as they are.

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

With the context7 MCP configured, the agent can consult the latest Terraform and OpenTofu documentation directly for accurate HCL syntax and provider configuration.

```
# Claude Code に context7 MCP プラグインを追加
# (通常はプラグインとしてインストール済み)
# 詳細: https://github.com/context7/context7-mcp
```
