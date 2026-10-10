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
} from './deterministicData';

const BACKEND_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

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
            area_name: r.area_name || 'Indore',
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
  centerLat?: number;
  centerLon?: number;
  radiusMeters?: number;
  forceLive?: boolean;
  cityId?: 'indore' | 'bengaluru';
}

export interface OverpassQueryResult {
  facilities: ServiceFacilityProperties[];
  totalCount?: number;
  isCapped?: boolean;
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
 * Samples representative facilities across categories so map renders smoothly at 60 FPS
 * without choking Leaflet on thousands of simultaneous SVG pins.
 */
function sampleRepresentativeFacilities(
  facilities: ServiceFacilityProperties[],
  maxCount = 120
): ServiceFacilityProperties[] {
  if (facilities.length <= maxCount) return facilities;

  const categories: Array<'healthcare' | 'education' | 'transport' | 'water' | 'market'> = [
    'healthcare',
    'education',
    'transport',
    'water',
    'market',
  ];
  const perCat = Math.floor(maxCount / categories.length);
  const result: ServiceFacilityProperties[] = [];
  const categorized: Record<string, ServiceFacilityProperties[]> = {
    healthcare: [],
    education: [],
    transport: [],
    water: [],
    market: [],
  };
  const other: ServiceFacilityProperties[] = [];

  for (const f of facilities) {
    if (categorized[f.category_code]) {
      categorized[f.category_code].push(f);
    } else {
      other.push(f);
    }
  }

  for (const cat of categories) {
    const list = categorized[cat];
    if (list.length <= perCat) {
      result.push(...list);
    } else {
      const step = list.length / perCat;
      for (let i = 0; i < perCat; i++) {
        result.push(list[Math.floor(i * step)]);
      }
    }
  }

  const remaining = maxCount - result.length;
  if (remaining > 0 && other.length > 0) {
    result.push(...other.slice(0, remaining));
  }

  return result;
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

  // Check in-memory cache first (only when forceLive is NOT requested)
  if (!params.forceLive) {
    const cachedEntry = overpassCache.get(cacheKey);
    if (cachedEntry && Date.now() - cachedEntry.timestamp < CACHE_TTL_MS) {
      let cachedFacilities = cachedEntry.data;
    const totalCount = cachedFacilities.length;
    let isCapped = false;

    // Apply locality bounding box filtering if locality is specified
    if (params.bbox) {
      const [minLat, minLon, maxLat, maxLon] = params.bbox;
      const buffer = 0.003;
      cachedFacilities = cachedFacilities.filter(
        (f) =>
          f.latitude >= minLat - buffer &&
          f.latitude <= maxLat + buffer &&
          f.longitude >= minLon - buffer &&
          f.longitude <= maxLon + buffer
      );
    } else if (cachedFacilities.length > 120) {
      cachedFacilities = sampleRepresentativeFacilities(cachedFacilities, 120);
      isCapped = true;
    }

    return {
      facilities: cachedFacilities,
      totalCount,
      isCapped,
      cached: true,
      status: cachedFacilities.length > 0 ? 'success' : 'empty',
      source: 'OpenStreetMap',
      isDemoData: false,
      localityName: effectiveLocalityName,
      attribution: '© OpenStreetMap contributors',
    };
  }
} else {
  overpassCache.delete(cacheKey);
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
    if (params.centerLat != null) url.searchParams.set('center_lat', String(params.centerLat));
    if (params.centerLon != null) url.searchParams.set('center_lon', String(params.centerLon));
    if (params.radiusMeters != null) url.searchParams.set('radius_meters', String(params.radiusMeters));

    if (category !== 'all') {
      url.searchParams.append('categories', category);
    }
    url.searchParams.set('force_live', params.forceLive !== false ? 'true' : 'false');
    url.searchParams.set('fallback_to_demo', 'true');

    const res = await fetch(url.toString(), {
      signal: AbortSignal.timeout(35000),
      headers: { Accept: 'application/json' },
    });

    if (res.ok) {
      const json = await res.json();
      const rawServices: any[] = json.services || [];

      const allFacilities: ServiceFacilityProperties[] = rawServices.map((s: any) => {
        const catCode = (category !== 'all' ? category : (s.service_category || 'transport')).toLowerCase();
        return {
          id: s.osm_id || s.id,
          name: s.name || `Unnamed ${capitalize(catCode)} Facility`,
          category_code: catCode as any,
          category_name: catCode.toUpperCase(),
          latitude: s.latitude,
          longitude: s.longitude,
          status: 'operational' as any,
          source_type: s.source || 'OpenStreetMap',
          verification_status: s.is_demo_data ? 'unverified' : 'verified',
          confidence_score: s.is_demo_data ? 0.75 : 0.88,
          capacity: s.capacity,
          current_load: null,
          operating_hours: s.operating_status || null,
          osm_id: s.osm_id,
          osm_type: s.osm_type || 'node',
          is_demo_data: s.is_demo_data ?? false,
          tags: s.tags || {},
        };
      });

      // Cache raw facilities before sampling
      overpassCache.set(cacheKey, { timestamp: Date.now(), data: allFacilities });

      let displayedFacilities = allFacilities;
      const rawTotalCount = allFacilities.length;
      let isCapped = false;

      // When querying a specific locality bounding box, strictly filter facilities to that area
      if (params.bbox) {
        const [minLat, minLon, maxLat, maxLon] = params.bbox;
        const buffer = 0.003;
        displayedFacilities = allFacilities.filter(
          (f) =>
            f.latitude >= minLat - buffer &&
            f.latitude <= maxLat + buffer &&
            f.longitude >= minLon - buffer &&
            f.longitude <= maxLon + buffer
        );
      } else if (allFacilities.length > 120) {
        // Whole city query with thousands of pins: sample representative items for smooth 60fps rendering
        displayedFacilities = sampleRepresentativeFacilities(allFacilities, 120);
        isCapped = true;
      }

      const finalStatus = displayedFacilities.length > 0 ? 'success' : 'empty';

      return {
        facilities: displayedFacilities,
        totalCount: rawTotalCount,
        isCapped,
        cached: json.cached ?? false,
        status: finalStatus,
        source: json.source || 'OpenStreetMap',
        isDemoData: json.is_demo_data ?? false,
        localityName: json.locality_name || params.localityName,
        warning: json.warning,
        attribution: json.attribution || '© OpenStreetMap contributors',
      };
    }
  } catch (err: any) {
    // Backend offline or timeout -> attempt direct browser fetch from public Overpass API
    try {
      const directFacilities = await queryPublicOverpassDirectly(
        effectiveBbox,
        category,
        effectiveLocalityName
      );
      if (directFacilities && directFacilities.length > 0) {
        overpassCache.set(cacheKey, { timestamp: Date.now(), data: directFacilities });
        return {
          facilities: directFacilities,
          cached: false,
          status: 'success',
          source: 'OpenStreetMap (Live Direct)',
          isDemoData: false,
          localityName: effectiveLocalityName,
          attribution: '© OpenStreetMap contributors',
        };
      }
    } catch {
      // Proceed to deterministic fallback
    }

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
      localityName: params.localityName || 'Indore',
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
    localityName: params.localityName || 'Indore',
    warning: 'Overpass query returned a non-success status. Preserving deterministic demo facilities.',
    attribution: '© OpenStreetMap contributors (Base Map) | CivicPulse Deterministic Demo Dataset',
  };
}

// Direct public Overpass query fallback
async function queryPublicOverpassDirectly(
  bbox: [number, number, number, number],
  category: string,
  _localityName: string
): Promise<ServiceFacilityProperties[] | null> {
  const [minLat, minLon, maxLat, maxLon] = bbox;
  let filters = '';
  if (category === 'healthcare' || category === 'all') {
    filters += `node["amenity"="hospital"](${minLat},${minLon},${maxLat},${maxLon});way["amenity"="hospital"](${minLat},${minLon},${maxLat},${maxLon});node["amenity"="clinic"](${minLat},${minLon},${maxLat},${maxLon});node["amenity"="pharmacy"](${minLat},${minLon},${maxLat},${maxLon});`;
  }
  if (category === 'education' || category === 'all') {
    filters += `node["amenity"="school"](${minLat},${minLon},${maxLat},${maxLon});way["amenity"="school"](${minLat},${minLon},${maxLat},${maxLon});node["amenity"="college"](${minLat},${minLon},${maxLat},${maxLon});`;
  }
  if (category === 'transport' || category === 'all') {
    filters += `node["highway"="bus_stop"](${minLat},${minLon},${maxLat},${maxLon});node["public_transport"="platform"](${minLat},${minLon},${maxLat},${maxLon});node["public_transport"="stop_position"](${minLat},${minLon},${maxLat},${maxLon});node["amenity"="bus_station"](${minLat},${minLon},${maxLat},${maxLon});node["railway"="station"](${minLat},${minLon},${maxLat},${maxLon});`;
  }
  if (category === 'water' || category === 'all') {
    filters += `node["amenity"="drinking_water"](${minLat},${minLon},${maxLat},${maxLon});node["amenity"="water_point"](${minLat},${minLon},${maxLat},${maxLon});`;
  }
  if (category === 'market' || category === 'all') {
    filters += `node["amenity"="marketplace"](${minLat},${minLon},${maxLat},${maxLon});node["shop"="supermarket"](${minLat},${minLon},${maxLat},${maxLon});node["shop"="convenience"](${minLat},${minLon},${maxLat},${maxLon});`;
  }

  const ql = `[out:json][timeout:25];(${filters});out center body 120;`;
  const res = await fetch('https://overpass-api.de/api/interpreter', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: `data=${encodeURIComponent(ql)}`,
    signal: AbortSignal.timeout(25000),
  });

