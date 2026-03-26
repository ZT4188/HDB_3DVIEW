# HDB 3D Population Simulation

A full-stack geospatial web application that renders Singapore's HDB flats in 3D and simulates population growth and decline across buildings over time.

![Tech Stack](https://img.shields.io/badge/frontend-React%2018%20%2B%20deck.gl-61DAFB?style=flat-square)
![Tech Stack](https://img.shields.io/badge/backend-FastAPI%20%2B%20Python-009688?style=flat-square)
![Tech Stack](https://img.shields.io/badge/database-PostgreSQL%20%2B%20PostGIS-336791?style=flat-square)
![Tech Stack](https://img.shields.io/badge/cloud-GCP%20Cloud%20Run-4285F4?style=flat-square)

## Features

- 🏢 **3D HDB Buildings** — All Singapore HDB blocks rendered in WebGL via deck.gl
- 🗺️ **Island Boundary** — Singapore coastline with solid green fill overlay
- 🖱️ **Building Selection** — Click any block to view address, unit counts (1–5 room)
- 👥 **Population Simulation** — Yearly births, deaths, and inter-flat moves
- 🎨 **Occupancy Heatmap** — Buildings colour-coded from vacant (green) to full (red)
- 📊 **Live Stats Panel** — Current year, total residents, deaths, move log
- ⏱️ **Timeline Replay** — Scrub through any simulated year
- 💾 **Session Management** — Save, restore, and compare simulation sessions

---

## Quick Start (Docker Compose)

### Prerequisites
- [Docker](https://docs.docker.com/get-docker/) + [Docker Compose](https://docs.docker.com/compose/install/)
- A [Mapbox token](https://account.mapbox.com/) (free tier is sufficient)

### 1. Clone the repo
```bash
git clone https://github.com/YOUR_USERNAME/hdb3d-simulation.git
cd hdb3d-simulation
```

### 2. Set environment variables
```bash
cp .env.example .env
# Edit .env and add your MAPBOX_TOKEN
```

### 3. Download HDB 3D data assets
```bash
# Run the asset preparation script (downloads + converts CityJSON → glTF)
bash scripts/prepare_assets.sh
```

### 4. Start all services
```bash
docker compose up --build
```

| Service | URL |
|---|---|
| Frontend | http://localhost:5173 |
| API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
| Redis | localhost:6379 |
| Postgres | localhost:5432 |

### 5. Seed the database
```bash
# In a second terminal (after services are running)
docker compose exec api python scripts/seed_db.py
```

---

## Project Structure

```
hdb3d-simulation/
├── frontend/               # React 18 + Vite + deck.gl
│   ├── src/
│   │   ├── components/     # Map, panels, controls, session list
│   │   ├── hooks/          # useSimulation, useWebSocket, useBuildings
│   │   ├── store/          # Zustand state slices
│   │   └── utils/          # Colour scale, GeoJSON helpers
│   ├── Dockerfile
│   └── package.json
│
├── backend/                # FastAPI application
│   ├── app/
│   │   ├── api/            # Route handlers (buildings, sessions, ws)
│   │   ├── models/         # SQLAlchemy ORM models
│   │   ├── schemas/        # Pydantic request/response schemas
│   │   └── services/       # Simulation engine, session logic
│   ├── alembic/            # DB migrations
│   ├── Dockerfile
│   └── requirements.txt
│
├── worker/                 # Celery worker (simulation ticks)
│   └── tasks.py
│
├── infra/
│   └── terraform/          # GCP Cloud Run + Cloud SQL + Redis
│
├── scripts/
│   ├── prepare_assets.sh   # Download + convert HDB 3D data
│   └── seed_db.py          # Seed buildings from hdb.json
│
├── docs/
│   ├── IMPLEMENTATION_PLAN.md
│   └── REFLECTION.md
│
├── docker-compose.yml
├── docker-compose.prod.yml
└── .env.example
```

---

## Development (without Docker)

### Backend
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# Requires local Postgres + Redis running
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

### Celery Worker
```bash
cd backend
celery -A worker.tasks worker --loglevel=info
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/buildings` | All HDB buildings as GeoJSON |
| `GET` | `/buildings/{id}` | Single building detail |
| `POST` | `/sessions` | Create simulation session |
| `GET` | `/sessions` | List all sessions |
| `POST` | `/sessions/{id}/assign` | Randomly assign initial residents |
| `POST` | `/sessions/{id}/start` | Start simulation |
| `POST` | `/sessions/{id}/pause` | Pause simulation |
| `GET` | `/sessions/{id}/snapshot/{year}` | Fetch year snapshot for replay |
| `WS` | `/ws/sessions/{id}` | Live tick events stream |

Full interactive docs at `http://localhost:8000/docs` (Swagger UI).

---

## Deployment (GCP)

See [`infra/terraform/README.md`](infra/terraform/README.md) for full GCP deployment instructions using Terraform.

Estimated cost: **~$65–90/month** at medium traffic using Cloud Run (scale-to-zero) + Cloud SQL + Memorystore Redis.

---

## Data Sources

- **HDB 3D Models**: [ualsg/hdb3d-data](https://github.com/ualsg/hdb3d-data) (CityJSON LoD1)
- **HDB Unit Data**: `hdb.json` from the same repository
- **Singapore Boundary**: [Singapore boundary GeoJSON](https://github.com/yinshanyang/singapore)

---

## License

MIT
