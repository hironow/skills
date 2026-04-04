# 8. Incident Response / Resilience / Maintenance

## 8.1 Alerting

### 8.1.1 Sentry Alerts

Sentry は unhandled exception 発生時に即座に通知を行う。

| Condition | Action |
|-----------|--------|
| New error (初見の例外) | Alert (Slack / Email) |
| Regression (修正済みエラーの再発) | Alert |
| Spike (短時間での error 急増) | Alert |

### 8.1.2 Cloud Monitoring Alerts (設定推奨)

Cloud Run の built-in metrics に対して alerting policy を設定する。

| Metric | Threshold (recommended) | Severity |
|--------|------------------------|----------|
| Error rate (5xx) | > 1% over 5 min | Critical |
| Request latency P95 | > 5s over 5 min | Warning |
| Instance count | = max instances | Warning |
| Memory utilization | > 90% | Warning |
| Container startup latency | > 10s | Warning |

### 8.1.3 Uptime Check (設定推奨)

Cloud Monitoring の Uptime Check で health check endpoint を外部から定期的に監視する。

| Item | Value |
|------|-------|
| Target | `GET /health` on Cloud Run service URL |
| Interval | 60s |
| Timeout | 10s |
| Alert | Consecutive failure (3 回連続) で通知 |

## 8.2 Rollback

### 8.2.1 Cloud Run Revision Rollback

Cloud Run は deploy ごとに immutable な revision を作成する。
障害発生時は traffic を前の revision に instant switch できる。

```
gcloud run services update-traffic {service} \
  --to-revisions={previous-revision}=100 \
  --region={region}
```

**Rollback 所要時間**: 数秒 (DNS propagation 不要、instant traffic switch)

### 8.2.2 Revision 確認

```
gcloud run revisions list --service={service} --region={region}
```

直近の revision 一覧が表示され、各 revision の image tag / 作成日時を確認できる。

### 8.2.3 Firestore Security Rules / Indexes Rollback

Firebase Security Rules には version 管理がないため、
rollback は git から前バージョンの rules file を取得して再 deploy する。

```
git show HEAD~1:firestore.rules > /tmp/firestore.rules.prev
firebase deploy --only firestore:rules
```

## 8.3 Maintenance Mode

### 8.3.1 Firebase Remote Config

Firebase Remote Config の `maintenance` parameter で
クライアント側の maintenance mode を制御する。
Backend の deploy やデータ移行中にクライアントからのリクエストを抑止する。

| Parameter | Type | Default | Effect |
|-----------|------|---------|--------|
| `maintenance` | boolean | `false` | `true` で client UI に maintenance 画面を表示 |

**操作**: Firebase Console > Remote Config > `maintenance` を `true` に変更 > Publish

### 8.3.2 Cloud Run Traffic Control

段階的なリリースが必要な場合、Cloud Run の traffic splitting を使用する。

```
gcloud run services update-traffic {service} \
  --to-revisions={new-revision}=10,{current-revision}=90 \
  --region={region}
```

## 8.4 Load Testing

### 8.4.1 k6

OpenAPI spec から k6 test script を生成し、
Cloud Run service に対して load test を実行する。

