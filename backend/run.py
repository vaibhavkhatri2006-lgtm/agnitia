import sys
from pathlib import Path

# Ensure backend root is in sys.path
BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import uvicorn
from app.config import settings


def main():
    # Render and other PaaS inject PORT and require binding to 0.0.0.0
    host = "0.0.0.0" if settings.PORT else settings.BACKEND_HOST
    port = settings.PORT or settings.BACKEND_PORT

    print(f"============================================================")
    print(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"Environment: {settings.ENVIRONMENT}")
    print(f"Listening on: http://{host}:{port}")
    print(f"API Docs:     http://{host}:{port}/docs")
    print(f"Health Probe: http://{host}:{port}/health")
    print(f"============================================================")
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=settings.DEBUG and not settings.PORT,
    )


if __name__ == "__main__":
    main()
