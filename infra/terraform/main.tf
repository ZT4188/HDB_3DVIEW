terraform {
  required_version = ">= 1.6"
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

# ── Artifact Registry ─────────────────────────────────────────
resource "google_artifact_registry_repository" "hdb3d" {
  location      = var.region
  repository_id = "hdb3d-simulation"
  format        = "DOCKER"
}

# ── Cloud SQL (PostgreSQL + PostGIS) ──────────────────────────
resource "google_sql_database_instance" "postgres" {
  name             = "hdb3d-postgres"
  database_version = "POSTGRES_15"
  region           = var.region

  settings {
    tier              = "db-f1-micro"  # ~$7/mo shared CPU
    availability_type = "ZONAL"

    backup_configuration {
      enabled            = true
      start_time         = "03:00"
      retained_backups   = 7
    }

    ip_configuration {
      ipv4_enabled    = false
      private_network = google_compute_network.vpc.id
    }
  }

  deletion_protection = false
}

resource "google_sql_database" "db" {
  name     = "hdb3d"
  instance = google_sql_database_instance.postgres.name
}

resource "google_sql_user" "user" {
  name     = "hdb3d"
  instance = google_sql_database_instance.postgres.name
  password = var.db_password
}

# ── Memorystore Redis ─────────────────────────────────────────
resource "google_redis_instance" "redis" {
  name           = "hdb3d-redis"
  memory_size_gb = 1
  region         = var.region
  tier           = "BASIC"

  authorized_network = google_compute_network.vpc.id
  connect_mode       = "PRIVATE_SERVICE_ACCESS"
}

# ── VPC ───────────────────────────────────────────────────────
resource "google_compute_network" "vpc" {
  name                    = "hdb3d-vpc"
  auto_create_subnetworks = true
}

resource "google_vpc_access_connector" "connector" {
  name          = "hdb3d-connector"
  region        = var.region
  network       = google_compute_network.vpc.name
  ip_cidr_range = "10.8.0.0/28"
}

# ── GCS Bucket (assets + frontend) ───────────────────────────
resource "google_storage_bucket" "assets" {
  name          = "${var.project_id}-hdb3d-assets"
  location      = "ASIA"
  force_destroy = true

  cors {
    origin          = ["*"]
    method          = ["GET", "HEAD"]
    response_header = ["Content-Type"]
    max_age_seconds = 3600
  }

  website {
    main_page_suffix = "index.html"
    not_found_page   = "index.html"
  }
}

resource "google_storage_bucket_iam_member" "public_assets" {
  bucket = google_storage_bucket.assets.name
  role   = "roles/storage.objectViewer"
  member = "allUsers"
}

# ── Cloud Run — API ───────────────────────────────────────────
resource "google_cloud_run_v2_service" "api" {
  name     = "hdb3d-api"
  location = var.region

  template {
    scaling {
      min_instance_count = 1  # Keep warm — needed for WebSocket sessions
      max_instance_count = 10
    }

    vpc_access {
      connector = google_vpc_access_connector.connector.id
      egress    = "PRIVATE_RANGES_ONLY"
    }

    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/hdb3d-simulation/api:latest"

      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
      }

      env {
        name  = "DATABASE_URL"
        value = "postgresql+asyncpg://hdb3d:${var.db_password}@${google_sql_database_instance.postgres.private_ip_address}/hdb3d"
      }
      env {
        name  = "REDIS_URL"
        value = "redis://${google_redis_instance.redis.host}:6379/0"
      }
      env {
        name  = "CELERY_BROKER_URL"
        value = "redis://${google_redis_instance.redis.host}:6379/1"
      }
    }
  }
}

# Allow unauthenticated access to API
resource "google_cloud_run_service_iam_member" "api_public" {
  location = google_cloud_run_v2_service.api.location
  service  = google_cloud_run_v2_service.api.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# ── Cloud Run — Celery Worker ─────────────────────────────────
resource "google_cloud_run_v2_service" "worker" {
  name     = "hdb3d-worker"
  location = var.region

  template {
    scaling {
      min_instance_count = 0
      max_instance_count = 5
    }

    vpc_access {
      connector = google_vpc_access_connector.connector.id
      egress    = "PRIVATE_RANGES_ONLY"
    }

    containers {
      image   = "${var.region}-docker.pkg.dev/${var.project_id}/hdb3d-simulation/api:latest"
      command = ["celery"]
      args    = ["-A", "worker.tasks", "worker", "--loglevel=info", "--concurrency=2"]

      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
      }

      env {
        name  = "DATABASE_URL"
        value = "postgresql+asyncpg://hdb3d:${var.db_password}@${google_sql_database_instance.postgres.private_ip_address}/hdb3d"
      }
      env {
        name  = "REDIS_URL"
        value = "redis://${google_redis_instance.redis.host}:6379/0"
      }
      env {
        name  = "CELERY_BROKER_URL"
        value = "redis://${google_redis_instance.redis.host}:6379/1"
      }
    }
  }
}
