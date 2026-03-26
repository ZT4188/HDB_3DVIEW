# Reflection Document

## Time Allocation

| Activity | % of Time | Notes |
|---|---|---|
| Planning & architecture | 15% | Solution design, tech selection, risk mapping |
| Research | 20% | deck.gl ScenegraphLayer docs, CityJSON format, PostGIS spatial queries, Celery + asyncio patterns |
| Coding | 55% | Backend models/API/sim engine, frontend components, docker-compose wiring |
| Documentation | 10% | README, inline comments, implementation plan |

---

## What I Would Have Done Differently

### 1. Start with a data spike on the CityJSON pipeline
The biggest unknown was the CityJSON → deck.gl rendering pipeline. I would now front-load a 2–3 hour spike: parse one building from `hdb3d-r.json`, render it in deck.gl, confirm performance — *before* designing any backend. That spike would have de-risked the most technically uncertain part early and potentially changed the rendering approach (e.g. opting for extruded polygons from the start rather than treating 3D models as the primary path).

### 2. Use MapLibre GL instead of Mapbox
Mapbox requires a token and has usage-based billing that adds operational friction. MapLibre GL JS is a drop-in OSS replacement that works with Singapore's free [OneMap tiles](https://www.onemap.gov.sg/docs/) — removing all map licensing concerns. I would make this the default from day one.

### 3. Ship a simpler simulation engine first
The NumPy-vectorised engine with births/deaths/moves is correct, but the *Celery + Redis pub/sub + WebSocket* plumbing around it is the real integration complexity. I would first implement the simulation loop as a simple `asyncio` background task running in the FastAPI process — no Celery, no Redis pub/sub. That would deliver the full simulation UX in half the time, with Celery as a later optimisation for scaling.

### 4. Use a monorepo tool (Turborepo or pnpm workspaces)
With a clear `frontend/` + `backend/` split, a monorepo tool would enable single-command linting, testing, and building across both packages, which matters as the codebase grows.

---

## Areas of Improvement with More Time

### Performance
- **Level-of-detail (LOD)**: At zoom < 13, render buildings as flat `GeoJsonLayer` extruded polygons (~10× faster). Switch to 3D models only at high zoom. deck.gl supports this natively via layer visibility conditions.
- **Incremental WebSocket diffs**: Currently the `resident_deltas` payload sends every building's count on every tick. For 10k+ buildings this is ~200KB per second. Switch to sending only changed buildings (delta compression).

### Simulation Fidelity
- Use real Singapore census data (Singstat) for age-stratified birth/death rates rather than flat rates.
- Model HDB flat types separately — 3-room flats have different occupancy profiles than 5-room flats.
- Add household formation (new couples moving into vacant flats) as a distinct event type.

### UX
- **Building search**: Typeahead search by address/block number to fly the camera to a specific building.
- **Comparison mode**: Split-screen two simulation sessions side-by-side.
- **Export**: Download the move log or yearly stats as CSV.

### Operations
- **CI/CD pipeline**: GitHub Actions workflow to run tests, build images, and deploy to Cloud Run on merge to `main`.
- **Observability**: Cloud Monitoring dashboards for API latency, WebSocket connection count, simulation queue depth.
- **Database backups**: Automated snapshot before each major seeding operation.
