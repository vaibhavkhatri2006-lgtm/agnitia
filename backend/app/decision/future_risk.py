"""
Future-Risk Foundation Engine (Stage 4D Task 3) for CivicPulse.
Calculates deterministic projections of demand growth and evaluates emerging civic risk.
Explicitly labeled as a demo estimate for planning exploration.
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models import GeographicArea, ServiceCategory, Service
from app.analytics.engine import default_analytics_engine, AnalyticsEngine
from app.analytics.distance import extract_centroid_lat_lon, haversine_distance_km


class FutureRiskService:
    """
    Computes deterministic forward-looking civic risk projections.
    Simulates demand growth over a planning horizon and evaluates capacity degradation.
    """

    SUPPORTED_SERVICES = [
        "healthcare",
        "education",
        "transport",
        "water",
        "market",
    ]

    def __init__(self, analytics_engine: Optional[AnalyticsEngine] = None):
        self.analytics = analytics_engine or default_analytics_engine

    def classify_risk(self, risk_score: float) -> str:
        """Categorizes continuous 0-100 risk score into standard planning risk tiers."""
        if risk_score >= 75.0:
            return "Critical Risk"
        if risk_score >= 55.0:
            return "High Risk"
        if risk_score >= 35.0:
            return "Moderate Risk"
        return "Low Risk"

    def estimate_future_risk(
        self,
        db: Session,
        growth_rate_pct: float = 15.0,
        time_horizon_years: int = 5,
        service_type: Optional[str] = None,
        area_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Calculates future civic risk under configurable demand growth.
        Deterministic, transparent, and labeled as a demo planning estimate.
        """
        # Input validations
        if not (0.0 <= growth_rate_pct <= 100.0):
            raise ValueError("Growth rate must be between 0.0 and 100.0 percent")

        if not (1 <= time_horizon_years <= 30):
            raise ValueError("Time horizon must be between 1 and 30 years")

        if service_type:
            norm_type = service_type.strip().lower()
            if norm_type not in self.SUPPORTED_SERVICES:
                raise ValueError(
                    f"Unsupported service type '{service_type}'. Supported services: {', '.join(self.SUPPORTED_SERVICES)}"
                )
            category = db.query(ServiceCategory).filter_by(code=norm_type).first()
            if not category:
                raise ValueError(f"Category '{norm_type}' not found")
            categories = [category]
        else:
            categories = db.query(ServiceCategory).filter_by(is_active=True).all()

        # Resolve areas
        if area_id is not None:
            area = db.query(GeographicArea).filter_by(id=area_id).first()
            if not area:
                raise ValueError(f"Geographic area with ID {area_id} not found")
            areas = [area]
        else:
            areas = (
                db.query(GeographicArea)
                .filter_by(area_type="neighbourhood")
                .order_by(GeographicArea.id)
                .all()
            )
            if not areas:
                areas = db.query(GeographicArea).order_by(GeographicArea.id).all()

        area_risk_items: List[Dict[str, Any]] = []
        total_pop = sum(a.population for a in areas) or 1
        weighted_current_risk = 0.0
        weighted_projected_risk = 0.0

        for area in areas:
            cur_pop = area.population
            proj_pop = int(round(cur_pop * (1.0 + growth_rate_pct / 100.0)))

            if area.geometry:
                c_lat, c_lon = extract_centroid_lat_lon(area.geometry)
            else:
                c_lat, c_lon = 12.9716, 77.5946

            area_cat_current_risks = []
            area_cat_projected_risks = []
            primary_vulns = []
            worst_cap_status = "Adequate"

            for cat in categories:
                # Find nearest service in catchment
                services = db.query(Service).filter_by(category_id=cat.id).all()
                nearest_svc: Optional[Service] = None
                min_dist = float("inf")
                for svc in services:
                    dist = haversine_distance_km(c_lat, c_lon, svc.latitude, svc.longitude)
                    if dist <= self.analytics.config.max_catchment_distance_km and dist < min_dist:
                        min_dist = dist
                        nearest_svc = svc

                cur_metrics = self.analytics.analyze_area_category(db, area, cat)
                cur_gap = cur_metrics["gap_score"]

                p_cur = self.analytics.calculate_capacity_and_pressure(nearest_svc, demand_population=cur_pop)
                p_proj = self.analytics.calculate_capacity_and_pressure(nearest_svc, demand_population=proj_pop)

                ratio_cur = min(p_cur["pressure_ratio"], 3.0)
                ratio_proj = min(p_proj["pressure_ratio"], 3.0)

                # Current & Projected Risk for category
                c_risk = round(min(100.0, max(0.0, (cur_gap * 0.60) + (ratio_cur / 3.0 * 40.0))), 1)
                p_risk = round(min(100.0, max(0.0, (cur_gap * 0.55) + (ratio_proj / 3.0 * 45.0))), 1)

                area_cat_current_risks.append(c_risk)
                area_cat_projected_risks.append(p_risk)

                if p_proj["pressure_category"] == "Critical":
                    worst_cap_status = "Critical"
                    primary_vulns.append(f"{cat.name} capacity severely overloaded under future demand")
                elif p_proj["pressure_category"] == "High" and worst_cap_status != "Critical":
                    worst_cap_status = "High"
                    primary_vulns.append(f"{cat.name} capacity approaching saturation")
                elif nearest_svc is None:
                    primary_vulns.append(f"No existing {cat.name} facility in catchment")

            avg_cur_area_risk = round(sum(area_cat_current_risks) / len(area_cat_current_risks), 1)
            avg_proj_area_risk = round(sum(area_cat_projected_risks) / len(area_cat_projected_risks), 1)
            area_risk_delta = round(max(0.0, avg_proj_area_risk - avg_cur_area_risk), 1)

            weighted_current_risk += avg_cur_area_risk * cur_pop
            weighted_projected_risk += avg_proj_area_risk * cur_pop

            primary_vuln_text = primary_vulns[0] if primary_vulns else "Gradual demand growth against existing infrastructure"

            area_risk_items.append({
                "area_id": area.id,
                "area_name": area.name,
                "current_population": cur_pop,
                "projected_population": proj_pop,
                "current_risk_score": avg_cur_area_risk,
                "projected_risk_score": avg_proj_area_risk,
                "risk_increase": area_risk_delta,
                "current_risk_category": self.classify_risk(avg_cur_area_risk),
                "projected_risk_category": self.classify_risk(avg_proj_area_risk),
                "capacity_status": worst_cap_status,
                "primary_vulnerability": primary_vuln_text,
            })

        systemic_current_risk = round(weighted_current_risk / total_pop, 1)
        systemic_projected_risk = round(weighted_projected_risk / total_pop, 1)
        net_risk_increase = round(max(0.0, systemic_projected_risk - systemic_current_risk), 1)

        current_risk_cat = self.classify_risk(systemic_current_risk)
        projected_risk_cat = self.classify_risk(systemic_projected_risk)

        if net_risk_increase >= 8.0 or systemic_projected_risk >= 70.0:
            risk_trend = "Accelerating Deficit"
        elif net_risk_increase >= 3.0:
            risk_trend = "Growing Pressure"
        else:
            risk_trend = "Stable"

        vulnerability_factors = [
            f"{growth_rate_pct:.1f}% population demand expansion over {time_horizon_years}-year planning horizon",
            "Depletion of municipal capacity headroom in high-density corridors",
            "Compounding risk in unserviced peripheral neighbourhoods",
        ]

        disclaimer = (
            f"Demo estimate for strategic planning only. Projections model uniform {growth_rate_pct:.1f}% "
            f"population demand increase over {time_horizon_years} years without compensatory facility additions."
        )

        return {
            "service_type": service_type,
            "growth_rate_pct": growth_rate_pct,
            "time_horizon_years": time_horizon_years,
            "evaluated_areas_count": len(areas),
            "current_risk_score": systemic_current_risk,
            "projected_risk_score": systemic_projected_risk,
            "risk_increase": net_risk_increase,
            "current_risk_category": current_risk_cat,
            "projected_risk_category": projected_risk_cat,
            "risk_trend": risk_trend,
            "areas_at_risk": area_risk_items,
            "vulnerability_factors": vulnerability_factors,
            "is_demo_estimate": True,
            "label": "Demo Estimate - Deterministic Future Risk Foundation",
            "disclaimer": disclaimer,
        }


# Singleton future risk service
default_future_risk_service = FutureRiskService()
