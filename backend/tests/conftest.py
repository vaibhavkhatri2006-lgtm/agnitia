"""
Pytest configuration and fixtures for CivicPulse test suite.
Ensures tests run exclusively against the isolated 'civicpulse_test' database,
creating all tables before the test session and dropping them afterwards.
Guarantees tests NEVER touch the real database ('civicpulse_real').
"""
import os
import sys
from pathlib import Path
from urllib.parse import urlparse, urlunparse

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.config import settings
from app.database import Base, get_db
import app.database as app_db
from app.main import app
from seed import seed_database


def resolve_test_database_url() -> str:
    """
    Derives the test database URL from environment or settings.
    Guarantees isolation from civicpulse_real.
    """
    custom_url = os.environ.get("TEST_DATABASE_URL")
    if custom_url:
        target_url = custom_url
    else:
        base_url = settings.DATABASE_URL
        if "civicpulse_real" in base_url:
            target_url = base_url.replace("civicpulse_real", "civicpulse_test")
        elif "sqlite" in base_url:
            target_url = "sqlite:///./civicpulse_test.db"
        else:
            # Remote databases (e.g. Supabase) must never be targeted by tests or dropped during test teardown
            target_url = "sqlite:///./civicpulse_test.db"

    # ABSOLUTE SAFETY INVARIANT: Never allow tests to target civicpulse_real or live Supabase
    if "civicpulse_real" in str(target_url) or "supabase" in str(target_url).lower():
        raise RuntimeError(
            "CRITICAL SECURITY ABORT: Test suite attempted to connect to live database or Supabase. "
            "Tests must strictly run against isolated test database."
        )

    return target_url


TEST_DATABASE_URL = resolve_test_database_url()

# For MySQL, ensure civicpulse_test schema exists before connecting to it
if "mysql" in TEST_DATABASE_URL and "@" in TEST_DATABASE_URL:
    try:
        parsed = urlparse(TEST_DATABASE_URL)
        server_url = urlunparse(parsed._replace(path="/mysql"))
        server_engine = create_engine(server_url, isolation_level="AUTOCOMMIT")
        with server_engine.connect() as conn:
            conn.execute(
                text("CREATE DATABASE IF NOT EXISTS civicpulse_test CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            )
        server_engine.dispose()
    except Exception:
        # Fall through to let engine creation report standard connectivity errors
        pass

test_engine = create_engine(
    TEST_DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

# Override application database engine and session factory
app_db.engine = test_engine
app_db.SessionLocal = TestingSessionLocal


def override_get_db():
    assert "civicpulse_real" not in str(test_engine.url), "FATAL: Test connection points to civicpulse_real!"
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """
    Session-level test lifecycle hook:
    1. Verifies test database is not civicpulse_real or live Supabase.
    2. Creates all tables before test execution.
    3. Seeds baseline data.
    4. Drops all tables after test execution completes.
    """
    assert "civicpulse_real" not in str(test_engine.url) and "supabase" not in str(test_engine.url).lower(), (
        "CRITICAL INVARIANT VIOLATION: Test suite connected to live database!"
    )

    # 1. Create tables before tests
    Base.metadata.create_all(bind=test_engine)

    # 2. Seed baseline deterministic data for tests that expect existing records
    db = TestingSessionLocal()
    try:
        seed_database(db)
    except Exception:
        db.rollback()
    finally:
        db.close()

    yield

    # 3. Drop all tables after tests
    assert "civicpulse_real" not in str(test_engine.url) and "supabase" not in str(test_engine.url).lower(), (
        "CRITICAL INVARIANT VIOLATION: Tear-down attempted on live database!"
    )
    if "mysql" in str(test_engine.url):
        with test_engine.connect() as conn:
            conn.execute(text("SET FOREIGN_KEY_CHECKS = 0;"))
            Base.metadata.drop_all(bind=conn)
            conn.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))
            conn.commit()
    else:
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session():
    """Provides a fresh transactional session on isolated test database."""
    assert "civicpulse_real" not in str(test_engine.url) and "supabase" not in str(test_engine.url).lower(), "FATAL: Session points to live database!"
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def db():
    """Alias for db_session fixture."""
    assert "civicpulse_real" not in str(test_engine.url) and "supabase" not in str(test_engine.url).lower(), "FATAL: Session points to live database!"
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client():
    """TestClient configured with test database dependency overrides."""
    return TestClient(app)
