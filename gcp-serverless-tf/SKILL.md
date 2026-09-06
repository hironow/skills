---
name: gcp-serverless-tf
description: >
  Generate and maintain Terraform/OpenTofu configurations for GCP serverless
  architectures (Cloud Run, Firestore, Cloud Tasks, Pub/Sub, Cloud Functions,
  Eventarc, Cloud Scheduler, Artifact Registry, Secret Manager).
  Use whenever the request involves Terraform, OpenTofu, .tf files, `tofu` or
  `terraform` commands, or infrastructure as code for those services — initial .tf
  generation, updating .tf after application code changes, and the
  Terraform-vs-OpenTofu choice — including Japanese requests such as
  "tfファイル作って" or "インフラをコード化".
  Not for application code, service selection, or gcloud-based deployment — that is
  gcp-serverless-appdev.
license: MIT
metadata:
  provenance: original
---

# GCP Serverless Terraform/OpenTofu Skill

Generate and maintain the Terraform/OpenTofu configuration for a GCP serverless architecture. Produce the `.tf` files that correspond to the architecture defined by the `gcp-serverless-appdev` skill (Cloud Run, Firestore, Cloud Tasks, Pub/Sub, and so on), and keep the `.tf` files in step with changes to the application code.

## Two Modes

### Mode 1: Init (initial generation)

The project has no `.tf` files yet. Read the user's application code (Dockerfile, main.py, docker-compose.yaml, …), identify the GCP services in use, and generate the corresponding set of `.tf` files.

### Mode 2: Diff (incremental update)

`.tf` files already exist. Read the application code changes (git diff or new files), identify the ones that affect infrastructure, and propose and apply the `.tf` diff.

## Workflow

### Step 1: Confirm the user's intent

Confirm the following (ask if unclear):

1. **Terraform or OpenTofu?** The syntax is almost identical, but the `required_providers` registry URL and state encryption differ.
2. **State backend** — a GCS bucket, local, or Terraform Cloud.
3. **Environment layout** — separate directories (recommended) or workspaces.

### Step 2: Read the application configuration

Read these files to extract the infrastructure requirements:

- `docker-compose.yaml` — infer services from the emulators in use
- `Dockerfile` — the Cloud Run container configuration
- `pyproject.toml` / `package.json` — identify services from GCP SDK dependencies
- `main.py` / application code — endpoints, Cloud Tasks / Pub/Sub calls
- `firestore.rules` — whether Firestore is present
- `firebase.json` — Firebase project configuration
- `.github/workflows/` — CI/CD configuration

### Step 3: Resource mapping

Map the detected services to Terraform resources. Read `references/resource-map.md` for the details.

Main mappings:

| GCP Service | Terraform Resource | Module |
|---|---|---|
| Cloud Run Service | `google_cloud_run_v2_service` | `modules/cloud-run/` |
| Cloud Run Job | `google_cloud_run_v2_job` | `modules/cloud-run/` |
| Firestore | `google_firestore_database` | `modules/firestore/` |
| Cloud Tasks Queue | `google_cloud_tasks_queue` | `modules/async/` |
| Pub/Sub Topic | `google_pubsub_topic` | `modules/async/` |
| Pub/Sub Subscription | `google_pubsub_subscription` | `modules/async/` |
| Cloud Functions | `google_cloudfunctions2_function` | `modules/functions/` |
| Eventarc Trigger | `google_eventarc_trigger` | `modules/async/` |
| Cloud Scheduler | `google_cloud_scheduler_job` | `modules/async/` |
| Artifact Registry | `google_artifact_registry_repository` | `modules/registry/` |
| Secret Manager | `google_secret_manager_secret` | `modules/secrets/` |
| Service Account | `google_service_account` | `modules/iam/` |
| IAM Binding | `google_project_iam_member` | `modules/iam/` |

### Step 4: Generate the directory structure

A structure that follows Google Cloud's published best practices:

