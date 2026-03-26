# Reflection Document

## Time Allocation

| Activity | % of Time | Notes |
|---|---|---|
| Planning & architecture | 20% | Solution design, tech stack evaluation, API surface, data model |
| Research | 15% | CityJSON/cjio pipeline, deck.gl ScenegraphLayer, PostGIS, Cloud Run WS support |
| Coding — backend | 35% | FastAPI, ORM models, simulation engine, Celery/WebSocket integration |
| Coding — frontend | 20% | deck.gl map, Zustand store, all UI components |
| DevOps / infra | 10% | Docker Compose, Dockerfiles, Terraform, CI pipeline |

---

## What I Would Have Done Differently

**1. Validate the CityJSON pipeline on day one.**
The CityJSON → glTF conversion (T-01) was the highest-risk task. I would prototype it immediately with a sample of 50 buildings before committing to the full architecture — a geometry format surprise could have forced an early pivot to pure extruded polygons.

**2. Use MapLibre GL JS from the start instead of Mapbox.**
Mapbox requires an API token which creates friction for reviewers. MapLibre GL JS is a fully open-source drop-in replacement using OpenStreetMap or Singapore's OneMap tiles at zero cost. Switching mid-project wastes time.

**3. Write the simulation engine as a pure function first.**
I would implement `services/simulation.py` as a standalone, synchronous, unit-tested function completely decoupled from FastAPI and Celery. Verify the demographic math works correctly, then wire it into async background tasks. This ordering dramatically reduces debugging complexity.

**4. Use SSE instead of WebSockets for tick delivery.**
Since tick data only flows server → client, Server-Sent Events would have been simpler than WebSockets: no reconnection logic, native browser support, works through any HTTP proxy, trivially supported by FastAPI's `StreamingResponse`. Simulation controls go through REST anyway, so full-duplex isn't needed.

**5. Bundle a small fixture dataset in the repo.**
A subset of ~500 buildings from one town (e.g. Tampines) committed as a fixture would let reviewers run `docker compose up` and see a populated map immediately, without the `prepare_assets.sh` download step. Lower friction = better first impression.

---

## Areas for Improvement with More Time

**Performance**
- Full CityJSON → glTF pipeline to render actual building footprint models instead of procedural boxes
- PostGIS `GIST` index + `ST_DWithin` for proximity-weighted move destinations instead of random sampling
- deck.gl LOD: switch to GeoJsonLayer at zoom < 13 to avoid rendering 12k 3D models when too small to distinguish

**Features**
- Proximity-weighted move logic: residents prefer nearby flats
- Singapore SingStat integration: town-level birth/death rates instead of flat national averages
- CSV / shareable link export of simulation results

**Reliability**
- Snapshot diff compression: store only resident count deltas per year (not full maps), reducing storage from ~50MB to ~5MB for 100 simulated years
- Celery Beat for periodic tick scheduling instead of a tight loop inside a single long-running task