| Item | Detail |
|------|--------|
| Tool | [k6](https://k6.io/) (Grafana) |
| Script Generation | openapi-generator-cli -> k6 script |
| Target | Cloud Run service URL (dev environment) |
| Execution | Local or CI |

### 8.4.2 runn Scenario Test

API の正常系フローを scenario として定義し、
deploy 後の smoke test として実行する。

| Item | Detail |
|------|--------|
| Tool | [runn](https://github.com/k1LoW/runn) |
| Format | YAML-based scenario definition |
| Protocol | HTTP / JSON-RPC 2.0 |
| Execution | CI pipeline (post-deploy) |

## 8.5 Incident Response Flow (推奨)

```
1. Detection
   |
   +--> Sentry alert / Cloud Monitoring alert / User report
   |
2. Triage
   |
   +--> Cloud Logging で error log 確認
   +--> Sentry で stack trace / breadcrumbs 確認
   +--> Cloud Monitoring で metrics 確認 (latency, error rate)
   |
3. Mitigation
   |
   +--> [Option A] Cloud Run revision rollback (即座)
   +--> [Option B] Maintenance mode ON (Firebase Remote Config)
   +--> [Option C] Hotfix deploy (build -> push -> deploy)
   |
4. Resolution
   |
   +--> Root cause fix + test
   +--> Normal deploy
   +--> Maintenance mode OFF
   |
5. Post-Mortem
   |
   +--> Timeline 記録
   +--> Root cause 分析
   +--> 再発防止策
```

## 8.6 Backup & Recovery

### 8.6.1 RPO / RTO 定義

| Store | Tier | RPO (目標復旧時点) | RTO (目標復旧時間) | 根拠 |
|-------|------|-------------------|-------------------|------|
| Firestore | Core | 1 hour (PITR) | 1 hour | PITR 有効化で最大 7 日前まで任意時点復元 |
| Cloud Storage | Core | 0 (versioning) | 30 min | Object versioning で即時復元 |
| Cloud Spanner | Extension | 1 hour (version GC) | 1 hour | Version GC policy 内の PITR |
| Neo4j (AuraDB) | Extension | Continuous | 1 hour | Managed backup (AuraDB 自動) |
| Qdrant (Qdrant Cloud) | Extension | Continuous | 1 hour | Managed snapshot (Qdrant Cloud 自動) |
| Elasticsearch (Elastic Cloud) | Extension | Continuous | 1 hour | Managed snapshot (Elastic Cloud 自動) |

### 8.6.2 Firestore

| Method | Detail |
|--------|--------|
| Managed Export | `gcloud firestore export gs://{bucket}` |
| Import | `gcloud firestore import gs://{bucket}/{export-path}` |
| Frequency | Daily scheduled export (Cloud Scheduler -> Cloud Functions) |
| Point-in-Time Recovery | Firestore PITR (最大 7 日前まで復元可能、要有効化) |

### 8.6.3 Cloud Storage

| Method | Detail |
|--------|--------|
| Object Versioning | Bucket-level versioning で上書き・削除前の version を保持 |
| Lifecycle Policy | N 日後の古い version を自動削除 |

### 8.6.4 Cloud Spanner [Extension]

| Method | Detail |
|--------|--------|
| Managed Backup | `gcloud spanner backups create` |
| Restore | `gcloud spanner databases restore` |
| PITR | Version GC policy (default 1 hour) 内の任意時点に復元可能 |

### 8.6.5 Neo4j / Qdrant / Elasticsearch [Extension]

本番環境では各 managed service (AuraDB, Qdrant Cloud, Elastic Cloud) を使用するため、
backup は各 provider の managed backup 機能に委譲する。

| Service | Managed Backup | Restore Method |
|---------|---------------|----------------|
| Neo4j AuraDB | Automatic daily snapshot | Console / API から restore |
| Qdrant Cloud | Automatic snapshot | Console から restore |
| Elastic Cloud | Automatic snapshot | Snapshot and Restore API |

Local development (Docker Compose) では volume snapshot または dump command で対応:

| Service | Local Backup Command |
|---------|---------------------|
| Neo4j | `neo4j-admin database dump` |
| Qdrant | Snapshot API (`POST /collections/{name}/snapshots`) |
| Elasticsearch | Snapshot and Restore API |

### 8.6.6 復元演習

| 項目 | 方針 |
|------|------|
| 頻度 | 四半期に 1 回 |
| 対象 | Core tier の全データストア (Firestore, Cloud Storage) |
| 検証内容 | Backup からの restore 実行、データ整合性確認、RTO 内完了の確認 |
| 記録 | 実施日・結果・改善事項を記録 |
