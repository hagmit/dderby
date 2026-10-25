locals {
  prefix  = "dderby-${var.environment}"
  workers = toset(["discovery", "video", "vision", "analytics"])
  buckets = toset(["raw-video", "frames", "cropped-images", "failed-extractions", "model-artifacts"])
  apis = toset([
    "run.googleapis.com", "storage.googleapis.com", "bigquery.googleapis.com",
    "artifactregistry.googleapis.com", "pubsub.googleapis.com", "cloudscheduler.googleapis.com",
    "secretmanager.googleapis.com", "logging.googleapis.com", "monitoring.googleapis.com",
    "iam.googleapis.com", "youtube.googleapis.com"
  ])
  storage_access = {
    video_raw_create    = { worker = "video", bucket = "raw-video", role = "roles/storage.objectCreator" }
    video_raw_read      = { worker = "video", bucket = "raw-video", role = "roles/storage.objectViewer" }
    video_frames_create = { worker = "video", bucket = "frames", role = "roles/storage.objectCreator" }
    video_frames_read   = { worker = "video", bucket = "frames", role = "roles/storage.objectViewer" }
    vision_frames_read  = { worker = "vision", bucket = "frames", role = "roles/storage.objectViewer" }
    vision_crop_create  = { worker = "vision", bucket = "cropped-images", role = "roles/storage.objectCreator" }
    vision_crop_read    = { worker = "vision", bucket = "cropped-images", role = "roles/storage.objectViewer" }
    vision_fail_create  = { worker = "vision", bucket = "failed-extractions", role = "roles/storage.objectCreator" }
    vision_fail_read    = { worker = "vision", bucket = "failed-extractions", role = "roles/storage.objectViewer" }
    model_create        = { worker = "analytics", bucket = "model-artifacts", role = "roles/storage.objectCreator" }
    model_read          = { worker = "analytics", bucket = "model-artifacts", role = "roles/storage.objectViewer" }
  }
}
resource "google_project_service" "api" {
  for_each           = local.apis
  project            = var.project_id
  service            = each.value
  disable_on_destroy = false
}
resource "google_service_account" "worker" {
  for_each     = local.workers
  account_id   = "${local.prefix}-${each.key}-worker"
  display_name = "${each.key} worker (${var.environment})"
  depends_on   = [google_project_service.api]
}
resource "google_service_account" "scheduler" {
  account_id = "${local.prefix}-scheduler"
  depends_on = [google_project_service.api]
}
resource "google_storage_bucket" "data" {
  for_each                    = local.buckets
  name                        = "${var.project_id}-${local.prefix}-${each.key}"
  location                    = var.region
  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"
  force_destroy               = false
  labels                      = { application = "dderby", environment = var.environment }
  versioning { enabled = true }
  depends_on = [google_project_service.api]
}
resource "google_storage_bucket_iam_member" "worker" {
  for_each = local.storage_access
  bucket   = google_storage_bucket.data[each.value.bucket].name
  role     = each.value.role
  member   = "serviceAccount:${google_service_account.worker[each.value.worker].email}"
}
resource "google_bigquery_dataset" "warehouse" {
  for_each                   = toset(["raw", "derived"])
  dataset_id                 = "dderby_${var.environment}_${each.key}"
  location                   = var.region
  delete_contents_on_destroy = false
  labels                     = { application = "dderby", environment = var.environment }
  depends_on                 = [google_project_service.api]
}
resource "google_bigquery_dataset_iam_member" "vision_raw" {
  dataset_id = google_bigquery_dataset.warehouse["raw"].dataset_id
  role       = "roles/bigquery.dataEditor"
  member     = "serviceAccount:${google_service_account.worker["vision"].email}"
}
resource "google_bigquery_dataset_iam_member" "analytics" {
  for_each   = { raw = "roles/bigquery.dataViewer", derived = "roles/bigquery.dataEditor" }
  dataset_id = google_bigquery_dataset.warehouse[each.key].dataset_id
  role       = each.value
  member     = "serviceAccount:${google_service_account.worker["analytics"].email}"
}
resource "google_project_iam_member" "query" {
  project = var.project_id
  role    = "roles/bigquery.jobUser"
  member  = "serviceAccount:${google_service_account.worker["analytics"].email}"
}
resource "google_artifact_registry_repository" "workers" {
  location      = var.region
  repository_id = "${local.prefix}-workers"
  format        = "DOCKER"
  depends_on    = [google_project_service.api]
}
resource "google_secret_manager_secret" "youtube" {
  secret_id = "${local.prefix}-youtube-api"
  replication {
    auto {}
  }
  depends_on = [google_project_service.api]
}
resource "google_secret_manager_secret_iam_member" "discovery" {
  secret_id = google_secret_manager_secret.youtube.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.worker["discovery"].email}"
}
resource "google_pubsub_topic" "dead_letter" {
  name       = "${local.prefix}-dead-letter"
  depends_on = [google_project_service.api]
}
resource "google_pubsub_subscription" "dead_letter" {
  name                       = "${local.prefix}-dead-letter"
  topic                      = google_pubsub_topic.dead_letter.id
  message_retention_duration = "1209600s"
  expiration_policy { ttl = "" }
}
resource "google_pubsub_topic" "queue" {
  for_each   = toset(["processing", "retry"])
  name       = "${local.prefix}-${each.key}"
  depends_on = [google_project_service.api]
}
resource "google_pubsub_subscription" "queue" {
  for_each                   = google_pubsub_topic.queue
  name                       = "${local.prefix}-${each.key}"
  topic                      = each.value.id
  ack_deadline_seconds       = 600
  message_retention_duration = "604800s"
  expiration_policy { ttl = "" }
  retry_policy {
    minimum_backoff = "10s"
    maximum_backoff = "600s"
  }
  dead_letter_policy {
    dead_letter_topic     = google_pubsub_topic.dead_letter.id
    max_delivery_attempts = 5
  }
}
resource "google_project_service_identity" "pubsub" {
  provider   = google-beta
  project    = var.project_id
  service    = "pubsub.googleapis.com"
  depends_on = [google_project_service.api]
}
resource "google_pubsub_topic_iam_member" "dlq" {
  topic  = google_pubsub_topic.dead_letter.id
  role   = "roles/pubsub.publisher"
  member = "serviceAccount:${google_project_service_identity.pubsub.email}"
}
resource "google_pubsub_subscription_iam_member" "dlq" {
  for_each     = google_pubsub_subscription.queue
  subscription = each.value.name
  role         = "roles/pubsub.subscriber"
  member       = "serviceAccount:${google_project_service_identity.pubsub.email}"
}
resource "google_pubsub_topic_iam_member" "publisher" {
  for_each = { discovery = "processing", video = "retry" }
  topic    = google_pubsub_topic.queue[each.value].id
  role     = "roles/pubsub.publisher"
  member   = "serviceAccount:${google_service_account.worker[each.key].email}"
}
resource "google_pubsub_subscription_iam_member" "consumer" {
  for_each     = { video = "processing", vision = "retry" }
  subscription = google_pubsub_subscription.queue[each.value].name
  role         = "roles/pubsub.subscriber"
  member       = "serviceAccount:${google_service_account.worker[each.key].email}"
}
resource "google_cloud_run_v2_job" "worker" {
  for_each            = var.enable_jobs ? var.worker_images : {}
  name                = "${local.prefix}-${each.key}"
  location            = var.region
  deletion_protection = true
  template {
    template {
      service_account = google_service_account.worker[each.key].email
      timeout         = "3600s"
      max_retries     = 1
      containers {
        image = each.value
        env {
          name  = "DDERBY_ENV"
          value = var.environment
        }
        env {
          name  = "GOOGLE_CLOUD_PROJECT"
          value = var.project_id
        }
        env {
          name  = "YOUTUBE_SECRET_RESOURCE"
          value = google_secret_manager_secret.youtube.id
        }
        resources {
          limits = { cpu = "1", memory = "2Gi" }
        }
      }
    }
  }
  lifecycle {
    precondition {
      condition     = length(var.worker_images) > 0
      error_message = "Supply implemented worker images before enabling jobs."
    }
  }
  depends_on = [google_project_service.api]
}
resource "google_cloud_run_v2_job_iam_member" "scheduler" {
  for_each = google_cloud_run_v2_job.worker
  name     = each.value.name
  location = var.region
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.scheduler.email}"
}
resource "google_cloud_scheduler_job" "worker" {
  for_each  = google_cloud_run_v2_job.worker
  name      = "${local.prefix}-${each.key}"
  region    = var.region
  schedule  = each.key == "discovery" ? "0 * * * *" : "*/15 * * * *"
  time_zone = "Asia/Tokyo"
  paused    = var.scheduler_paused
  http_target {
    http_method = "POST"
    uri         = "https://run.googleapis.com/v2/projects/${var.project_id}/locations/${var.region}/jobs/${each.value.name}:run"
    body        = base64encode("{}")
    headers     = { "Content-Type" = "application/json" }
    oauth_token {
      service_account_email = google_service_account.scheduler.email
      scope                 = "https://www.googleapis.com/auth/cloud-platform"
    }
  }
  depends_on = [google_cloud_run_v2_job_iam_member.scheduler]
}
resource "google_logging_metric" "worker_failure" {
  name   = "${local.prefix}-worker-failure"
  filter = "resource.type=\"cloud_run_job\" AND resource.labels.job_name=~\"^${local.prefix}-\" AND jsonPayload.event=\"worker_failure\""
  metric_descriptor {
    metric_kind = "DELTA"
    value_type  = "INT64"
  }
  depends_on = [google_project_service.api]
}
resource "google_monitoring_alert_policy" "worker_failure" {
  display_name          = "${local.prefix} worker failure"
  combiner              = "OR"
  notification_channels = var.notification_channels
  conditions {
    display_name = "Worker failure event"
    condition_threshold {
      filter          = "resource.type=\"cloud_run_job\" AND metric.type=\"logging.googleapis.com/user/${google_logging_metric.worker_failure.name}\""
      comparison      = "COMPARISON_GT"
      threshold_value = 0
      duration        = "0s"
      aggregations {
        alignment_period   = "300s"
        per_series_aligner = "ALIGN_DELTA"
      }
    }
  }
  depends_on = [google_project_service.api]
}