```
terraform/                    # or infra/
├── modules/
│   ├── cloud-run/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   ├── firestore/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   ├── async/                # Cloud Tasks, Pub/Sub, Eventarc, Scheduler
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   ├── registry/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   ├── secrets/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   └── iam/
│       ├── main.tf
│       ├── variables.tf
│       └── outputs.tf
├── environments/
│   ├── dev/
│   │   ├── main.tf           # module calls + dev-specific values
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   ├── backend.tf        # state backend configuration
│   │   └── terraform.tfvars  # dev environment variables
│   ├── staging/
│   │   └── ...
│   └── prod/
│       └── ...
└── versions.tf               # provider version constraints (shared)
```

### Step 5: Check the latest specification through MCP

Before writing `.tf` files, confirm the latest resource specification through MCP. GCP resource attributes (especially the Cloud Run v2 and Firestore parameters) change often, so general knowledge alone is easily inaccurate.

**Available MCP servers:**

1. **google-dev-knowledge** — the latest documentation for the GCP Terraform provider
   ```
   mcp__google-dev-knowledge__search_documents
   → "terraform google_cloud_run_v2_service configuration"
   → "terraform google_firestore_database resource"
   ```

2. **context7** — the latest Terraform/OpenTofu syntax. Resolve "hashicorp/terraform" / "opentofu" with `resolve-library-id`, then look up "module structure best practices" / "provider version constraints" with `query-docs`.

**How to use them:**
1. For each resource you generate, search `google-dev-knowledge` for the latest attributes.
2. When unsure about syntax, check the latest Terraform/OpenTofu syntax with `context7`.
3. If the bundled `references/resource-map.md` and the MCP results disagree, the MCP results win.

**When MCP is unavailable:**
Work from the bundled references only, and append the setup notice from `references/mcp-setup.md` to the end of the answer.

### Step 6: Generate the .tf files

Read `references/resource-map.md` for the resource definition templates, confirm the latest specification through MCP, then generate the `.tf` files.

**Principles when generating:**

1. **Terraform/OpenTofu compatibility**: the HCL is shared in principle. Where they differ, say so in a comment.
2. **Fixed region**: default to `asia-northeast1` (following the Core Principle of `gcp-serverless-appdev`).
3. **Variables**: no hard-coding. `project_id`, `region`, and `environment` are variables.
4. **API enablement**: include `google_project_service` in each module, controlled by an `enable_apis` variable.
5. **Least-privilege IAM**: grant service accounts only the roles they need.
6. **Naming**: resource names use underscores; a resource that is the only one of its kind is named `main`.

## Diff mode in detail

The update flow when `.tf` files already exist:

1. **Detect changes**: read `git diff` or the files the user points at.
2. **Judge the infrastructure impact**: look for these change patterns
   - a new GCP SDK import → a new resource is needed
   - a new endpoint → Cloud Run environment variables or service settings
   - a new Cloud Tasks / Pub/Sub call → add a queue or topic
   - a Dockerfile change → Artifact Registry or build settings
   - a new environment variable → Secret Manager or Cloud Run env vars
3. **Propose the .tf diff**: present the diff for the `.tf` files that need adding or changing.
4. **Recommend `terraform plan`**: prompt the user to confirm with `terraform plan` before applying.

## References

| Situation | Read this |
|---|---|
| Resource definition templates | `references/resource-map.md` |
| MCP setup notice | `references/mcp-setup.md` |

## Terraform vs OpenTofu

| Item | Terraform | OpenTofu |
|---|---|---|
| Provider registry | `registry.terraform.io` | `registry.opentofu.org` |
| State encryption | Terraform Cloud only | native |
| License | BSL 1.1 | MPL 2.0 (OSS) |
| HCL compatibility | the baseline | almost fully compatible |
| `required_providers` | `source = "hashicorp/google"` | same (with a fallback) |

In practice the `.tf` file contents are almost identical; only the wording of `versions.tf` needs care.
