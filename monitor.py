import requests
import os
from datetime import datetime, timezone, timedelta

GROUP_ID = "289573924"
API_KEY = os.environ["ROBLOX_API_KEY"]
WEBHOOK_URL = os.environ["DISCORD_WEBHOOK"]
DEV_USER_IDS = {"2861521893", "940951115", "744477563"}

AUDIT_URL = f"https://apis.roblox.com/cloud/v2/groups/{GROUP_ID}/audit-log-entries"

ACTION_LABELS = {
    "SavePlace": "saved a place",
    "PublishPlace": "published a place",
    "CreatePlace": "created a new place",
    "DeletePlace": "deleted a place",
    "ConfigureGame": "changed game settings",
    "CreateAsset": "uploaded an asset",
    "CreateItems": "created items",
}

username_cache = {}
cutoff = datetime.now(timezone.utc) - timedelta(minutes=6)


def get_username(user_id):
    if user_id in username_cache:
        return username_cache[user_id]
    try:
        r = requests.get(f"https://users.roblox.com/v1/users/{user_id}", timeout=10)
        if r.status_code == 200:
        print(f"[DEBUG] Status: {r.status_code}")
        entries = r.json().get("auditLogEntries", [])
        print(f"[DEBUG] Entry count: {len(entries)}")
        for entry in entries:
            print(f"[DEBUG] action={entry.get('action')} time={entry.get('createTime')} actor={entry.get('actor')}")
            name = r.json().get("name", user_id)
            username_cache[user_id] = name
            return name
    except Exception:
        pass
    return str(user_id)


def send_webhook(message):
    try:
        requests.post(WEBHOOK_URL, json={"content": message}, timeout=10)
    except Exception:
        pass


def extract_user_id(actor):
    user = actor.get("user", {})
    raw = user.get("id", "") or user.get("userId", "")
    return str(raw).replace("users/", "")


headers = {"x-api-key": API_KEY}
params = {"maxPageSize": 50}

try:
    r = requests.get(AUDIT_URL, headers=headers, params=params, timeout=15)
    if r.status_code == 200:
        for entry in r.json().get("auditLogEntries", []):
            create_time = entry.get("createTime", "")
            try:
                entry_time = datetime.fromisoformat(create_time.replace("Z", "+00:00"))
            except Exception:
                continue

            if entry_time < cutoff:
                continue

            user_id = extract_user_id(entry.get("actor", {}))
            if user_id not in DEV_USER_IDS:
                continue

            action = entry.get("action", "")
            label = ACTION_LABELS.get(action)
            if not label:
                continue

            username = get_username(user_id)
            details = entry.get("details", {})
            place_name = details.get("placeName") or details.get("targetName") or ""
            place_part = f" — **{place_name}**" if place_name else ""

            send_webhook(f"**{username}** {label}{place_part}")
except Exception as e:
    print(f"[ERROR] {e}")
    raise
