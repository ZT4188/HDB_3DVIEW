output "api_url" {
  description = "Cloud Run API service URL"
  value       = google_cloud_run_v2_service.api.uri
}

output "assets_bucket" {
  description = "GCS bucket for static assets and frontend"
  value       = google_storage_bucket.assets.name
}

output "redis_host" {
  description = "Memorystore Redis host (private)"
  value       = google_redis_instance.redis.host
  sensitive   = true
}

output "postgres_ip" {
  description = "Cloud SQL private IP"
  value       = google_sql_database_instance.postgres.private_ip_address
  sensitive   = true
}
