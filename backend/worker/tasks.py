"""
Celery Worker Tasks — runs simulation ticks as background jobs.
"""

import asyncio
import json
import os

import redis as sync_redis
from celery import Celery
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.models.models import SimSession, YearlySnapshot, SimStatus
from app.services.simulation import run_simulation_tick

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://hdb3d:hdb3dlocal@localhost:5432/hdb3d",
)

celery_app = Celery("worker", broker=CELERY_BROKER_URL)

# Async engine for use inside tasks
engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

WS_CHANNEL_PREFIX = "sim:tick:"
TICK_INTERVAL_SECONDS = 2  # Simulated year = 2 real seconds


def _run_async(coro):
    """Helper to run async code inside a Celery (sync) task."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(bind=True)
def start_simulation_task(self, session_id: str):
    """
    Runs simulation ticks in a loop until the session is paused or deleted.
    Each tick advances by one simulated year.
    """
    r = sync_redis.from_url(REDIS_URL)

    async def _run():
        async with AsyncSessionLocal() as db:
            from sqlalchemy import select
            while True:
                # Check current session status
                result = await db.execute(
                    select(SimSession).where(SimSession.id == session_id)
                )
                session = result.scalar_one_or_none()
                if not session or session.status != SimStatus.running:
                    break

                # Run one year tick
                tick_data = await run_simulation_tick(session_id, db)
                if not tick_data:
                    break

                session.current_year += 1
                session.years_simulated += 1
                session.total_residents = tick_data["total_residents"]
                session.total_deaths = (session.total_deaths or 0) + tick_data["total_deaths"]

                # Store snapshot for timeline replay
                snapshot = YearlySnapshot(
                    session_id=session_id,
                    year=session.current_year,
                    total_residents=tick_data["total_residents"],
                    total_births=tick_data["total_births"],
                    total_deaths=tick_data["total_deaths"],
                    resident_map=tick_data["resident_map"],
                    move_log=tick_data["move_log"],
                )
                db.add(snapshot)
                await db.commit()

                # Publish tick to WebSocket clients via Redis pub/sub
                message = json.dumps({
                    "type": "tick",
                    "year": session.current_year,
                    "years_simulated": session.years_simulated,
                    "total_residents": tick_data["total_residents"],
                    "total_births": tick_data["total_births"],
                    "total_deaths": tick_data["total_deaths"],
                    "resident_deltas": tick_data["resident_map"],
                    "move_log": tick_data["move_log"],
                })
                r.publish(f"{WS_CHANNEL_PREFIX}{session_id}", message)

                await asyncio.sleep(TICK_INTERVAL_SECONDS)

    _run_async(_run())


@celery_app.task
def pause_simulation_task(session_id: str):
    """
    Signal the running simulation to stop by setting status to paused in DB.
    The start_simulation_task loop checks this on each iteration.
    """
    # The status is already updated via the API endpoint before this task fires.
    # This task exists as a hook for future cleanup / notifications.
    pass
