from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional, List


class Settings(BaseSettings):
    bot_token: str = Field(..., alias="BOT_TOKEN")
    database_url: str = Field(..., alias="DATABASE_URL")
    jwt_secret: str = Field(..., alias="JWT_SECRET")
    allowed_origins: str = Field("http://localhost:5173", alias="ALLOWED_ORIGINS")
    sentry_dsn: Optional[str] = Field(None, alias="SENTRY_DSN")
    otel_exporter_otlp_endpoint: Optional[str] = Field(None, alias="OTEL_EXPORTER_OTLP_ENDPOINT")

    max_shift_hours: int = Field(12, alias="MAX_SHIFT_HOURS")
    rounding_minutes: int = Field(15, alias="ROUNDING_MINUTES")
    required_break_after_hours: int = Field(4, alias="REQUIRED_BREAK_AFTER_HOURS")
    min_break_minutes: int = Field(15, alias="MIN_BREAK_MINUTES")

    class Config:
        case_sensitive = True
        env_file = ".env"

    @property
    def allowed_origins_list(self) -> List[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]


settings = Settings()  # type: ignore