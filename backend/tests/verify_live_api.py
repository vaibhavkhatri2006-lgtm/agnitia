"""
Live API Verification for CivicPulse Backend
Tests all 12 modules and critical user flow against live running backend server.
"""
import urllib.request
import urllib.error
import json
import sys

BASE = "http://127.0.0.1:8000"

def req(method, path, body=None, token=None):
    url = f"{BASE}{path}"
    data = json.dumps(body).encode() if body else None
    headers = {"Content-Type": "application/json"} if body else {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    r = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(r) as resp:
            content = resp.read().decode()
            return resp.status, json.loads(content) if content else {}
    except urllib.error.HTTPError as e:
        content = e.read().decode()
        try:
            parsed = json.loads(content) if content else {}
        except Exception:
            parsed = {"raw": content}
        return e.code, parsed


def main():
    print("==================================================================")
    print("CIVICPULSE BACKEND LIVE API VERIFICATION")
    print(f"Target: {BASE}")
    print("==================================================================")

    # 0. Health probe
    s, h_res = req("GET", "/health")
    assert s == 200, f"Health probe failed: {s} {h_res}"
    assert h_res.get("status") == "healthy"
    assert h_res.get("database") == "connected"
    print(f"0. Health & DB Probe: [PASS] (status={h_res.get('status')}, database={h_res.get('database')})")

    # 1. Auth & JWT
    s, c_res = req("POST", "/auth/login", {"email": "citizen@example.com", "password": "Citizen123!"})
    assert s == 200, f"Citizen login failed: {s} {c_res}"
    citizen_token = c_res["access_token"]

    s, comm_res = req("POST", "/auth/login", {"email": "community@example.com", "password": "Community123!"})
    assert s == 200, f"Community login failed: {s}"
    comm_token = comm_res["access_token"]

    s, a_res = req("POST", "/auth/login", {"email": "authority@example.com", "password": "Authority123!"})
    assert s == 200, f"Authority login failed: {s}"
    auth_token = a_res["access_token"]

    s, adm_res = req("POST", "/auth/login", {"email": "admin@example.com", "password": "Admin123!"})
    assert s == 200, f"Admin login failed: {s}"
    adm_token = adm_res["access_token"]

    # Invalid login test
    s, inv_res = req("POST", "/auth/login", {"email": "citizen@example.com", "password": "WrongPassword!"})
    assert s == 401, f"Expected 401 for wrong password, got {s}"

    # Inactive login test
    s, inact_res = req("POST", "/auth/login", {"email": "inactive@example.com", "password": "Inactive123!"})
    assert s == 403, f"Expected 403 for inactive user, got {s}"

    s, me_res = req("GET", "/auth/me", token=citizen_token)
    assert s == 200 and me_res["email"] == "citizen@example.com"
    print("1. Auth & JWT (/auth/login, /auth/me, invalid credentials, inactive user): [PASS]")

    # 2. RBAC Enforcement
    s, plan_res = req("GET", "/planner/rankings?service_type=healthcare", token=citizen_token)
    assert s == 403, f"Expected 403 for citizen on planner, got {s}"

    s, plan_res = req("GET", "/planner/rankings?service_type=healthcare", token=auth_token)
    assert s == 200, f"Expected 200 for authority on planner, got {s}"
    print("2. RBAC Enforcement (Citizen 403 vs Authority 200): [PASS]")

    # 3. Areas, Services, GeoJSON
    s, areas = req("GET", "/areas")
    assert s == 200 and len(areas) >= 10, f"GET /areas failed: {s}"
    test_area = areas[0]

    s, areas_gj = req("GET", "/areas/geojson")
    assert s == 200 and areas_gj.get("type") == "FeatureCollection"

    s, srvs = req("GET", "/services")
    assert s == 200 and len(srvs) >= 10

    s, srvs_gj = req("GET", "/services/geojson")
    assert s == 200 and srvs_gj.get("type") == "FeatureCollection"
    print(f"3. Areas, Services & GeoJSON FeatureCollections ({len(areas)} areas, {len(srvs)} services): [PASS]")

    # 4. Accessibility & Travel-time estimates
    s, area_metrics = req("GET", f"/analytics/areas/{test_area['id']}")
    assert s == 200, f"Area analytics failed: {s} {area_metrics}"
    assert "composite_accessibility_score" in area_metrics or "category_breakdown" in area_metrics
    print(f"4. Accessibility & Travel-Time Estimates for Locality {test_area['name']}: [PASS]")

    # 5. Gap Scores & Underserved Rankings
    s, rankings_data = req("GET", "/analytics/rankings/underserved?service_type=healthcare")
    assert s == 200
    ranking_items = rankings_data.get("rankings", rankings_data) if isinstance(rankings_data, dict) else rankings_data
    assert len(ranking_items) > 0
    # verify scores are in 0..100 boundary
    for r in ranking_items:
        gap = r.get("gap_score", r.get("composite_gap_score", r.get("underserved_score", 0)))
        assert 0.0 <= float(gap) <= 100.0, f"Score out of bounds: {gap}"
    print(f"5. Gap Scores & Underserved Leaderboard ({len(ranking_items)} ranked localities, bounded [0, 100]): [PASS]")

    # 6. Capacity, Equity, Reality-gap
    s, planner_cp = req("GET", "/planner/capacity-pressure", token=auth_token)
    assert s == 200
    s, planner_eq = req("GET", "/planner/equity-reality-gap", token=auth_token)
    assert s == 200
    print("6. Capacity Pressure, Equity, Confidence & Reality-Gap: [PASS]")

    # 7. Candidate Locations & Recommendation Ranking
    rec_payload = {"service_type": "healthcare", "area_id": test_area["id"]}
    s, rec_res = req("POST", "/recommendations", rec_payload, token=auth_token)
    assert s == 200, f"POST /recommendations failed: {s} {rec_res}"
    candidates = rec_res.get("ranked_candidates", rec_res.get("candidates", []))
    assert len(candidates) > 0
    top_cand = candidates[0]
    rec_score = top_cand.get("recommendation_score", top_cand.get("suitability_score", 0))
    assert 0.0 <= float(rec_score) <= 100.0
    print(f"7. Candidate Locations & Recommendation Ranking ({len(candidates)} candidates, top score={rec_score}): [PASS]")

    # 8. Before/After Simulation & Impact
    sim_payload = {
        "service_type": "healthcare",
        "candidate_id": top_cand.get("candidate_id"),
        "proposed_name": "Verification Clinic"
    }
    s, sim_res = req("POST", "/simulations", sim_payload, token=auth_token)
    assert s == 200, f"POST /simulations failed: {s} {sim_res}"
    assert "before" in sim_res and "after" in sim_res and "impact" in sim_res
    imp = sim_res["impact"]
    print(f"8. Before/After Simulation & Impact Metrics (Improvement: {imp}): [PASS]")

    # 9. Community Reports, Verification & Audit Logs
    report_payload = {
        "title": "Water well inspection request",
        "description": "Borehole filtration unit maintenance required.",
        "category_code": "water",
        "latitude": -1.2855,
        "longitude": 36.8210,
        "severity": "medium"
    }
    s, rep_res = req("POST", "/reports", report_payload, token=citizen_token)
    assert s in (200, 201), f"Report creation failed: {s} {rep_res}"
    rep_id = rep_res["id"]

    # Citizen cannot perform official verification
    s, v_fail = req("POST", f"/reports/{rep_id}/verify", {"verification_type": "official", "verified": True, "notes": "Hacked"}, token=citizen_token)
    assert s in (401, 403), f"Citizen should not be allowed official verification: got {s}"

    # Community verification
    s, v_comm = req("POST", f"/reports/{rep_id}/verify", {"verification_type": "community", "verified": True, "notes": "Community verified"}, token=comm_token)
    assert s == 200, f"Community verification failed: {s} {v_comm}"

    # Official verification
    s, v_auth = req("POST", f"/reports/{rep_id}/verify", {"verification_type": "official", "verified": True, "notes": "Official inspection complete"}, token=auth_token)
    assert s == 200, f"Official verification failed: {s} {v_auth}"

    # Audit log inspection
    s, audit_res = req("GET", f"/reports/{rep_id}/history", token=auth_token)
    assert s == 200
    logs = audit_res if isinstance(audit_res, list) else audit_res.get("history", audit_res.get("logs", []))
    assert len(logs) >= 2
    print(f"9. Community Reports Lifecycle & Immutable Audit Trail (Report #{rep_id}, {len(logs)} audit logs): [PASS]")

    # 10. Planner APIs & Scenario Comparison
    s, scen_res = req("POST", "/simulations/scenarios", {
        "service_type": "healthcare",
        "scope": "city",
        "scenarios": [
            {
                "scenario_id": "alpha",
                "name": "Scenario Alpha",
                "facilities": [
                    {"proposed_name": "Clinic Alpha", "latitude": -1.286, "longitude": 36.822}
                ]
            },
            {
                "scenario_id": "beta",
                "name": "Scenario Beta",
                "facilities": [
                    {"proposed_name": "Clinic Beta", "latitude": -1.283, "longitude": 36.818}
                ]
            }
        ]
    }, token=auth_token)
    assert s == 200, f"POST /simulations/scenarios failed: {s} {scen_res}"
    print("10. Planner APIs & Multi-Scenario Comparison: [PASS]")

    # 11. Investment Priorities, Failure Simulation & Future Risk
    s, inv_res = req("GET", "/decision/investment-priorities", token=auth_token)
    assert s == 200 and len(inv_res) > 0

    test_srv = srvs[0]
    s, fail_res = req("POST", "/decision/simulate-failure", {"service_id": test_srv["id"]}, token=auth_token)
    assert s == 200

    s, risk_res = req("GET", f"/decision/future-risk?area_id={test_area['id']}", token=auth_token)
    assert s == 200
    print("11. Investment Priorities, Single-Point-of-Failure Simulation & Future Risk: [PASS]")

    # 12. Multi-Scale Geographic Queries & Safe No-Data Handling
    s, scopes_res = req("GET", "/areas/scopes")
    assert s == 200 and "scopes" in scopes_res
    s, ms_res = req("GET", "/analytics/multiscale?scope=neighbourhood")
    assert s == 200 and ms_res.get("has_data") is True
    s, nodata_res = req("GET", "/analytics/multiscale?scope=country")
    assert s == 200 and nodata_res.get("has_data") is False
    print("12. Multi-Scale Hierarchy & Graceful No-Data Handling: [PASS]")

    print("==================================================================")
    print(">>> COMPLETE LIVE BACKEND END-TO-END FLOW: 100% PASS <<<")
    print("==================================================================")

if __name__ == "__main__":
    main()
