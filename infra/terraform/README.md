# GCP Infrastructure (Terraform)

Provisions the full production stack on Google Cloud Platform.

## Prerequisites

- [Terraform](https://developer.hashicorp.com/terraform/install) >= 1.6
- [gcloud CLI](https://cloud.google.com/sdk/docs/install) authenticated
- A GCP project with billing enabled

## Enable required APIs

```bash
gcloud services enable \
  run.googleapis.com \
  sqladmin.googleapis.com \
  redis.googleapis.com \
  vpcaccess.googleapis.com \
  artifactregistry.googleapis.com \
  storage.googleapis.com \
  --project=YOUR_PROJECT_ID
```

## Deploy

```bash
cd infra/terraform

# Create terraform.tfvars (never commit this file)
cat > terraform.tfvars <<EOF
project_id  = "your-gcp-project-id"
region      = "asia-southeast1"
db_password = "a-strong-password-here"
EOF

terraform init
terraform plan
terraform apply
```

## After deploy

1. Build and push Docker images:
```bash
gcloud auth configure-docker asia-southeast1-docker.pkg.dev

docker build -t asia-southeast1-docker.pkg.dev/YOUR_PROJECT/hdb3d-simulation/api:latest ./backend
docker push asia-southeast1-docker.pkg.dev/YOUR_PROJECT/hdb3d-simulation/api:latest
```

2. Run DB migrations:
```bash
# Cloud Run jobs can be used for one-off migration runs
gcloud run jobs create db-migrate \
  --image=asia-southeast1-docker.pkg.dev/YOUR_PROJECT/hdb3d-simulation/api:latest \
  --command="alembic" \
  --args="upgrade,head" \
  --region=asia-southeast1
gcloud run jobs execute db-migrate --region=asia-southeast1
```

3. Seed buildings:
```bash
gcloud run jobs create db-seed \
  --image=asia-southeast1-docker.pkg.dev/YOUR_PROJECT/hdb3d-simulation/api:latest \
  --command="python" \
  --args="scripts/seed_db.py" \
  --region=asia-southeast1
gcloud run jobs execute db-seed --region=asia-southeast1
```

4. Upload frontend build to GCS:
```bash
cd frontend && npm run build
gsutil -m rsync -r dist/ gs://YOUR_PROJECT-hdb3d-assets/
```

## Estimated cost at medium traffic (~200 DAU)

| Resource | Tier | Est. $/mo |
|---|---|---|
| Cloud Run API | min=1 instance | ~$15–30 |
| Cloud Run Worker | min=0 | ~$5–10 |
| Cloud SQL | db-f1-micro | ~$10 |
| Memorystore Redis | 1GB Basic | ~$35 |
| GCS + CDN | standard | ~$5–10 |
| **Total** | | **~$70–95** |

> **Tip**: Swap Memorystore for [Upstash Redis](https://upstash.com) to cut Redis cost to ~$0–5/mo for medium traffic.
