from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.routes.auth import get_current_user
from app.schemas import UserOut
from app.models import User, UserRole, UserStatus

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db), user=Depends(get_current_user)):
    if user.role not in (UserRole.manager, UserRole.admin):
        raise HTTPException(status_code=403, detail="forbidden")
    users = db.query(User).order_by(User.id.asc()).all()
    return [UserOut.model_validate(u) for u in users]


@router.patch("/users/{id}", response_model=UserOut)
def patch_user(id: int, role: UserRole | None = None, status: UserStatus | None = None, db: Session = Depends(get_db), user=Depends(get_current_user)):
    if user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="forbidden")
    u = db.query(User).filter(User.id == id).one()
    if role is not None:
        u.role = role
    if status is not None:
        u.status = status
    db.commit()
    db.refresh(u)
    return UserOut.model_validate(u)