import os

# Ensure test settings before importing app
os.environ.setdefault("BOT_TOKEN", "test:token")
os.environ.setdefault("JWT_SECRET", "testsecret")
os.environ.setdefault("ALLOWED_ORIGINS", "http://localhost")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")

import pytest
from fastapi.testclient import TestClient
from app.main import create_app
from app.db import Base, engine


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client():
    app = create_app()
    return TestClient(app)