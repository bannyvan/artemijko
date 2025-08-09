from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import asyncio

from app.middleware import setup_middlewares, limiter
from app.instrumentation import init_sentry, init_otel
from app.routes import auth as auth_routes
from app.routes import me as me_routes
from app.routes import shifts as shifts_routes
from app.routes import reports as reports_routes
from app.routes import requests as requests_routes
from app.routes import admin as admin_routes
from app.db import SessionLocal
from app.services.shifts_service import enforce_auto_stop, BusinessRuleError
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler


def create_app() -> FastAPI:
    app = FastAPI(title="TimeTracker API", version="1.0.0")

    init_sentry()
    init_otel(app)
    setup_middlewares(app)

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    app.include_router(auth_routes.router)
    app.include_router(me_routes.router)
    app.include_router(shifts_routes.router)
    app.include_router(shifts_routes.breaks_router)
    app.include_router(reports_routes.router)
    app.include_router(requests_routes.router)
    app.include_router(admin_routes.router)

    @app.exception_handler(BusinessRuleError)
    async def business_rule_handler(request: Request, exc: BusinessRuleError):
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.on_event("startup")
    async def start_tasks():
        async def periodic_auto_stop():
            while True:
                try:
                    db = SessionLocal()
                    enforce_auto_stop(db)
                    db.close()
                except Exception:
                    pass
                await asyncio.sleep(300)
        asyncio.create_task(periodic_auto_stop())

    return app


app = create_app()