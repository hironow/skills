# GCP Serverless Terraform Resource Map

各 GCP サーバーレスサービスに対応する Terraform リソース定義のテンプレート。
MCP で最新仕様を確認した上で、以下をベースに `.tf` を生成する。

## Table of Contents

1. [Provider & Versions](#1-provider--versions)
2. [Cloud Run Service](#2-cloud-run-service)
3. [Cloud Run Job](#3-cloud-run-job)
4. [Firestore](#4-firestore)
5. [Cloud Tasks](#5-cloud-tasks)
6. [Pub/Sub](#6-pubsub)
7. [Eventarc](#7-eventarc)
8. [Cloud Scheduler](#8-cloud-scheduler)
9. [Cloud Functions](#9-cloud-functions)
10. [Artifact Registry](#10-artifact-registry)
11. [Secret Manager](#11-secret-manager)
12. [IAM & Service Account](#12-iam--service-account)
13. [API Enablement](#13-api-enablement)
14. [State Backend](#14-state-backend)

---

## 1. Provider & Versions

### Terraform

```hcl
# versions.tf
terraform {
  required_version = ">= 1.9"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 6.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = ">= 6.0"
    }
  }
}
```

### OpenTofu

```hcl
# versions.tf
terraform {
  required_version = ">= 1.8"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 6.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = ">= 6.0"
    }
  }
}
```

### Provider Configuration

```hcl
# provider.tf (environment root)
provider "google" {
  project = var.project_id
  region  = var.region
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
}
```

### Common Variables

```hcl
# variables.tf (environment root)
variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "asia-northeast1"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
}
```

---

## 2. Cloud Run Service

```hcl
# modules/cloud-run/main.tf
resource "google_cloud_run_v2_service" "main" {
  name     = var.service_name
  location = var.region

  template {
    containers {
      image = var.container_image

      ports {
        container_port = var.container_port
      }

      resources {
        limits = {
          cpu    = var.cpu
          memory = var.memory
        }
      }

      dynamic "env" {
        for_each = var.env_vars
        content {
          name  = env.value.name
          value = env.value.value
        }
      }

      dynamic "env" {
        for_each = var.secret_env_vars
        content {
          name = env.value.name
          value_source {
            secret_key_ref {
              secret  = env.value.secret_id
              version = env.value.version
            }
          }
        }
      }
    }

    scaling {
      min_instance_count = var.min_instances
      max_instance_count = var.max_instances
    }

    service_account = var.service_account_email
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }
}

# Public access (if needed)
resource "google_cloud_run_v2_service_iam_member" "public" {
  count    = var.allow_unauthenticated ? 1 : 0
  name     = google_cloud_run_v2_service.main.name
  location = var.region
  role     = "roles/run.invoker"
  member   = "allUsers"
}
```

```hcl
# modules/cloud-run/variables.tf
variable "service_name" {
  type = string
}

variable "region" {
  type    = string
  default = "asia-northeast1"
}

variable "container_image" {
  type = string
}

variable "container_port" {
  type    = number
  default = 8080
}

variable "cpu" {
  type    = string
  default = "1"
}

variable "memory" {
  type    = string
  default = "512Mi"
}

variable "min_instances" {
  type    = number
  default = 0
}

variable "max_instances" {
  type    = number
  default = 10
}

variable "env_vars" {
  type = list(object({
    name  = string
    value = string
  }))
  default = []
}

variable "secret_env_vars" {
  type = list(object({
    name      = string
    secret_id = string
    version   = string
  }))
  default = []
}

variable "service_account_email" {
  type = string
}

variable "allow_unauthenticated" {
  type    = bool
  default = false
}
```

```hcl
# modules/cloud-run/outputs.tf
output "service_url" {
  value = google_cloud_run_v2_service.main.uri
}

output "service_name" {
  value = google_cloud_run_v2_service.main.name
}
```

---

## 3. Cloud Run Job

```hcl
resource "google_cloud_run_v2_job" "main" {
  name     = var.job_name
  location = var.region

  template {
    template {
      containers {
        image = var.container_image

        resources {
          limits = {
            cpu    = var.cpu
            memory = var.memory
          }
        }

        dynamic "env" {
          for_each = var.env_vars
          content {
            name  = env.value.name
            value = env.value.value
          }
        }
      }

      timeout         = var.timeout
      service_account = var.service_account_email
    }

    task_count = var.task_count
  }
}
```

---

## 4. Firestore

```hcl
# modules/firestore/main.tf
resource "google_firestore_database" "main" {
  project     = var.project_id
  name        = var.database_name
  location_id = var.region
  type        = "FIRESTORE_NATIVE"

  delete_protection_state = var.environment == "prod" ? "DELETE_PROTECTION_ENABLED" : "DELETE_PROTECTION_DISABLED"
}

# Firestore indexes (if defined in code)
resource "google_firestore_index" "indexes" {
  for_each   = { for idx in var.indexes : idx.collection => idx }
  project    = var.project_id
  database   = google_firestore_database.main.name
  collection = each.value.collection

  dynamic "fields" {
    for_each = each.value.fields
    content {
      field_path = fields.value.field_path
      order      = fields.value.order
    }
  }
}
```

---

## 5. Cloud Tasks

```hcl
# modules/async/cloud_tasks.tf
resource "google_cloud_tasks_queue" "queues" {
  for_each = { for q in var.task_queues : q.name => q }
  name     = each.value.name
  location = var.region

  rate_limits {
    max_dispatches_per_second = each.value.max_dispatches_per_second
    max_concurrent_dispatches = each.value.max_concurrent_dispatches
  }

  retry_config {
    max_attempts       = each.value.max_attempts
    max_retry_duration = each.value.max_retry_duration
    min_backoff        = each.value.min_backoff
    max_backoff        = each.value.max_backoff
  }
}
```

---

## 6. Pub/Sub

```hcl
# modules/async/pubsub.tf
resource "google_pubsub_topic" "topics" {
  for_each = { for t in var.pubsub_topics : t.name => t }
  name     = each.value.name

  message_retention_duration = each.value.retention
}

resource "google_pubsub_subscription" "subscriptions" {
  for_each = { for s in var.pubsub_subscriptions : s.name => s }
  name     = each.value.name
  topic    = each.value.topic

  ack_deadline_seconds = each.value.ack_deadline

  dynamic "push_config" {
    for_each = each.value.push_endpoint != null ? [1] : []
    content {
      push_endpoint = each.value.push_endpoint

      oidc_token {
        service_account_email = each.value.service_account_email
      }
    }
  }

  retry_policy {
    minimum_backoff = each.value.min_backoff
    maximum_backoff = each.value.max_backoff
  }
}
```

---

## 7. Eventarc

```hcl
# modules/async/eventarc.tf
resource "google_eventarc_trigger" "triggers" {
  for_each = { for t in var.eventarc_triggers : t.name => t }
  name     = each.value.name
  location = var.region

  matching_criteria {
    attribute = "type"
    value     = each.value.event_type
  }

  dynamic "matching_criteria" {
    for_each = each.value.filters
    content {
      attribute = matching_criteria.value.attribute
      value     = matching_criteria.value.value
    }
  }

  destination {
    cloud_run_service {
      service = each.value.target_service
      region  = var.region
    }
  }

  service_account = each.value.service_account_email
}
```

---

## 8. Cloud Scheduler

```hcl
# modules/async/scheduler.tf
resource "google_cloud_scheduler_job" "jobs" {
  for_each  = { for j in var.scheduler_jobs : j.name => j }
  name      = each.value.name
  region    = var.region
  schedule  = each.value.schedule
  time_zone = each.value.time_zone

  dynamic "http_target" {
    for_each = each.value.http_target != null ? [each.value.http_target] : []
    content {
      uri         = http_target.value.uri
      http_method = http_target.value.method

      oidc_token {
        service_account_email = http_target.value.service_account_email
      }
    }
  }

  retry_config {
    retry_count = each.value.retry_count
  }
}
```

---

## 9. Cloud Functions

```hcl
# modules/functions/main.tf
resource "google_cloudfunctions2_function" "main" {
  name     = var.function_name
  location = var.region

  build_config {
    runtime     = var.runtime
    entry_point = var.entry_point

    source {
      storage_source {
        bucket = var.source_bucket
        object = var.source_object
      }
    }
  }

  service_config {
    max_instance_count    = var.max_instances
    available_memory      = var.memory
    timeout_seconds       = var.timeout
    service_account_email = var.service_account_email

    dynamic "environment_variables" {
      for_each = var.env_vars
      content {
        key   = environment_variables.key
        value = environment_variables.value
      }
    }
  }
}
```

---

## 10. Artifact Registry

```hcl
# modules/registry/main.tf
resource "google_artifact_registry_repository" "main" {
  location      = var.region
  repository_id = var.repository_id
  format        = "DOCKER"
  description   = var.description

  cleanup_policies {
    id     = "keep-recent"
    action = "KEEP"

    most_recent_versions {
      keep_count = var.keep_count
    }
  }
}
```

---

## 11. Secret Manager

```hcl
# modules/secrets/main.tf
resource "google_secret_manager_secret" "secrets" {
  for_each  = toset(var.secret_ids)
  secret_id = each.value

  replication {
    auto {}
  }
}
```

---

## 12. IAM & Service Account

```hcl
# modules/iam/main.tf
resource "google_service_account" "cloud_run" {
  account_id   = "${var.service_name}-sa"
  display_name = "Service Account for ${var.service_name}"
}

resource "google_project_iam_member" "roles" {
  for_each = toset(var.roles)
  project  = var.project_id
  role     = each.value
  member   = "serviceAccount:${google_service_account.cloud_run.email}"
}
```

### Typical Roles for GCP Serverless

```hcl
# Cloud Run service that uses Firestore + Cloud Tasks + Pub/Sub
locals {
  cloud_run_roles = [
    "roles/datastore.user",           # Firestore
    "roles/cloudtasks.enqueuer",      # Cloud Tasks
    "roles/pubsub.publisher",         # Pub/Sub publish
    "roles/secretmanager.secretAccessor", # Secret Manager
    "roles/logging.logWriter",        # Cloud Logging
    "roles/monitoring.metricWriter",  # Cloud Monitoring
  ]
}
```

---

## 13. API Enablement

```hcl
# modules/apis/main.tf
resource "google_project_service" "apis" {
  for_each = toset(var.enable_apis ? var.apis : [])
  service  = each.value

  disable_on_destroy = false
}

# Common APIs for GCP serverless
variable "apis" {
  default = [
    "run.googleapis.com",
    "firestore.googleapis.com",
    "cloudtasks.googleapis.com",
    "pubsub.googleapis.com",
    "cloudfunctions.googleapis.com",
    "eventarc.googleapis.com",
    "cloudscheduler.googleapis.com",
    "artifactregistry.googleapis.com",
    "secretmanager.googleapis.com",
    "cloudbuild.googleapis.com",
    "iam.googleapis.com",
  ]
}
```

---

## 14. State Backend

### GCS Backend

```hcl
# environments/dev/backend.tf
terraform {
  backend "gcs" {
    bucket = "my-project-terraform-state"
    prefix = "dev"
  }
}
```

### Local Backend

```hcl
# environments/dev/backend.tf
terraform {
  backend "local" {
    path = "terraform.tfstate"
  }
}
```

### OpenTofu with State Encryption

```hcl
# environments/dev/backend.tf
terraform {
  backend "gcs" {
    bucket = "my-project-tofu-state"
    prefix = "dev"
  }

  encryption {
    key_provider "gcp_kms" "main" {
      kms_encryption_key = "projects/${var.project_id}/locations/${var.region}/keyRings/tofu/cryptoKeys/state"
      key_length         = 32
    }

    method "aes_gcm" "main" {
      keys = key_provider.gcp_kms.main
    }

    state {
      method   = method.aes_gcm.main
      enforced = true
    }
  }
}
```

---

## Diff Detection Patterns

アプリケーションコードの変更から Terraform への影響を検出するパターン:

| Code Change | Terraform Impact |
|---|---|
| 新しい `google-cloud-tasks` import | `google_cloud_tasks_queue` 追加 |
| 新しい `google-cloud-pubsub` import | `google_pubsub_topic` + subscription 追加 |
| 新 endpoint / router 追加 | Cloud Run env vars 更新の可能性 |
| 新しい `firebase-admin` 利用 | Firestore / Auth 関連リソース確認 |
| Dockerfile ベースイメージ変更 | Artifact Registry 設定確認 |
| 環境変数追加 (.env) | Secret Manager or Cloud Run env 追加 |
| `google-cloud-scheduler` import | `google_cloud_scheduler_job` 追加 |
| Firestore security rules 変更 | Firestore index 更新の可能性 |
| 新しいサービス（microservice）追加 | 新 Cloud Run service + SA + IAM |
