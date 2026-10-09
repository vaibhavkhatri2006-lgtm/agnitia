import sys
from pathlib import Path

# Ensure backend root is in sys.path
BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import uvicorn
from app.config import settings


def main():
    print(f"============================================================")
    print(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"Environment: {settings.ENVIRONMENT}")
    print(f"Listening on: http://{settings.BACKEND_HOST}:{settings.BACKEND_PORT}")
    print(f"API Docs:     http://{settings.BACKEND_HOST}:{settings.BACKEND_PORT}/docs")
    print(f"Health Probe: http://{settings.BACKEND_HOST}:{settings.BACKEND_PORT}/health")
    print(f"============================================================")
    uvicorn.run(
        "app.main:app",
        host=settings.BACKEND_HOST,
        port=settings.BACKEND_PORT,
        reload=settings.DEBUG,
    )


if __name__ == "__main__":
    main()
