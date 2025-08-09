from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from typing import Optional, Literal
import csv
import io
from openpyxl import Workbook

from app.models import Shift
from app.services.shifts_service import compute_shift_seconds, rounded_seconds


Period = Literal["day", "week", "month"]


def period_bounds(period: Period, now: Optional[datetime] = None) -> tuple[datetime, datetime]:
    now = now or datetime.utcnow()
    if period == "day":
        start = datetime(now.year, now.month, now.day)
        end = start + timedelta(days=1)
    elif period == "week":
        start = datetime(now.year, now.month, now.day) - timedelta(days=now.weekday())
        end = start + timedelta(days=7)
    else:
        start = datetime(now.year, now.month, 1)
        if now.month == 12:
            end = datetime(now.year + 1, 1, 1)
        else:
            end = datetime(now.year, now.month + 1, 1)
    return start, end


def summary(db: Session, period: Period, user_id: Optional[int], department_id: Optional[int], project_id: Optional[int]):
    start, end = period_bounds(period)
    q = db.query(Shift).filter(Shift.started_at >= start, Shift.started_at < end)
    if user_id:
        q = q.filter(Shift.user_id == user_id)
    if project_id:
        q = q.filter(Shift.project_id == project_id)
    # department filtering omitted due to no departments table; placeholder for extension

    items = {}
    for s in q.all():
        seconds = compute_shift_seconds(s)
        rsec = rounded_seconds(seconds)
        row = items.get(s.user_id, {"total": 0, "rounded": 0})
        row["total"] += seconds
        row["rounded"] += rsec
        items[s.user_id] = row

    result = [
        {"user_id": uid, "total_seconds": v["total"], "rounded_seconds": v["rounded"]}
        for uid, v in items.items()
    ]
    return start, end, result


def export_csv(summary_items) -> bytes:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["user_id", "total_seconds", "rounded_seconds"])
    for it in summary_items:
        writer.writerow([it["user_id"], it["total_seconds"], it["rounded_seconds"]])
    return buf.getvalue().encode()


def export_xlsx(summary_items) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.append(["user_id", "total_seconds", "rounded_seconds"])
    for it in summary_items:
        ws.append([it["user_id"], it["total_seconds"], it["rounded_seconds"]])
    stream = io.BytesIO()
    wb.save(stream)
    return stream.getvalue()