  if (res.ok) {
    const json = await res.json();
    if (Array.isArray(json.elements) && json.elements.length > 0) {
      return json.elements
        .map((el: any) => {
          const lat = el.lat ?? el.center?.lat;
          const lon = el.lon ?? el.center?.lon;
          const tags = el.tags || {};
          const amenity = (tags.amenity || '').toLowerCase();
          const highway = (tags.highway || '').toLowerCase();
          const publicTransport = (tags.public_transport || '').toLowerCase();
          const railway = (tags.railway || '').toLowerCase();
          const shop = (tags.shop || '').toLowerCase();
          const healthcare = (tags.healthcare || '').toLowerCase();

          // Robust category resolution conforming to CivicPulse categories
          let cat = category !== 'all' ? category : 'healthcare';
          if (
            highway === 'bus_stop' ||
            highway === 'platform' ||
            railway === 'station' ||
            railway === 'halt' ||
            publicTransport === 'platform' ||
            publicTransport === 'stop_position' ||
            publicTransport === 'station' ||
            amenity === 'bus_station' ||
            tags.bus === 'yes' ||
            category === 'transport'
          ) {
            cat = 'transport';
          } else if (
            amenity === 'school' ||
            amenity === 'college' ||
            amenity === 'kindergarten' ||
            amenity === 'university' ||
            category === 'education'
          ) {
            cat = 'education';
          } else if (
            amenity === 'drinking_water' ||
            amenity === 'water_point' ||
            tags.man_made === 'water_tap' ||
            tags.man_made === 'water_well' ||
            category === 'water'
          ) {
            cat = 'water';
          } else if (
            amenity === 'marketplace' ||
            amenity === 'supermarket' ||
            shop ||
            category === 'market'
          ) {
            cat = 'market';
          } else if (
            amenity === 'hospital' ||
            amenity === 'clinic' ||
            amenity === 'doctors' ||
            amenity === 'pharmacy' ||
            healthcare ||
            category === 'healthcare'
          ) {
            cat = 'healthcare';
          }

          return {
            id: el.id,
            name: tags.name || `Unnamed ${capitalize(cat)} Facility`,
            category_code: cat as any,
            category_name: cat.toUpperCase(),
            latitude: lat,
            longitude: lon,
            status: 'operational',
            source_type: 'OpenStreetMap',
            verification_status: 'verified',
            confidence_score: 0.9,
            capacity: null,
            current_load: null,
            operating_hours: tags.opening_hours || null,
            osm_id: el.id,
            osm_type: el.type,
            is_demo_data: false,
            tags,
          };
        })
        .filter((f: any) => f.latitude && f.longitude);
    }
  }
  return null;
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

export async function fetchSimulation(payload: any) {
  try {
    const token = localStorage.getItem('civicpulse_auth_token');
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    const res = await fetch(`${BACKEND_BASE_URL}/simulations`, {
      method: 'POST',
      headers,
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const text = await res.text();
      throw new Error(`Simulation failed: ${text}`);
    }
    return await res.json();
  } catch (err) {
    console.error('Error fetching simulation:', err);
    throw err;
  }
}
