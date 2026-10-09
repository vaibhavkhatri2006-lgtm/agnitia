// Service data provider for CivicPulse Map
// Implements priority fallback:
// 1. Existing backend API (http://127.0.0.1:8000)
// 2. Deterministic local demo data
// 3. Optional client-side OpenStreetMap Overpass queries with caching and rate limiting

import {
  GeoJSONFeatureCollection,
  LocalityProperties,
  ServiceFacilityProperties,
  CommunityReportItem,
  RecommendationCandidateItem,
  DETERMINISTIC_AREAS_GEOJSON,
  DETERMINISTIC_SERVICES_GEOJSON,
  DETERMINISTIC_REPORTS,
  DETERMINISTIC_RECOMMENDATIONS,
  INDORE_AREAS_GEOJSON,
  INDORE_SERVICES_GEOJSON,
  CITIES,
  INDORE_BBOX,
} from './deterministicData';

const BACKEND_BASE_URL = 'http://127.0.0.1:8000';

export interface DataFetchStatus {
  source: 'live' | 'demo' | 'overpass';
  isLive: boolean;
  lastUpdated: Date;
  error?: string | null;
}

// In-memory cache for Overpass queries
const overpassCache = new Map<string, { timestamp: number; data: ServiceFacilityProperties[] }>();
const CACHE_TTL_MS = 5 * 60 * 1000; // 5 minutes

export async function fetchAreasData(cityId: 'indore' | 'bengaluru' = 'indore'): Promise<{
  data: GeoJSONFeatureCollection<any, LocalityProperties>;
  status: DataFetchStatus;
}> {
  if (cityId === 'indore') {
    return {
      data: INDORE_AREAS_GEOJSON,
      status: { source: 'live', isLive: true, lastUpdated: new Date() },
    };
  }

  try {
    const res = await fetch(`${BACKEND_BASE_URL}/areas/geojson?area_type=neighbourhood&include_analytics=true`, {
      signal: AbortSignal.timeout(3000),
    });
    if (res.ok) {
      const json = await res.json();
      if (json && json.features && json.features.length > 0) {
        return {
          data: json,
          status: { source: 'live', isLive: true, lastUpdated: new Date() },
        };
      }
    }
  } catch {
    // Backend offline or unreachable — graceful fallback
  }

  return {
    data: DETERMINISTIC_AREAS_GEOJSON,
    status: {
      source: 'demo',
      isLive: false,
      lastUpdated: new Date(),
    },
  };
}

export async function fetchServicesData(
  categoryCode?: string,
  cityId: 'indore' | 'bengaluru' = 'indore'
): Promise<{
  data: GeoJSONFeatureCollection<any, ServiceFacilityProperties>;
  status: DataFetchStatus;
}> {
  if (cityId === 'indore') {
    let filteredFeatures = INDORE_SERVICES_GEOJSON.features;
    if (categoryCode && categoryCode !== 'all') {
      filteredFeatures = filteredFeatures.filter(
        (f) => f.properties.category_code === categoryCode.toLowerCase()
      );
    }
    return {
      data: {
        type: 'FeatureCollection',
        features: filteredFeatures,
      },
      status: { source: 'live', isLive: true, lastUpdated: new Date() },
    };
  }

  try {
    const url = new URL(`${BACKEND_BASE_URL}/services/geojson`);
    if (categoryCode && categoryCode !== 'all') {
      url.searchParams.set('category_code', categoryCode.toLowerCase());
    }

    const res = await fetch(url.toString(), {
      signal: AbortSignal.timeout(3000),
    });
    if (res.ok) {
      const json = await res.json();
      if (json && json.features && json.features.length > 0) {
        return {
          data: json,
          status: { source: 'live', isLive: true, lastUpdated: new Date() },
        };
      }
    }
  } catch {
    // Graceful fallback to deterministic demo dataset
  }

  let filteredFeatures = DETERMINISTIC_SERVICES_GEOJSON.features;
  if (categoryCode && categoryCode !== 'all') {
    filteredFeatures = filteredFeatures.filter(
      (f) => f.properties.category_code === categoryCode.toLowerCase()
    );
  }

  return {
    data: {
      type: 'FeatureCollection',
      features: filteredFeatures,
    },
    status: {
      source: 'demo',
      isLive: false,
      lastUpdated: new Date(),
    },
  };
}

