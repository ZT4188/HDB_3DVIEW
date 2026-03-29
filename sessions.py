"""
Sessions API — create, list, control simulation sessions.
"""

import uuid
import os
from celery import Celery
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.models import SimSession, BuildingResidents, Building, YearlySnapshot, SimStatus
from app.services.simulation import assign_residents

router = APIRouter()

celery_app = Celery(broker=os.getenv("CELERY_BROKER_URL", "redis://redis:6379/1"))


@router.post("")
async def create_session(name: str, db: AsyncSession = Depends(get_db)):
    session = SimSession(id=str(uuid.uuid4()), name=name)
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


@router.get("")
async def list_sessions(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SimSession).order_by(SimSession.created_at.desc()))
    sessions = result.scalars().all()
    return sessions


@router.get("/{session_id}")
async def get_session(session_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SimSession).where(SimSession.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.post("/{session_id}/assign")
async def assign_residents_endpoint(session_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SimSession).where(SimSession.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    stats = await assign_residents(session_id, db)
    session.total_residents = stats["total_residents"]
    await db.commit()
    return {"message": "Residents assigned", **stats}


@router.post("/{session_id}/start")
async def start_simulation(session_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SimSession).where(SimSession.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.status == SimStatus.running:
        return {"message": "Already running"}

    session.status = SimStatus.running
    await db.commit()

    celery_app.send_task("worker.tasks.start_simulation_task", args=[session_id])
    return {"message": "Simulation started", "session_id": session_id}


@router.post("/{session_id}/pause")
async def pause_simulation(session_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SimSession).where(SimSession.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    session.status = SimStatus.paused
    await db.commit()
    return {"message": "Simulation paused"}


@router.delete("/{session_id}")
async def delete_session(session_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SimSession).where(SimSession.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    await db.delete(session)
    await db.commit()
    return {"message": "Session deleted"}


@router.get("/{session_id}/snapshot/{year}")
async def get_snapshot(session_id: str, year: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(YearlySnapshot)
        .where(YearlySnapshot.session_id == session_id)
        .where(YearlySnapshot.year == year)
    )
    snapshot = result.scalar_one_or_none()
    if not snapshot:
        raise HTTPException(status_code=404, detail="Snapshot not found")
    return {
        "year": snapshot.year,
        "total_residents": snapshot.total_residents,
        "total_deaths": snapshot.total_deaths,
        "total_births": snapshot.total_births,
        "resident_map": snapshot.resident_map,
        "move_log": snapshot.move_log,
    }