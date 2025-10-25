terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 4.50.0"
    }
  }
}

provider "google" {
  project = var.gcp_project_id
  region  = var.gcp_region
}

# --------------------------------------------------------------------------------
# Core Services & APIs
# --------------------------------------------------------------------------------

resource "google_project_service" "cloudbuild" {
  service = "cloudbuild.googleapis.com"
}

resource "google_project_service" "artifactregistry" {
  service = "artifactregistry.googleapis.com"
}

resource "google_project_service" "run" {
  service = "run.googleapis.com"
}

resource "google_project_service" "secretmanager" {
  service = "secretmanager.googleapis.com"
}

resource "google_project_service" "redis" {
  service = "redis.googleapis.com"
}

# --------------------------------------------------------------------------------
# Artifact Registry - To store our Docker image
# --------------------------------------------------------------------------------

resource "google_artifact_registry_repository" "docker_repo" {
  location      = var.gcp_region
  repository_id = "intellidocs-repo"
  format        = "DOCKER"
  depends_on    = [google_project_service.artifactregistry]
}

# --------------------------------------------------------------------------------
# Cloud Build - To build and push our Docker image
# --------------------------------------------------------------------------------

resource "google_cloudbuild_trigger" "build_trigger" {
  name        = "build-and-push-on-apply"
  description = "Builds and pushes the Docker image when terraform apply is run"

  # We are using an inline build configuration here for simplicity
  build {
    # The first step is to build the docker image
    step {
      name = "gcr.io/cloud-builders/docker"
      args = [
        "build",
        "-t",
        "${google_artifact_registry_repository.docker_repo.location}-docker.pkg.dev/${var.gcp_project_id}/${google_artifact_registry_repository.repository_id}/intellidocs-app:latest",
        ".", # Build from the root of the project
      ]
    }

    # The second step pushes the image to Artifact Registry
    step {
      name = "gcr.io/cloud-builders/docker"
      args = [
        "push",
        "${google_artifact_registry_repository.docker_repo.location}-docker.pkg.dev/${var.gcp_project_id}/${google_artifact_registry_repository.repository_id}/intellidocs-app:latest",
      ]
    }

    # This is the image that will be used by Cloud Run
    images = ["${google_artifact_registry_repository.docker_repo.location}-docker.pkg.dev/${var.gcp_project_id}/${google_artifact_registry_repository.repository_id}/intellidocs-app:latest"]
  }

  # This is a bit of a trick to make it run every time we apply
  # It uses the current timestamp as a substitution
  substitutions = {
    _TIMESTAMP = timestamp()
  }
  depends_on = [google_project_service.cloudbuild]
}

# --------------------------------------------------------------------------------
# Cloud Storage - For document uploads
# --------------------------------------------------------------------------------

resource "google_storage_bucket" "documents_bucket" {
  name          = "${var.gcp_project_id}-intellidocs-documents"
  location      = var.gcp_region
  force_destroy = true # Set to false in a real production environment
}

# --------------------------------------------------------------------------------
# Memorystore (Redis) - For Celery
# --------------------------------------------------------------------------------

resource "google_redis_instance" "celery_redis" {
  name           = "celery-broker"
  tier           = "BASIC" # Use BASIC for dev/test, STANDARD_HA for production
  memory_size_gb = 1
  depends_on     = [google_project_service.redis]
}

# --------------------------------------------------------------------------------
# Secret Manager - For storing secrets securely
# --------------------------------------------------------------------------------

resource "google_secret_manager_secret" "mongo_uri_secret" {
  secret_id = "mongo-db-connection"

  replication {
    automatic = true
  }
  depends_on = [google_project_service.secretmanager]
}

resource "google_secret_manager_secret_version" "mongo_uri_version" {
  secret      = google_secret_manager_secret.mongo_uri_secret.id
  secret_data = var.mongo_db_connection
}

resource "google_secret_manager_secret" "flask_key_secret" {
  secret_id = "flask-secret-key"

  replication {
    automatic = true
  }
}

resource "google_secret_manager_secret_version" "flask_key_version" {
  secret      = google_secret_manager_secret.flask_key_secret.id
  secret_data = var.flask_secret_key
}

# --------------------------------------------------------------------------------
# IAM - Permissions for Cloud Run to access secrets
# --------------------------------------------------------------------------------

resource "google_secret_manager_secret_iam_member" "mongo_secret_accessor" {
  project   = var.gcp_project_id
  secret_id = google_secret_manager_secret.mongo_uri_secret.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_project_service_identity.run.email}" # Default Cloud Run service account
}

resource "google_secret_manager_secret_iam_member" "flask_secret_accessor" {
  project   = var.gcp_project_id
  secret_id = google_secret_manager_secret.flask_key_secret.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_project_service_identity.run.email}"
}

# --------------------------------------------------------------------------------
# Cloud Run - The Flask Web Server
# --------------------------------------------------------------------------------

resource "google_cloud_run_v2_service" "flask_app" {
  name     = "intellidocs-flask-app"
  location = var.gcp_region

  template {
    containers {
      image = "${google_artifact_registry_repository.docker_repo.location}-docker.pkg.dev/${var.gcp_project_id}/${google_artifact_registry_repository.repository_id}/intellidocs-app:latest"

      env {
        name  = "GCS_BUCKET_NAME"
        value = google_storage_bucket.documents_bucket.name
      }
      env {
        name  = "REDIS_URL"
        value = "redis://${google_redis_instance.celery_redis.host}:${google_redis_instance.celery_redis.port}"
      }
      env {
        name = "MONGO_DB_CONNECTION"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.mongo_uri_secret.secret_id
            version = "latest"
          }
        }
      }
      env {
        name = "FLASK_SECRET_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.flask_key_secret.secret_id
            version = "latest"
          }
        }
      }
    }
  }

  # Allow public access
  ingress = "INGRESS_TRAFFIC_ALL"

  depends_on = [
    google_cloudbuild_trigger.build_trigger,
    google_secret_manager_secret_iam_member.mongo_secret_accessor,
    google_secret_manager_secret_iam_member.flask_secret_accessor,
  ]
}

# --------------------------------------------------------------------------------
# Cloud Run - The Celery Worker
# --------------------------------------------------------------------------------

resource "google_cloud_run_v2_service" "celery_worker" {
  name     = "intellidocs-celery-worker"
  location = var.gcp_region

  # This is a background worker, so no public ingress
  ingress = "INGRESS_TRAFFIC_INTERNAL_ONLY"

  template {
    containers {
      image = "${google_artifact_registry_repository.docker_repo.location}-docker.pkg.dev/${var.gcp_project_id}/${google_artifact_registry_repository.repository_id}/intellidocs-app:latest"
      command = ["celery", "-A", "main.celery", "worker", "--loglevel=info"]

      env {
        name  = "GCS_BUCKET_NAME"
        value = google_storage_bucket.documents_bucket.name
      }
      env {
        name  = "REDIS_URL"
        value = "redis://${google_redis_instance.celery_redis.host}:${google_redis_instance.celery_redis.port}"
      }
      env {
        name = "MONGO_DB_CONNECTION"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.mongo_uri_secret.secret_id
            version = "latest"
          }
        }
      }
    }
  }

  depends_on = [
    google_cloudbuild_trigger.build_trigger,
    google_secret_manager_secret_iam_member.mongo_secret_accessor,
  ]
}
