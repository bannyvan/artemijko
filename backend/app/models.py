from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum, Boolean, JSON, Index, UniqueConstraint
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime
import enum
from app.db import Base


class UserRole(str, enum.Enum):
    employee = "employee"
    manager = "manager"
    admin = "admin"


class UserStatus(str, enum.Enum):
    active = "active"
    inactive = "inactive"


class BreakType(str, enum.Enum):
    technical = "technical"
    lunch = "lunch"
    personal = "personal"


class RequestType(str, enum.Enum):
    vacation = "vacation"
    dayoff = "dayoff"
    sick = "sick"


class RequestStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class ShiftStatus(str, enum.Enum):
    active = "active"
    paused = "paused"
    finished = "finished"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tg_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.employee, nullable=False)
    department_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[UserStatus] = mapped_column(Enum(UserStatus), default=UserStatus.active, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    shifts = relationship("Shift", back_populates="user")


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Shift(Base):
    __tablename__ = "shifts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime, index=True, nullable=False)
    paused_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    resumed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, index=True, nullable=True)
    status: Mapped[ShiftStatus] = mapped_column(Enum(ShiftStatus), default=ShiftStatus.active, index=True, nullable=False)
    project_id: Mapped[int | None] = mapped_column(ForeignKey("projects.id"), nullable=True)
    note: Mapped[str | None] = mapped_column(String(500), nullable=True)

    user = relationship("User", back_populates="shifts")
    project = relationship("Project")
    breaks = relationship("Break", back_populates="shift")

    __table_args__ = (
        Index("ix_shifts_user_status", "user_id", "status"),
    )


class Break(Base):
    __tablename__ = "breaks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    shift_id: Mapped[int] = mapped_column(ForeignKey("shifts.id"), index=True, nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    type: Mapped[BreakType] = mapped_column(Enum(BreakType), nullable=False)

    shift = relationship("Shift", back_populates="breaks")


class Request(Base):
    __tablename__ = "requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    type: Mapped[RequestType] = mapped_column(Enum(RequestType), nullable=False)
    status: Mapped[RequestStatus] = mapped_column(Enum(RequestStatus), default=RequestStatus.pending, index=True, nullable=False)
    from_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    to_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    days: Mapped[int] = mapped_column(Integer, nullable=False)
    approver_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    comment: Mapped[str | None] = mapped_column(String(500), nullable=True)


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), index=True, nullable=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    entity: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    source: Mapped[str] = mapped_column(String(50), nullable=False, default="WebApp")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("ix_audit_user_action", "user_id", "action"),
    )


class IdempotencyKey(Base):
    __tablename__ = "idempotency_keys"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    key: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "action", "key", name="uq_idem_user_action_key"),
    )