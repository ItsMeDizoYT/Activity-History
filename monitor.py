import requests
import os
import json
from datetime import datetime, timezone, timedelta

PLACE_ID = "104113832581752"
API_KEY = os.environ["ROBLOX_API_KEY"].strip()
WEBHOOK_URL = os.environ["DISCORD_WEBHOOK"]
STATE_FILE = "state.json"

headers = {"x-api-key": API_KEY}

def get_username(user_id):
    try:
        r = requests.get(f"https://users.roblox.com/v1/users/{user_id}", timeout=10)
        if r.status_code == 200:
            return r.json().get("name", str(user_id))
    except Exception:
        pass
    return str(user_id)

def send_webhook(message):
    try:
        requests.post(WEBHOOK_URL, json={"content": message}, timeout=10)
    except Exception:
        pass

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"tc_members": []}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

state = load_state()

# Team Create session members
try:
    r = requests.get(
        f"https://apis.roblox.com/legacy-develop/v1/places/{PLACE_ID}/teamcreate/active_session/members",
        headers=headers,
        timeout=15
    )
    print(f"[TC] {r.status_code} {r.text[:300]}")
    if r.status_code == 200:
        data = r.json()
        members = data.get("data", []) if isinstance(data, dict) else data
        current_ids = set(str(m.get("userId") or m.get("id", "")) for m in members)
        previous_ids = set(state.get("tc_members", []))

        for uid in current_ids - previous_ids:
            send_webhook(f"**{get_username(uid)}** joined Studio")
        for uid in previous_ids - current_ids:
            send_webhook(f"**{get_username(uid)}** left Studio")

        state["tc_members"] = list(current_ids)
except Exception as e:
    print(f"[TC ERROR] {e}")

# Place version history
cutoff = datetime.now(timezone.utc) - timedelta(minutes=6)
try:
    r = requests.get(
        f"https://apis.roblox.com/place-version-history-api/v1/{PLACE_ID}/history",
        headers=headers,
        params={"limit": 10},
        timeout=15
    )
    print(f"[VH] {r.status_code} {r.text[:500]}")
    if r.status_code == 200:
        data = r.json()
        versions = data.get("versions") or data.get("data") or []
        for v in versions:
            created = v.get("createdAt") or v.get("createTime") or v.get("Created", "")
            try:
                vtime = datetime.fromisoformat(created.replace("Z", "+00:00"))
            except Exception:
                continue
            if vtime < cutoff:
                continue
            version_num = v.get("versionNumber") or v.get("version") or "?"
            creator = v.get("creatorName") or v.get("creator", {}).get("name") or "Unknown"
            send_webhook(f"**{creator}** saved place — version **{version_num}**")
except Exception as e:
    print(f"[VH ERROR] {e}")

save_state(state)