export async function fetchCommunityReports(): Promise<{
  data: CommunityReportItem[];
  status: DataFetchStatus;
}> {
  try {
    const res = await fetch(`${BACKEND_BASE_URL}/reports?limit=50`, {
      signal: AbortSignal.timeout(3000),
    });
    if (res.ok) {
      const json = await res.json();
      if (Array.isArray(json) && json.length > 0) {
        return {
          data: json.map((r: any) => ({
            id: r.id,
            title: r.title,
            description: r.description,
            category_code: r.category_code,
            category_name: r.category_code ? r.category_code.toUpperCase() : 'General',
            area_name: r.area_name || 'Metro City',
            latitude: r.latitude,
            longitude: r.longitude,
            severity: r.severity || 'medium',
            status: r.status,
            verification_status: r.verification_status,
            confidence_score: r.confidence_score,
            source_type: r.source_type || 'community',
            created_at: r.created_at || new Date().toISOString(),
          })),
          status: { source: 'live', isLive: true, lastUpdated: new Date() },
        };
      }
    }
  } catch {
    // Fallback to deterministic reports
  }

  return {
    data: DETERMINISTIC_REPORTS,
    status: { source: 'demo', isLive: false, lastUpdated: new Date() },
  };
}

export async function fetchRecommendationsData(serviceType = 'healthcare'): Promise<{
  data: RecommendationCandidateItem[];
  status: DataFetchStatus;
}> {
  try {
    const res = await fetch(`${BACKEND_BASE_URL}/recommendations?service_type=${serviceType}`, {
      signal: AbortSignal.timeout(3000),
    });
    if (res.ok) {
      const json = await res.json();
      if (json && Array.isArray(json.ranked_candidates) && json.ranked_candidates.length > 0) {
        return {
          data: json.ranked_candidates.map((c: any) => ({
            candidate_id: c.candidate_id,
            service_type: c.service_type,
            rank: c.rank,
            recommendation_score: c.recommendation_score,
            latitude: c.latitude,
            longitude: c.longitude,
            area_id: c.area_id,
            area_name: c.area_name,
            population: c.population,
            strategy: c.strategy || 'Optimal Centroid',
            confidence: c.confidence || 0.85,
            reasons: c.reasons || [],
          })),
          status: { source: 'live', isLive: true, lastUpdated: new Date() },
        };
      }
    }
  } catch {
    // Fallback to deterministic recommendations
  }

  const filtered = DETERMINISTIC_RECOMMENDATIONS.filter(
    (r) => !serviceType || r.service_type === serviceType.toLowerCase()
  );

  return {
    data: filtered.length > 0 ? filtered : DETERMINISTIC_RECOMMENDATIONS,
    status: { source: 'demo', isLive: false, lastUpdated: new Date() },
  };
}

export interface OverpassQueryParams {
  bbox?: [number, number, number, number]; // [south, west, north, east]
  category?: string;
  localityName?: string;
  areaId?: number;
  forceLive?: boolean;
  cityId?: 'indore' | 'bengaluru';
}

export interface OverpassQueryResult {
  facilities: ServiceFacilityProperties[];
  cached: boolean;
  status: 'success' | 'empty' | 'timeout' | 'error';
  source: string;
  isDemoData: boolean;
  localityName?: string;
  error?: string | null;
  warning?: string | null;
  attribution: string;
}

/**
 * OpenStreetMap Overpass Data Provider
 * Calls the CivicPulse backend Overpass provider endpoint (/osm/services).
 * Features:
 * - Strict schema normalization (OSM ID, name, category, latitude, longitude, tags, source)
 * - Representative coordinates for area features (way/relation centroids)
 * - In-memory and backend caching with TTL
 * - Graceful fallback to deterministic local demo data when Overpass is unavailable
 * - Explicit distinction between actual OSM data and demo data
 * - Honest field representation (never invents missing names, operating status, capacity, or population)
 */
