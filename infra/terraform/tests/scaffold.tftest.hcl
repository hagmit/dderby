mock_provider "google" {}
mock_provider "google-beta" {}
variables {
  project_id = "dderby-test-project"
}
run "safe_defaults" {
  command = plan
  assert {
    condition     = length(google_storage_bucket.data) == 5 && length(google_bigquery_dataset.warehouse) == 2
    error_message = "Expected five buckets and raw/derived datasets."
  }
  assert {
    condition     = length(google_cloud_run_v2_job.worker) == 0 && length(google_cloud_scheduler_job.worker) == 0
    error_message = "Unimplemented workers must not be scheduled by default."
  }
  assert {
    condition     = alltrue([for b in google_storage_bucket.data : !b.force_destroy && b.public_access_prevention == "enforced" && b.versioning[0].enabled])
    error_message = "Data buckets must resist accidental deletion and public access."
  }
  assert {
    condition     = alltrue([for d in google_bigquery_dataset.warehouse : !d.delete_contents_on_destroy])
    error_message = "Warehouse destruction must not delete data implicitly."
  }
  assert {
    condition     = length(google_service_account.worker) == 4 && length(google_pubsub_subscription.queue) == 2
    error_message = "Expected role-separated workers and pull queues."
  }
}
run "jobs_are_paused" {
  command = plan
  variables {
    enable_jobs = true
    worker_images = {
      discovery = "asia-northeast1-docker.pkg.dev/dderby-test-project/workers/discovery@sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    }
  }
  assert {
    condition     = google_cloud_scheduler_job.worker["discovery"].paused
    error_message = "Scheduler must start paused."
  }
  assert {
    condition     = google_cloud_run_v2_job.worker["discovery"].deletion_protection
    error_message = "Job deletion protection must be enabled."
  }
}
run "invalid_environment" {
  command = plan
  variables { environment = "staging" }
  expect_failures = [var.environment]
}
run "mutable_image_rejected" {
  command = plan
  variables { worker_images = { discovery = "example/image:latest" } }
  expect_failures = [var.worker_images]
}
run "empty_jobs_rejected" {
  command = plan
  variables { enable_jobs = true }
  expect_failures = [var.enable_jobs]
}
