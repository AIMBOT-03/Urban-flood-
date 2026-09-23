from ..ml.predict import predict_risk
from ..ml.train_model import FEATURES
from . import sms

RISK_RANK = {"Low": 0, "Medium": 1, "High": 2}


def build_feature_vector(zone: dict, conditions: dict) -> dict:
    merged = {
        "rainfall_mm_hr": conditions["rainfall_mm_hr"],
        "river_level_m": conditions["river_level_m"],
        "river_rise_rate_m_hr": conditions["river_rise_rate_m_hr"],
        "elevation_m": zone["elevation_m"],
        "slope_deg": zone["slope_deg"],
        "distance_to_river_km": zone["distance_to_river_km"],
        "drainage_density": zone["drainage_density"],
        "active_drain_count": conditions["active_drain_count"],
        "citizen_report_count": conditions["citizen_report_count"],
    }
    return {f: merged[f] for f in FEATURES}


def evaluate_zone(storage, zone_id: str, notify_on_escalation: bool = True) -> dict:
    zone = storage.get_zone(zone_id)
    conditions = storage.get_conditions(zone_id)
    if not zone or not conditions:
        raise ValueError(f"Unknown zone_id: {zone_id}")

    previous_state = storage.get_risk_state(zone_id) or {"level": "Low"}
    features = build_feature_vector(zone, conditions)
    result = predict_risk(features)
    result["features"] = features
    storage.set_risk_state(zone_id, {k: v for k, v in result.items() if k != "features"})

    escalated_to_high = (
        notify_on_escalation
        and result["level"] == "High"
        and previous_state.get("level") != "High"
    )

    alert_sent = None
    if escalated_to_high:
        numbers = storage.get_phones_for_zone(zone_id)
        message = (
            f"AquaAlert Odisha: HIGH flood risk predicted for {zone['name']}, {zone['city']} "
            f"in the next 0-6 hours. Please move to higher ground and avoid low-lying areas."
        )
        sms_result = sms.send_sms(numbers, message)
        alert_sent = {"recipients": len(numbers), **sms_result}
        if sms_result.get("sent"):
            log_message = (
                f"Auto-alert: {zone['name']} ({zone['city']}) escalated to HIGH risk. "
                f"SMS sent to {len(numbers)} registered number(s)."
            )
        else:
            log_message = (
                f"Auto-alert: {zone['name']} ({zone['city']}) escalated to HIGH risk, but SMS "
                f"FAILED to send to {len(numbers)} registered number(s): {sms_result.get('error')}"
            )
        storage.add_action_log({"actor": "system", "message": log_message, "zone_id": zone_id})

    return {
        "zone_id": zone_id,
        "risk": result,
        "escalated_to_high": bool(escalated_to_high),
        "alert_sent": alert_sent,
    }


def evaluate_all_zones(storage) -> list[dict]:
    return [evaluate_zone(storage, z["zone_id"]) for z in storage.list_zones()]
