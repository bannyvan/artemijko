import hashlib
import hmac
import json
import time
from urllib.parse import urlencode
from app.config import settings


def make_init_data(user_id: int) -> str:
    user = json.dumps({"id": user_id, "first_name": "Test"}, separators=(",", ":"))
    payload = {
        "auth_date": str(int(time.time())),
        "query_id": "AAE",
        "user": user,
    }
    data_check_string = "\n".join(f"{k}={payload[k]}" for k in sorted(payload.keys()))
    secret = hashlib.sha256(settings.bot_token.encode()).digest()
    hash_ = hmac.new(secret, data_check_string.encode(), hashlib.sha256).hexdigest()
    payload["hash"] = hash_
    return urlencode(payload)


def test_auth_telegram_success(client):
    init_data = make_init_data(9999)
    r = client.post("/auth/telegram", params={"initData": init_data})
    assert r.status_code == 200
    assert "access_token" in r.json()


def test_auth_telegram_invalid(client):
    r = client.post("/auth/telegram", params={"initData": "bad=data&hash=0"})
    assert r.status_code == 401