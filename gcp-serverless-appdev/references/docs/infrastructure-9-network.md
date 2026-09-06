# 9. Network / Ingress / Boundary Defense / TLS

## 9.1 Public Ingress: Cloud Run Default Domain

At deploy time a Cloud Run service is automatically given a `*.run.app` domain
and a Google-managed TLS certificate.

### 9.1.1 Default Domain

```
https://{service-identifier}.run.app
```

> **Note**: The URL format is non-deterministic and cannot be predicted.
> Retrieve it with `gcloud run services describe` after deploy.

| Item | Detail |
|------|--------|
| TLS | Google-managed (auto-renewed, no configuration required) |
| Certificate Authority | Google Trust Services or Let's Encrypt |
| Protocol | HTTPS only (HTTP -> HTTPS redirect) |

### 9.1.2 Custom Domain (Optional)

To use your own domain, either use Cloud Run domain mapping or place an
external HTTP(S) Load Balancer in front.

| Method | Use Case |
|--------|----------|
| Cloud Run domain mapping | Simple custom domain assignment |
| External HTTP(S) LB | When CDN, WAF, or multi-region routing is needed |

When using a custom domain, set a CNAME / A record in DNS and wait for the
Google-managed certificate to be provisioned (up to 24 hours).

## 9.2 Ingress Control

### 9.2.1 Cloud Run Ingress Setting

The `--ingress` flag of Cloud Run restricts which traffic can reach the service.

| Setting | Allowed Range | Use Case |
|---------|---------|----------|
| `all` | Internet + internal | Frontend (public-facing) |
| `internal` | VPC + GCP services only | Internal API (Cloud Tasks/Scheduler callback) |
| `internal-and-cloud-load-balancing` | VPC + GCP services + LB | Public service behind an LB |

### 9.2.2 Recommended Configuration

| Service | Ingress | Rationale |
|---------|---------|-----------|
| Frontend (Cloud Run) | `all` | Accessed directly by end users |
| Backend (Cloud Run) | `all` | Accessed from the frontend and client apps |
| Internal callback endpoint | `internal` | Only from Cloud Tasks / Scheduler |

If the backend is restricted to `internal`, traffic from the frontend to the
backend must go through a serverless VPC connector inside the same VPC.
In the initial configuration the boundary is secured with `all` plus Firebase
Auth token verification.

## 9.3 Service-to-Service Authentication

### 9.3.1 GCP Service -> Cloud Run

When Cloud Tasks, Cloud Scheduler, or Eventarc call a Cloud Run endpoint, they
automatically attach an OIDC token tied to a service account.
Setting `--no-allow-unauthenticated` on the Cloud Run side rejects any request
that does not carry a valid OIDC token.

```
Cloud Tasks / Scheduler
  |
  +--> Attach OIDC token (service account) to the Authorization header
  |
Cloud Run (--no-allow-unauthenticated)
  |
  +--> IAM verifies the OIDC token
  +--> Only SAs holding roles/run.invoker are allowed
```

### 9.3.2 Backend -> External API

Egress from the backend to external APIs (LLM provider, TTS, and so on) uses the
Cloud Run default egress (public internet).

| Item | Detail |
|------|--------|
| Egress | Public internet (default) |
| Authentication | API key / OAuth token (Secret Manager / dotenvx) |
| Rate Limiting | Application-level (follows the quota of the external API) |

## 9.4 CORS Policy

When the frontend and backend are on different origins, set CORS headers on the
backend. Browser-origin requests to a Cloud Storage bucket also require CORS
configuration.

### 9.4.1 Backend CORS

Set `allow_origins`, `allow_methods`, and `allow_headers` in FastAPI middleware.

### 9.4.2 Cloud Storage CORS

Create `cors.json` and apply it with `gsutil cors set cors.json gs://{bucket}`.

| Item | Detail |
|------|--------|
| Allowed Origins | Frontend domain (dev/prd) |
| Allowed Methods | GET (download) |
| Max Age | 3600s |

## 9.5 DDoS Protection

Because Cloud Run traffic passes through the Google Front End (GFE), Layer 3/4
DDoS protection is provided automatically by the GCP infrastructure.

When Layer 7 (application-level) protection is needed, combine Cloud Armor with
an External HTTP(S) Load Balancer.

| Tier | Protection | Configuration |
|------|-----------|---------------|
| Default (GFE) | L3/L4 DDoS mitigation | Automatic, no config required |
| Cloud Armor (Optional) | L7 WAF, rate limiting, geo-blocking | Requires External LB |

## 9.6 Firewall / VPC (Optional)

By default Cloud Run runs outside the VPC.
To access resources inside the VPC (Cloud SQL, Memorystore, and so on),
configure **Direct VPC egress** (recommended) or a Serverless VPC Access connector.

| Method | Status | Throughput | Cost |
|--------|--------|-----------|------|
| **Direct VPC egress** | GA (recommended) | ~2x that of the connector | No idle cost |
| Serverless VPC Access connector | GA (legacy) | Standard | Connector instance billed continuously |

A VPC is not needed in the initial configuration. VPC design becomes necessary
when self-hosting Extension tier data stores on GCE / GKE.

## 9.7 Network Summary

```
Internet
  |
  +--> [Cloud Run: Frontend] --ingress=all, HTTPS (Google-managed TLS)
  |         |
  |         +--> [Cloud Run: Backend] --ingress=all, Firebase Auth token
  |                   |
  |                   +--> [Firestore] (IAM, Admin SDK)
  |                   +--> [Cloud Storage] (IAM)
  |                   +--> [Cloud Tasks] (IAM) --> callback to Cloud Run (OIDC)
  |                   +--> [External API] (API key, egress via public internet)
  |
  +--> [Cloud Tasks / Scheduler / Eventarc]
           |
           +--> [Cloud Run: Backend] --no-allow-unauthenticated (OIDC)
```

Legend:
- Internet: End-user access
- Cloud Run: Frontend: Public-facing web application
- Cloud Run: Backend: API server (authenticated)
- Firestore / Cloud Storage: Data layer (IAM-protected)
- Cloud Tasks / Scheduler / Eventarc: Async triggers (OIDC-authenticated)
- External API: Third-party services (API key)
