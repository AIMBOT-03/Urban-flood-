import re
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator

from ..storage import get_storage
from ..services import sms

router = APIRouter(prefix="/api/alerts", tags=["alerts"])

PHONE_RE = re.compile(r"^[6-9]\d{9}$")  # Indian 10-digit mobile numbers


class SubscribeRequest(BaseModel):
    phone: str
    zone_id: str

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        digits = re.sub(r"\D", "", v)[-10:]
        if not PHONE_RE.match(digits):
            raise ValueError("Enter a valid 10-digit Indian mobile number")
        return digits


class SendAlertRequest(BaseModel):
    message: str


@router.post("/subscribe")
def subscribe(body: SubscribeRequest):
    storage = get_storage()
    zone = storage.get_zone(body.zone_id)
    if not zone:
        raise HTTPException(404, "Zone not found")
    entry = storage.register_phone(body.phone, body.zone_id)
    return {"status": "subscribed", "zone": zone["name"], **entry}


@router.get("/zone/{zone_id}")
def zone_subscriber_count(zone_id: str):
    storage = get_storage()
    numbers = storage.get_phones_for_zone(zone_id)
    return {"zone_id": zone_id, "subscriber_count": len(numbers)}


@router.post("/send/{zone_id}")
def send_manual_alert(zone_id: str, body: SendAlertRequest):
    storage = get_storage()
    zone = storage.get_zone(zone_id)
    if not zone:
        raise HTTPException(404, "Zone not found")
    numbers = storage.get_phones_for_zone(zone_id)
    result = sms.send_sms(numbers, body.message)
    storage.add_action_log({
        "actor": "admin",
        "message": f"Manual alert sent to {zone['name']} ({zone['city']}): \"{body.message}\" "
                   f"-> {len(numbers)} recipient(s).",
        "zone_id": zone_id,
    })
    return {"recipients": len(numbers), **result}


@router.get("/mock-log")
def mock_log():
    return sms.get_mock_log()
