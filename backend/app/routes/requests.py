from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from app.db import get_db
from app.routes.auth import get_current_user
from app.schemas import RequestCreateIn, RequestOut, RequestPatchIn
from app.services import requests_service as svc
from app.models import UserRole, RequestType, RequestStatus
from app.middleware import log_audit

router = APIRouter(prefix="/requests", tags=["requests"])


@router.get("/", response_model=list[RequestOut])
def list_my_requests(db: Session = Depends(get_db), user=Depends(get_current_user)):
    reqs = svc.list_requests(db, user.id)
    return [RequestOut.model_validate(r) for r in reqs]


@router.post("/", response_model=RequestOut)
async def create_request(payload: RequestCreateIn, db: Session = Depends(get_db), user=Depends(get_current_user)):
    req = svc.create_request(
        db,
        user_id=user.id,
        type_=RequestType(payload.type),
        from_date=datetime.combine(payload.from_date, datetime.min.time()),
        to_date=datetime.combine(payload.to_date, datetime.min.time()),
        days=payload.days,
        comment=payload.comment,
    )
    await log_audit(user.id, 'create', 'request', req.id, payload.model_dump())
    return RequestOut.model_validate(req)


@router.patch("/{id}", response_model=RequestOut)
async def patch_request(id: int, payload: RequestPatchIn, db: Session = Depends(get_db), user=Depends(get_current_user)):
    if user.role not in (UserRole.manager, UserRole.admin):
        raise HTTPException(status_code=403, detail="forbidden")
    req = svc.patch_request(db, id, RequestStatus(payload.status) if payload.status else None, payload.comment, approver_id=user.id)
    await log_audit(user.id, 'patch', 'request', req.id, payload.model_dump())
    return RequestOut.model_validate(req)