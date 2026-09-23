import os
import uuid
from fastapi import APIRouter, HTTPException, UploadFile, File, Form

from ..storage import get_storage

router = APIRouter(prefix="/api/reports", tags=["reports"])

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
REPORT_TYPES = {"blocked_drain", "waterlogging", "other"}


@router.post("")
async def create_report(
    zone_id: str = Form(...),
    description: str = Form(...),
    report_type: str = Form("other"),
    lat: float | None = Form(None),
    lon: float | None = Form(None),
    photo: UploadFile | None = File(None),
):
    storage = get_storage()
    zone = storage.get_zone(zone_id)
    if not zone:
        raise HTTPException(404, "Zone not found")
    if report_type not in REPORT_TYPES:
        report_type = "other"

    photo_url = None
    if photo is not None:
        if photo.content_type not in ALLOWED_IMAGE_TYPES:
            raise HTTPException(400, "Photo must be JPEG, PNG, or WEBP")
        ext = os.path.splitext(photo.filename or "")[1] or ".jpg"
        filename = f"{uuid.uuid4()}{ext}"
        contents = await photo.read()
        if len(contents) > 8 * 1024 * 1024:
            raise HTTPException(400, "Photo too large (max 8MB)")
        with open(os.path.join(UPLOAD_DIR, filename), "wb") as f:
            f.write(contents)
        photo_url = f"/uploads/{filename}"

    report = storage.add_report({
        "zone_id": zone_id,
        "description": description,
        "report_type": report_type,
        "lat": lat,
        "lon": lon,
        "photo_url": photo_url,
    })

    conditions = storage.get_conditions(zone_id) or {}
    patch = {"citizen_report_count": conditions.get("citizen_report_count", 0) + 1}
    if report_type == "blocked_drain":
        patch["active_drain_count"] = conditions.get("active_drain_count", 0) + 1
    storage.update_conditions(zone_id, patch)

    return report


@router.get("")
def list_reports(zone_id: str | None = None):
    storage = get_storage()
    reports = storage.list_reports(zone_id)
    severity_rank = {"blocked_drain": 2, "waterlogging": 1, "other": 0}
    return sorted(reports, key=lambda r: severity_rank.get(r["report_type"], 0), reverse=True)


@router.patch("/{report_id}")
def update_report(report_id: str, status: str = Form(...)):
    storage = get_storage()
    updated = storage.update_report(report_id, {"status": status})
    if not updated:
        raise HTTPException(404, "Report not found")
    return updated
