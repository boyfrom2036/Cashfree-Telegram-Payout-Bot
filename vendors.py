"""
vendors.py — Local JSON storage for frequent vendors.
Saves to vendors.json in the same folder as the bot.
"""
import json
import os
from datetime import datetime

VENDORS_FILE = os.path.join(os.path.dirname(__file__), "vendors.json")


def _load() -> dict:
    if not os.path.exists(VENDORS_FILE):
        return {}
    with open(VENDORS_FILE, "r") as f:
        return json.load(f)


def _save(data: dict):
    with open(VENDORS_FILE, "w") as f:
        json.dump(data, f, indent=2)


def save_vendor(name: str, bank_account: str, ifsc: str):
    """Save or update a vendor. Increments pay_count each time they're paid."""
    data = _load()
    key = f"{bank_account}_{ifsc}"
    if key in data:
        data[key]["pay_count"] += 1
        data[key]["last_paid"] = datetime.now().isoformat()
    else:
        data[key] = {
            "name": name,
            "bank_account": bank_account,
            "ifsc": ifsc,
            "pay_count": 1,
            "last_paid": datetime.now().isoformat()
        }
    _save(data)


def get_frequent_vendors(limit: int = 5) -> list[dict]:
    """Return top vendors sorted by pay_count descending."""
    data = _load()
    vendors = list(data.values())
    vendors.sort(key=lambda x: x["pay_count"], reverse=True)
    return vendors[:limit]


def get_all_vendors() -> list[dict]:
    data = _load()
    return list(data.values())