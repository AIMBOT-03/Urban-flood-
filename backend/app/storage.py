"""
Storage abstraction with two backends:
  - MongoDB (used when MONGODB_URI is set and reachable)
  - in-memory (automatic fallback so the app still runs end-to-end on a
    laptop/judging setup with no database configured)

Every route module goes through `get_storage()` instead of touching pymongo
or dicts directly, so the rest of the app doesn't care which backend is live.
"""
import os
import json
import time
import uuid
from datetime import datetime, timezone

ZONES_JSON_PATH = os.path.join(os.path.dirname(__file__), "data", "zones.json")

BASELINE_CONDITIONS = {
    "rainfall_mm_hr": 0.5,
    "river_level_m": 1.8,
    "river_rise_rate_m_hr": 0.0,
    "active_drain_count": 0,
    "citizen_report_count": 0,
}


def _now():
    return datetime.now(timezone.utc).isoformat()


def _load_zone_defs():
    with open(ZONES_JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


class BaseStorage:
    mode = "base"

    def list_zones(self):
        raise NotImplementedError

    def get_zone(self, zone_id):
        raise NotImplementedError

    def get_conditions(self, zone_id):
        raise NotImplementedError

    def update_conditions(self, zone_id, patch):
        raise NotImplementedError

    def set_risk_state(self, zone_id, risk_result):
        raise NotImplementedError

    def register_phone(self, phone, zone_id):
        raise NotImplementedError

    def get_phones_for_zone(self, zone_id):
        raise NotImplementedError

    def add_report(self, report):
        raise NotImplementedError

    def list_reports(self, zone_id=None):
        raise NotImplementedError

    def update_report(self, report_id, patch):
        raise NotImplementedError

    def add_action_log(self, entry):
        raise NotImplementedError

    def list_action_log(self):
        raise NotImplementedError


class MemoryStorage(BaseStorage):
    mode = "memory"

    def __init__(self):
        zone_defs = _load_zone_defs()
        self.zones = {z["zone_id"]: {**z} for z in zone_defs}
        self.conditions = {
            zid: {**BASELINE_CONDITIONS, "zone_id": zid, "updated_at": _now()}
            for zid in self.zones
        }
        self.risk_state = {
            zid: {"level": "Low", "probability": 0.1, "source": "init", "updated_at": _now()}
            for zid in self.zones
        }
        self.phones = []  # list of {phone, zone_id, registered_at}
        self.reports = []  # list of report dicts
        self.action_log = []  # list of {message, actor, created_at}

    def list_zones(self):
        return list(self.zones.values())

    def get_zone(self, zone_id):
        return self.zones.get(zone_id)

    def get_conditions(self, zone_id):
        return self.conditions.get(zone_id)

    def update_conditions(self, zone_id, patch):
        if zone_id not in self.conditions:
            return None
        self.conditions[zone_id].update(patch)
        self.conditions[zone_id]["updated_at"] = _now()
        return self.conditions[zone_id]

    def set_risk_state(self, zone_id, risk_result):
        self.risk_state[zone_id] = {**risk_result, "updated_at": _now()}
        return self.risk_state[zone_id]

    def get_risk_state(self, zone_id):
        return self.risk_state.get(zone_id)

    def register_phone(self, phone, zone_id):
        existing = next((p for p in self.phones if p["phone"] == phone and p["zone_id"] == zone_id), None)
        if existing:
            return existing
        entry = {"phone": phone, "zone_id": zone_id, "registered_at": _now()}
        self.phones.append(entry)
        return entry

    def get_phones_for_zone(self, zone_id):
        return [p["phone"] for p in self.phones if p["zone_id"] == zone_id]

    def add_report(self, report):
        report = {**report, "report_id": str(uuid.uuid4()), "created_at": _now(), "status": "pending"}
        self.reports.append(report)
        return report

    def list_reports(self, zone_id=None):
        if zone_id:
            return [r for r in self.reports if r["zone_id"] == zone_id]
        return list(self.reports)

    def update_report(self, report_id, patch):
        for r in self.reports:
            if r["report_id"] == report_id:
                r.update(patch)
                return r
        return None

    def add_action_log(self, entry):
        entry = {**entry, "action_id": str(uuid.uuid4()), "created_at": _now()}
        self.action_log.append(entry)
        return entry

    def list_action_log(self):
        return list(reversed(self.action_log))


class MongoStorage(BaseStorage):
    mode = "mongo"

    def __init__(self, client, db_name="aquaalert"):
        self.client = client
        self.db = client[db_name]
        self._seed_zones_if_empty()

    def _seed_zones_if_empty(self):
        if self.db.zones.count_documents({}) == 0:
            zone_defs = _load_zone_defs()
            self.db.zones.insert_many([{**z, "_id": z["zone_id"]} for z in zone_defs])
            self.db.conditions.insert_many([
                {"_id": z["zone_id"], "zone_id": z["zone_id"], **BASELINE_CONDITIONS, "updated_at": _now()}
                for z in zone_defs
            ])
            self.db.risk_state.insert_many([
                {"_id": z["zone_id"], "zone_id": z["zone_id"], "level": "Low", "probability": 0.1,
                 "source": "init", "updated_at": _now()}
                for z in zone_defs
            ])

    def list_zones(self):
        return [{k: v for k, v in z.items() if k != "_id"} for z in self.db.zones.find({})]

    def get_zone(self, zone_id):
        z = self.db.zones.find_one({"_id": zone_id})
        if not z:
            return None
        z.pop("_id", None)
        return z

    def get_conditions(self, zone_id):
        c = self.db.conditions.find_one({"_id": zone_id})
        if not c:
            return None
        c.pop("_id", None)
        return c

    def update_conditions(self, zone_id, patch):
        patch = {**patch, "updated_at": _now()}
        self.db.conditions.update_one({"_id": zone_id}, {"$set": patch}, upsert=True)
        return self.get_conditions(zone_id)

    def set_risk_state(self, zone_id, risk_result):
        doc = {**risk_result, "zone_id": zone_id, "updated_at": _now()}
        self.db.risk_state.update_one({"_id": zone_id}, {"$set": doc}, upsert=True)
        return doc

    def get_risk_state(self, zone_id):
        r = self.db.risk_state.find_one({"_id": zone_id})
        if not r:
            return None
        r.pop("_id", None)
        return r

    def register_phone(self, phone, zone_id):
        existing = self.db.phones.find_one({"phone": phone, "zone_id": zone_id})
        if existing:
            existing.pop("_id", None)
            return existing
        entry = {"phone": phone, "zone_id": zone_id, "registered_at": _now()}
        self.db.phones.insert_one({**entry})
        return entry

    def get_phones_for_zone(self, zone_id):
        return [p["phone"] for p in self.db.phones.find({"zone_id": zone_id})]

    def add_report(self, report):
        report = {**report, "report_id": str(uuid.uuid4()), "created_at": _now(), "status": "pending"}
        self.db.reports.insert_one({**report})
        return report

    def list_reports(self, zone_id=None):
        query = {"zone_id": zone_id} if zone_id else {}
        return [{k: v for k, v in r.items() if k != "_id"} for r in self.db.reports.find(query)]

    def update_report(self, report_id, patch):
        self.db.reports.update_one({"report_id": report_id}, {"$set": patch})
        r = self.db.reports.find_one({"report_id": report_id})
        if r:
            r.pop("_id", None)
        return r

    def add_action_log(self, entry):
        entry = {**entry, "action_id": str(uuid.uuid4()), "created_at": _now()}
        self.db.action_log.insert_one({**entry})
        return entry

    def list_action_log(self):
        docs = list(self.db.action_log.find({}).sort("created_at", -1))
        for d in docs:
            d.pop("_id", None)
        return docs


_storage_instance = None


def get_storage():
    global _storage_instance
    if _storage_instance is not None:
        return _storage_instance

    mongo_uri = os.getenv("MONGODB_URI", "").strip()
    if mongo_uri:
        try:
            from pymongo import MongoClient
            client = MongoClient(mongo_uri, serverSelectionTimeoutMS=2000)
            client.admin.command("ping")
            _storage_instance = MongoStorage(client, os.getenv("MONGODB_DB", "aquaalert"))
            print("[storage] Connected to MongoDB.")
            return _storage_instance
        except Exception as exc:
            print(f"[storage] MongoDB unavailable ({exc}); falling back to in-memory storage.")

    _storage_instance = MemoryStorage()
    print("[storage] Using in-memory storage (no MONGODB_URI set or Mongo unreachable).")
    return _storage_instance
