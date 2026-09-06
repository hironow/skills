# 6. Monitoring / Error Tracking / Logging

## 6.1 Error Tracking: Sentry

**Service**: [Sentry](https://sentry.io/)

A real-time error tracking platform. It provides unhandled exception capture,
breadcrumbs (event context), release tracking, and performance monitoring.

### 6.1.1 Integration Points

| Component | SDK | Purpose |
|-----------|-----|---------|
| Frontend | `@sentry/nextjs` | Client-side error capture + Web Vitals |
| Backend | `sentry-sdk[fastapi]` | Server-side exception capture + trace |

### 6.1.2 Configuration

| Setting | Detail |
|---------|--------|
| DSN | Injected through an environment variable |
| Environment | `APP_ENV` (dev/prd) |
| Release | Git commit SHA or version tag |
| Sample Rate | Configurable per environment |

## 6.2 Logging: Cloud Logging + structlog

**Service**: [Google Cloud Logging](https://cloud.google.com/logging)

Cloud Run stdout/stderr is collected into Cloud Logging automatically.

### 6.2.1 Application-Level Logging

**Library**: [structlog](https://www.structlog.org/)

A structured logging library. It emits structured logs in JSON format and integrates with
Cloud Logging filtering / alerting based on severity, trace, and labels.

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
| Export | Log sink to BigQuery / Cloud Storage / Pub/Sub |

## 6.3 Metrics & Alerting: Cloud Monitoring

**Service**: [Google Cloud Monitoring](https://cloud.google.com/monitoring)

It collects Cloud Run built-in metrics automatically.
Custom metrics, uptime checks, and alerting policies can be configured.

### 6.3.1 Built-in Cloud Run Metrics

| Metric | Description |
|--------|-------------|
| Request Count | Total request count by response code |
| Request Latency | P50/P95/P99 latency distribution |
| Instance Count | Active instance count |
| CPU Utilization | Per-instance CPU usage |
| Memory Utilization | Per-instance memory usage |
| Container Startup Latency | Cold start time |

### 6.3.2 SLI / SLO Definitions

**SLI (Service Level Indicator)**: the metric that measures service quality.
**SLO (Service Level Objective)**: the target value for an SLI.

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
| Email | Secondary: critical alerts only |

### 6.3.5 Incident Escalation

For the first response after an incident is detected, see [infrastructure-8-incident.md Section 8.5](infrastructure-8-incident.md#85-incident-response-flow-recommended).

## 6.4 LLM Observability (Optional)

For LLM-based applications, introduce a specialized platform for tracking
prompts, completions, and evaluations.

| Tool | Purpose |
|------|---------|
| Weights & Biases (Weave) | LLM trace, prompt versioning, evaluation |
| Laminar | LLM observability, cost tracking |

## 6.5 Security Scanning: Semgrep

**Tool**: [Semgrep](https://semgrep.dev/)

A static analysis tool for security vulnerability detection.
Custom rules can be defined to enforce project-specific security patterns.

| Item | Detail |
|------|--------|
| Integration | CI pipeline (GitHub Actions) |
| Rules | Built-in + custom `.semgrep/` rules |
| Target | Python source code |

## 6.6 Analytics: Google Analytics (Optional)

Web analytics can be collected through the Firebase integration.
The measurement stream is specified with `NEXT_PUBLIC_GOOGLE_ANALYTICS_ID`.