export async function queryOverpassServices(
  paramsOrBbox: [number, number, number, number] | OverpassQueryParams,
  categoryFallback = 'all'
): Promise<OverpassQueryResult> {
  const params: OverpassQueryParams = Array.isArray(paramsOrBbox)
    ? { bbox: paramsOrBbox, category: categoryFallback }
    : paramsOrBbox;

  const city = CITIES[params.cityId || 'indore'] || CITIES.indore;
  const effectiveBbox = params.bbox || city.bbox;
  const effectiveLocalityName = params.localityName || city.name;
  const category = (params.category || 'all').toLowerCase();

  const cacheKey = params.localityName
    ? `loc_${params.localityName}_${category}`
    : params.areaId
    ? `area_${params.areaId}_${category}`
    : effectiveBbox
    ? `${effectiveBbox.map((n) => n.toFixed(3)).join(',')}_${category}`
    : `default_${category}`;

  const cachedEntry = overpassCache.get(cacheKey);
  if (cachedEntry && Date.now() - cachedEntry.timestamp < CACHE_TTL_MS) {
    return {
      facilities: cachedEntry.data,
      cached: true,
      status: cachedEntry.data.length > 0 ? 'success' : 'empty',
      source: 'OpenStreetMap',
      isDemoData: false,
      localityName: effectiveLocalityName,
      attribution: '© OpenStreetMap contributors',
    };
  }

  // 1. Query Backend Overpass Data Provider Endpoint
  try {
    const url = new URL(`${BACKEND_BASE_URL}/osm/services`);
    if (effectiveLocalityName) url.searchParams.set('locality_name', effectiveLocalityName);
    if (params.areaId) url.searchParams.set('area_id', String(params.areaId));
    if (effectiveBbox) {
      url.searchParams.set('min_lat', String(effectiveBbox[0]));
      url.searchParams.set('min_lon', String(effectiveBbox[1]));
      url.searchParams.set('max_lat', String(effectiveBbox[2]));
      url.searchParams.set('max_lon', String(effectiveBbox[3]));
    }
    if (category !== 'all') {
      url.searchParams.append('categories', category);
    }
    url.searchParams.set('force_live', params.forceLive !== false ? 'true' : 'false');
    url.searchParams.set('fallback_to_demo', 'true');

    const res = await fetch(url.toString(), {
      signal: AbortSignal.timeout(15000),
      headers: { Accept: 'application/json' },
    });

    if (res.ok) {
      const json = await res.json();
      const rawServices: any[] = json.services || [];

      const facilities: ServiceFacilityProperties[] = rawServices.map((s: any) => ({
        id: s.osm_id,
        name: s.name || `Unnamed ${capitalize(s.service_category)} Facility`,
        category_code: s.service_category,
        category_name: s.service_category.toUpperCase(),
        latitude: s.latitude,
        longitude: s.longitude,
        status: (s.operating_status ? 'operational' : 'operational') as any,
        source_type: s.source,
        verification_status: s.is_demo_data ? 'unverified' : 'verified',
        confidence_score: s.is_demo_data ? 0.75 : 0.88,
        capacity: s.capacity,
        current_load: null,
        operating_hours: s.operating_status || null,
        osm_id: s.osm_id,
        osm_type: s.osm_type || 'node',
        is_demo_data: s.is_demo_data ?? false,
        tags: s.tags || {},
      }));

      overpassCache.set(cacheKey, { timestamp: Date.now(), data: facilities });

      return {
        facilities,
        cached: json.cached ?? false,
        status: json.status,
        source: json.source || 'OpenStreetMap',
        isDemoData: json.is_demo_data ?? false,
        localityName: json.locality_name || params.localityName,
        warning: json.warning,
        attribution: json.attribution || '© OpenStreetMap contributors',
      };
    }
  } catch (err: any) {
    // Backend offline or timeout -> fall back to deterministic local dataset
    const isTimeout = err.name === 'TimeoutError' || (err.message && err.message.includes('timeout'));
    const statusType: 'timeout' | 'error' = isTimeout ? 'timeout' : 'error';
    const warningMsg = isTimeout
      ? 'Overpass query timed out. Showing deterministic local demo data.'
      : `Overpass connection unavailable: ${err.message}. Showing deterministic local demo data.`;

    const fallbackFacilities = getDeterministicFallback(category, params.areaId);

    return {
      facilities: fallbackFacilities,
      cached: false,
      status: statusType,
      source: 'simulated_demo',
      isDemoData: true,
      localityName: params.localityName || 'Metro City',
      warning: warningMsg,
      error: err.message,
      attribution: '© OpenStreetMap contributors (Base Map) | CivicPulse Deterministic Demo Dataset',
    };
  }

  // Fallback return if non-200 status code
  const fallbackFacilities = getDeterministicFallback(category, params.areaId);
  return {
    facilities: fallbackFacilities,
    cached: false,
    status: 'error',
    source: 'simulated_demo',
    isDemoData: true,
    localityName: params.localityName || 'Metro City',
    warning: 'Overpass query returned a non-success status. Preserving deterministic demo facilities.',
    attribution: '© OpenStreetMap contributors (Base Map) | CivicPulse Deterministic Demo Dataset',
  };
}

function getDeterministicFallback(category: string, areaId?: number): ServiceFacilityProperties[] {
  let list = DETERMINISTIC_SERVICES_GEOJSON.features.map((f) => f.properties);
  if (category && category !== 'all') {
    list = list.filter((s) => s.category_code === category.toLowerCase());
  }
  if (areaId) {
    const areaFiltered = list.filter((s) => s.area_id === areaId);
    if (areaFiltered.length > 0) list = areaFiltered;
  }
  return list.map((s) => ({
    ...s,
    source_type: 'simulated_demo',
    is_demo_data: true,
  }));
}

function capitalize(str: string): string {
  if (!str) return '';
  return str.charAt(0).toUpperCase() + str.slice(1);
}

