import logging
from typing import Dict, Any
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings

logger = logging.getLogger("civicpulse.database")

# Build engine connection args depending on dialect
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for future ORM models (models are NOT created in Stage 0)
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
