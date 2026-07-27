import requests
import time
import os

GROUP_ID = "289573924"
API_KEY = os.environ["ROBLOX_API_KEY"]
WEBHOOK_URL = os.environ["DISCORD_WEBHOOK"]
DEV_USER_IDS = {"2861521893", "940951115"}

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


def get_username(user_id):
    if user_id in username_cache:
        return username_cache[user_id]
    try:
        r = requests.get(f"https://users.roblox.com/v1/users/{user_id}", timeout=10)
        if r.status_code == 200:
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


def fetch_entries():
    headers = {"x-api-key": API_KEY}
    params = {"maxPageSize": 50}
    try:
        r = requests.get(AUDIT_URL, headers=headers, params=params, timeout=15)
        if r.status_code == 200:
            return r.json().get("auditLogEntries", [])
    except Exception:
        pass
    return []


def extract_user_id(actor):
    user = actor.get("user", {})
    raw = user.get("id", "") or user.get("userId", "")
    return str(raw).replace("users/", "")


for entry in fetch_entries():
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
