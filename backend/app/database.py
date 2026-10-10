import logging
from typing import Dict, Any
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from pathlib import Path
from app.config import settings, BACKEND_DIR

logger = logging.getLogger("civicpulse.database")

# Resolve database URL
db_url = settings.DATABASE_URL
if db_url.startswith("sqlite:///./"):
    sqlite_file = (BACKEND_DIR / db_url.replace("sqlite:///./", "")).resolve()
    db_url = f"sqlite:///{sqlite_file}"

connect_args = {}
if db_url.startswith("sqlite"):
    connect_args["check_same_thread"] = False

try:
    engine = create_engine(
        db_url,
        connect_args=connect_args,
        pool_pre_ping=True,
        pool_recycle=3600,
        echo=False,
    )
    with engine.connect() as test_conn:
        test_conn.execute(text("SELECT 1"))
except Exception as e:
    logger.warning(f"Could not connect to configured DATABASE_URL ({db_url}): {e}. Falling back to local SQLite.")
    sqlite_fallback = (BACKEND_DIR / "civicpulse.db").resolve()
    engine = create_engine(
        f"sqlite:///{sqlite_fallback}",
        connect_args={"check_same_thread": False},
        pool_pre_ping=True,
        echo=False,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for ORM models
Base = declarative_base()


def get_db():
    """Dependency generator for database sessions in API requests."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_database_connection() -> Dict[str, Any]:
    """
    Validates connectivity to the configured database.
    Executes a lightweight query (SELECT 1).
    """
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1")).scalar()
            if result == 1:
                return {
                    "status": "connected",
                    "dialect": engine.dialect.name,
                    "url_scheme": settings.DATABASE_URL.split("://")[0] if "://" in settings.DATABASE_URL else "unknown",
                }
            return {
                "status": "unhealthy",
                "error": "Unexpected probe result",
            }
    except Exception as exc:
        logger.error(f"Database connection check failed: {exc}")
        return {
            "status": "disconnected",
            "error": str(exc),
        }
