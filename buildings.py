"""
Buildings API — serves HDB block data as GeoJSON for deck.gl.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.models import Building

router = APIRouter()


@router.get("")
async def get_all_buildings(db: AsyncSession = Depends(get_db)):
    """
    Returns all HDB buildings as a GeoJSON FeatureCollection.
    Used by the deck.gl ScenegraphLayer / GeoJsonLayer on the frontend.
    """
    result = await db.execute(select(Building))
    buildings = result.scalars().all()

    features = [
        {
            "type": "Feature",
            "id": b.id,
            "geometry": {
                "type": "Point",
                "coordinates": [b.longitude, b.latitude],
            },
            "properties": {
                "id": b.id,
                "address": b.address,
                "blk_no": b.blk_no,
                "street": b.street,
                "dwelling_units": b.dwelling_units,
                "cityjson_id": b.cityjson_id,
            },
        }
        for b in buildings
    ]

    return {"type": "FeatureCollection", "features": features}


@router.get("/{building_id}")
async def get_building(building_id: str, db: AsyncSession = Depends(get_db)):
    """
    Returns full detail for a single building — used by the info side panel.
    """
    result = await db.execute(
        select(Building).where(Building.id == building_id)
    )
    building = result.scalar_one_or_none()

    if not building:
        raise HTTPException(status_code=404, detail="Building not found")

    return {
        "id": building.id,
        "address": building.address,
        "blk_no": building.blk_no,
        "street": building.street,
        "latitude": building.latitude,
        "longitude": building.longitude,
        "dwelling_units": building.dwelling_units,
        "units": {
            "1_room": building.room_1,
            "2_room": building.room_2,
            "3_room": building.room_3,
            "4_room": building.room_4,
            "5_room": building.room_5,
        },
    }