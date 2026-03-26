"""
Population Simulation Engine

Uses NumPy for vectorised operations across all HDB buildings.
Based loosely on Singapore's demographic statistics:
  - Crude birth rate: ~0.9% per year
  - Crude death rate: ~0.55% per year
  - Inter-flat move rate: ~2% of residents per year
"""

import numpy as np
import random
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.models.models import Building, BuildingResidents, YearlySnapshot

# Singapore demographic rates (annual)
BIRTH_RATE = 0.009
DEATH_RATE = 0.0055
MOVE_RATE = 0.02


async def assign_residents(session_id: str, db: AsyncSession) -> dict:
    """
    Randomly assign initial residents to all buildings for a new session.
    Each building gets a random occupancy between 40% and 90% of dwelling_units.
    """
    result = await db.execute(select(Building))
    buildings = result.scalars().all()

    total = 0
    resident_entries = []

    for building in buildings:
        capacity = building.dwelling_units
        if capacity == 0:
            count = 0
        else:
            # Assume avg 2.5 residents per dwelling unit, with variance
            avg_residents = capacity * random.uniform(0.4, 0.9) * 2.5
            count = max(0, int(np.random.normal(avg_residents, avg_residents * 0.1)))
            count = min(count, capacity * 5)  # Hard cap: 5 residents per unit

        total += count
        resident_entries.append(
            BuildingResidents(
                session_id=session_id,
                building_id=building.id,
                residents=count,
            )
        )

    db.add_all(resident_entries)
    await db.flush()

    return {"total_residents": total, "buildings_assigned": len(buildings)}


async def run_simulation_tick(session_id: str, db: AsyncSession) -> dict:
    """
    Advance the simulation by one year.

    Returns a dict with:
      - year: new current year
      - total_residents, total_births, total_deaths
      - resident_map: {building_id: count}
      - move_log: [{from_id, to_id, count}]
    """
    # Load current resident state
    result = await db.execute(
        select(BuildingResidents)
        .where(BuildingResidents.session_id == session_id)
    )
    entries = result.scalars().all()

    if not entries:
        return {}

    building_ids = [e.building_id for e in entries]
    counts = np.array([e.residents for e in entries], dtype=float)

    # ── Births ──────────────────────────────────────────────
    births_per_building = np.random.poisson(counts * BIRTH_RATE)
    total_births = int(births_per_building.sum())

    # ── Deaths ──────────────────────────────────────────────
    deaths_per_building = np.random.poisson(counts * DEATH_RATE)
    total_deaths = int(deaths_per_building.sum())

    # ── Inter-flat moves ────────────────────────────────────
    movers = np.random.poisson(counts * MOVE_RATE).astype(int)
    movers = np.minimum(movers, counts.astype(int))  # Can't move more than exist

    move_log = []
    total_movers = int(movers.sum())
    if total_movers > 0:
        # Sample destination buildings (weighted by available capacity)
        n = len(building_ids)
        dest_indices = np.random.randint(0, n, size=total_movers)

        from_counts = np.zeros(n, dtype=int)
        to_counts = np.zeros(n, dtype=int)

        offset = 0
        for i, num_moving in enumerate(movers):
            if num_moving == 0:
                continue
            dests = dest_indices[offset:offset + num_moving]
            for d in dests:
                if d != i:
                    from_counts[i] += 1
                    to_counts[d] += 1
            offset += num_moving

        # Build move log (aggregate per from→to pair, sampled)
        for i in range(n):
            if from_counts[i] > 0:
                move_log.append({
                    "from_id": building_ids[i],
                    "to_id": building_ids[int(np.random.randint(0, n))],
                    "count": int(from_counts[i]),
                })

        counts -= from_counts
        counts += to_counts

    # ── Apply births / deaths ───────────────────────────────
    counts = counts + births_per_building - deaths_per_building
    counts = np.maximum(counts, 0).astype(int)

    total_residents = int(counts.sum())

    # ── Persist updated counts ──────────────────────────────
    for entry, new_count in zip(entries, counts):
        entry.residents = int(new_count)
    await db.flush()

    resident_map = {bid: int(c) for bid, c in zip(building_ids, counts)}

    return {
        "total_residents": total_residents,
        "total_births": total_births,
        "total_deaths": total_deaths,
        "resident_map": resident_map,
        "move_log": move_log[:100],  # Cap log at 100 entries per year
    }
