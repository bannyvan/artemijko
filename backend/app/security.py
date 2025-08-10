import hmac
import hashlib
import urllib.parse
from datetime import datetime, timedelta
from typing import Optional
import jwt

from app.config import settings


def validate_telegram_init_data(init_data_raw: str) -> dict:
    parsed = urllib.parse.parse_qs(init_data_raw, keep_blank_values=True)
    data_check_string_parts = []
    received_hash = parsed.get("hash", [""])[0]
    for key in sorted(k for k in parsed.keys() if k != "hash"):
        value = parsed[key][0]
        data_check_string_parts.append(f"{key}={value}")
    data_check_string = "\n".join(data_check_string_parts)

    secret_key = hashlib.sha256(settings.bot_token.encode()).digest()
    computed_hash = hmac.new(secret_key, msg=data_check_string.encode(), digestmod=hashlib.sha256).hexdigest()

    if not hmac.compare_digest(computed_hash, received_hash):
        raise ValueError("Invalid initData hash")

    # Parse user JSON field if present
    user_json = parsed.get("user", [None])[0]
    if user_json:
        import json
        user = json.loads(user_json)
    else:
        user = {}

    return {
        "user": user,
        "auth_date": parsed.get("auth_date", [None])[0],
        "query_id": parsed.get("query_id", [None])[0],
    }


def create_access_token(sub: str, expires_delta: Optional[timedelta] = None) -> str:
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=30))
    to_encode = {"sub": sub, "exp": expire}
    return jwt.encode(to_encode, settings.jwt_secret, algorithm="HS256")


def create_refresh_token(sub: str, expires_delta: Optional[timedelta] = None) -> str:
    expire = datetime.utcnow() + (expires_delta or timedelta(days=7))
    to_encode = {"sub": sub, "exp": expire, "type": "refresh"}
    return jwt.encode(to_encode, settings.jwt_secret, algorithm="HS256")


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])