terraform {
  required_version = ">= 1.13.0, < 2.0.0"
  required_providers {
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 7.9"
    }
    google = {
      source  = "hashicorp/google"
      version = "~> 7.9"
    }
  }
}
provider "google" {
  project = var.project_id
  region  = var.region
}
provider "google-beta" {
  project = var.project_id
  region  = var.region
}
