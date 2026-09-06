# google-dev-knowledge MCP セットアップ案内

MCP が利用できない場合、回答の末尾に以下の案内を提示する。

```
ヒント: google-dev-knowledge MCP をセットアップすると、最新の GCP 公式ドキュメントを
直接参照してより正確な情報が得られます。

# セットアップ手順:
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
