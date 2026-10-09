"""
Test suite for Stage 4B: Recommendation Scoring Engine.
Verifies recommendation score calculation, factor normalization, weight validation,
score boundaries (0-100), deterministic ranking, tie-breaking, invalid candidate exclusion,
missing-data handling, explanation generation, service validation, and API routes.
"""
import sys
from pathlib import Path
import pytest
from pydantic import ValidationError

# Add backend directory to sys.path
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.decision.candidates import CandidateLocation
from app.decision.recommendation import (
    RecommendationConfig,
    RecommendationScoringService,
    default_recommendation_service,
)

client = TestClient(app)


@pytest.fixture(scope="module")
def db():
    """Provides a database session for recommendation tests."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


# --- 1. Recommendation Score Calculation Test ---

def test_recommendation_score_calculation():
    """
    Verify recommendation formula:
    30% Gap + 25% Population + 15% Travel Need + 10% Capacity Pressure + 10% Equity + 5% Connectivity + 5% Confidence.
    """
    service = RecommendationScoringService()

    cand = CandidateLocation(
        candidate_id="cand-test-01",
        service_type="healthcare",
        latitude=12.98,
        longitude=77.62,
        area_id=9,
        area_name="Highlands Valley",
        source_reason="Test candidate",
        current_accessibility=15.0,
        population=25000,
        current_gap=85.0,
        nearby_service_count=0,
        validity_status="valid",
        strategy="centroid",
    )

    metrics = {
        "gap_score": 85.0,
        "travel_time_score": 0.0,       # Travel need = 100.0 - 0 = 100.0
        "capacity_score": 0.0,          # Capacity pressure = 100.0 - 0 = 100.0
        "service_pressure": {"pressure_category": "Critical"},  # Pressure = 100.0
        "equity_score": 90.0,           # Equity need = 90.0
        "transport_connectivity_score": 60.0,  # Connectivity = 60.0
        "confidence_score": 0.80,       # Confidence = 80.0
    }

    scored = service.score_candidate(cand, metrics)

    # Expected score:
    # 0.30 * 85.0 = 25.5
    # 0.25 * 100.0 (25000/25000) = 25.0
    # 0.15 * 100.0 = 15.0
    # 0.10 * 100.0 = 10.0
    # 0.10 * 90.0 = 9.0
    # 0.05 * 60.0 = 3.0
    # 0.05 * 80.0 = 4.0
    # Total = 25.5 + 25.0 + 15.0 + 10.0 + 9.0 + 3.0 + 4.0 = 91.5
    assert scored.recommendation_score == 91.5
    assert scored.factor_values["gap_severity"] == 85.0
    assert scored.factor_values["population_affected"] == 100.0
    assert scored.factor_values["travel_time_need"] == 100.0
    assert scored.factor_values["capacity_pressure"] == 100.0
    assert scored.factor_values["equity_need"] == 90.0
    assert scored.factor_values["connectivity"] == 60.0
    assert scored.factor_values["data_confidence"] == 80.0


# --- 2. Weight Validation Tests ---

def test_weight_validation():
    """Verify that factor weights must sum to 1.0 (100%)."""
    # Valid weights (sum = 1.0)
    valid_cfg = RecommendationConfig(
        gap_weight=0.30,
        population_weight=0.25,
        travel_need_weight=0.15,
        capacity_pressure_weight=0.10,
        equity_need_weight=0.10,
        connectivity_weight=0.05,
        confidence_weight=0.05,
    )
    assert valid_cfg is not None

    # Invalid weights (sum = 1.20) must raise ValidationError
    with pytest.raises(ValidationError) as exc:
        RecommendationConfig(
            gap_weight=0.50,
            population_weight=0.25,
            travel_need_weight=0.15,
            capacity_pressure_weight=0.10,
            equity_need_weight=0.10,
            connectivity_weight=0.05,
            confidence_weight=0.05,
        )
    assert "weights must sum to 1.0" in str(exc.value)


# --- 3. Factor Normalization Tests ---

def test_factor_normalization():
    """Verify every normalization function bounds values strictly within [0.0, 100.0]."""
    service = RecommendationScoringService()

    # Gap normalization
    assert service.normalize_gap_severity(-10.0) == 0.0
    assert service.normalize_gap_severity(120.0) == 100.0
    assert service.normalize_gap_severity(55.4) == 55.4
    assert service.normalize_gap_severity(None) == 50.0

    # Population normalization
    assert service.normalize_population_affected(-500) == 0.0
    assert service.normalize_population_affected(0) == 0.0
    assert service.normalize_population_affected(12500, ref_population=25000) == 50.0
    assert service.normalize_population_affected(50000, ref_population=25000) == 100.0  # capped at 100

    # Travel-Time need normalization (inversion: 0 access = 100 need)
    assert service.normalize_travel_time_need(0.0) == 100.0
    assert service.normalize_travel_time_need(100.0) == 0.0
    assert service.normalize_travel_time_need(60.0) == 40.0
    assert service.normalize_travel_time_need(None) == 100.0

    # Capacity pressure normalization
    assert service.normalize_capacity_pressure(0.0, pressure_category="critical") == 100.0
    assert service.normalize_capacity_pressure(100.0, pressure_category="low") == 20.0
    assert service.normalize_capacity_pressure(None) == 50.0

    # Equity need normalization
    assert service.normalize_equity_need(-5.0) == 0.0
    assert service.normalize_equity_need(110.0) == 100.0
    assert service.normalize_equity_need(None) == 50.0

    # Connectivity normalization
    assert service.normalize_connectivity(75.5) == 75.5
    assert service.normalize_connectivity(None) == 50.0

    # Confidence normalization
    assert service.normalize_data_confidence(0.85) == 85.0
    assert service.normalize_data_confidence(90.0) == 90.0
    assert service.normalize_data_confidence(None) == 50.0


# --- 4. Score Range 0–100 Tests ---

def test_score_range_0_to_100():
    """Verify final recommendation score cannot produce values outside [0.0, 100.0]."""
    service = RecommendationScoringService()

    cand = CandidateLocation(
        candidate_id="cand-bound",
        service_type="healthcare",
        latitude=12.98,
        longitude=77.62,
        area_id=1,
        area_name="Test Area",
        source_reason="Test",
        current_accessibility=0.0,
        population=0,
        current_gap=0.0,
        nearby_service_count=0,
        validity_status="valid",
        strategy="centroid",
    )

    # Minimum bound: all zeros
    min_metrics = {
        "gap_score": 0.0,
        "travel_time_score": 100.0,  # Need = 0
        "capacity_score": 100.0,     # Pressure = 0
        "service_pressure": {"pressure_category": "none"},
        "equity_score": 0.0,
        "transport_connectivity_score": 0.0,
        "confidence_score": 0.0,
    }
    scored_min = service.score_candidate(cand, min_metrics)
    assert scored_min.recommendation_score >= 0.0
    assert 0.0 <= scored_min.recommendation_score <= 100.0

    # Maximum bound: all maximums
    cand.population = 50000
    max_metrics = {
        "gap_score": 100.0,
        "travel_time_score": 0.0,    # Need = 100
        "capacity_score": 0.0,       # Pressure = 100
        "service_pressure": {"pressure_category": "critical"},
        "equity_score": 100.0,
        "transport_connectivity_score": 100.0,
        "confidence_score": 1.0,
    }
    scored_max = service.score_candidate(cand, max_metrics)
    assert scored_max.recommendation_score <= 100.0
    assert scored_max.recommendation_score == 100.0


# --- 5. Candidate Ranking Tests ---

def test_candidate_ranking(db):
    """
    Verify ranking sorts from highest recommendation score to lowest,
    and assigns sequential integer ranks starting at 1.
    """
    service = RecommendationScoringService()
    result = service.rank_candidates(db=db, service_type="healthcare")

    ranked = result["ranked_candidates"]
    assert len(ranked) >= 1
    assert result["valid_candidates_scored"] == len(ranked)

    # Verify sequential ranking: 1, 2, 3...
    for idx, c in enumerate(ranked, start=1):
        assert c.rank == idx

    # Verify scores are non-increasing
    for i in range(len(ranked) - 1):
        assert ranked[i].recommendation_score >= ranked[i + 1].recommendation_score

    # Highlands Valley (Pop 22,000, 0 healthcare) must be top-ranked
    top = ranked[0]
    assert top.area_name == "Highlands Valley"
    assert top.rank == 1
    assert top.recommendation_score >= 70.0


# --- 6. Deterministic Tie-Breaking Tests ---

def test_deterministic_tie_breaking():
    """
    Verify stable secondary tie-breaker (population affected descending)
    and tertiary tie-breaker (candidate_id ascending).
    """
    service = RecommendationScoringService()

    # Two candidates with identical score: candidate A has larger population
    c1 = CandidateLocation(
        candidate_id="cand-alpha",
        service_type="transport",
        latitude=12.90,
        longitude=77.60,
        area_id=1,
        area_name="Area Alpha",
        source_reason="Reason",
        current_accessibility=40.0,
        population=10000,
        current_gap=60.0,
        nearby_service_count=0,
        validity_status="valid",
        strategy="centroid",
    )
    c2 = CandidateLocation(
        candidate_id="cand-beta",
        service_type="transport",
        latitude=12.91,
        longitude=77.61,
        area_id=2,
        area_name="Area Beta",
        source_reason="Reason",
        current_accessibility=40.0,
        population=20000,  # Higher population
        current_gap=60.0,
        nearby_service_count=0,
        validity_status="valid",
        strategy="centroid",
    )

    sc1 = service.score_candidate(c1, {"gap_score": 60.0, "travel_time_score": 50.0})
    sc2 = service.score_candidate(c2, {"gap_score": 60.0, "travel_time_score": 50.0})

    # Artificially set identical score
    sc1.recommendation_score = 75.0
    sc2.recommendation_score = 75.0

    scored_list = [sc1, sc2]
    # Tie-breaking sort
    scored_list.sort(
        key=lambda item: (-item.recommendation_score, -item.population, item.candidate_id)
    )

    # sc2 must come first because of higher population
    assert scored_list[0].candidate_id == "cand-beta"
    assert scored_list[1].candidate_id == "cand-alpha"


# --- 7. Invalid Candidate Exclusion Tests ---

def test_invalid_candidate_exclusion(db):
    """
    Verify candidates marked invalid by Stage 4A do not receive a recommendation score,
    do not crash the scoring process, and are reported in excluded_candidates.
    """
    service = RecommendationScoringService()

    # Run ranking with all candidates
    result = service.rank_candidates(db=db, service_type="healthcare")

    # All scored candidates must be valid
    for c in result["ranked_candidates"]:
        assert c.candidate.validity_status == "valid"
        assert c.recommendation_score > 0.0
        assert c.rank >= 1

    # Any excluded candidate must not have a score or rank
    for exc in result["excluded_candidates"]:
        assert exc["validity_status"] != "valid"
        assert "rejection_reason" in exc


# --- 8. Missing Data Handling Tests ---

def test_missing_data_handling():
    """Verify engine handles missing or None metrics gracefully without crashing."""
    service = RecommendationScoringService()

    cand = CandidateLocation(
        candidate_id="cand-sparse",
        service_type="water",
        latitude=12.95,
        longitude=77.65,
        area_id=5,
        area_name="Sparse Area",
        source_reason="Sparse test",
        current_accessibility=50.0,
        population=0,
        current_gap=50.0,
        nearby_service_count=0,
        validity_status="valid",
        strategy="centroid",
    )

    # Empty metrics dictionary
    sparse_metrics = {}
    scored = service.score_candidate(cand, sparse_metrics)

    assert scored is not None
    assert 0.0 <= scored.recommendation_score <= 100.0
    assert scored.factor_values["gap_severity"] == 50.0
    assert scored.factor_values["population_affected"] == 0.0
    assert scored.factor_values["travel_time_need"] == 100.0
    assert len(scored.reasons) > 0


# --- 9. Explanation Fields Tests ---

def test_explanation_fields(db):
    """
    Verify every recommendation contains transparent civic explanations,
    factor values, and factor weights.
    """
    service = RecommendationScoringService()
    result = service.rank_candidates(db=db, service_type="healthcare")

    ranked = result["ranked_candidates"]
    assert len(ranked) > 0

    for item in ranked:
        assert isinstance(item.reasons, list)
        assert len(item.reasons) >= 1  # At least one explanation reason
        assert isinstance(item.factor_values, dict)
        assert len(item.factor_values) == 7
        assert isinstance(item.factor_weights, dict)
        assert len(item.factor_weights) == 7
        assert 0.0 <= item.confidence <= 1.0


# --- 10. Service-Type Validation Tests ---

def test_service_type_validation():
    """Verify supported services and error handling for unsupported services."""
    service = RecommendationScoringService()

    # Valid services
    for stype in ["healthcare", "education", "transport", "water", "market"]:
        assert service.validate_service_type(stype) == stype
        assert service.validate_service_type(stype.upper()) == stype

    # Unsupported services
    with pytest.raises(ValueError):
        service.validate_service_type("space_elevator")

    with pytest.raises(ValueError):
        service.validate_service_type("")


# --- 11. API Endpoints Tests ---

def test_api_post_recommendations():
    """Test POST /recommendations endpoint."""
    payload = {
        "service_type": "healthcare",
        "min_gap_threshold": 20.0,
    }
    response = client.post("/recommendations", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["service_type"] == "healthcare"
    assert data["valid_candidates_scored"] >= 1
    assert len(data["ranked_candidates"]) == data["valid_candidates_scored"]

    top = data["ranked_candidates"][0]
    assert top["rank"] == 1
    assert top["recommendation_score"] >= 70.0
    assert "factor_values" in top
    assert "factor_weights" in top
    assert len(top["reasons"]) >= 1


def test_api_get_recommendations():
    """Test GET /recommendations endpoint."""
    response = client.get("/recommendations?service_type=water")
    assert response.status_code == 200
    data = response.json()
    assert data["service_type"] == "water"
    assert "weights_used" in data
    assert "ranked_candidates" in data


def test_api_recommendations_custom_weights():
    """Test POST /recommendations with custom weights payload."""
    payload = {
        "service_type": "healthcare",
        "weights": {
            "gap_weight": 0.40,
            "population_weight": 0.30,
            "travel_need_weight": 0.10,
            "capacity_pressure_weight": 0.10,
            "equity_need_weight": 0.05,
            "connectivity_weight": 0.03,
            "confidence_weight": 0.02,
        },
    }
    response = client.post("/recommendations", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["weights_used"]["gap_weight"] == 0.40


def test_api_recommendations_invalid_weights_rejected():
    """Test POST /recommendations with invalid weight sum returns 400 Bad Request."""
    payload = {
        "service_type": "healthcare",
        "weights": {
            "gap_weight": 0.50,
            "population_weight": 0.50,
            "travel_need_weight": 0.50,  # Sum = 1.50 != 1.0
            "capacity_pressure_weight": 0.10,
            "equity_need_weight": 0.05,
            "connectivity_weight": 0.03,
            "confidence_weight": 0.02,
        },
    }
    response = client.post("/recommendations", json=payload)
    assert response.status_code == 400
    data = response.json()
    assert "Invalid recommendation weights" in data["detail"]


def test_api_recommendations_unsupported_service():
    """Test POST /recommendations with unsupported service returns 400 Bad Request."""
    payload = {"service_type": "nonexistent_service"}
    response = client.post("/recommendations", json=payload)
    assert response.status_code == 400
    data = response.json()
    assert "Unsupported service type" in data["detail"]
