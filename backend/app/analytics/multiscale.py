"""
Multi-Scale Geographic Analysis Service for CivicPulse (Stage 10).
Supports deterministic analytics across administrative scales:
- Local
- Neighbourhood
- District/Ward
- City
- Region/State
- Country
- Global

Reuses existing GeographicArea models and AnalyticsEngine.
Guarantees consistent parent-child hierarchy validation and explicit, structured
no-data responses when higher geographic scales are unavailable.
"""
from typing import List, Dict, Any, Optional, Set, Tuple
from sqlalchemy.orm import Session

from app.models import GeographicArea, ServiceCategory, Service, PopulationCell
from app.analytics.engine import default_analytics_engine
from app.analytics.distance import extract_centroid_lat_lon, haversine_distance_km
from app.schemas.multiscale import (
    GeographicHierarchyNode,
    HierarchyValidationReport,
    HierarchyRelationshipValidationResponse,
    ScopeAvailabilityItem,
    MultiScaleScopesResponse,
    MultiScaleAreaSummary,
    MultiScaleAnalyticsResponse,
)


class MultiScaleService:
    """
    Service coordinating multi-scale hierarchy navigation, parent-child validation,
    and scale-aware accessibility & gap analytics.
    """

    # Hierarchy level ranking: higher rank = higher administrative container
    LEVEL_ORDER = {
        "local": 1,
        "cell": 1,
        "neighbourhood": 2,
        "neighborhood": 2,
        "ward": 3,
        "district": 3,
        "district/ward": 3,
        "city": 4,
        "region": 5,
        "state": 5,
        "region/state": 5,
        "country": 6,
        "nation": 6,
        "global": 7,
        "world": 7,
    }

    CANONICAL_SCOPES = [
        "local",
        "neighbourhood",
        "ward",
        "city",
        "region",
        "country",
        "global",
    ]

    SCOPE_DESCRIPTIONS = {
        "local": "Fine-grained demographic census blocks and population cells",
        "neighbourhood": "Primary residential zones, communities, and neighbourhoods",
        "ward": "Electoral administrative wards and municipal districts",
        "city": "Consolidated municipal metropolitan urban boundary",
        "region": "Metropolitan regional planning authority or provincial state",
        "country": "National sovereign territory and federal infrastructure",
        "global": "International comparative indicators and cross-border standards",
    }

    def normalize_scope(self, scope: Any) -> Optional[str]:
        """Normalizes user-supplied scope alias to canonical scope name."""
        if hasattr(scope, "default"):
            scope = scope.default
        if not scope or not isinstance(scope, str):
            return None
        cleaned = scope.lower().strip().replace(" ", "_").replace("-", "_")
        if cleaned in ["district", "ward", "district/ward", "districts", "wards"]:
            return "ward"
        if cleaned in ["neighbourhood", "neighborhood", "neighbourhoods", "neighborhoods"]:
            return "neighbourhood"
        if cleaned in ["city", "metro", "municipal", "citywide"]:
            return "city"
        if cleaned in ["local", "cell", "cells", "block", "census_block"]:
            return "local"
        if cleaned in ["region", "state", "region/state", "provincial", "regional"]:
            return "region"
        if cleaned in ["country", "nation", "national"]:
            return "country"
        if cleaned in ["global", "world", "international"]:
            return "global"
        return cleaned

    # --- 1. Scope Availability Discovery ---
    def get_scope_availability(self, db: Session) -> MultiScaleScopesResponse:
        """
        Discovers data availability for all canonical scales without inventing synthetic data.
        """
        existing_types = {
            row[0].lower()
            for row in db.query(GeographicArea.area_type).distinct().all()
            if row[0]
        }
        has_cells = db.query(PopulationCell).count() > 0

        items: List[ScopeAvailabilityItem] = []
        supported: List[str] = []
        unavailable: List[str] = []

        for scope in self.CANONICAL_SCOPES:
            display_name = scope.title()
            if scope == "ward":
                display_name = "District / Ward"
            elif scope == "region":
                display_name = "Region / State"

            count = 0
            is_available = False

            if scope == "local":
                # Local scale is supported via population cells or local areas
                cell_count = db.query(PopulationCell).count()
                local_area_count = db.query(GeographicArea).filter(GeographicArea.area_type == "local").count()
                count = cell_count + local_area_count
                is_available = count > 0
            elif scope == "ward":
                count = db.query(GeographicArea).filter(
                    GeographicArea.area_type.in_(["ward", "district"])
                ).count()
                is_available = count > 0
            else:
                count = db.query(GeographicArea).filter(GeographicArea.area_type == scope).count()
                is_available = count > 0

            if is_available:
                supported.append(scope)
            else:
                unavailable.append(scope)

            items.append(
                ScopeAvailabilityItem(
                    scope=scope,
                    display_name=display_name,
                    available=is_available,
                    area_count=count,
                    description=self.SCOPE_DESCRIPTIONS.get(scope, ""),
                )
            )

        return MultiScaleScopesResponse(
            supported_scopes=supported,
            unavailable_scopes=unavailable,
            scopes=items,
        )

    # --- 2. Parent-Child Geographic Relationship Validation ---
    def validate_relationship_types(
        self, parent_type: Optional[str], child_type: Optional[str]
    ) -> Tuple[bool, str]:
        """
        Validates whether a child area type can logically exist within a parent area type.
        """
        if not parent_type or not child_type:
            return False, "Both parent_type and child_type must be specified"

        p_norm = self.normalize_scope(parent_type)
        c_norm = self.normalize_scope(child_type)

        p_rank = self.LEVEL_ORDER.get(p_norm)
        c_rank = self.LEVEL_ORDER.get(c_norm)

        if p_rank is None:
            return False, f"Unrecognized parent administrative scale: '{parent_type}'"
        if c_rank is None:
            return False, f"Unrecognized child administrative scale: '{child_type}'"

        if c_rank >= p_rank:
            return (
                False,
                f"Invalid hierarchy order: child scale '{child_type}' (level {c_rank}) cannot contain or be parent to '{parent_type}' (level {p_rank}). Child must have strictly lower scale.",
            )

        return (
            True,
            f"Valid hierarchy relationship: '{child_type}' (level {c_rank}) can be nested under '{parent_type}' (level {p_rank}).",
        )

    def validate_hierarchy_integrity(self, db: Session) -> HierarchyValidationReport:
        """
        Thoroughly audits the entire geographic database to verify:
        - Parent existence (no orphaned foreign keys).
        - Hierarchy scale ordering (parent has higher scale rank than child).
        - Absence of circular loops or self-referential links.
        """
        areas = db.query(GeographicArea).all()
        area_map = {a.id: a for a in areas}

        errors: List[str] = []
        valid_count = 0
        orphan_count = 0
        circular_count = 0
        root_count = 0
        levels_found: Set[str] = set()

        for a in areas:
            levels_found.add(a.area_type)
            if a.parent_id is None:
                root_count += 1
                continue

            # Check 1: Parent exists
            parent = area_map.get(a.parent_id)
            if not parent:
                orphan_count += 1
                errors.append(
                    f"Area '{a.name}' (id={a.id}) has invalid parent_id={a.parent_id} (not found in database)"
                )
                continue

            # Check 2: Direct self-reference
            if a.parent_id == a.id:
                circular_count += 1
                errors.append(f"Area '{a.name}' (id={a.id}) has self-referential parent_id={a.id}")
                continue

            # Check 3: Circular chain detection
            visited = {a.id}
            curr = parent
            has_loop = False
            while curr and curr.parent_id is not None:
                if curr.parent_id in visited:
                    has_loop = True
                    circular_count += 1
                    errors.append(
                        f"Circular hierarchy cycle detected: area id={curr.parent_id} loops back through id={curr.id}"
                    )
                    break
                visited.add(curr.id)
                curr = area_map.get(curr.parent_id)

            if has_loop:
                continue

            # Check 4: Hierarchy ordering
            valid_rel, rel_msg = self.validate_relationship_types(parent.area_type, a.area_type)
            if not valid_rel:
                errors.append(
                    f"Hierarchy scale mismatch between child '{a.name}' ({a.area_type}) and parent '{parent.name}' ({parent.area_type}): {rel_msg}"
                )
                continue

            valid_count += 1

        # Calculate max depth
        max_depth = 1
        for a in areas:
            depth = 1
            curr = a
            while curr and curr.parent_id is not None:
                curr = area_map.get(curr.parent_id)
                if curr:
                    depth += 1
            if depth > max_depth:
                max_depth = depth

        is_valid = len(errors) == 0

        return HierarchyValidationReport(
            status="valid" if is_valid else "invalid",
            is_valid=is_valid,
            total_areas=len(areas),
            root_areas_count=root_count,
            max_depth=max_depth,
            levels_found=sorted(list(levels_found)),
            valid_relationships_count=valid_count,
            orphan_count=orphan_count,
            circular_references_count=circular_count,
            errors=errors,
        )

    # --- 3. Hierarchy Tree Builder ---
    def build_hierarchy_tree(self, db: Session) -> List[GeographicHierarchyNode]:
        """
        Builds a recursive tree representation of the administrative hierarchy
        from top-level root areas down to leaf units.
        """
        areas = db.query(GeographicArea).all()
        nodes: Dict[int, GeographicHierarchyNode] = {}

        for a in areas:
            nodes[a.id] = GeographicHierarchyNode(
                id=a.id,
                name=a.name,
                area_type=a.area_type,
                population=int(a.population),
                parent_id=a.parent_id,
                children=[],
            )

        root_nodes: List[GeographicHierarchyNode] = []
        for a in areas:
            node = nodes[a.id]
            if a.parent_id and a.parent_id in nodes:
                nodes[a.parent_id].children.append(node)
            else:
                root_nodes.append(node)

        return root_nodes

    # --- 4. Multi-Scale Analytics Aggregation ---
    def analyze_scope(
        self,
        db: Session,
        scope: str,
        category_code: Optional[str] = None,
    ) -> MultiScaleAnalyticsResponse:
        """
        Executes scope-aware analysis reusing the existing analytics engine.
        Returns explicit structured no-data response for unavailable scopes.
        """
        norm_scope = self.normalize_scope(scope)
        if not norm_scope or norm_scope not in self.LEVEL_ORDER:
            return MultiScaleAnalyticsResponse(
                scope=scope,
                available=False,
                status="no_data",
                message=f"Unsupported geographic scale '{scope}'. Supported scales: {', '.join(self.CANONICAL_SCOPES)}",
                total_areas=0,
                total_population=0,
                areas=[],
            )

        # Handle unavailable higher scales explicitly
        if norm_scope in ["region", "country", "global"]:
            return MultiScaleAnalyticsResponse(
                scope=norm_scope,
                available=False,
                status="no_data",
                message=(
                    f"Geographic scale '{norm_scope}' is unavailable in the current municipal dataset. "
                    f"No official data exists at the {norm_scope.title()} tier. "
                    f"Supported active scales: local, neighbourhood, ward, city."
                ),
                total_areas=0,
                total_population=0,
                average_accessibility=None,
                average_gap=None,
                coverage_pct=None,
                areas=[],
                is_demo_data=True,
                label=f"Multi-Scale Analysis - {norm_scope.title()} Scale Unavailable",
            )

        # Retrieve areas corresponding to requested scope
        if norm_scope == "ward":
            areas = db.query(GeographicArea).filter(
                GeographicArea.area_type.in_(["ward", "district"])
            ).order_by(GeographicArea.id).all()
        elif norm_scope == "city":
            areas = db.query(GeographicArea).filter(
                GeographicArea.area_type == "city"
            ).order_by(GeographicArea.id).all()
        elif norm_scope == "neighbourhood":
            areas = db.query(GeographicArea).filter(
                GeographicArea.area_type == "neighbourhood"
            ).order_by(GeographicArea.id).all()
        elif norm_scope == "local":
            # Local scale: evaluate local population cells
            cells = db.query(PopulationCell).order_by(PopulationCell.id).all()
            if not cells:
                return MultiScaleAnalyticsResponse(
                    scope="local",
                    available=False,
                    status="no_data",
                    message="No local population cells or census blocks available.",
                    total_areas=0,
                    total_population=0,
                    areas=[],
                )

            # Analyze local population cells
            local_summaries: List[MultiScaleAreaSummary] = []
            total_pop = 0
            weighted_access = 0.0

            for cell in cells:
                parent_area = db.query(GeographicArea).filter_by(id=cell.area_id).first()
                p_name = parent_area.name if parent_area else f"Area {cell.area_id}"

                # Local cell accessibility: evaluate using parent area or cell coordinates
                if parent_area:
                    cell_analytics = default_analytics_engine.analyze_area_overall(db, parent_area)
                    access = float(cell_analytics["composite_accessibility_score"])
                    gap = float(cell_analytics["composite_gap_score"])
                    desert = cell_analytics["composite_desert_classification"]
                else:
                    access = 50.0
                    gap = 50.0
                    desert = "At Risk"

                pop = int(cell.population or 0)
                total_pop += pop
                weighted_access += access * pop

                local_summaries.append(
                    MultiScaleAreaSummary(
                        area_id=cell.id,
                        name=f"Cell {cell.id} ({p_name})",
                        area_type="local",
                        population=pop,
                        parent_id=cell.area_id,
                        parent_name=p_name,
                        accessibility_score=access,
                        gap_score=gap,
                        desert_classification=desert,
                        child_count=0,
                    )
                )

            avg_access = round(weighted_access / max(1, total_pop), 1)
            avg_gap = round(100.0 - avg_access, 1)

            return MultiScaleAnalyticsResponse(
                scope="local",
                available=True,
                status="success",
                message=f"Evaluated {len(cells)} local population cell units",
                total_areas=len(cells),
                total_population=total_pop,
                average_accessibility=avg_access,
                average_gap=avg_gap,
                coverage_pct=round(avg_access, 1),
                areas=local_summaries,
                is_demo_data=True,
                label="Multi-Scale Geographic Analysis - Local Cells",
            )
        else:
            areas = db.query(GeographicArea).filter(
                GeographicArea.area_type == norm_scope
            ).order_by(GeographicArea.id).all()

        if not areas:
            return MultiScaleAnalyticsResponse(
                scope=norm_scope,
                available=False,
                status="no_data",
                message=f"No geographic areas found matching scale '{norm_scope}'",
                total_areas=0,
                total_population=0,
                areas=[],
            )

        # Compute metrics across areas for this scale
        area_summaries: List[MultiScaleAreaSummary] = []
        total_pop = 0
        weighted_access = 0.0
        covered_pop = 0

        for a in areas:
            summary = default_analytics_engine.analyze_area_overall(db, a)
            access = float(summary["composite_accessibility_score"])
            gap = float(summary["composite_gap_score"])
            desert = summary["composite_desert_classification"]

            child_count = db.query(GeographicArea).filter_by(parent_id=a.id).count()
            parent = db.query(GeographicArea).filter_by(id=a.parent_id).first() if a.parent_id else None

            pop = int(a.population)
            total_pop += pop
            weighted_access += access * pop

            if access >= 60.0 or desert in ["Well Served", "Adequate"]:
                covered_pop += pop

            area_summaries.append(
                MultiScaleAreaSummary(
                    area_id=a.id,
                    name=a.name,
                    area_type=a.area_type,
                    population=pop,
                    parent_id=a.parent_id,
                    parent_name=parent.name if parent else None,
                    accessibility_score=access,
                    gap_score=gap,
                    desert_classification=desert,
                    child_count=child_count,
                )
            )

        avg_access = round(weighted_access / max(1, total_pop), 1)
        avg_gap = round(100.0 - avg_access, 1)
        cov_pct = round((covered_pop / max(1, total_pop)) * 100.0, 1)

        return MultiScaleAnalyticsResponse(
            scope=norm_scope,
            available=True,
            status="success",
            message=f"Evaluated {len(areas)} areas at {norm_scope.title()} scale",
            total_areas=len(areas),
            total_population=total_pop,
            average_accessibility=avg_access,
            average_gap=avg_gap,
            coverage_pct=cov_pct,
            areas=area_summaries,
            is_demo_data=True,
            label=f"Multi-Scale Geographic Analysis - {norm_scope.title()} Level",
        )


default_multiscale_service = MultiScaleService()
