# 4. CI/CD Pipeline / Container Registry / Deployment

## 4.1 CI/CD Platform: GitHub Actions

**Service**: [GitHub Actions](https://docs.github.com/en/actions)

GitHub-native の CI/CD platform。Repository event (push, PR) を trigger に
workflow を実行する。GCP への認証は Workload Identity Federation (OIDC) を使用し、
long-lived service account key を排除する。

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

同一 branch に対する workflow は最新のみ実行し、in-progress の previous run は cancel する。

```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true
```

### 4.1.4 Path Filtering

Backend / Frontend の変更を path filter で分離し、
無関係なコンポーネントの build/test をスキップする。

## 4.2 Container Build: Cloud Build

**Service**: [Google Cloud Build](https://cloud.google.com/build)

GCP-managed の CI/CD service。Dockerfile からの container build に加え、
Secret Manager との native integration により、build 時の secret injection が容易。

GitHub Actions との使い分け: 基本は GitHub Actions で CI/CD を実行し、
Cloud Build は GCP Secret Manager 連携が必要な場合や
Artifact Registry への直接 push が必要な場合に補完的に使用する。

### 4.2.1 Configuration

| Item | Value |
|------|-------|
| Config File | `cloudbuild.yaml` |
| Timeout | 600s |
| Secret Source | Google Cloud Secret Manager |

## 4.3 Container / Package Registry: Artifact Registry

[Section 1.4 (infrastructure-1-compute.md)](infrastructure-1-compute.md#14-container--package-registry-artifact-registry) を参照。

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

Automated dependency update bot。PR を自動生成し、dependency の minor/patch update を
group 化して提案する。

### 4.5.1 Configuration

| Setting | Value |
|---------|-------|
| Schedule | Weekends only |
| Timezone | `Asia/Tokyo` |
| Stability Days | 7 (publish 後 7 日経過してから提案) |
| Grouping | Minor と patch を別グループ |

## 4.6 Environment Variable Management: dotenvx

**Tool**: [dotenvx](https://dotenvx.com/)

`.env` file の暗号化管理ツール。Environment ごとの `.env.{env}` file を
public key で暗号化して repository に commit し、deploy 時に private key で復号する。

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

OpenAPI spec や Pydantic model からの自動生成コードが最新であることを CI で検証する。
