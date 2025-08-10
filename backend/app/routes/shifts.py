from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from app.db import get_db
from app.routes.auth import get_current_user
from app.schemas import ShiftOut, StartShiftIn, BreakOut, StartBreakIn, WarningResponse
from app.middleware import log_audit
from app.services import shifts_service as svc
from app.models import BreakType
from app.middleware import limiter

router = APIRouter(prefix="/shifts", tags=["shifts"])


@router.get("/", response_model=list[ShiftOut])
def list_shifts(from_: Optional[datetime] = None, to: Optional[datetime] = None, user_id: Optional[int] = None, project_id: Optional[int] = None, db: Session = Depends(get_db), user=Depends(get_current_user)):
    shifts = svc.list_shifts(db, from_, to, user_id, project_id)
    return [ShiftOut.model_validate(s) for s in shifts]


@router.post("/start", response_model=ShiftOut)
@limiter.limit("30/minute")
def start_shift(payload: StartShiftIn, db: Session = Depends(get_db), user=Depends(get_current_user), idempotency_key: Optional[str] = Header(default=None, alias="Idempotency-Key")):
    if not idempotency_key:
        raise HTTPException(status_code=400, detail="Idempotency-Key required")
    try:
        shift = svc.start_shift(db, user.id, payload.project_id, payload.note, idempotency_key)
    except svc.BusinessRuleError as e:
        raise HTTPException(status_code=400, detail=str(e))
    await log_audit(user.id, 'start', 'shift', shift.id, {'project_id': payload.project_id, 'note': payload.note})
    return ShiftOut.model_validate(shift)


@router.post("/pause", response_model=ShiftOut)
@limiter.limit("60/minute")
async def pause_shift(db: Session = Depends(get_db), user=Depends(get_current_user)):
    try:
        shift = svc.pause_shift(db, user.id)
    except svc.BusinessRuleError as e:
        raise HTTPException(status_code=400, detail=str(e))
    await log_audit(user.id, 'pause', 'shift', shift.id, None)
    return ShiftOut.model_validate(shift)


@router.post("/resume", response_model=ShiftOut)
@limiter.limit("60/minute")
async def resume_shift(db: Session = Depends(get_db), user=Depends(get_current_user)):
    try:
        shift = svc.resume_shift(db, user.id)
    except svc.BusinessRuleError as e:
        raise HTTPException(status_code=400, detail=str(e))
    await log_audit(user.id, 'resume', 'shift', shift.id, None)
    return ShiftOut.model_validate(shift)


@router.post("/finish", response_model=ShiftOut)
@limiter.limit("30/minute")
async def finish_shift(db: Session = Depends(get_db), user=Depends(get_current_user), idempotency_key: Optional[str] = Header(default=None, alias="Idempotency-Key")):
    if not idempotency_key:
        raise HTTPException(status_code=400, detail="Idempotency-Key required")
    try:
        shift = svc.finish_shift(db, user.id, idempotency_key)
    except svc.BusinessRuleError as e:
        raise HTTPException(status_code=400, detail=str(e))
    await log_audit(user.id, 'finish', 'shift', shift.id, None)
    return ShiftOut.model_validate(shift)


@router.get("/{shift_id}/breaks", response_model=list[BreakOut])
def get_breaks(shift_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    brs = svc.list_breaks(db, shift_id)
    return [BreakOut.model_validate(b) for b in brs]


@router.post("/../breaks/start", response_model=BreakOut, include_in_schema=False)
async def legacy():
    # placeholder to ensure path order
    pass


breaks_router = APIRouter(prefix="/breaks", tags=["breaks"])


@breaks_router.post("/start", response_model=BreakOut)
async def start_break(payload: StartBreakIn, db: Session = Depends(get_db), user=Depends(get_current_user)):
    try:
        br = svc.start_break(db, user.id, BreakType(payload.type))
    except svc.BusinessRuleError as e:
        raise HTTPException(status_code=400, detail=str(e))
    await log_audit(user.id, 'start', 'break', br.id, {'type': payload.type})
    return BreakOut.model_validate(br)


@breaks_router.post("/finish", response_model=BreakOut)
async def finish_break(db: Session = Depends(get_db), user=Depends(get_current_user)):
    try:
        br = svc.finish_break(db, user.id)
    except svc.BusinessRuleError as e:
        raise HTTPException(status_code=400, detail=str(e))
    await log_audit(user.id, 'finish', 'break', br.id, None)
    return BreakOut.model_validate(br)