from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional

from app.models import Request, RequestType, RequestStatus


def list_requests(db: Session, user_id: int):
    return db.query(Request).filter(Request.user_id == user_id).order_by(Request.id.desc()).all()


def create_request(db: Session, user_id: int, type_: RequestType, from_date: datetime, to_date: datetime, days: int, comment: str | None):
    req = Request(
        user_id=user_id,
        type=type_,
        status=RequestStatus.pending,
        from_date=from_date,
        to_date=to_date,
        days=days,
        comment=comment,
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    return req


def patch_request(db: Session, id_: int, status: RequestStatus | None, comment: str | None, approver_id: int | None):
    req = db.query(Request).filter(Request.id == id_).one()
    if status is not None:
        req.status = status
    if comment is not None:
        req.comment = comment
    if approver_id is not None:
        req.approver_id = approver_id
    db.commit()
    db.refresh(req)
    return req