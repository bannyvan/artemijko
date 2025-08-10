from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from datetime import datetime, timedelta
from typing import Optional

from app.models import Shift, ShiftStatus, Break, BreakType, IdempotencyKey
from app.config import settings


class BusinessRuleError(Exception):
    pass


def get_active_shift(db: Session, user_id: int) -> Optional[Shift]:
    return db.query(Shift).filter(Shift.user_id == user_id, Shift.status != ShiftStatus.finished).order_by(Shift.id.desc()).first()


def enforce_auto_stop(db: Session):
    now = datetime.utcnow()
    max_delta = timedelta(hours=settings.max_shift_hours)
    candidates = db.query(Shift).filter(Shift.status != ShiftStatus.finished).all()
    for s in candidates:
        start_point = s.resumed_at or s.started_at
        if now - start_point > max_delta:
            s.status = ShiftStatus.finished
            s.finished_at = now
    db.commit()


def use_idempotency(db: Session, user_id: int, action: str, key: Optional[str]):
    if not key:
        return
    idem = IdempotencyKey(user_id=user_id, action=action, key=key)
    db.add(idem)
    try:
        db.commit()
    except Exception:
        db.rollback()
        # key already used; just allow idempotent behavior by not failing
        pass


def start_shift(db: Session, user_id: int, project_id: Optional[int], note: Optional[str], idempotency_key: Optional[str]):
    enforce_auto_stop(db)
    existing = get_active_shift(db, user_id)
    if existing and existing.status in (ShiftStatus.active, ShiftStatus.paused):
        raise BusinessRuleError("Active shift already exists")

    use_idempotency(db, user_id, "start_shift", idempotency_key)

    shift = Shift(
        user_id=user_id,
        started_at=datetime.utcnow(),
        status=ShiftStatus.active,
        project_id=project_id,
        note=note,
    )
    db.add(shift)
    db.commit()
    db.refresh(shift)
    return shift


def pause_shift(db: Session, user_id: int):
    enforce_auto_stop(db)
    shift = get_active_shift(db, user_id)
    if not shift or shift.status != ShiftStatus.active:
        raise BusinessRuleError("No active shift to pause")

    shift.status = ShiftStatus.paused
    shift.paused_at = datetime.utcnow()
    db.commit()
    db.refresh(shift)
    return shift


def resume_shift(db: Session, user_id: int):
    enforce_auto_stop(db)
    shift = get_active_shift(db, user_id)
    if not shift or shift.status != ShiftStatus.paused:
        raise BusinessRuleError("No paused shift to resume")

    shift.status = ShiftStatus.active
    shift.resumed_at = datetime.utcnow()
    db.commit()
    db.refresh(shift)
    return shift


def finish_shift(db: Session, user_id: int, idempotency_key: Optional[str]):
    enforce_auto_stop(db)
    shift = get_active_shift(db, user_id)
    if not shift or shift.status == ShiftStatus.finished:
        raise BusinessRuleError("No active shift to finish")

    use_idempotency(db, user_id, "finish_shift", idempotency_key)

    shift.status = ShiftStatus.finished
    shift.finished_at = datetime.utcnow()
    db.commit()
    db.refresh(shift)
    return shift


def start_break(db: Session, user_id: int, type_: BreakType):
    shift = get_active_shift(db, user_id)
    if not shift or shift.status != ShiftStatus.active:
        raise BusinessRuleError("Break allowed only during active shift")

    shift.status = ShiftStatus.paused
    shift.paused_at = datetime.utcnow()

    br = Break(shift_id=shift.id, started_at=datetime.utcnow(), type=type_)
    db.add(br)
    db.commit()
    db.refresh(br)
    return br


def finish_break(db: Session, user_id: int):
    shift = get_active_shift(db, user_id)
    if not shift or shift.status != ShiftStatus.paused:
        raise BusinessRuleError("No paused shift/break to finish")

    br = db.query(Break).filter(Break.shift_id == shift.id, Break.finished_at.is_(None)).order_by(Break.id.desc()).first()
    if not br:
        raise BusinessRuleError("No active break found")

    br.finished_at = datetime.utcnow()
    shift.status = ShiftStatus.active
    shift.resumed_at = datetime.utcnow()
    db.commit()
    db.refresh(br)
    return br


def list_shifts(db: Session, from_dt: Optional[datetime], to_dt: Optional[datetime], user_id: Optional[int], project_id: Optional[int]):
    q = db.query(Shift)
    if from_dt:
        q = q.filter(Shift.started_at >= from_dt)
    if to_dt:
        q = q.filter(Shift.started_at <= to_dt)
    if user_id:
        q = q.filter(Shift.user_id == user_id)
    if project_id:
        q = q.filter(Shift.project_id == project_id)
    q = q.order_by(Shift.started_at.desc())
    return q.all()


def list_breaks(db: Session, shift_id: int):
    return db.query(Break).filter(Break.shift_id == shift_id).order_by(Break.started_at.asc()).all()


def detect_warnings_for_shift(shift: Shift) -> list[str]:
    warnings: list[str] = []
    now = datetime.utcnow()
    max_hours = settings.max_shift_hours
    if shift.status != ShiftStatus.finished:
        start_point = shift.resumed_at or shift.started_at
        if (now - start_point) > timedelta(hours=max_hours):
            warnings.append("Shift exceeds maximum duration; auto-finished may apply")

    # required break policy
    if shift.resumed_at:
        continuous = now - shift.resumed_at
    else:
        continuous = now - shift.started_at
    if continuous > timedelta(hours=settings.required_break_after_hours):
        # Check last break duration
        last_break = None
        if shift.breaks:
            last_break = max(shift.breaks, key=lambda b: b.id)
        if not last_break or not last_break.finished_at or (last_break.finished_at - last_break.started_at) < timedelta(minutes=settings.min_break_minutes):
            warnings.append("Minimum break required due to continuous work policy")

    return warnings


def rounding_minutes() -> int:
    return max(1, settings.rounding_minutes)


def rounded_seconds(seconds: int) -> int:
    step = rounding_minutes() * 60
    return int((seconds + step - 1) // step * step)


def compute_shift_seconds(shift: Shift) -> int:
    end = shift.finished_at or datetime.utcnow()
    return int((end - shift.started_at).total_seconds())