from fastapi import APIRouter
from pydantic import BaseModel

from ..storage import get_storage

router = APIRouter(prefix="/api/admin", tags=["admin"])


class ActionLogEntry(BaseModel):
    message: str
    zone_id: str | None = None


@router.get("/overview")
def overview():
    storage = get_storage()
    zones = storage.list_zones()
    counts = {"Low": 0, "Medium": 0, "High": 0}
    zone_summaries = []
    total_subscribers = 0

    for z in zones:
        state = storage.get_risk_state(z["zone_id"]) or {"level": "Low", "probability": 0}
        counts[state["level"]] = counts.get(state["level"], 0) + 1
        subs = len(storage.get_phones_for_zone(z["zone_id"]))
        total_subscribers += subs
        zone_summaries.append({
            "zone_id": z["zone_id"],
            "name": z["name"],
            "city": z["city"],
            "risk": state,
            "subscribers": subs,
        })

    reports = storage.list_reports()
    pending_reports = [r for r in reports if r.get("status") == "pending"]

    return {
        "risk_counts": counts,
        "total_zones": len(zones),
        "total_subscribers": total_subscribers,
        "total_reports": len(reports),
        "pending_reports": len(pending_reports),
        "zones": zone_summaries,
    }


@router.get("/actions")
def list_actions():
    storage = get_storage()
    return storage.list_action_log()


@router.post("/actions")
def add_action(entry: ActionLogEntry):
    storage = get_storage()
    return storage.add_action_log({"actor": "admin", "message": entry.message, "zone_id": entry.zone_id})
