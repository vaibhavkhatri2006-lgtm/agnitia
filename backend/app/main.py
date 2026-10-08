from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import check_database_connection

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="CivicPulse - Civic Infrastructure & Analytics Platform API",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure Cross-Origin Resource Sharing (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Root"])
def read_root():
    """Root endpoint welcoming developers and clients."""
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "message": "Welcome to the CivicPulse API. Visit /docs for OpenAPI documentation.",
        "health_check": "/health",
    }


@app.get("/health", tags=["Health"])
def health_check():
    """
    Health check endpoint verifying backend and database status.
    Returns 200 OK when backend is operational.
    """
    db_status = check_database_connection()
    is_db_connected = db_status.get("status") == "connected"

    payload = {
        "status": "healthy" if is_db_connected else "degraded",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "database": db_status.get("status", "unknown"),
        "database_dialect": db_status.get("dialect", "unknown"),
    }

    if not is_db_connected:
        payload["database_error"] = db_status.get("error")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=payload,
        )

    return payload
