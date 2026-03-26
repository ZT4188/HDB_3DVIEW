#!/usr/bin/env python3
"""
Seed the buildings table from hdb.json (from ualsg/hdb3d-data).

Usage:
  docker compose exec api python scripts/seed_db.py
  # or locally:
  python scripts/seed_db.py --hdb-json path/to/hdb.json
"""

import asyncio
import json
import os
import sys
import hashlib
import argparse

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.models.models import Building, Base
from app.database import engine

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://hdb3d:hdb3dlocal@localhost:5432/hdb3d",
)

AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


def make_building_id(blk_no: str, street: str) -> str:
    key = f"{blk_no}_{street}".upper().replace(" ", "_")
    return hashlib.md5(key.encode()).hexdigest()[:12]


async def seed(hdb_json_path: str):
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    with open(hdb_json_path, "r") as f:
        data = json.load(f)

    # hdb.json structure: list of records with keys like
    # blk_no, street, max_floor_lvl, year_completed,
    # 1room_sold, 2room_sold, 3room_sold, 4room_sold, 5room_sold,
    # total_dwelling_units, lat, lng (approximate)
    records = data if isinstance(data, list) else data.get("records", [])

    buildings = []
    for r in records:
        blk_no = str(r.get("blk_no", "")).strip()
        street = str(r.get("street", "")).strip()
        if not blk_no or not street:
            continue

        lat = float(r.get("lat", r.get("latitude", 1.3521)))
        lng = float(r.get("lng", r.get("longitude", 103.8198)))

        b = Building(
            id=make_building_id(blk_no, street),
            blk_no=blk_no,
            street=street,
            address=f"BLK {blk_no} {street}, SINGAPORE",
            dwelling_units=int(r.get("total_dwelling_units", 0)),
            room_1=int(r.get("1room_sold", r.get("1room_rental", 0))),
            room_2=int(r.get("2room_sold", r.get("2room_rental", 0))),
            room_3=int(r.get("3room_sold", 0)),
            room_4=int(r.get("4room_sold", 0)),
            room_5=int(r.get("5room_sold", 0)),
            latitude=lat,
            longitude=lng,
            cityjson_id=r.get("cityjson_id"),
        )
        buildings.append(b)

    async with AsyncSessionLocal() as db:
        # Upsert: skip existing IDs
        from sqlalchemy.dialects.postgresql import insert
        for b in buildings:
            stmt = insert(Building).values(
                id=b.id, blk_no=b.blk_no, street=b.street,
                address=b.address, dwelling_units=b.dwelling_units,
                room_1=b.room_1, room_2=b.room_2, room_3=b.room_3,
                room_4=b.room_4, room_5=b.room_5,
                latitude=b.latitude, longitude=b.longitude,
                cityjson_id=b.cityjson_id,
            ).on_conflict_do_nothing(index_elements=["id"])
            await db.execute(stmt)
        await db.commit()

    print(f"✅ Seeded {len(buildings)} buildings.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--hdb-json",
        default=os.path.join(os.path.dirname(__file__), "../assets/hdb.json"),
        help="Path to hdb.json from ualsg/hdb3d-data",
    )
    args = parser.parse_args()
    asyncio.run(seed(args.hdb_json))
