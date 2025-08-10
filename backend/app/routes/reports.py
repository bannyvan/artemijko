from fastapi import APIRouter, Depends, Response, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, Literal

from app.db import get_db
from app.routes.auth import get_current_user
from app.schemas import ReportSummaryResponse, ReportSummaryItem
from app.services import reports_service as svc

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/summary", response_model=ReportSummaryResponse)
def summary(period: Literal["day", "week", "month"], user_id: Optional[int] = None, department_id: Optional[int] = None, project_id: Optional[int] = None, db: Session = Depends(get_db), user=Depends(get_current_user)):
    start, end, items = svc.summary(db, period, user_id, department_id, project_id)
    return {
        "period": period,
        "from_dt": start,
        "to_dt": end,
        "items": [ReportSummaryItem(**i) for i in items]
    }


@router.get("/export.csv")
def export_csv(period: Literal["day", "week", "month"], user_id: Optional[int] = None, department_id: Optional[int] = None, project_id: Optional[int] = None, db: Session = Depends(get_db), user=Depends(get_current_user)):
    _, _, items = svc.summary(db, period, user_id, department_id, project_id)
    content = svc.export_csv(items)
    return Response(content=content, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=report.csv"})


@router.get("/export.xlsx")
def export_xlsx(period: Literal["day", "week", "month"], user_id: Optional[int] = None, department_id: Optional[int] = None, project_id: Optional[int] = None, db: Session = Depends(get_db), user=Depends(get_current_user)):
    _, _, items = svc.summary(db, period, user_id, department_id, project_id)
    content = svc.export_xlsx(items)
    return Response(content=content, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": "attachment; filename=report.xlsx"})