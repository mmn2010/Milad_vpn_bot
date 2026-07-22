import httpx
import random
import string
import ssl
from datetime import datetime, timedelta
from config import PANEL_URL, PANEL_TOKEN

def generate_random_username(length=8):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

async def create_user_in_panel(is_test: bool = False, volume_bytes: int = None, days: int = None) -> dict:
    username = generate_random_username()
    if is_test:
        data_limit = 104857600
        expire_date = (datetime.now() + timedelta(hours=24)).strftime("%Y-%m-%dT%H:%M:%S+03:30")
        note = "Free Test - Telegram Bot"
    else:
        data_limit = volume_bytes if volume_bytes else 1073741824
        days = days if days else 30
        expire_date = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%S+03:30")
        note = "Created by Telegram Bot"
    payload = {
        "username": username,
        "status": "active",
        "data_limit": data_limit,
        "hwid_limit": None,
        "expire": expire_date,
        "note": note,
        "group_ids": [4],
        "proxy_settings": {"shadowsocks": {"method": "chacha20-ietf-poly1305"}},
        "next_plan": None
    }
    headers = {"Authorization": f"Bearer {PANEL_TOKEN}", "Content-Type": "application/json"}
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    try:
        async with httpx.AsyncClient(verify=ssl_context) as client:
            response = await client.post(PANEL_URL, json=payload, headers=headers)
            if response.status_code == 200 or response.status_code == 201:
                return {"success": True, "username": username, "data": response.json()}
            else:
                return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

async def get_user_info_from_panel(vpn_username: str) -> dict:
    url = f"{PANEL_URL}/{vpn_username}"
    headers = {"Authorization": f"Bearer {PANEL_TOKEN}"}
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    try:
        async with httpx.AsyncClient(verify=ssl_context) as client:
            response = await client.get(url, headers=headers)
            if response.status_code == 200:
                return {"success": True, "data": response.json()}
            else:
                return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}
    except Exception as e:
        return {"success": False, "error": str(e)}
