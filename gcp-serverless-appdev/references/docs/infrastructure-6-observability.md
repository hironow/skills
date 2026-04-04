# 6. Monitoring / Error Tracking / Logging

## 6.1 Error Tracking: Sentry

**Service**: [Sentry](https://sentry.io/)

Real-time error tracking platform。Unhandled exception, breadcrumbs (event context),
release tracking, performance monitoring を提供する。

### 6.1.1 Integration Points

| Component | SDK | Purpose |
|-----------|-----|---------|
| Frontend | `@sentry/nextjs` | Client-side error capture + Web Vitals |
| Backend | `sentry-sdk[fastapi]` | Server-side exception capture + trace |

### 6.1.2 Configuration

| Setting | Detail |
|---------|--------|
| DSN | Environment variable で inject |
| Environment | `APP_ENV` (dev/prd) |
| Release | Git commit SHA or version tag |
| Sample Rate | Configurable per environment |

## 6.2 Logging: Cloud Logging + structlog

**Service**: [Google Cloud Logging](https://cloud.google.com/logging)

Cloud Run の stdout/stderr は自動的に Cloud Logging に集約される。

### 6.2.1 Application-Level Logging

**Library**: [structlog](https://www.structlog.org/)

Structured logging library。JSON format の structured log を出力し、
Cloud Logging の severity, trace, labels による filtering / alerting と統合する。

| Property | Detail |
|----------|--------|
| Format | JSON (structured) |
| Integration | Cloud Logging auto-ingest from stdout |
| Context | Automatic context binding (request ID, user ID, etc.) |

### 6.2.2 Cloud Logging Characteristics

| Property | Detail |
|----------|--------|
| Collection | Automatic for Cloud Run (stdout/stderr) |
| Retention | Default 30 days (configurable) |
| Integration | Cloud Monitoring alerts via log-based metrics |
| Export | BigQuery / Cloud Storage / Pub/Sub へのログ sink |

## 6.3 Metrics & Alerting: Cloud Monitoring

**Service**: [Google Cloud Monitoring](https://cloud.google.com/monitoring)

Cloud Run の built-in metrics を自動収集する。
Custom metrics, uptime checks, alerting policy を設定可能。

### 6.3.1 Built-in Cloud Run Metrics

| Metric | Description |
|--------|-------------|
| Request Count | Total request count by response code |
| Request Latency | P50/P95/P99 latency distribution |
| Instance Count | Active instance count |
| CPU Utilization | Per-instance CPU usage |
| Memory Utilization | Per-instance memory usage |
| Container Startup Latency | Cold start time |

### 6.3.2 SLI / SLO 定義

**SLI (Service Level Indicator)**: サービス品質を測定する指標。
**SLO (Service Level Objective)**: SLI に対する目標値。

| SLI | Measurement | SLO | Window |
|-----|-------------|-----|--------|
| Availability | `1 - (5xx responses / total responses)` | >= 99.5% | 30-day rolling |
| Latency (P95) | Request latency P95 | <= 3s | 30-day rolling |
| Latency (P99) | Request latency P99 | <= 10s | 30-day rolling |
| Error Rate | `5xx responses / total responses` | <= 0.5% | 30-day rolling |

### 6.3.3 Alerting Policy

| Alert | Condition | Window | Severity | Notification |
|-------|-----------|--------|----------|-------------|
| High Error Rate | 5xx rate > 1% | 5 min | Critical | Slack + Email |
| High Latency | P95 > 5s | 5 min | Warning | Slack |
| Instance Saturation | instances = max_instances | 5 min | Warning | Slack |
| Memory Pressure | memory > 90% | 5 min | Warning | Slack |
| Uptime Failure | Health check 3 consecutive failures | 3 min | Critical | Slack + Email |
| Cloud Tasks Failure | Failed task count > 0 | 1 hour | Warning | Slack |

### 6.3.4 Notification Channel

| Channel | Use Case |
|---------|----------|
| Slack (webhook) | Primary: all alerts |
| Email | Secondary: Critical alerts のみ |

### 6.3.5 Incident Escalation

障害検知後の初動は [infrastructure-8-incident.md Section 8.5](infrastructure-8-incident.md#85-incident-response-flow-推奨) を参照。

## 6.4 LLM Observability (Optional)

LLM-based application では、prompt / completion / evaluation の
tracking に specialized platform を導入する。

| Tool | Purpose |
|------|---------|
| Weights & Biases (Weave) | LLM trace, prompt versioning, evaluation |
| Laminar | LLM observability, cost tracking |

## 6.5 Security Scanning: Semgrep

**Tool**: [Semgrep](https://semgrep.dev/)

Static analysis tool for security vulnerability detection。
Custom rule を定義して project-specific な security pattern を enforce できる。

| Item | Detail |
|------|--------|
| Integration | CI pipeline (GitHub Actions) |
| Rules | Built-in + custom `.semgrep/` rules |
| Target | Python source code |

## 6.6 Analytics: Google Analytics (Optional)

Firebase Integration 経由で Web analytics を収集可能。
`NEXT_PUBLIC_GOOGLE_ANALYTICS_ID` で measurement stream を指定する。
