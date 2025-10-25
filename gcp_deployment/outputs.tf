output "flask_app_url" {
  description = "The public URL of the deployed Flask application."
  value       = google_cloud_run_v2_service.flask_app.uri
}

output "document_bucket_name" {
  description = "The name of the Google Cloud Storage bucket for documents."
  value       = google_storage_bucket.documents_bucket.name
}
