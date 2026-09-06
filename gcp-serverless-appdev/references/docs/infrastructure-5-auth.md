# 5. Authentication / Authorization / Secrets

## 5.1 User Authentication: Firebase Authentication

**Service**: [Firebase Authentication](https://firebase.google.com/docs/auth)

A managed identity platform. It integrates identity providers such as Google, Apple, and
email-password, and provides JWT (ID Token) based authentication.
The client SDK manages the token lifecycle (refresh, expiry) automatically,
and the backend verifies the token with the Admin SDK.

### 5.1.1 Key Characteristics

| Property | Detail |
|----------|--------|
| Token Format | JWT (RS256) |
| Token Lifetime | 1 hour (auto-refresh by client SDK) |
| Identity Providers | Configurable (Google, Apple, Email, etc.) |
| User Management | Firebase Console / Admin SDK |
| Multi-tenancy | Project-level isolation |

### 5.1.2 Authentication Flow

```
Client App
  |
  +--> Firebase Auth SDK (sign-in with provider)
  |
  +--> Receive ID Token (JWT)
  |
  +--> Send ID Token in Authorization header to Backend
  |
Backend (Cloud Run)
  |
  +--> Verify ID Token via Firebase Admin SDK
  |
  +--> Extract uid, claims from verified token
```

## 5.2 Backend Authorization

### 5.2.1 Service-to-Service Authentication

Communication between GCP services (Cloud Tasks -> Cloud Run, Cloud Scheduler -> Cloud Run,
Cloud Functions -> Cloud Run) uses service account authentication with OIDC tokens.
Ingress is controlled with the Cloud Run `--ingress` setting
(`all` / `internal` / `internal-and-cloud-load-balancing`).

### 5.2.2 Firestore Security Rules

Direct access from the client SDK is controlled with declarative rules:

- `request.auth != null` : authenticated users only
- `request.auth.uid == resource.data.uid` : only the user's own data
- Read and write are controlled individually at the collection and document level

## 5.3 Secret Management: Google Cloud Secret Manager

**Service**: [Google Cloud Secret Manager](https://cloud.google.com/secret-manager)

Versioned secret storage. Sensitive values such as API keys and credentials are access-controlled
with GCP IAM and fetched programmatically from application code.

Cloud Build and Cloud Run read them with `roles/secretmanager.secretAccessor`.

### 5.3.1 Key Characteristics

| Property | Detail |
|----------|--------|
| Versioning | Automatic (create, access, destroy per version) |
| Access Control | IAM-based per-secret |
| Rotation | Manual or automated via Cloud Functions |
| Audit | Cloud Audit Logs |
| Replication | Automatic or user-managed |

## 5.4 CI/CD Authentication: Workload Identity Federation

**Service**: [Workload Identity Federation](https://cloud.google.com/iam/docs/workload-identity-federation)

A mechanism that exchanges a token from an external identity provider (GitHub OIDC) for a
short-lived GCP IAM credential. There is no need to store a service account key file in
GitHub Secrets, which eliminates key rotation work and leak risk.

### 5.4.1 Authentication Flow

```
GitHub Actions Runner
  |
  +--> Request OIDC token from GitHub
  |
  +--> Present OIDC token to GCP Security Token Service
  |
  +--> Receive short-lived GCP access token
  |
  +--> Use access token for GCP API calls
```

### 5.4.2 Required Resources

| Resource | Purpose |
|----------|---------|
| Workload Identity Pool | Validation context for the GitHub token |
| Workload Identity Provider | GitHub OIDC issuer mapping |
| Service Account | `github-actions@{project}.iam.gserviceaccount.com` |

### 5.4.3 Service Account Roles

| Role | Purpose |
|------|---------|
| `roles/artifactregistry.writer` | Pushing container images / packages |
| `roles/cloudbuild.builds.editor` | Cloud Build job execution |
| `roles/storage.objectCreator` | Build artifact upload |
| `roles/storage.admin` | Storage bucket management |
| `roles/iam.serviceAccountUser` | SA impersonation when deploying to Cloud Run |
| `roles/secretmanager.secretAccessor` | Reading secrets at build time |

## 5.5 Secret Management: Single Source of Truth Policy

The source of truth (SSOT) for runtime secrets is defined as follows.
It makes the responsibility boundary between the two systems (dotenvx / Secret Manager) explicit,
and unifies the update procedure and audit path used during an incident.

### 5.5.1 SSOT Matrix

| Secret type | Source of truth (SSOT) | Rationale |
|----------|------------|------|
| CI/CD authentication (GCP OIDC) | GitHub Secrets | Read only by the CI runner. Outside GCP |
| dotenvx decryption key | GitHub Secrets | Build-time injection. Never read from outside CI |
| Runtime API Keys (LLM, TTS, etc.) | **dotenvx** | Injected into the container at deploy time. Secret Manager not needed |
| Firebase Config (public) | **dotenvx** | Non-sensitive. Included in the client bundle |
| GCP Service Account Key | **None (forbidden)** | Replaced by Workload Identity Federation |
| Cloud Build-only secret | **Secret Manager** | Only when Cloud Build native integration is required |

### 5.5.2 Operational Rules

| Rule | Detail |
|------|--------|
| Always exactly one source of truth | Never store the same secret in both dotenvx and Secret Manager |
| Update procedure | dotenvx: `dotenvx set KEY=VALUE -f .env.{env}` -> commit -> deploy |
| Audit | dotenvx: track changes through git history / Secret Manager: Cloud Audit Logs |
| Rotation | When rotating an API key, update the matching .env.{env} in dotenvx and redeploy |

### 5.5.3 Conditions for Using Secret Manager

Use Secret Manager only in the following cases:

1. Secrets that Cloud Build reads at build time (for example, decrypting the dotenvx key itself)
2. When a secret must be passed to Cloud Run through a volume mount rather than an environment variable
3. When application code must fetch a secret dynamically (rotation without redeploy)

For every other runtime secret, dotenvx is the source of truth.

## 5.6 Firebase Project Isolation

Each environment uses its own independent Firebase / GCP project,
keeping data, config, and IAM completely separate.

| Environment | Firebase Project | Purpose |
|-------------|-----------------|---------|
| Development | `{name}-dev` | Integration / staging |
| Production | `{name}-prd` | Live service |
