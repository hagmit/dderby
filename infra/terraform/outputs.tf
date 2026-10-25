output "buckets" {
  value = { for key, bucket in google_storage_bucket.data : key => bucket.name }
}
output "datasets" {
  value = { for key, dataset in google_bigquery_dataset.warehouse : key => dataset.dataset_id }
}
output "worker_accounts" {
  value = { for key, account in google_service_account.worker : key => account.email }
}
output "youtube_secret_resource" {
  value = google_secret_manager_secret.youtube.id
}
output "artifact_repository" {
  value = google_artifact_registry_repository.workers.id
}
output "job_names" {
  value = { for key, job in google_cloud_run_v2_job.worker : key => job.name }
}
