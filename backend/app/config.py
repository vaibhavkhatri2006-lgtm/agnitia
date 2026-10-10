from pathlib import Path
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = BACKEND_DIR.parent


class Settings(BaseSettings):
    APP_NAME: str = "CivicPulse API"
    APP_VERSION: str = "0.5.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    BACKEND_HOST: str = "127.0.0.1"
    BACKEND_PORT: int = 8000
    PORT: Optional[int] = None # Render injects PORT
    DATABASE_URL: str = "sqlite:///./civicpulse.db"
    FRONTEND_URL: Optional[str] = "https://civicpulse-frontend-xbem.onrender.com"
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,https://civicpulse-frontend-xbem.onrender.com"

    # Authentication & JWT Configuration
    JWT_SECRET_KEY: str = "civicpulse-development-secret-key-change-in-production-32bytesmin"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Operational Mode: 'demo' or 'real'
    CIVICPULSE_MODE: str = "demo"

    # OpenStreetMap / Overpass API Configuration
    OVERPASS_URL: str = "https://overpass-api.de/api/interpreter"
    OVERPASS_TIMEOUT_SECONDS: int = 25
    OSM_USER_AGENT: str = "CivicPulse/1.0 (https://github.com/CivicPulse; contact@civicpulse.org)"
    OSM_CACHE_TTL_HOURS: int = 24

    # OSRM (Open Source Routing Machine) Configuration
    USE_OSRM: bool = False
    OSRM_BASE_URL: Optional[str] = None
    OSRM_TIMEOUT_SECONDS: float = 3.0

    model_config = SettingsConfigDict(
        env_file=(str(BACKEND_DIR / ".env"), str(ROOT_DIR / ".env"), ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origins(self) -> List[str]:
        """
        Parses allowed CORS origins safely without allowing unrestricted credentials.
        Never emits ['*'] when credentials are enabled.
        """
        origins: List[str] = []
        if self.ALLOWED_ORIGINS and self.ALLOWED_ORIGINS.strip() != "*":
            origins.extend([
                o.strip().rstrip("/")
                for o in self.ALLOWED_ORIGINS.split(",")
                if o.strip() and o.strip() != "*"
            ])
        if self.FRONTEND_URL and self.FRONTEND_URL.strip() != "*":
            clean_frontend = self.FRONTEND_URL.strip().rstrip("/")
            if clean_frontend and clean_frontend not in origins:
                origins.append(clean_frontend)

        # Fallback to standard safe development origins if empty
        if not origins:
            origins = ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"]

        return origins


settings = Settings()
