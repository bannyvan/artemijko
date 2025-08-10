from sqlalchemy.orm import Session
from app.security import validate_telegram_init_data, create_access_token, create_refresh_token, decode_token
from app.models import User, UserRole, UserStatus
from datetime import timedelta


class AuthService:
    @staticmethod
    def authenticate_via_telegram(db: Session, init_data_raw: str) -> tuple[User, str, str]:
        data = validate_telegram_init_data(init_data_raw)
        tg_user = data.get("user", {})
        tg_id = str(tg_user.get("id")) if tg_user.get("id") is not None else None
        if not tg_id:
            raise ValueError("user.id missing in initData")

        user = db.query(User).filter(User.tg_id == tg_id).one_or_none()
        if not user:
            user = User(tg_id=tg_id, role=UserRole.employee, status=UserStatus.active)
            db.add(user)
            db.commit()
            db.refresh(user)

        access = create_access_token(sub=str(user.id), expires_delta=timedelta(minutes=30))
        refresh = create_refresh_token(sub=str(user.id), expires_delta=timedelta(days=7))
        return user, access, refresh

    @staticmethod
    def refresh_access(token: str) -> str:
        payload = decode_token(token)
        if payload.get("type") != "refresh":
            raise ValueError("Invalid refresh token")
        sub = payload.get("sub")
        return create_access_token(sub=sub)