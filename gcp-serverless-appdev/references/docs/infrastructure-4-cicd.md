# 4. CI/CD Pipeline / Container Registry / Deployment

## 4.1 CI/CD Platform: GitHub Actions

**Service**: [GitHub Actions](https://docs.github.com/en/actions)

A GitHub-native CI/CD platform. It runs workflows triggered by repository events (push, PR).
Authentication to GCP uses Workload Identity Federation (OIDC),
which eliminates long-lived service account keys.

### 4.1.1 Pipeline Structure

```
Push / PR
  |
  +---> [Format & Lint]  -- parallel
  +---> [Test]           -- parallel
  +---> [Build & Push]   -- on push to main/develop only
  +---> [Deploy]         -- on push to main/develop only (post-build)
```

### 4.1.2 Workflow Configuration

| Workflow | Trigger | Timeout | Runner |
|----------|---------|---------|--------|
| Format & Lint | push, PR | 10 min | ubuntu-24.04 |
| Test | push, PR | 10 min | ubuntu-24.04 |
| Build & Push | push (main/develop) | 10 min | ubuntu-24.04 |

### 4.1.3 Concurrency Control

For a given branch, only the latest workflow runs; a previous run still in progress is cancelled.

```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true
```

### 4.1.4 Path Filtering

Backend and frontend changes are separated with path filters,
so builds and tests for unrelated components are skipped.

## 4.2 Container Build: Cloud Build

**Service**: [Google Cloud Build](https://cloud.google.com/build)

A GCP-managed CI/CD service. On top of building containers from a Dockerfile,
its native integration with Secret Manager makes injecting secrets at build time easy.

Choosing between this and GitHub Actions: run CI/CD on GitHub Actions by default, and use
Cloud Build as a complement when integration with GCP Secret Manager is needed,
or when a direct push to Artifact Registry is needed.

### 4.2.1 Configuration

| Item | Value |
|------|-------|
| Config File | `cloudbuild.yaml` |
| Timeout | 600s |
| Secret Source | Google Cloud Secret Manager |

## 4.3 Container / Package Registry: Artifact Registry

See [Section 1.4 (infrastructure-1-compute.md)](infrastructure-1-compute.md#14-container-registry-artifact-registry).

### 4.3.1 Docker Image

| Item | Value |
|------|-------|
| Format | Docker |
| Location | `us-central1` |

### 4.3.2 Python Package

| Item | Value |
|------|-------|
| Format | Python |
| Location | `asia-northeast1` |
| Build Tool | `flit` (PEP 517/518) |
| Publish | `uv publish` via GitHub Actions |

## 4.4 Image Tagging Strategy

| Branch | Tag Format | Example |
|--------|------------|---------|
| `develop` | `dev-{short-sha}` | `dev-abc1234` |
| `main` | `prd-{short-sha}` | `prd-def5678` |

## 4.5 Dependency Management: Renovate

**Service**: [Renovate](https://docs.renovatebot.com/)

An automated dependency update bot. It opens PRs automatically and proposes minor/patch
dependency updates in groups.

### 4.5.1 Configuration

| Setting | Value |
|---------|-------|
| Schedule | Weekends only |
| Timezone | `Asia/Tokyo` |
| Stability Days | 7 (proposed only after 7 days have passed since publication) |
| Grouping | Minor and patch in separate groups |

## 4.6 Environment Variable Management: dotenvx

**Tool**: [dotenvx](https://dotenvx.com/)

A tool for managing encrypted `.env` files. The per-environment `.env.{env}` file is encrypted
with a public key and committed to the repository, then decrypted with the private key at deploy time.

### 4.6.1 File Structure

```
.env          # Base (shared, non-sensitive)
.env.dev      # Development (encrypted)
.env.prd      # Production (encrypted)
.env.keys     # Private keys (git-ignored)
```

### 4.6.2 Key Management

| Key | Storage |
|-----|---------|
| `DOTENV_PRIVATE_KEY_DEV` | GitHub Secrets |
| `DOTENV_PRIVATE_KEY_PRD` | GitHub Secrets |

## 4.7 Code Quality Gates

### 4.7.1 Linting & Formatting

| Tool | Target | Purpose |
|------|--------|---------|
| ruff | Python | Linting + formatting (replaces flake8, black, isort) |
| Biome | TypeScript/JavaScript | Linting + formatting (replaces ESLint, Prettier) |
| Semgrep | Python | Security-focused static analysis (custom rules) |

### 4.7.2 Type Checking

| Tool | Target |
|------|--------|
| mypy | Python |
| TypeScript compiler | Frontend |

### 4.7.3 Code Generation Validation

CI verifies that code generated from the OpenAPI spec and from Pydantic models is up to date.
