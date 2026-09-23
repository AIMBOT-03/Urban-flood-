import math
from fastapi import APIRouter, HTTPException, Query

from ..storage import get_storage

router = APIRouter(prefix="/api/zones", tags=["zones"])


def _haversine_km(lat1, lon1, lat2, lon2):
    R = 6371
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def _zone_with_state(storage, zone):
    state = storage.get_risk_state(zone["zone_id"]) or {"level": "Low", "probability": 0}
    conditions = storage.get_conditions(zone["zone_id"]) or {}
    return {**zone, "risk": state, "conditions": conditions}


@router.get("")
def list_zones():
    storage = get_storage()
    return [_zone_with_state(storage, z) for z in storage.list_zones()]


@router.get("/nearest")
def nearest_zone(lat: float = Query(...), lon: float = Query(...)):
    storage = get_storage()
    zones = storage.list_zones()
    if not zones:
        raise HTTPException(404, "No zones configured")
    best = min(zones, key=lambda z: _haversine_km(lat, lon, z["lat"], z["lon"]))
    distance_km = _haversine_km(lat, lon, best["lat"], best["lon"])
    return {**_zone_with_state(storage, best), "distance_km": round(distance_km, 2)}


@router.get("/{zone_id}")
def get_zone(zone_id: str):
    storage = get_storage()
    zone = storage.get_zone(zone_id)
    if not zone:
        raise HTTPException(404, "Zone not found")
    return _zone_with_state(storage, zone)
