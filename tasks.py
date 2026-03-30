import json
import os
import time

import redis as sync_redis
from celery import Celery
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.models.models import SimSession, YearlySnapshot, SimStatus, BuildingResidents
import numpy as np
import random

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/1")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

# Sync DATABASE_URL — replace asyncpg with psycopg2
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://hdb3d:hdb3dlocal@postgres:5432/hdb3d"
).replace("postgresql+asyncpg://", "postgresql+psycopg2://")

celery_app = Celery("worker", broker=CELERY_BROKER_URL)

WS_CHANNEL_PREFIX = "sim:tick:"
TICK_INTERVAL_SECONDS = 2
BIRTH_RATE = 0.009
DEATH_RATE = 0.0055
MOVE_RATE  = 0.02


def run_tick_sync(session_id: str, db_session):
    """Synchronous simulation tick using plain SQLAlchemy."""
    from sqlalchemy import select as sa_select
    entries = db_session.execute(
        sa_select(BuildingResidents).where(BuildingResidents.session_id == session_id)
    ).scalars().all()

    if not entries:
        return {}

    building_ids = [e.building_id for e in entries]
    counts = np.array([e.residents for e in entries], dtype=float)

    births  = np.random.poisson(counts * BIRTH_RATE)
    deaths  = np.random.poisson(counts * DEATH_RATE)
    movers  = np.minimum(np.random.poisson(counts * MOVE_RATE).astype(int), counts.astype(int))

    move_log = []
    n = len(building_ids)
    from_counts = np.zeros(n, dtype=int)
    to_counts   = np.zeros(n, dtype=int)

    for i, num in enumerate(movers):
        if num == 0:
            continue
        dests = np.random.randint(0, n, size=num)
        for d in dests:
            if d != i:
                from_counts[i] += 1
                to_counts[d]   += 1
        if from_counts[i] > 0:
            move_log.append({
                "from_id": building_ids[i],
                "to_id":   building_ids[int(np.random.randint(0, n))],
                "count":   int(from_counts[i]),
            })

    counts = np.maximum(counts + births - deaths - from_counts + to_counts, 0).astype(int)

    for entry, new_count in zip(entries, counts):
        entry.residents = int(new_count)
    db_session.flush()

    return {
        "total_residents": int(counts.sum()),
        "total_births":    int(births.sum()),
        "total_deaths":    int(deaths.sum()),
        "resident_map":    {bid: int(c) for bid, c in zip(building_ids, counts)},
        "move_log":        move_log[:100],
    }


@celery_app.task(bind=True)
def start_simulation_task(self, session_id: str):
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    Session = sessionmaker(bind=engine)
    r = sync_redis.from_url(REDIS_URL)

    try:
        while True:
            with Session() as db:
                session = db.execute(
                    select(SimSession).where(SimSession.id == session_id)
                ).scalar_one_or_none()

                if not session or session.status != SimStatus.running:
                    break

                tick_data = run_tick_sync(session_id, db)
                if not tick_data:
                    break

                session.current_year    += 1
                session.years_simulated += 1
                session.total_residents  = tick_data["total_residents"]
                session.total_deaths     = (session.total_deaths or 0) + tick_data["total_deaths"]

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
                db.commit()

            message = json.dumps({
                "type":            "tick",
                "year":            session.current_year,
                "years_simulated": session.years_simulated,
                "total_residents": tick_data["total_residents"],
                "total_births":    tick_data["total_births"],
                "total_deaths":    tick_data["total_deaths"],
                "resident_deltas": tick_data["resident_map"],
                "move_log":        tick_data["move_log"],
            })
            r.publish(f"{WS_CHANNEL_PREFIX}{session_id}", message)
            time.sleep(TICK_INTERVAL_SECONDS)
    finally:
        engine.dispose()
        r.close()


@celery_app.task
def pause_simulation_task(session_id: str):
    pass
