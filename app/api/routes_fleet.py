"""Fleet API Routes."""

from fastapi import APIRouter, HTTPException
from typing import List
from app.schemas.fleet import Satellite, FleetSummaryItem, SatelliteBase
from app.repositories.fleet_repo import FleetRepository

router = APIRouter(prefix="/api/fleet", tags=["Fleet"])


@router.get("", response_model=List[FleetSummaryItem])
def get_fleet_summary():
    """Returns high-level status, risk scores, and active incident counts for all fleet spacecraft."""
    return FleetRepository.get_fleet_summary()


@router.get("/{satellite_id}", response_model=Satellite)
def get_satellite(satellite_id: str):
    sat = FleetRepository.get_satellite_by_id(satellite_id)
    if not sat:
        raise HTTPException(status_code=404, detail="Satellite not found")
    return sat


@router.post("", response_model=Satellite)
def create_satellite(payload: SatelliteBase):
    sat = FleetRepository.create_satellite(
        name=payload.name,
        mode=payload.mode,
        status=payload.status,
        risk_score=payload.risk_score
    )
    sat["subsystems"] = []
    return sat
