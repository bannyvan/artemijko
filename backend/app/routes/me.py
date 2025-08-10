from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas import MeResponse, UserOut
from app.routes.auth import get_current_user
from app.config import settings

router = APIRouter(tags=["me"])


@router.get("/me", response_model=MeResponse)
def me(user=Depends(get_current_user)):
    return {
        "user": UserOut.model_validate(user),
        "settings": {
            "rounding_minutes": settings.rounding_minutes,
            "max_shift_hours": settings.max_shift_hours,
            "required_break_after_hours": settings.required_break_after_hours,
            "min_break_minutes": settings.min_break_minutes,
        },
    }