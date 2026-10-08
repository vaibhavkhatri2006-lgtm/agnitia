from app.routes.auth import router as auth_router
from app.routes.analytics import router as analytics_router
from app.routes.decision import router as decision_router

__all__ = ["auth_router", "analytics_router", "decision_router"]
