from fastapi import FastAPI, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.db import SessionLocal
from app.models import AuditLog
from datetime import datetime


limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])  # global limit


def setup_middlewares(app: FastAPI):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"]
    )


async def log_audit(user_id: int | None, action: str, entity: str, entity_id: int | None, payload: dict | None, source: str = "WebApp"):
    db = SessionLocal()
    try:
        log = AuditLog(
            user_id=user_id,
            action=action,
            entity=entity,
            entity_id=entity_id,
            payload=payload,
            source=source,
            created_at=datetime.utcnow(),
        )
        db.add(log)
        db.commit()
    finally:
        db.close()