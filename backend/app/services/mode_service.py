"""
CivicPulse Mode Management Service.
Allows toggling and querying the operational data mode between 'demo' (deterministic synthetic dataset)
and 'real' (live OpenStreetMap ingestion with verified provenance).
"""
import logging
from typing import Dict, Any, List
from app.config import settings

logger = logging.getLogger(__name__)

# In-memory runtime override; defaults to settings.CIVICPULSE_MODE
_active_mode: str = getattr(settings, "CIVICPULSE_MODE", "demo").lower()


def get_current_mode() -> str:
    """Return the active operational mode ('demo' or 'real')."""
    return _active_mode


def set_current_mode(new_mode: str) -> str:
    """Set the active operational mode ('demo' or 'real'). Raises ValueError on invalid mode."""
    global _active_mode
    normalized = new_mode.strip().lower()
    if normalized not in ("demo", "real"):
        raise ValueError(f"Invalid mode '{new_mode}'. Supported modes are 'demo' and 'real'.")
    _active_mode = normalized
    logger.info("CivicPulse operational mode updated to: %s", _active_mode)
    return _active_mode


def is_real_mode() -> bool:
    """Check if CivicPulse is currently operating in Real Data Mode."""
    return get_current_mode() == "real"


def is_demo_mode() -> bool:
    """Check if CivicPulse is currently operating in Demo Mode."""
    return get_current_mode() == "demo"


def get_mode_metadata() -> Dict[str, Any]:
    """Return detailed metadata about the operational mode, sources, and routing capabilities."""
    mode = get_current_mode()
    osrm_configured = bool(getattr(settings, "OSRM_BASE_URL", None))
    osrm_enabled = bool(getattr(settings, "USE_OSRM", False)) and osrm_configured

    if mode == "real":
        description = (
            "REAL DATA MODE: Analysis is powered by OpenStreetMap imported facilities, "
            "documented census/public populations, and validated GPS coordinates. "
            "No synthetic or invented figures are used."
        )
        active_sources: List[str] = ["osm", "official_census", "documented_public"]
    else:
        description = (
            "DEMO MODE: Analysis uses deterministic, reproducible simulated data designed "
            "for demonstration, planning walkthroughs, and offline testing without internet dependency."
        )
        active_sources: List[str] = ["simulated_demo", "synthetic_baseline"]

    return {
        "mode": mode,
        "description": description,
        "demo_available": True,
        "real_available": True,
        "active_sources": active_sources,
        "osrm_enabled": osrm_enabled,
        "osrm_configured": osrm_configured,
    }
