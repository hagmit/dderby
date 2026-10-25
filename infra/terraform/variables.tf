variable "project_id" {
  type        = string
  description = "Existing dedicated GCP project; do not supply credentials here."
  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{4,28}[a-z0-9]$", var.project_id))
    error_message = "Supply a valid GCP project ID."
  }
}
variable "environment" {
  type    = string
  default = "dev"
  validation {
    condition     = contains(["dev", "prod"], var.environment)
    error_message = "environment must be dev or prod."
  }
}
variable "region" {
  type    = string
  default = "asia-northeast1"
}
variable "enable_jobs" {
  type    = bool
  default = false
  validation {
    condition     = !var.enable_jobs || length(var.worker_images) > 0
    error_message = "Supply worker image digests before enabling jobs."
  }
}
variable "worker_images" {
  type        = map(string)
  default     = {}
  description = "Implemented worker image digests keyed by discovery/video/vision/analytics."
  validation {
    condition = alltrue([for key, image in var.worker_images :
      contains(["discovery", "video", "vision", "analytics"], key) &&
      can(regex("@sha256:[a-f0-9]{64}$", image))
    ])
    error_message = "Only known workers and immutable SHA256 image digests are allowed."
  }
}
variable "scheduler_paused" {
  type    = bool
  default = true
}
variable "notification_channels" {
  type        = list(string)
  default     = []
  description = "Existing Monitoring notification channel resource names."
}
