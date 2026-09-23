from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..storage import get_storage
from ..services.risk_engine import evaluate_zone, evaluate_all_zones

router = APIRouter(prefix="/api", tags=["predict"])


class SimulateConditions(BaseModel):
    rainfall_mm_hr: float | None = Field(None, ge=0, le=500)
    river_level_m: float | None = Field(None, ge=0, le=30)
    river_rise_rate_m_hr: float | None = Field(None, ge=-5, le=10)
    active_drain_count: int | None = Field(None, ge=0)


@router.post("/predict/all")
def predict_all():
    storage = get_storage()
    return evaluate_all_zones(storage)


@router.post("/predict/{zone_id}")
def predict_zone(zone_id: str):
    storage = get_storage()
    try:
        return evaluate_zone(storage, zone_id)
    except ValueError as exc:
        raise HTTPException(404, str(exc))


@router.post("/simulate/{zone_id}")
def simulate_zone(zone_id: str, body: SimulateConditions):
    """Demo/testing endpoint: override a zone's live conditions (e.g. spike
    rainfall + river level) and immediately recompute its risk, so judges can
    watch a zone go High and trigger the SMS pipeline live."""
    storage = get_storage()
    zone = storage.get_zone(zone_id)
    if not zone:
        raise HTTPException(404, "Zone not found")

    patch = {k: v for k, v in body.model_dump().items() if v is not None}
    if patch:
        storage.update_conditions(zone_id, patch)

    return evaluate_zone(storage, zone_id)
