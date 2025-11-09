terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "us-central1"
}

variable "sendgrid_api_key" {
  description = "SendGrid API Key"
  type        = string
  sensitive   = true
}

# Enable required APIs
resource "google_project_service" "vision_api" {
  service = "vision.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "firestore_api" {
  service = "firestore.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "cloudfunctions_api" {
  service = "cloudfunctions.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "cloudbuild_api" {
  service = "cloudbuild.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "cloudscheduler_api" {
  service = "cloudscheduler.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "storage_api" {
  service = "storage.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "aiplatform_api" {
  service = "aiplatform.googleapis.com"
  disable_on_destroy = false
}

# Create Firestore database
resource "google_firestore_database" "database" {
  name        = "(default)"
  location_id = var.region
  type        = "FIRESTORE_NATIVE"

  depends_on = [google_project_service.firestore_api]
}

# Create Cloud Storage bucket for receipts
resource "google_storage_bucket" "receipts" {
  name          = "${var.project_id}-receipts"
  location      = var.region
  force_destroy = false

  uniform_bucket_level_access = true

  cors {
    origin          = ["*"]
    method          = ["GET", "HEAD", "PUT", "POST", "DELETE"]
    response_header = ["*"]
    max_age_seconds = 3600
  }

  lifecycle_rule {
    condition {
      age = 365
    }
    action {
      type = "Delete"
    }
  }

  depends_on = [google_project_service.storage_api]
}

# Cloud Scheduler job for weekly emails
resource "google_cloud_scheduler_job" "weekly_summary" {
  name             = "weekly-expense-summary"
  description      = "Send weekly expense summaries every Monday at 9 AM"
  schedule         = "0 9 * * 1"
  time_zone        = "America/New_York"
  attempt_deadline = "320s"

  http_target {
    http_method = "GET"
    uri         = "https://${var.region}-${var.project_id}.cloudfunctions.net/send_weekly_summary"
  }

  depends_on = [google_project_service.cloudscheduler_api]
}

# Service account for Cloud Functions
resource "google_service_account" "functions_sa" {
  account_id   = "expense-tracker-functions"
  display_name = "Expense Tracker Cloud Functions Service Account"
}

# Grant necessary permissions to service account
resource "google_project_iam_member" "functions_sa_vision" {
  project = var.project_id
  role    = "roles/cloudvision.admin"
  member  = "serviceAccount:${google_service_account.functions_sa.email}"
}

resource "google_project_iam_member" "functions_sa_firestore" {
  project = var.project_id
  role    = "roles/datastore.user"
  member  = "serviceAccount:${google_service_account.functions_sa.email}"
}

resource "google_project_iam_member" "functions_sa_storage" {
  project = var.project_id
  role    = "roles/storage.objectViewer"
  member  = "serviceAccount:${google_service_account.functions_sa.email}"
}

resource "google_project_iam_member" "functions_sa_aiplatform" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.functions_sa.email}"
}

# Output values
output "project_id" {
  value = var.project_id
}

output "receipts_bucket_name" {
  value = google_storage_bucket.receipts.name
}

output "service_account_email" {
  value = google_service_account.functions_sa.email
}
