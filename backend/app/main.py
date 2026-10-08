from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import settings
from app.database import check_database_connection
from app.routes.auth import router as auth_router
from app.routes.analytics import router as analytics_router

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="CivicPulse - Civic Infrastructure, Accessibility & Community Analytics API",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {"name": "Root", "description": "Core platform and metadata"},
        {"name": "Health", "description": "Application & database health probes"},
        {"name": "Authentication & RBAC", "description": "User login, token issuance, and role-based access control"},
        {"name": "Geospatial & Analytics Engine", "description": "Deterministic spatial accessibility, gap scoring, and service desert analytics"},
    ],
)

# Configure Cross-Origin Resource Sharing (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(auth_router)
app.include_router(analytics_router)


# --- Global Exception Handlers for Consistent Error Responses ---

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "status_code": exc.status_code,
            "error_code": f"HTTP_{exc.status_code}",
        },
        headers=getattr(exc, "headers", None),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Request validation failed",
            "errors": exc.errors(),
            "status_code": 422,
            "error_code": "VALIDATION_ERROR",
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    # In production/clean mode: do not expose internal tracebacks or secrets
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An internal server error occurred.",
            "status_code": 500,
            "error_code": "INTERNAL_SERVER_ERROR",
        },
    )


# --- Root & Health Endpoints ---

@app.get("/", tags=["Root"])
def read_root():
    """Root endpoint welcoming developers and clients."""
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "message": "Welcome to the CivicPulse API. Visit /docs for OpenAPI documentation.",
        "health_check": "/health",
        "auth_login": "/auth/login",
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
