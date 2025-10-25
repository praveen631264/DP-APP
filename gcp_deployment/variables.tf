variable "gcp_project_id" {
  description = "The GCP project ID to deploy to."
  type        = string
}

variable "gcp_region" {
  description = "The GCP region to deploy resources in."
  type        = string
  default     = "us-central1"
}

variable "mongo_db_connection" {
  description = "The full connection string for the MongoDB Atlas database."
  type        = string
  sensitive   = true
}

variable "flask_secret_key" {
  description = "A secret key for Flask session management."
  type        = string
  sensitive   = true
}
