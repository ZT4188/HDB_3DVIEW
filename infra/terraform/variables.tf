variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region (asia-southeast1 = Singapore)"
  type        = string
  default     = "asia-southeast1"
}

variable "db_password" {
  description = "PostgreSQL password for hdb3d user"
  type        = string
  sensitive   = true
}
