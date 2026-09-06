# 8. Incident Response / Resilience / Maintenance

## 8.1 Alerting

### 8.1.1 Sentry Alerts

Sentry notifies immediately when an unhandled exception occurs.

| Condition | Action |
|-----------|--------|
| New error (an exception seen for the first time) | Alert (Slack / Email) |
| Regression (an already-fixed error recurring) | Alert |
| Spike (a sharp increase in errors over a short period) | Alert |

### 8.1.2 Cloud Monitoring Alerts (Recommended Setup)

Set an alerting policy on the built-in metrics of Cloud Run.

| Metric | Threshold (recommended) | Severity |
|--------|------------------------|----------|
| Error rate (5xx) | > 1% over 5 min | Critical |
| Request latency P95 | > 5s over 5 min | Warning |
| Instance count | = max instances | Warning |
| Memory utilization | > 90% | Warning |
| Container startup latency | > 10s | Warning |

### 8.1.3 Uptime Check (Recommended Setup)

Use a Cloud Monitoring Uptime Check to monitor the health check endpoint
periodically from outside.

| Item | Value |
|------|-------|
| Target | `GET /health` on Cloud Run service URL |
| Interval | 60s |
| Timeout | 10s |
| Alert | Notify on consecutive failures (3 in a row) |

## 8.2 Rollback

### 8.2.1 Cloud Run Revision Rollback

Cloud Run creates an immutable revision for every deploy.
When an incident occurs, traffic can be switched instantly to the previous revision.

```
gcloud run services update-traffic {service} \
  --to-revisions={previous-revision}=100 \
  --region={region}
```

**Time required for rollback**: a few seconds (no DNS propagation needed, instant traffic switch)

### 8.2.2 Checking Revisions

```
gcloud run revisions list --service={service} --region={region}
```

This shows a list of the most recent revisions, with the image tag and creation
time of each revision.

### 8.2.3 Firestore Security Rules / Indexes Rollback

Firebase Security Rules have no version management, so a rollback means fetching
the previous version of the rules file from git and deploying it again.

```
git show HEAD~1:firestore.rules > /tmp/firestore.rules.prev
firebase deploy --only firestore:rules
```

## 8.3 Maintenance Mode

### 8.3.1 Firebase Remote Config

The `maintenance` parameter of Firebase Remote Config controls client-side
maintenance mode.
It suppresses requests from clients during a backend deploy or a data migration.

| Parameter | Type | Default | Effect |
|-----------|------|---------|--------|
| `maintenance` | boolean | `false` | `true` shows a maintenance screen in the client UI |

**Operation**: Firebase Console > Remote Config > change `maintenance` to `true` > Publish

### 8.3.2 Cloud Run Traffic Control

When a gradual release is needed, use Cloud Run traffic splitting.

```
gcloud run services update-traffic {service} \
  --to-revisions={new-revision}=10,{current-revision}=90 \
  --region={region}
```

## 8.4 Load Testing

### 8.4.1 k6

Generate a k6 test script from the OpenAPI spec and run a load test against the
Cloud Run service.

| Item | Detail |
|------|--------|
| Tool | [k6](https://k6.io/) (Grafana) |
| Script Generation | openapi-generator-cli -> k6 script |
| Target | Cloud Run service URL (dev environment) |
| Execution | Local or CI |

### 8.4.2 runn Scenario Test

Define the happy-path flow of the API as a scenario and run it as a smoke test
after deploy.

| Item | Detail |
|------|--------|
| Tool | [runn](https://github.com/k1LoW/runn) |
| Format | YAML-based scenario definition |
| Protocol | HTTP / JSON-RPC 2.0 |
| Execution | CI pipeline (post-deploy) |

## 8.5 Incident Response Flow (Recommended)

```
1. Detection
   |
   +--> Sentry alert / Cloud Monitoring alert / User report
   |
2. Triage
   |
   +--> Check error logs in Cloud Logging
   +--> Check stack trace / breadcrumbs in Sentry
   +--> Check metrics in Cloud Monitoring (latency, error rate)
   |
3. Mitigation
   |
   +--> [Option A] Cloud Run revision rollback (immediate)
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
   +--> Record the timeline
   +--> Analyze the root cause
   +--> Define recurrence prevention measures
```

## 8.6 Backup & Recovery

### 8.6.1 RPO / RTO Definitions

| Store | Tier | RPO (recovery point objective) | RTO (recovery time objective) | Rationale |
|-------|------|-------------------|-------------------|------|
| Firestore | Core | 1 hour (PITR) | 1 hour | With PITR enabled, restore to any point up to 7 days back |
| Cloud Storage | Core | 0 (versioning) | 30 min | Immediate restore through object versioning |
| Cloud Spanner | Extension | 1 hour (version GC) | 1 hour | PITR within the version GC policy |
| Neo4j (AuraDB) | Extension | Continuous | 1 hour | Managed backup (automatic in AuraDB) |
| Qdrant (Qdrant Cloud) | Extension | Continuous | 1 hour | Managed snapshot (automatic in Qdrant Cloud) |
| Elasticsearch (Elastic Cloud) | Extension | Continuous | 1 hour | Managed snapshot (automatic in Elastic Cloud) |

### 8.6.2 Firestore

| Method | Detail |
|--------|--------|
| Managed Export | `gcloud firestore export gs://{bucket}` |
| Import | `gcloud firestore import gs://{bucket}/{export-path}` |
| Frequency | Daily scheduled export (Cloud Scheduler -> Cloud Functions) |
| Point-in-Time Recovery | Firestore PITR (can restore up to 7 days back; must be enabled) |

### 8.6.3 Cloud Storage

| Method | Detail |
|--------|--------|
| Object Versioning | Bucket-level versioning retains the version from before an overwrite or delete |
| Lifecycle Policy | Automatically delete old versions after N days |

### 8.6.4 Cloud Spanner [Extension]

| Method | Detail |
|--------|--------|
| Managed Backup | `gcloud spanner backups create` |
| Restore | `gcloud spanner databases restore` |
| PITR | Can restore to any point within the version GC policy (default 1 hour) |

### 8.6.5 Neo4j / Qdrant / Elasticsearch [Extension]

Production uses the managed service for each of these (AuraDB, Qdrant Cloud,
Elastic Cloud), so backup is delegated to each provider's managed backup feature.

| Service | Managed Backup | Restore Method |
|---------|---------------|----------------|
| Neo4j AuraDB | Automatic daily snapshot | Restore from the console or API |
| Qdrant Cloud | Automatic snapshot | Restore from the console |
| Elastic Cloud | Automatic snapshot | Snapshot and Restore API |

In local development (Docker Compose), use a volume snapshot or a dump command:

| Service | Local Backup Command |
|---------|---------------------|
| Neo4j | `neo4j-admin database dump` |
| Qdrant | Snapshot API (`POST /collections/{name}/snapshots`) |
| Elasticsearch | Snapshot and Restore API |

### 8.6.6 Restore Drill

| Item | Policy |
|------|------|
| Frequency | Once per quarter |
| Scope | All Core tier data stores (Firestore, Cloud Storage) |
| What to verify | Run a restore from backup, check data integrity, confirm completion within RTO |
| Record | Record the date performed, the result, and improvement items |
