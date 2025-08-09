from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime, date
from typing import Optional, Literal, List


class JWTTokens(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"


class UserOut(BaseModel):
    id: int
    tg_id: str
    role: Literal["employee", "manager", "admin"]
    department_id: Optional[int]
    status: Literal["active", "inactive"]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MeResponse(BaseModel):
    user: UserOut
    settings: dict


class ShiftOut(BaseModel):
    id: int
    user_id: int
    started_at: datetime
    paused_at: Optional[datetime]
    resumed_at: Optional[datetime]
    finished_at: Optional[datetime]
    status: Literal["active", "paused", "finished"]
    project_id: Optional[int]
    note: Optional[str]

    model_config = ConfigDict(from_attributes=True)


class BreakOut(BaseModel):
    id: int
    shift_id: int
    started_at: datetime
    finished_at: Optional[datetime]
    type: Literal["technical", "lunch", "personal"]

    model_config = ConfigDict(from_attributes=True)


class StartShiftIn(BaseModel):
    project_id: Optional[int] = None
    note: Optional[str] = None


class StartBreakIn(BaseModel):
    type: Literal["technical", "lunch", "personal"]


class RequestCreateIn(BaseModel):
    type: Literal["vacation", "dayoff", "sick"]
    from_date: date
    to_date: date
    days: int
    comment: Optional[str] = None


class RequestOut(BaseModel):
    id: int
    user_id: int
    type: Literal["vacation", "dayoff", "sick"]
    status: Literal["pending", "approved", "rejected"]
    from_date: datetime
    to_date: datetime
    days: int
    approver_id: Optional[int]
    comment: Optional[str]

    model_config = ConfigDict(from_attributes=True)


class RequestPatchIn(BaseModel):
    status: Optional[Literal["pending", "approved", "rejected"]] = None
    comment: Optional[str] = None


class ReportSummaryItem(BaseModel):
    user_id: int
    total_seconds: int
    rounded_seconds: int


class ReportSummaryResponse(BaseModel):
    period: Literal["day", "week", "month"]
    from_dt: datetime
    to_dt: datetime
    items: List[ReportSummaryItem]


class WarningResponse(BaseModel):
    warnings: List[str] = Field(default_factory=list)


class AdminUserPatchIn(BaseModel):
    role: Optional[Literal["employee","manager","admin"]] = None
    status: Optional[Literal["active","inactive"]] = None