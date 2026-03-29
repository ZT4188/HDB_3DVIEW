"""
HDB 3D Simulation — FastAPI Application Entry Point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import buildings, sessions, websocket
from app.database import engine, Base

app = FastAPI(
    title="HDB 3D Simulation API",
    description="Geospatial API for HDB building data and population simulation",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(buildings.router, prefix="/buildings", tags=["buildings"])
app.include_router(sessions.router, prefix="/sessions", tags=["sessions"])
app.include_router(websocket.router, tags=["websocket"])


@app.get("/health")
async def health():
    return {"status": "ok"}