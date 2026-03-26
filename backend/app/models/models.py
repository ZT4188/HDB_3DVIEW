"""
ORM Models for HDB 3D Simulation
"""

from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Float, DateTime, ForeignKey,
    JSON, Enum as SAEnum
)
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class SimStatus(str, enum.Enum):
    idle = "idle"
    running = "running"
    paused = "paused"
    completed = "completed"


class Building(Base):
    """HDB building block with unit counts and geometry."""
    __tablename__ = "buildings"

    id = Column(String, primary_key=True)          # e.g. "BLK123A_STREETNAME"
    blk_no = Column(String, nullable=False)
    street = Column(String, nullable=False)
    address = Column(String, nullable=False)
    dwelling_units = Column(Integer, default=0)
    room_1 = Column(Integer, default=0)
    room_2 = Column(Integer, default=0)
    room_3 = Column(Integer, default=0)
    room_4 = Column(Integer, default=0)
    room_5 = Column(Integer, default=0)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    # CityJSON feature id for 3D model lookup
    cityjson_id = Column(String, nullable=True)

    residents = relationship("BuildingResidents", back_populates="building")


class SimSession(Base):
    """A named simulation session."""
    __tablename__ = "sim_sessions"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    status = Column(SAEnum(SimStatus), default=SimStatus.idle)
    current_year = Column(Integer, default=2025)
    years_simulated = Column(Integer, default=0)
    total_residents = Column(Integer, default=0)
    total_deaths = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    residents = relationship("BuildingResidents", back_populates="session")
    snapshots = relationship("YearlySnapshot", back_populates="session")


class BuildingResidents(Base):
    """Resident count per building per session (current state)."""
    __tablename__ = "building_residents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, ForeignKey("sim_sessions.id"), nullable=False)
    building_id = Column(String, ForeignKey("buildings.id"), nullable=False)
    residents = Column(Integer, default=0)

    session = relationship("SimSession", back_populates="residents")
    building = relationship("Building", back_populates="residents")


class YearlySnapshot(Base):
    """Full resident state snapshot stored after each simulated year."""
    __tablename__ = "yearly_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, ForeignKey("sim_sessions.id"), nullable=False)
    year = Column(Integer, nullable=False)
    total_residents = Column(Integer, default=0)
    total_deaths = Column(Integer, default=0)
    total_births = Column(Integer, default=0)
    # {building_id: resident_count, ...}
    resident_map = Column(JSON, nullable=False)
    # [{from_id, to_id, count}, ...]
    move_log = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("SimSession", back_populates="snapshots")
