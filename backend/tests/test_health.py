import sys
from pathlib import Path

# Add backend directory to sys.path so 'app' is importable
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root_endpoint():
    """Verify that root endpoint responds with basic application info."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "CivicPulse" in data["app"]
    assert data["health_check"] == "/health"


def test_health_check_endpoint():
    """Verify that /health endpoint responds with healthy status and database connection."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"
    assert "version" in data
    assert "app" in data
