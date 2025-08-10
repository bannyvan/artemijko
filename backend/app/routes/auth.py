from fastapi import APIRouter, Depends, HTTPException, Response, Cookie
from sqlalchemy.orm import Session
from fastapi import status

from app.db import get_db
from app.schemas import JWTTokens, MeResponse, UserOut
from app.services.auth_service import AuthService
from app.config import settings
from app.security import decode_token
from app.models import User
from app.middleware import limiter

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/telegram", response_model=JWTTokens)
@limiter.limit("10/minute")
def auth_telegram(initData: str, response: Response, db: Session = Depends(get_db)):
    try:
        user, access, refresh = AuthService.authenticate_via_telegram(db, initData)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid initData")

    response.set_cookie(
        key="refresh_token",
        value=refresh,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=7 * 24 * 3600,
        path="/auth/refresh",
    )
    return {"access_token": access}


@router.post("/refresh", response_model=JWTTokens)
def refresh_access_token(response: Response, refresh_token: str | None = Cookie(default=None, alias="refresh_token")):
    if not refresh_token:
        raise HTTPException(status_code=401, detail="missing refresh token")
    try:
        access = AuthService.refresh_access(refresh_token)
    except Exception:
        raise HTTPException(status_code=401, detail="invalid refresh token")
    return {"access_token": access}


from fastapi import Header

def get_current_user(db: Session = Depends(get_db), authorization: str | None = Header(default=None, alias="Authorization")) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="missing bearer token")
    token = authorization.split(" ", 1)[1]
    try:
        payload = decode_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="invalid token")
    user_id = int(payload.get("sub"))
    user = db.query(User).filter(User.id == user_id).one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="user not found")
    return user