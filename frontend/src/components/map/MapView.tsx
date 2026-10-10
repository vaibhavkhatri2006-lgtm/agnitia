import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { MapContainer, TileLayer, Marker, Popup, GeoJSON, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import {
  AlertTriangle,
  AlertCircle,
  Sparkles,
  Layers,
  MapPin,
  RefreshCw,
  Search,
  CheckCircle2,
  Clock,
  X,
  Compass,
  Info,
} from 'lucide-react';

import {
  GeoJSONFeatureCollection,
  LocalityProperties,
  ServiceFacilityProperties,
  CommunityReportItem,
  RecommendationCandidateItem,
  METRO_CITY_CENTER,
  METRO_CITY_DEFAULT_ZOOM,
  CITIES,
  INDORE_AREAS_GEOJSON,
  INDORE_SERVICES_GEOJSON,
  DETERMINISTIC_AREAS_GEOJSON,
  DETERMINISTIC_SERVICES_GEOJSON,
  DETERMINISTIC_REPORTS,
  DETERMINISTIC_RECOMMENDATIONS,
} from '../../services/deterministicData';
import {
  fetchAreasData,
  fetchServicesData,
  fetchCommunityReports,
  fetchRecommendationsData,
  queryOverpassServices,
  DataFetchStatus,
} from '../../services/mapDataProvider';

// Leaflet default icon fallback configuration
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
});

// Category visual palettes and SVG icons
const CATEGORY_CONFIG: Record<
  string,
  { label: string; color: string; bg: string; border: string; text: string; icon: string }
> = {
  healthcare: {
    label: 'Healthcare',
    color: '#ef4444',
    bg: '#fee2e2',
    border: '#f87171',
    text: '#b91c1c',
    icon: `<svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="currentColor"><path d="M10 4a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1v5h5a1 1 0 0 1 1 1v2a1 1 0 0 1-1 1h-5v5a1 1 0 0 1-1 1h-2a1 1 0 0 1-1-1v-5H5a1 1 0 0 1-1-1v-2a1 1 0 0 1 1-1h5V4z"/></svg>`,
  },
  education: {
    label: 'Education',
    color: '#3b82f6',
    bg: '#dbeafe',
    border: '#60a5fa',
    text: '#1d4ed8',
    icon: `<svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M22 10v6M2 10l10-5 10 5-10 5z"/><path d="M6 12v5c3 3 9 3 12 0v-5"/></svg>`,
  },
  transport: {
    label: 'Transport',
    color: '#f59e0b',
    bg: '#fef3c7',
    border: '#fbbf24',
    text: '#b45309',
    icon: `<svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><rect width="16" height="16" x="4" y="3" rx="3"/><path d="M4 11h16"/><circle cx="8" cy="15" r="1.5" fill="currentColor"/><circle cx="16" cy="15" r="1.5" fill="currentColor"/><path d="m6 19-1.5 2"/><path d="m18 19 1.5 2"/></svg>`,
  },
  water: {
    label: 'Water & Sanitation',
    color: '#06b6d4',
    bg: '#cffafe',
    border: '#22d3ee',
    text: '#0e7490',
    icon: `<svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z"/></svg>`,
  },
  market: {
    label: 'Markets & Food',
    color: '#10b981',
    bg: '#d1fae5',
    border: '#34d399',
    text: '#047857',
    icon: `<svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="21" r="1"/><circle cx="19" cy="21" r="1"/><path d="M2.05 2.05h2l2.66 12.42a2 2 0 0 0 2 1.58h9.78a2 2 0 0 0 1.95-1.57l1.65-7.43H5.12"/></svg>`,
  },
};

// Robust Category Resolver with alias recognition
function getCategoryConfig(categoryCode?: string, fallback = 'transport') {
  if (!categoryCode) return CATEGORY_CONFIG[fallback.toLowerCase()] || CATEGORY_CONFIG.transport;
  const code = categoryCode.toLowerCase().trim();
  if (CATEGORY_CONFIG[code]) return CATEGORY_CONFIG[code];
  if (
    code.includes('transport') ||
    code.includes('bus') ||
    code.includes('transit') ||
    code.includes('station') ||
    code.includes('train') ||
    code.includes('rail')
  ) {
    return CATEGORY_CONFIG.transport;
  }
  if (
    code.includes('health') ||
    code.includes('hospital') ||
    code.includes('clinic') ||
    code.includes('medic') ||
    code.includes('doctor') ||
    code.includes('pharmacy')
  ) {
    return CATEGORY_CONFIG.healthcare;
  }
  if (
    code.includes('educat') ||
    code.includes('school') ||
    code.includes('college') ||
    code.includes('univers') ||
    code.includes('kindergarten')
  ) {
    return CATEGORY_CONFIG.education;
  }
  if (
    code.includes('water') ||
    code.includes('sanitat') ||
    code.includes('tap') ||
    code.includes('well')
  ) {
    return CATEGORY_CONFIG.water;
  }
  if (
    code.includes('market') ||
    code.includes('food') ||
    code.includes('shop') ||
    code.includes('grocery') ||
    code.includes('mandi')
  ) {
    return CATEGORY_CONFIG.market;
  }
  return CATEGORY_CONFIG[fallback.toLowerCase()] || CATEGORY_CONFIG.healthcare;
}

// Create custom pin icons with Leaflet L.divIcon
function createCategoryPinIcon(categoryCode?: string, isOverpass = false, fallbackCategory = 'transport') {
  const cfg = getCategoryConfig(categoryCode, fallbackCategory);
  const badgeHtml = `
    <div style="
      position: relative;
      background-color: ${cfg.color};
      width: 28px;
      height: 28px;
      border-radius: 50% 50% 50% 0;
      transform: rotate(-45deg);
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 4px 8px rgba(0,0,0,0.3);
      border: 2px solid #ffffff;
      cursor: pointer;
    ">
      <div style="
        width: 17px;
        height: 17px;
        border-radius: 50%;
        background-color: #ffffff;
        transform: rotate(45deg);
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: inset 0 1px 2px rgba(0,0,0,0.1);
      ">
        <div style="color: ${cfg.color}; display: flex; align-items: center; justify-content: center;">
          ${cfg.icon}
        </div>
      </div>
    </div>
    ${
      isOverpass
        ? `<div style="position: absolute; bottom: -3px; right: -3px; background: #4f46e5; color: white; border-radius: 9999px; padding: 1px 3.5px; font-size: 7.5px; font-weight: 800; border: 1.5px solid white; box-shadow: 0 1px 3px rgba(0,0,0,0.35); line-height: 1; letter-spacing: -0.2px;">OSM</div>`
        : ''
    }
  `;

  return L.divIcon({
    html: `<div style="position: relative; width: 28px; height: 28px; display: flex; align-items: center; justify-content: center;">${badgeHtml}</div>`,
    className: 'custom-leaflet-pin',
    iconSize: [28, 28],
    iconAnchor: [14, 28],
    popupAnchor: [0, -28],
  });
}

function createReportPinIcon(severity: string) {
  const color = severity === 'critical' ? '#dc2626' : severity === 'high' ? '#ea580c' : '#f59e0b';
  return L.divIcon({
    html: `
      <div style="
        background-color: ${color};
        color: white;
        width: 26px;
        height: 26px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 4px 10px rgba(220,38,38,0.4);
        border: 2px solid white;
      ">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
      </div>
    `,
    className: 'custom-report-pin',
    iconSize: [26, 26],
    iconAnchor: [13, 13],
    popupAnchor: [0, -13],
  });
}

function createRecommendationPinIcon(rank: number) {
  return L.divIcon({
    html: `
      <div style="
        background: linear-gradient(135deg, #7c3aed 0%, #4f46e5 100%);
        color: white;
        width: 30px;
        height: 30px;
        border-radius: 8px;
        transform: rotate(45deg);
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 4px 12px rgba(124, 58, 237, 0.45);
        border: 2px solid white;
      ">
        <span style="transform: rotate(-45deg); font-weight: 800; font-size: 11px;">#${rank}</span>
      </div>
    `,
    className: 'custom-recommendation-pin',
    iconSize: [30, 30],
    iconAnchor: [15, 15],
    popupAnchor: [0, -15],
  });
}

function capitalize(s: string): string {
  if (!s) return '';
  return s.charAt(0).toUpperCase() + s.slice(1);
}

export interface OsmProblemItem {
  title: string;
  description: string;
  severity: 'critical' | 'high' | 'medium';
}

export interface OsmLocalityProblemReport {
  localityId: number;
  localityName: string;
  category: string;
  categoryLabel: string;
  facilityCount: number;
  hasNoData: boolean;
  totalCityCount?: number;
  problems: OsmProblemItem[];
  queriedAt: Date;
}

function generateOsmProblems(
  locality: LocalityProperties,
  category: string,
  facilityCount: number
): OsmProblemItem[] {
  const problems: OsmProblemItem[] = [];
  const cat = category.toLowerCase();
  const pop = locality.population || 40000;
  const areaName = locality.name.split('/')[0].trim();

  if (facilityCount === 0) {
    if (cat === 'water' || cat === 'all') {
      problems.push({
        title: 'Zero Public Drinking Water Points',
        description: `OpenStreetMap records 0 mapped drinking water points, public taps, or municipal dispensers in ${areaName}. All ${pop.toLocaleString()} residents rely entirely on private borewells or municipal tankers.`,
        severity: 'critical',
      });
    }
    if (cat === 'healthcare' || cat === 'all') {
      problems.push({
        title: 'Primary Healthcare Accessibility Void',
        description: `0 operational clinics or primary health dispensaries recorded in ${areaName} on OpenStreetMap. Emergency lag to regional center (${locality.nearest_service || 'MY Hospital'}, est. ${locality.travel_time || '15 mins'}).`,
        severity: 'critical',
      });
    }
    if (cat === 'education' || cat === 'all') {
      problems.push({
        title: 'Public Education Deficit',
        description: `No public schools or educational amenities recorded in ${areaName} on OpenStreetMap. Students face extended transit commutes to adjacent wards.`,
        severity: 'high',
      });
    }
    if (cat === 'transport' || cat === 'all') {
      problems.push({
        title: 'Public Transit Blindspot',
        description: `0 public transit halts or bus boarding points mapped in ${areaName}. Last-mile civic connectivity is severely compromised.`,
        severity: 'high',
      });
    }
    if (cat === 'market' || cat === 'all') {
      problems.push({
        title: 'Fresh Produce Food Desert',
        description: `Zero municipal sabzi mandis or daily essential food markets mapped within ${areaName}.`,
        severity: 'medium',
      });
    }
  } else {
    // Facilities found -> calculate per-capita deficit
    const perCapita = Math.round(pop / facilityCount);
    if (cat === 'healthcare' || cat === 'all') {
      if (facilityCount < 3) {
        problems.push({
          title: 'High Population-to-Clinic Ratio',
          description: `Only ${facilityCount} medical facility for ${pop.toLocaleString()} residents (~${perCapita.toLocaleString()} residents per facility vs WHO standard of 1 per 10,000).`,
          severity: 'high',
        });
      }
    }
    if (cat === 'water' || cat === 'all') {
      if (facilityCount < 3) {
        problems.push({
          title: 'Low Public Water Point Density',
          description: `Only ${facilityCount} public water point mapped for ${pop.toLocaleString()} residents. Heavy load on existing infrastructure.`,
          severity: 'high',
        });
      }
    }
    if (cat === 'transport' || cat === 'all') {
      if (facilityCount < 4) {
        problems.push({
          title: 'Transit Stop Capacity Bottleneck',
          description: `Only ${facilityCount} transit stops mapped. Feeder buses experience overcrowding during peak morning hours.`,
          severity: 'medium',
        });
      }
    }
    if (cat === 'education' || cat === 'all') {
      if (facilityCount < 3) {
        problems.push({
          title: 'Classroom Capacity Deficit',
          description: `Only ${facilityCount} educational facility for ${pop.toLocaleString()} residents. High student-to-school ratio.`,
          severity: 'medium',
        });
      }
    }
  }

  // Include locality's specific municipal gap if not already covered
  if (locality.main_gap && !problems.some((p) => p.description.includes(locality.main_gap!))) {
    problems.push({
      title: 'Municipal Deficit',
      description: locality.main_gap,
      severity: locality.gap_score && locality.gap_score > 35 ? 'critical' : 'high',
    });
  }

  return problems;
}

// Controller component to smoothly fly/pan to selected localities or cities
function MapViewController({ targetCenter, targetZoom }: { targetCenter?: [number, number]; targetZoom?: number }) {
  const map = useMap();
  useEffect(() => {
    if (targetCenter) {
      map.flyTo(targetCenter, targetZoom || 13, { duration: 1.2 });
    }
  }, [targetCenter, targetZoom, map]);
  return null;
}

export type MapLayerType = 'services' | 'accessibility' | 'gap' | 'reports' | 'recommendations';

export interface MapViewProps {
  center?: [number, number];
  zoom?: number;
  activeLayer?: MapLayerType;
  onLocalitySelect?: (locality: LocalityProperties | null) => void;
  className?: string;
  initialCategory?: string;
  initialCity?: 'indore' | 'bengaluru';
}

export const MapView: React.FC<MapViewProps> = ({
  center = METRO_CITY_CENTER,
  zoom = METRO_CITY_DEFAULT_ZOOM,
  activeLayer: initialLayer = 'services',
  onLocalitySelect,
  className = 'w-full h-full min-h-[520px]',
  initialCategory = 'all',
  initialCity = 'indore',
}) => {
  // City Focus State (Primary: Indore, MP)
  const [selectedCity, setSelectedCity] = useState<'indore' | 'bengaluru'>(initialCity);
  const [mapTargetCenter, setMapTargetCenter] = useState<[number, number] | undefined>(CITIES[initialCity]?.center || center);
  const [mapTargetZoom, setMapTargetZoom] = useState<number | undefined>(CITIES[initialCity]?.zoom || zoom);

  // Layer and Filter State
  const [activeLayer, setActiveLayer] = useState<MapLayerType>(initialLayer);
  const [selectedCategory, setSelectedCategory] = useState<string>(initialCategory);
  const [selectedLocality, setSelectedLocality] = useState<LocalityProperties | null>(null);

  // Data State - Pre-populated synchronously so map renders immediately without blank state
  const [areas, setAreas] = useState<GeoJSONFeatureCollection<any, LocalityProperties> | null>(() => {
    return initialCity === 'indore' ? INDORE_AREAS_GEOJSON : DETERMINISTIC_AREAS_GEOJSON;
  });
  const [services, setServices] = useState<ServiceFacilityProperties[]>(() => {
    const coll = initialCity === 'indore' ? INDORE_SERVICES_GEOJSON : DETERMINISTIC_SERVICES_GEOJSON;
    return coll.features.map((f: any) => f.properties);
  });
  const [reports, setReports] = useState<CommunityReportItem[]>(() => DETERMINISTIC_REPORTS);
  const [recommendations, setRecommendations] = useState<RecommendationCandidateItem[]>(() => DETERMINISTIC_RECOMMENDATIONS);
  const [overpassFacilities, setOverpassFacilities] = useState<ServiceFacilityProperties[]>([]);
  const [osmProblemReport, setOsmProblemReport] = useState<OsmLocalityProblemReport | null>(null);

  // Telemetry & UI State
  const [dataStatus, setDataStatus] = useState<DataFetchStatus>(() => ({
    source: 'live',
    isLive: true,
    lastUpdated: new Date(),
  }));
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isQueryingOverpass, setIsQueryingOverpass] = useState<boolean>(false);
  const [osmNotice, setOsmNotice] = useState<{
    type: 'loading' | 'success' | 'empty' | 'timeout' | 'error';
    message: string;
  } | null>(null);
  const [tileError, setTileError] = useState<boolean>(false);

  // Load backend / deterministic data on mount & category/city change with resilient fallbacks
  useEffect(() => {
    let isMounted = true;
    async function loadAllData() {
      try {
        const [areasResult, servicesResult, reportsResult, recsResult] = await Promise.allSettled([
          fetchAreasData(selectedCity),
          fetchServicesData(selectedCategory, selectedCity),
          fetchCommunityReports(),
          fetchRecommendationsData(selectedCategory === 'all' ? 'healthcare' : selectedCategory),
        ]);

        if (!isMounted) return;

        if (areasResult.status === 'fulfilled' && areasResult.value?.data) {
          setAreas(areasResult.value.data);
        }
        if (servicesResult.status === 'fulfilled' && servicesResult.value?.data?.features) {
          setServices(servicesResult.value.data.features.map((f) => f.properties));
          setDataStatus(servicesResult.value.status);
        }
        if (reportsResult.status === 'fulfilled' && reportsResult.value?.data) {
          setReports(reportsResult.value.data);
        }
        if (recsResult.status === 'fulfilled' && recsResult.value?.data) {
          setRecommendations(recsResult.value.data);
        }
      } catch (err) {
        console.error('Error loading map datasets:', err);
      } finally {
        if (isMounted) setIsLoading(false);
      }
    }

    loadAllData();
    return () => {
      isMounted = false;
    };
  }, [selectedCategory, selectedCity]);

  // Synchronize external selection, filter OSM pins to boundary, and pan map to locality
  const handleSelectLocality = useCallback(
    (loc: LocalityProperties | null, geomOverride?: any) => {
      setSelectedLocality(loc);
      if (loc) {
        let geom = geomOverride || (loc as any).geometry;
        if (!geom && areas?.features) {
          const match = areas.features.find((f: any) => (f.properties?.id ?? f.id) === loc.id);
          geom = match?.geometry;
        }

        let minLat = Infinity, maxLat = -Infinity, minLon = Infinity, maxLon = -Infinity;
        if (geom && geom.type === 'Polygon' && geom.coordinates?.[0]?.length > 0) {
          const coords = geom.coordinates[0];
          for (const [cLon, cLat] of coords) {
            if (cLat < minLat) minLat = cLat;
            if (cLat > maxLat) maxLat = cLat;
            if (cLon < minLon) minLon = cLon;
            if (cLon > maxLon) maxLon = cLon;
          }
          const avgLon = coords.reduce((acc: number, c: number[]) => acc + c[0], 0) / coords.length;
          const avgLat = coords.reduce((acc: number, c: number[]) => acc + c[1], 0) / coords.length;
          setMapTargetCenter([avgLat, avgLon]);
          setMapTargetZoom(15);
        }

        // Filter existing OSM facilities so pins from distant neighbourhoods don't bleed in
        setOverpassFacilities((prev) => {
          if (prev.length === 0 || minLat === Infinity) return [];
          const buffer = 0.003;
          return prev.filter(
            (f) =>
              f.latitude >= minLat - buffer &&
              f.latitude <= maxLat + buffer &&
              f.longitude >= minLon - buffer &&
              f.longitude <= maxLon + buffer
          );
        });

        // Set baseline problem report for selected locality
        const baselineProblems = generateOsmProblems(loc, selectedCategory, 0);
        setOsmProblemReport({
          localityId: loc.id,
          localityName: loc.name,
          category: selectedCategory,
          categoryLabel: selectedCategory === 'all' ? 'Civic' : capitalize(selectedCategory),
          facilityCount: 0,
          hasNoData: true,
          problems: baselineProblems,
          queriedAt: new Date(),
        });
      } else {
        const city = CITIES[selectedCity] || CITIES.indore;
        setMapTargetCenter(city.center);
        setMapTargetZoom(city.zoom);
        setOsmProblemReport(null);
      }

      if (onLocalitySelect) {
        onLocalitySelect(loc);
      }
    },
    [areas, selectedCity, selectedCategory, onLocalitySelect]
  );

  // Switch City Context
  const handleCityChange = (cityId: 'indore' | 'bengaluru') => {
    setSelectedCity(cityId);
    setSelectedLocality(null);
    setOverpassFacilities([]);
    setOsmNotice(null);
    setOsmProblemReport(null);
    const city = CITIES[cityId];
    if (city) {
      setMapTargetCenter(city.center);
      setMapTargetZoom(city.zoom);
    }
    // Pre-populate with city defaults immediately
    const coll = cityId === 'indore' ? INDORE_SERVICES_GEOJSON : DETERMINISTIC_SERVICES_GEOJSON;
    setServices(coll.features.map((f: any) => f.properties));
    setAreas(cityId === 'indore' ? INDORE_AREAS_GEOJSON : DETERMINISTIC_AREAS_GEOJSON);
  };

  // Execute Overpass search for selected locality or bounding box
  const handleQueryOverpass = async (
    targetLocality?: LocalityProperties | null,
    categoryOverride?: string
  ) => {
    setIsQueryingOverpass(true);
    setOverpassFacilities([]);
    const target = targetLocality || selectedLocality;
    const catToQuery = categoryOverride || selectedCategory;
    const city = CITIES[selectedCity] || CITIES.indore;
    const locName = target
      ? target.name.split('/')[0].split(',')[0].trim()
      : selectedCity === 'indore'
      ? 'Indore'
      : city.name;
    const catLabel = catToQuery === 'all' ? 'Civic' : capitalize(catToQuery);

    setOsmNotice({
      type: 'loading',
      message: `Querying OpenStreetMap Overpass provider for ${catLabel} amenities in ${locName}...`,
    });

    // Compute exact bounding box and centroid if a locality is selected
    let targetBbox: [number, number, number, number] | undefined = undefined;
    let centerLat: number | undefined = undefined;
    let centerLon: number | undefined = undefined;

    if (target) {
      const feat = areas?.features?.find((f: any) => (f.properties?.id ?? f.id) === target.id);
      if (feat && feat.geometry && feat.geometry.coordinates && feat.geometry.coordinates[0]?.length > 0) {
        const coords: [number, number][] = feat.geometry.coordinates[0];
        let minLat = Infinity, maxLat = -Infinity, minLon = Infinity, maxLon = -Infinity;
        for (const [cLon, cLat] of coords) {
          if (cLat < minLat) minLat = cLat;
          if (cLat > maxLat) maxLat = cLat;
          if (cLon < minLon) minLon = cLon;
          if (cLon > maxLon) maxLon = cLon;
        }
        if (minLat !== Infinity) {
          targetBbox = [minLat, minLon, maxLat, maxLon];
          centerLat = (minLat + maxLat) / 2;
          centerLon = (minLon + maxLon) / 2;
        }
      }
    }

    try {
      const res = await queryOverpassServices({
        localityName: locName,
        areaId: target ? target.id : undefined,
        bbox: target ? targetBbox : city.bbox,
        centerLat,
        centerLon,
        radiusMeters: 1800,
        category: catToQuery,
        forceLive: true,
        cityId: selectedCity,
      });

      setIsQueryingOverpass(false);

      if (target) {
        // Specific locality query
        const count = res.facilities.length;
        const problems = generateOsmProblems(target, catToQuery, count);

        setOsmProblemReport({
          localityId: target.id,
          localityName: target.name,
          category: catToQuery,
          categoryLabel: catLabel,
          facilityCount: count,
          hasNoData: count === 0,
          totalCityCount: res.totalCount,
          problems,
          queriedAt: new Date(),
        });

        if (count === 0) {
          setOverpassFacilities([]);
          setOsmNotice({
            type: 'empty',
            message: `⚠️ No ${catLabel} facilities found in ${target.name} on OpenStreetMap. Zero mapped public amenities exist within this boundary.`,
          });
        } else {
          setOverpassFacilities(res.facilities);
          setOsmNotice({
            type: 'success',
            message: `Retrieved ${count} ${catLabel} facilities in ${target.name} from OpenStreetMap (${res.cached ? 'from cache' : 'fresh Overpass query'}).`,
          });
        }
      } else {
        // Whole city query (smooth rendering with representative sampling)
        setOverpassFacilities(res.facilities);
        setOsmProblemReport(null);

        const total = res.totalCount || res.facilities.length;
        if (res.isCapped) {
          setOsmNotice({
            type: 'success',
            message: `Retrieved ${total.toLocaleString()} ${catLabel} facilities from OpenStreetMap across ${city.name}. Displaying top ${res.facilities.length} distributed facilities for smooth 60fps rendering. Select a locality to inspect all local data.`,
          });
        } else {
          setOsmNotice({
            type: 'success',
            message: `Retrieved ${res.facilities.length} ${catLabel} facilities from OpenStreetMap (${res.cached ? 'from cache' : 'fresh Overpass query'}).`,
          });
        }
      }
    } catch (err: any) {
      setIsQueryingOverpass(false);
      setOsmNotice({
        type: 'error',
        message: `OpenStreetMap query failed: ${err.message}. Preserving deterministic local data.`,
      });
    }
  };

  // GeoJSON style for locality boundaries
  const getLocalityStyle = useCallback(
    (feature: any) => {
      const props = feature?.properties as LocalityProperties;

      if (activeLayer === 'accessibility') {
        const score = props?.accessibility_score ?? 50;
        let fillColor = '#ef4444'; // Red < 40
        let strokeColor = '#dc2626';

        if (score >= 80) {
          fillColor = '#10b981'; // Green: Well Served
          strokeColor = '#059669';
        } else if (score >= 60) {
          fillColor = '#eab308'; // Yellow: Adequate
          strokeColor = '#d97706';
        } else if (score >= 40) {
          fillColor = '#f97316'; // Orange: Underserved
          strokeColor = '#ea580c';
        }

        return {
          color: strokeColor,
          weight: 3.5,
          fillColor,
          fillOpacity: 0.35,
        };
      }

      if (activeLayer === 'gap') {
        const gap = props?.gap_score ?? 30;
        let fillColor = '#10b981'; // Low gap (< 20)
        let strokeColor = '#059669';

        if (gap >= 60) {
          fillColor = '#ef4444'; // Critical Desert
          strokeColor = '#dc2626';
        } else if (gap >= 40) {
          fillColor = '#f97316'; // Underserved
          strokeColor = '#ea580c';
        } else if (gap >= 20) {
          fillColor = '#eab308'; // Moderate
          strokeColor = '#d97706';
        }

        return {
          color: strokeColor,
          weight: 3.5,
          fillColor,
          fillOpacity: 0.35,
        };
      }

      // Default high-contrast civic highlight for selected area
      return {
        color: '#1d4ed8',
        weight: 3.5,
        fillColor: '#3b82f6',
        fillOpacity: 0.3,
      };
    },
    [activeLayer]
  );

  // GeoJSON feature interactions (hover, click)
  const onEachFeature = useCallback(
    (feature: any, layer: L.Layer) => {
      const props = feature.properties as LocalityProperties;
      layer.on({
        click: (e) => {
          L.DomEvent.stopPropagation(e);
          handleSelectLocality(props, feature.geometry);
        },
        mouseover: (e) => {
          const l = e.target;
          l.setStyle({ fillOpacity: 0.55, weight: 3.5 });
        },
        mouseout: (e) => {
          const l = e.target;
          l.setStyle(getLocalityStyle(feature));
        },
      });

      // Tooltip for quick identification
      layer.bindTooltip(
        `<div style="font-family: inherit; font-size: 11px; padding: 2px;">
           <strong style="color: #0f172a; font-size: 12px;">${props.name}</strong><br/>
           <span style="color: #64748b;">Population:</span> <strong>${props.population ? props.population.toLocaleString() : 'N/A'}</strong><br/>
           ${props.accessibility_score != null ? `<span style="color: #64748b;">Access:</span> <strong>${props.accessibility_score}/100</strong><br/>` : ''}
           ${props.gap_score != null ? `<span style="color: #ef4444;">Gap:</span> <strong>${props.gap_score}%</strong><br/>` : ''}
           <span style="color: #2563eb; font-weight: 600; display: inline-block; margin-top: 3px;">👉 Click to focus & inspect area</span>
         </div>`,
        { sticky: true, className: 'civic-map-tooltip' }
      );
    },
    [getLocalityStyle, handleSelectLocality]
  );

  // Filter facilities based on selected category and selected locality boundary
  const displayedServices = useMemo(() => {
    let list = selectedCategory === 'all' ? services : services.filter((s) => s.category_code === selectedCategory);

    if (selectedLocality) {
      const feat = areas?.features?.find((f: any) => (f.properties?.id ?? f.id) === selectedLocality.id);
      if (feat && feat.geometry && feat.geometry.coordinates?.[0]?.length > 0) {
        const coords = feat.geometry.coordinates[0];
        let minLat = Infinity, maxLat = -Infinity, minLon = Infinity, maxLon = -Infinity;
        for (const [cLon, cLat] of coords) {
          if (cLat < minLat) minLat = cLat;
          if (cLat > maxLat) maxLat = cLat;
          if (cLon < minLon) minLon = cLon;
          if (cLon > maxLon) maxLon = cLon;
        }
        if (minLat !== Infinity) {
          const buffer = 0.003;
          list = list.filter(
            (s) =>
              s.latitude >= minLat - buffer &&
              s.latitude <= maxLat + buffer &&
              s.longitude >= minLon - buffer &&
              s.longitude <= maxLon + buffer
          );
        }
      }
    }

    return list;
  }, [services, selectedCategory, selectedLocality, areas]);

  // Render boundary ONLY when user has selected an area (do NOT show all areas by default)
  const activeAreasGeoJson = useMemo(() => {
    if (!areas || !selectedLocality) {
      return null;
    }
    return {
      type: 'FeatureCollection',
      features: areas.features.filter((f: any) => {
        const featId = f.properties?.id ?? f.id;
        return String(featId) === String(selectedLocality.id);
      }),
    };
  }, [areas, selectedLocality]);

  return (
    <div className={`relative rounded-2xl overflow-hidden border border-slate-200 shadow-sm bg-slate-50 flex flex-col ${className}`}>
      {/* Top Map Control Bar */}
      <div className="bg-white/95 backdrop-blur-md px-4 py-3 border-b border-slate-200 flex flex-wrap items-center justify-between gap-3 z-10">
        {/* Layer Selector */}
        <div className="flex items-center gap-2">
          <Layers className="w-4 h-4 text-blue-600" />
          <span className="text-xs font-bold uppercase tracking-wider text-slate-500 mr-1">Layer:</span>
          <div className="flex bg-slate-100 p-0.5 rounded-lg border border-slate-200 text-xs font-medium">
            <button
              onClick={() => setActiveLayer('services')}
              className={`px-3 py-1.5 rounded-md transition-all ${
                activeLayer === 'services'
                  ? 'bg-white text-blue-700 font-semibold shadow-sm'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Services
            </button>
            <button
              onClick={() => setActiveLayer('accessibility')}
              className={`px-3 py-1.5 rounded-md transition-all ${
                activeLayer === 'accessibility'
                  ? 'bg-white text-blue-700 font-semibold shadow-sm'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Accessibility
            </button>
            <button
              onClick={() => setActiveLayer('gap')}
              className={`px-3 py-1.5 rounded-md transition-all ${
                activeLayer === 'gap'
                  ? 'bg-white text-blue-700 font-semibold shadow-sm'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Service Gaps
            </button>
            <button
              onClick={() => setActiveLayer('reports')}
              className={`px-3 py-1.5 rounded-md transition-all ${
                activeLayer === 'reports'
                  ? 'bg-white text-blue-700 font-semibold shadow-sm'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Reports ({reports.length})
            </button>
            <button
              onClick={() => setActiveLayer('recommendations')}
              className={`px-3 py-1.5 rounded-md transition-all ${
                activeLayer === 'recommendations'
                  ? 'bg-white text-blue-700 font-semibold shadow-sm'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Recommendations
            </button>
          </div>
        </div>

        {/* City Focus, Area Selection, Category Filter & Overpass OSM Search */}
        <div className="flex items-center gap-2 flex-wrap">
          {/* City Focus Dropdown */}
          <div className="flex items-center gap-1.5 bg-blue-50/80 border border-blue-200/80 rounded-lg px-2.5 py-1 text-xs shadow-2xs">
            <Compass className="w-3.5 h-3.5 text-blue-600 shrink-0" />
            <select
              value={selectedCity}
              onChange={(e) => handleCityChange(e.target.value as 'indore' | 'bengaluru')}
              className="bg-transparent text-xs font-bold text-blue-900 outline-none cursor-pointer"
              title="Select Focus City"
            >
              <option value="indore">Indore, MP (Primary)</option>
              <option value="bengaluru">Bengaluru (Test Bed)</option>
            </select>
          </div>

          {/* Area / Locality Selector Dropdown */}
          <div className="flex items-center gap-1.5 bg-blue-50/90 border border-blue-200 rounded-lg px-2.5 py-1 text-xs shadow-2xs">
            <MapPin className="w-3.5 h-3.5 text-blue-600 shrink-0" />
            <select
              value={selectedLocality ? String(selectedLocality.id) : ''}
              onChange={(e) => {
                const val = e.target.value;
                if (!val) {
                  handleSelectLocality(null);
                } else {
                  const feat = areas?.features?.find((f: any) => String(f.properties?.id ?? f.id) === val);
                  if (feat) {
                    handleSelectLocality(feat.properties, feat.geometry);
                  }
                }
              }}
              className="bg-transparent text-xs font-bold text-blue-950 outline-none cursor-pointer max-w-[210px]"
              title="Select a specific area or neighbourhood to focus on"
            >
              <option value="">📍 Select an Area / Locality...</option>
              {areas?.features?.map((f: any) => (
                <option key={f.properties?.id ?? f.id} value={String(f.properties?.id ?? f.id)}>
                  {f.properties?.name || `Area #${f.id}`}
                </option>
              ))}
            </select>
            {selectedLocality && (
              <button
                onClick={() => handleSelectLocality(null)}
                className="text-blue-500 hover:text-blue-800 font-bold ml-1 text-xs px-1"
                title="Clear locality selection"
              >
                ×
              </button>
            )}
          </div>

          {/* Category Selector with Live Icon Badge */}
          <div className="flex items-center gap-1.5 bg-white border border-slate-200 rounded-lg px-2 py-1 shadow-sm">
            <span
              className="w-5 h-5 rounded-md flex items-center justify-center shrink-0 text-white shadow-xs"
              style={{ backgroundColor: getCategoryConfig(selectedCategory).color }}
              dangerouslySetInnerHTML={{ __html: getCategoryConfig(selectedCategory).icon }}
            />
            <select
              value={selectedCategory}
              onChange={(e) => {
                const newCat = e.target.value;
                const hadExistingOsm = overpassFacilities.length > 0;
                setSelectedCategory(newCat);
                setOverpassFacilities([]);
                setOsmNotice(null);
                if (hadExistingOsm) {
                  handleQueryOverpass(selectedLocality, newCat);
                }
              }}
              className="text-xs font-semibold bg-transparent text-slate-700 focus:outline-none cursor-pointer"
            >
              <option value="all">🌐 All Service Types</option>
              <option value="healthcare">🏥 Healthcare (Clinics/Hospitals)</option>
              <option value="education">🎓 Education (Schools/Colleges)</option>
              <option value="transport">🚌 Transport (Hubs/Stops)</option>
              <option value="water">💧 Water & Sanitation</option>
              <option value="market">🛒 Essential Food Markets</option>
            </select>
          </div>

          {/* Overpass Query Trigger with Category-Matched Icon & Theme */}
          <button
            onClick={() => handleQueryOverpass()}
            disabled={isQueryingOverpass}
            title={
              selectedLocality
                ? `Query live OpenStreetMap amenities for ${selectedLocality.name}`
                : `Query live OpenStreetMap amenities for ${CITIES[selectedCity]?.name || 'city'}`
            }
            className="flex items-center gap-1.5 text-xs font-semibold text-white px-3 py-1.5 rounded-lg transition-all shadow-sm disabled:opacity-50 cursor-pointer hover:brightness-105 active:scale-95"
            style={{
              backgroundColor:
                selectedCategory !== 'all'
                  ? getCategoryConfig(selectedCategory).color
                  : '#4f46e5',
            }}
          >
            {isQueryingOverpass ? (
              <RefreshCw className="w-3.5 h-3.5 animate-spin text-white" />
            ) : (
              <span
                className="w-3.5 h-3.5 flex items-center justify-center text-white shrink-0"
                dangerouslySetInnerHTML={{
                  __html:
                    selectedCategory !== 'all'
                      ? getCategoryConfig(selectedCategory).icon
                      : `<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>`,
                }}
              />
            )}
            <span>
              {isQueryingOverpass
                ? 'Querying OSM...'
                : selectedLocality
                ? `Query OSM ${selectedCategory !== 'all' ? capitalize(selectedCategory) : ''} (${selectedLocality.name.split('/')[0].trim()})`
                : `Query OSM ${selectedCategory !== 'all' ? capitalize(selectedCategory) : ''}`}
            </span>
          </button>
        </div>
      </div>

      {/* Quick Locality Selector Pills Bar */}
      <div className="bg-slate-50/95 backdrop-blur-xs px-4 py-1.5 border-b border-slate-200/80 flex items-center gap-2 overflow-x-auto text-[11px] z-10">
        <span className="text-slate-500 font-semibold shrink-0 flex items-center gap-1">
          <MapPin className="w-3 h-3 text-slate-400" />
          Choose Locality:
        </span>
        {areas?.features?.map((f: any) => {
          const isSelected = selectedLocality && String(selectedLocality.id) === String(f.properties?.id ?? f.id);
          return (
            <button
              key={`pill-${f.properties?.id ?? f.id}`}
              onClick={() => handleSelectLocality(f.properties, f.geometry)}
              className={`px-3 py-1 rounded-full font-medium shrink-0 transition-all cursor-pointer ${
                isSelected
                  ? 'bg-blue-600 text-white shadow-xs font-semibold'
                  : 'bg-white hover:bg-slate-100 text-slate-700 border border-slate-200 hover:border-slate-300'
              }`}
            >
              {f.properties?.name?.split('/')[0]?.trim()}
            </button>
          );
        })}
        {selectedLocality && (
          <button
            onClick={() => handleSelectLocality(null)}
            className="text-blue-600 hover:text-blue-800 font-semibold text-[11px] ml-auto shrink-0 flex items-center gap-0.5 cursor-pointer"
          >
            <span>Reset to Whole City</span>
            <span className="font-bold">×</span>
          </button>
        )}
      </div>

      {/* Main Map Canvas */}
      <div className="relative flex-1 w-full h-full min-h-[460px]">
        {/* Loading Overlay */}
        {isLoading && (
          <div className="absolute inset-0 z-[1000] bg-white/70 backdrop-blur-xs flex items-center justify-center">
            <div className="bg-white px-4 py-3 rounded-xl shadow-lg border border-slate-200 flex items-center gap-3">
              <RefreshCw className="w-5 h-5 text-blue-600 animate-spin" />
              <span className="text-sm font-semibold text-slate-700">Loading civic geospatial data...</span>
            </div>
          </div>
        )}

        {/* Tile Error Fallback Notice */}
        {tileError && (
          <div className="absolute top-4 left-4 z-[1000] max-w-sm bg-amber-50 border border-amber-200 text-amber-900 p-3 rounded-xl shadow-md text-xs flex gap-2">
            <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
            <div>
              <p className="font-bold">Map Tiles Degraded</p>
              <p className="text-amber-800">
                OpenStreetMap tiles are currently slow or unreachable. Civic facilities and boundaries remain interactive.
              </p>
            </div>
          </div>
        )}

        {/* Leaflet MapContainer */}
        <MapContainer
          center={center}
          zoom={zoom}
          style={{ height: '100%', width: '100%', minHeight: '460px' }}
          scrollWheelZoom={true}
        >
          {/* OpenStreetMap TileLayer with visible attribution and no API key required */}
          <TileLayer
            url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener noreferrer">OpenStreetMap contributors</a> | CivicPulse'
            maxZoom={19}
            eventHandlers={{
              tileerror: () => {
                setTileError(true);
              },
            }}
          />

          <MapViewController targetCenter={mapTargetCenter} targetZoom={mapTargetZoom} />

          {/* Locality Boundary - Render ONLY for the selected area */}
          {activeAreasGeoJson && (
            <GeoJSON
              key={`selected-area-${selectedLocality?.id}`}
              data={activeAreasGeoJson as any}
              style={getLocalityStyle}
              onEachFeature={onEachFeature}
            />
          )}

          {/* Service Facilities Markers */}
          {(activeLayer === 'services' || activeLayer === 'accessibility' || activeLayer === 'gap') && (
            <>
              {displayedServices.map((facility, idx) => (
                <Marker
                  key={`srv-${facility.id ?? idx}-${facility.category_code}-${selectedCategory}`}
                  position={[facility.latitude, facility.longitude]}
                  icon={createCategoryPinIcon(
                    facility.category_code,
                    false,
                    selectedCategory !== 'all' ? selectedCategory : 'healthcare'
                  )}
                >
                  <Popup className="civic-custom-popup">
                    <div className="font-sans min-w-[220px] p-1">
                      <div className="flex items-center justify-between gap-2 border-b border-slate-100 pb-2 mb-2">
                        <span className="text-[10px] font-bold uppercase tracking-wider text-blue-700 bg-blue-50 px-2 py-0.5 rounded">
                          {facility.category_name}
                        </span>
                        <div className="flex items-center gap-1.5 text-xs">
                          <span
                            className={`w-2 h-2 rounded-full ${
                              facility.status === 'operational'
                                ? 'bg-emerald-500'
                                : facility.status === 'degraded'
                                ? 'bg-amber-500'
                                : 'bg-red-500'
                            }`}
                          />
                          <span className="capitalize font-medium text-slate-600 text-[11px]">{facility.status}</span>
                        </div>
                      </div>

                      <h4 className="font-bold text-slate-900 text-sm leading-tight mb-1">{facility.name}</h4>
                      {facility.area_name && (
                        <p className="text-xs text-slate-500 flex items-center gap-1 mb-2">
                          <MapPin className="w-3 h-3 text-slate-400" />
                          {facility.area_name}
                        </p>
                      )}

                      {facility.capacity != null && (
                        <div className="bg-slate-50 p-2 rounded-lg border border-slate-100 mb-2">
                          <div className="flex justify-between text-[11px] font-medium text-slate-600 mb-1">
                            <span>Capacity Load:</span>
                            <span className="font-bold text-slate-900">
                              {facility.current_load ?? 0} / {facility.capacity}
                            </span>
                          </div>
                          <div className="w-full bg-slate-200 h-1.5 rounded-full overflow-hidden">
                            <div
                              className={`h-full rounded-full ${
                                ((facility.current_load ?? 0) / facility.capacity) * 100 > 90
                                  ? 'bg-red-500'
                                  : 'bg-blue-600'
                              }`}
                              style={{
                                width: `${Math.min(100, Math.round(((facility.current_load ?? 0) / facility.capacity) * 100))}%`,
                              }}
                            />
                          </div>
                        </div>
                      )}

                      {facility.operating_hours && (
                        <p className="text-[11px] text-slate-600 flex items-center gap-1 mb-2">
                          <Clock className="w-3 h-3 text-slate-400" />
                          {facility.operating_hours}
                        </p>
                      )}

                      <div className="flex items-center justify-between text-[10px] text-slate-400 pt-2 border-t border-slate-100">
                        <span>Source: {facility.source_type}</span>
                        <span className="flex items-center gap-1 text-emerald-600 font-medium">
                          <CheckCircle2 className="w-3 h-3" />
                          {facility.verification_status}
                        </span>
                      </div>
                    </div>
                  </Popup>
                </Marker>
              ))}

              {/* Overpass Live Imported Amenities */}
              {overpassFacilities
                .filter((facility) => {
                  if (selectedCategory === 'all') return true;
                  const cat = (facility.category_code || '').toLowerCase();
                  const sel = selectedCategory.toLowerCase();
                  if (!cat) return true;
                  return cat === sel || cat.includes(sel) || sel.includes(cat);
                })
                .map((facility, idx) => {
                  const effectiveCategory =
                    (selectedCategory !== 'all' ? selectedCategory : facility.category_code) || 'transport';
                  const cfg = getCategoryConfig(effectiveCategory);
                  const displayCategoryName = (
                    selectedCategory !== 'all'
                      ? selectedCategory
                      : facility.category_name || facility.category_code || 'transport'
                  ).toUpperCase();

                  return (
                    <Marker
                      key={`osm-${facility.id ?? idx}-${effectiveCategory}-${selectedCategory}`}
                      position={[facility.latitude, facility.longitude]}
                      icon={createCategoryPinIcon(
                        effectiveCategory,
                        true,
                        selectedCategory !== 'all' ? selectedCategory : 'transport'
                      )}
                    >
                      <Popup className="civic-custom-popup">
                        <div className="font-sans min-w-[230px] p-1">
                          <div className="flex items-center justify-between gap-2 border-b border-slate-100 pb-2 mb-2">
                            <span
                              className="text-[10px] font-bold px-2 py-0.5 rounded uppercase tracking-wider"
                              style={{ backgroundColor: cfg.bg, color: cfg.text }}
                            >
                              {displayCategoryName}
                            </span>
                            <span
                              className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                                facility.is_demo_data
                                  ? 'bg-amber-50 text-amber-800'
                                  : 'bg-indigo-100 text-indigo-800'
                              }`}
                            >
                              {facility.is_demo_data ? 'Demo Fallback' : 'OSM Live'}
                            </span>
                          </div>

                          <h4 className="font-bold text-slate-900 text-sm leading-tight mb-1">
                            {facility.name}
                          </h4>

                      <div className="text-[11px] text-slate-500 space-y-1 mb-2">
                        <p className="flex items-center gap-1">
                          <MapPin className="w-3 h-3 text-slate-400" />
                          <span>
                            {facility.latitude.toFixed(4)}, {facility.longitude.toFixed(4)}
                            {facility.osm_type && facility.osm_type !== 'node' ? ' (Area Centroid)' : ''}
                          </span>
                        </p>
                        {facility.osm_id && (
                          <p className="text-[10px] font-mono text-slate-400">
                            OSM ID: #{facility.osm_id} ({facility.osm_type || 'node'})
                          </p>
                        )}
                        {facility.operating_hours && (
                          <p className="flex items-center gap-1 text-slate-600">
                            <Clock className="w-3 h-3 text-slate-400" />
                            <span>{facility.operating_hours}</span>
                          </p>
                        )}
                        {facility.capacity != null && (
                          <p className="text-slate-600 font-medium">Reported Capacity: {facility.capacity}</p>
                        )}
                      </div>

                      {/* OpenStreetMap Raw Tags Breakdown */}
                      {facility.tags && Object.keys(facility.tags).length > 0 && (
                        <div className="bg-slate-50 p-2 rounded-lg border border-slate-100 mb-2 text-[10px] text-slate-600 space-y-0.5">
                          {facility.tags.amenity && (
                            <div><span className="font-semibold text-slate-700">amenity:</span> {facility.tags.amenity}</div>
                          )}
                          {facility.tags.healthcare && (
                            <div><span className="font-semibold text-slate-700">healthcare:</span> {facility.tags.healthcare}</div>
                          )}
                          {facility.tags.highway && (
                            <div><span className="font-semibold text-slate-700">highway:</span> {facility.tags.highway}</div>
                          )}
                          {facility.tags.operator && (
                            <div><span className="font-semibold text-slate-700">operator:</span> {facility.tags.operator}</div>
                          )}
                        </div>
                      )}

                      <div className="flex items-center justify-between text-[10px] text-slate-400 pt-2 border-t border-slate-100">
                        <span>Source: {facility.source_type}</span>
                        <span className="text-indigo-600 font-bold">ODbL 1.0</span>
                      </div>
                    </div>
                  </Popup>
                </Marker>
              );
            })}
            </>
          )}

          {/* Community Reports Layer */}
          {activeLayer === 'reports' &&
            reports.map((report) => (
              <Marker
                key={`rep-${report.id}`}
                position={[report.latitude, report.longitude]}
                icon={createReportPinIcon(report.severity)}
              >
                <Popup>
                  <div className="font-sans min-w-[220px] p-1">
                    <div className="flex items-center justify-between gap-2 mb-1">
                      <span
                        className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded ${
                          report.severity === 'critical'
                            ? 'bg-red-100 text-red-800'
                            : 'bg-amber-100 text-amber-800'
                        }`}
                      >
                        {report.severity} Alert
                      </span>
                      <span className="text-[11px] font-mono text-slate-400">{report.created_at}</span>
                    </div>
                    <h4 className="font-bold text-slate-900 text-sm leading-snug">{report.title}</h4>
                    <p className="text-xs text-slate-600 mt-1 leading-relaxed">{report.description}</p>
                    <div className="mt-3 pt-2 border-t border-slate-100 flex justify-between items-center text-[11px]">
                      <span className="font-semibold text-slate-700">{report.area_name}</span>
                      <span className="font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded">
                        {report.verification_status}
                      </span>
                    </div>
                  </div>
                </Popup>
              </Marker>
            ))}

          {/* Recommended Locations Layer */}
          {activeLayer === 'recommendations' &&
            recommendations.map((rec) => (
              <Marker
                key={`rec-${rec.candidate_id}`}
                position={[rec.latitude, rec.longitude]}
                icon={createRecommendationPinIcon(rec.rank)}
              >
                <Popup>
                  <div className="font-sans min-w-[240px] p-1">
                    <div className="flex items-center justify-between gap-2 mb-1">
                      <span className="text-[10px] font-extrabold uppercase tracking-wider bg-purple-100 text-purple-800 px-2 py-0.5 rounded flex items-center gap-1">
                        <Sparkles className="w-3 h-3" /> Rank #{rec.rank}
                      </span>
                      <span className="text-xs font-bold text-purple-700">Score: {rec.recommendation_score}</span>
                    </div>
                    <h4 className="font-bold text-slate-900 text-sm mt-1">{rec.area_name} Planned Intervention</h4>
                    <p className="text-xs text-slate-500 capitalize">Category: {rec.service_type}</p>
                    <div className="mt-2 text-xs text-slate-600 bg-slate-50 p-2 rounded-lg border border-slate-100">
                      <p className="font-semibold text-slate-800 mb-1">Recommendation Reasons:</p>
                      <ul className="list-disc list-inside space-y-0.5 text-[11px]">
                        {rec.reasons.map((r, i) => (
                          <li key={i}>{r}</li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </Popup>
              </Marker>
            ))}
        </MapContainer>

        {/* Overpass Status Alert Notice Banner */}
        {osmNotice && (
          <div
            className={`absolute top-4 left-4 z-[1000] max-w-md backdrop-blur-md px-3.5 py-2.5 rounded-xl shadow-lg border text-xs flex items-center gap-2.5 animate-in fade-in duration-200 ${
              osmNotice.type === 'loading'
                ? 'bg-blue-50/95 border-blue-200 text-blue-900'
                : osmNotice.type === 'success'
                ? 'bg-emerald-50/95 border-emerald-200 text-emerald-900'
                : osmNotice.type === 'empty'
                ? 'bg-amber-50/95 border-amber-200 text-amber-900'
                : osmNotice.type === 'timeout'
                ? 'bg-orange-50/95 border-orange-200 text-orange-900'
                : 'bg-rose-50/95 border-rose-200 text-rose-900'
            }`}
          >
            {osmNotice.type === 'loading' && <RefreshCw className="w-4 h-4 text-blue-600 animate-spin shrink-0" />}
            {osmNotice.type === 'success' && <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />}
            {osmNotice.type === 'empty' && <Info className="w-4 h-4 text-amber-600 shrink-0" />}
            {osmNotice.type === 'timeout' && <Clock className="w-4 h-4 text-orange-600 shrink-0" />}
            {osmNotice.type === 'error' && <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0" />}
            <span className="font-medium leading-relaxed">{osmNotice.message}</span>
            <button
              onClick={() => setOsmNotice(null)}
              className="text-slate-400 hover:text-slate-600 ml-auto shrink-0 p-0.5 rounded"
              title="Dismiss"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        )}

        {/* Area Inspector Side Panel: Prompts selection when unselected, reveals details once selected */}
        {!selectedLocality ? (
          <div className="absolute top-4 right-4 z-[1000] w-76 bg-white/95 backdrop-blur-md rounded-2xl p-4 shadow-xl border border-slate-200 text-xs animate-in fade-in duration-200">
            <div className="flex items-center gap-2 mb-1.5 text-slate-900 font-extrabold text-sm">
              <MapPin className="w-4 h-4 text-blue-600" />
              <span>Select an Area in Indore</span>
            </div>
            <p className="text-slate-500 text-[11px] leading-relaxed mb-3">
              Choose an area below or from the toolbar to view its boundary, population census, and service deficits:
            </p>
            <div className="space-y-1.5">
              {areas?.features?.map((f: any) => (
                <button
                  key={`prompt-${f.properties?.id ?? f.id}`}
                  onClick={() => handleSelectLocality(f.properties, f.geometry)}
                  className="w-full text-left px-3 py-2 rounded-xl bg-slate-50 hover:bg-blue-50 hover:text-blue-700 border border-slate-200/80 text-[11px] font-semibold flex items-center justify-between transition-colors cursor-pointer group"
                >
                  <span className="truncate">{f.properties?.name}</span>
                  <span className="text-[10px] text-slate-400 group-hover:text-blue-600 font-bold shrink-0 ml-1">
                    Select →
                  </span>
                </button>
              ))}
            </div>
            <div className="mt-3 pt-2.5 border-t border-slate-100 text-[10px] text-slate-400 flex items-center gap-1">
              <Compass className="w-3 h-3 text-slate-400" />
              <span>Click any locality to focus and inspect</span>
            </div>
          </div>
        ) : (
          <div className="absolute top-4 right-4 z-[1000] w-84 max-h-[calc(100vh-140px)] flex flex-col bg-white/95 backdrop-blur-md rounded-2xl p-4 shadow-xl border border-slate-200 animate-in fade-in slide-in-from-right-4 duration-300">
            {/* Header */}
            <div className="flex items-start justify-between border-b border-slate-100 pb-2.5 mb-2.5 shrink-0">
              <div>
                <span className="text-[10px] font-bold uppercase tracking-wider text-blue-600 bg-blue-50 px-2 py-0.5 rounded">
                  {selectedLocality.area_type}
                </span>
                <h3 className="text-base font-extrabold text-slate-900 mt-1 leading-tight">{selectedLocality.name}</h3>
              </div>
              <button
                onClick={() => handleSelectLocality(null)}
                className="text-slate-400 hover:text-slate-600 p-1 rounded-lg hover:bg-slate-100 transition-colors cursor-pointer"
                title="Close inspector"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Scrollable Body */}
            <div className="overflow-y-auto space-y-2.5 pr-1 text-xs flex-1">
              {/* Locality Quick Metrics */}
              <div className="grid grid-cols-2 gap-2 bg-slate-50 p-2 rounded-xl border border-slate-100">
                <div>
                  <span className="text-[10px] text-slate-500 block">Population</span>
                  <span className="font-extrabold text-slate-800 text-xs">
                    {selectedLocality.population.toLocaleString()}
                  </span>
                </div>
                <div>
                  <span className="text-[10px] text-slate-500 block">Accessibility</span>
                  <span
                    className={`font-bold text-xs ${
                      (selectedLocality.accessibility_score ?? 50) >= 80
                        ? 'text-emerald-700'
                        : (selectedLocality.accessibility_score ?? 50) >= 60
                        ? 'text-amber-700'
                        : 'text-red-700'
                    }`}
                  >
                    {selectedLocality.accessibility_score ?? 'N/A'} / 100
                  </span>
                </div>
                {selectedLocality.nearest_service && (
                  <div className="col-span-2 pt-1 border-t border-slate-200/60 flex items-center justify-between text-[11px]">
                    <span className="text-slate-500">Nearest Amenity:</span>
                    <span className="font-semibold text-slate-800 truncate max-w-[170px]" title={selectedLocality.nearest_service}>
                      {selectedLocality.nearest_service}
                    </span>
                  </div>
                )}
                {selectedLocality.travel_time && (
                  <div className="col-span-2 flex items-center justify-between text-[11px]">
                    <span className="text-slate-500">Est. Travel Time:</span>
                    <span className="font-semibold text-slate-800">{selectedLocality.travel_time}</span>
                  </div>
                )}
              </div>

              {/* No Related Data Warning Banner */}
              {osmProblemReport?.hasNoData ? (
                <div className="bg-amber-50/95 border border-amber-200/90 rounded-xl p-3 text-xs shadow-2xs">
                  <div className="flex items-center gap-1.5 text-amber-950 font-bold mb-1">
                    <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
                    <span>No {osmProblemReport.categoryLabel} Amenities Found</span>
                  </div>
                  <p className="text-amber-900 text-[11px] leading-relaxed">
                    OpenStreetMap currently has <strong>zero mapped {osmProblemReport.categoryLabel.toLowerCase()} facilities</strong> within {selectedLocality.name.split('/')[0].trim()}&apos;s boundary.
                  </p>
                  <div className="mt-2 pt-2 border-t border-amber-200/70 text-[11px] text-amber-950 flex items-center justify-between">
                    <span className="text-amber-800 font-medium">Affected Population:</span>
                    <strong className="font-extrabold">{selectedLocality.population.toLocaleString()} residents</strong>
                  </div>
                </div>
              ) : osmProblemReport && !osmProblemReport.hasNoData ? (
                <div className="bg-emerald-50/95 border border-emerald-200/90 rounded-xl p-2.5 text-xs shadow-2xs">
                  <div className="flex items-center justify-between text-emerald-950 font-bold mb-0.5">
                    <span className="flex items-center gap-1.5 text-[11px]">
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                      OSM Facilities Verified
                    </span>
                    <span className="bg-emerald-100 text-emerald-800 px-2 py-0.5 rounded-full text-[10px] font-extrabold">
                      {osmProblemReport.facilityCount} Facilities Live
                    </span>
                  </div>
                  <p className="text-emerald-800 text-[10px]">
                    Mapped within {selectedLocality.name.split('/')[0].trim()} boundary via OpenStreetMap.
                  </p>
                </div>
              ) : null}

              {/* Problems Related to OSM Selected Query */}
              {osmProblemReport && osmProblemReport.problems.length > 0 && (
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-slate-800 flex items-center gap-1 text-[11px]">
                      <AlertCircle className="w-3.5 h-3.5 text-rose-600 shrink-0" />
                      Problems Detected via OSM
                    </span>
                    <span className="text-[10px] font-extrabold uppercase bg-rose-50 text-rose-700 px-1.5 py-0.5 rounded border border-rose-100">
                      {osmProblemReport.problems.length} Deficits
                    </span>
                  </div>
                  <div className="space-y-1.5 max-h-48 overflow-y-auto pr-0.5">
                    {osmProblemReport.problems.map((prob, i) => (
                      <div
                        key={`osm-prob-${i}`}
                        className={`p-2.5 rounded-xl border text-[11px] space-y-0.5 shadow-2xs ${
                          prob.severity === 'critical'
                            ? 'bg-rose-50/90 border-rose-200 text-rose-950'
                            : prob.severity === 'high'
                            ? 'bg-orange-50/90 border-orange-200 text-orange-950'
                            : 'bg-amber-50/90 border-amber-200 text-amber-950'
                        }`}
                      >
                        <div className="flex items-center justify-between gap-1">
                          <span className="font-bold flex items-center gap-1.5">
                            <span
                              className={`w-1.5 h-1.5 rounded-full shrink-0 ${
                                prob.severity === 'critical'
                                  ? 'bg-rose-600'
                                  : prob.severity === 'high'
                                  ? 'bg-orange-600'
                                  : 'bg-amber-600'
                              }`}
                            />
                            {prob.title}
                          </span>
                          <span
                            className={`text-[9px] uppercase font-bold px-1.5 py-0.5 rounded shrink-0 ${
                              prob.severity === 'critical'
                                ? 'bg-rose-200/80 text-rose-800'
                                : 'bg-orange-200/80 text-orange-800'
                            }`}
                          >
                            {prob.severity}
                          </span>
                        </div>
                        <p className="text-[11px] leading-relaxed opacity-90">{prob.description}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Primary Gap Card if no OSM report */}
              {!osmProblemReport && selectedLocality.main_gap && (
                <div className="bg-red-50/70 border border-red-100 p-2.5 rounded-xl">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-red-600 block mb-0.5">
                    Primary Service Gap
                  </span>
                  <p className="font-semibold text-red-900 leading-snug">{selectedLocality.main_gap}</p>
                </div>
              )}
            </div>

            {/* Actions Footer */}
            <div className="pt-2.5 mt-2 border-t border-slate-100 shrink-0 space-y-2">
              <button
                onClick={() => handleQueryOverpass(selectedLocality)}
                disabled={isQueryingOverpass}
                className="w-full flex items-center justify-center gap-1.5 text-xs font-bold bg-indigo-600 hover:bg-indigo-700 text-white py-2 px-3 rounded-xl transition-all shadow-xs disabled:opacity-50 cursor-pointer"
              >
                {isQueryingOverpass ? (
                  <RefreshCw className="w-3.5 h-3.5 animate-spin text-white" />
                ) : (
                  <Search className="w-3.5 h-3.5 text-white" />
                )}
                <span>
                  {isQueryingOverpass ? 'Querying OSM...' : `Query OSM for ${selectedLocality.name.split('/')[0].trim()}`}
                </span>
              </button>

              <div className="flex items-center gap-1 text-[10px]">
                <button
                  onClick={() => setActiveLayer('gap')}
                  className="flex-1 py-1 px-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold text-center transition-colors cursor-pointer"
                >
                  Service Gaps
                </button>
                <button
                  onClick={() => setActiveLayer('recommendations')}
                  className="flex-1 py-1 px-1.5 rounded-lg bg-purple-50 hover:bg-purple-100 text-purple-700 font-semibold text-center transition-colors cursor-pointer"
                >
                  Interventions
                </button>
                <button
                  onClick={() => setActiveLayer('reports')}
                  className="flex-1 py-1 px-1.5 rounded-lg bg-blue-50 hover:bg-blue-100 text-blue-700 font-semibold text-center transition-colors cursor-pointer"
                >
                  Reports ({reports.length})
                </button>
              </div>

              <div className="flex items-center justify-between text-[10px] text-slate-400 pt-1 border-t border-slate-100">
                <span className="flex items-center gap-1">
                  <Compass className="w-3 h-3 text-slate-400" />
                  {dataStatus.isLive ? 'Backend Live Engine' : 'Deterministic Seed Model'}
                </span>
                <button
                  onClick={() => handleSelectLocality(null)}
                  className="text-blue-600 hover:text-blue-800 font-semibold cursor-pointer"
                >
                  Reset City
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Floating Map Legend (Bottom-Left) */}
        <div className="absolute bottom-6 left-4 z-[1000] bg-white/90 backdrop-blur-md px-3.5 py-3 rounded-2xl shadow-lg border border-slate-200 text-xs max-w-[260px]">
          <h4 className="font-bold text-slate-800 text-[11px] uppercase tracking-wider mb-2 flex items-center gap-1.5">
            <MapPin className="w-3.5 h-3.5 text-blue-600" />
            <span>Map Legend</span>
          </h4>

          {/* Color scale for accessibility & gap layers */}
          {(activeLayer === 'accessibility' || activeLayer === 'gap') && (
            <div className="space-y-1 mb-2.5 pb-2.5 border-b border-slate-100">
              <span className="text-[10px] font-bold text-slate-500 block">Accessibility Tiers:</span>
              <div className="grid grid-cols-2 gap-1 text-[10px]">
                <div className="flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-sm bg-emerald-500 shrink-0" />
                  <span className="text-slate-600">Well Served (80+)</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-sm bg-amber-400 shrink-0" />
                  <span className="text-slate-600">Adequate (60-79)</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-sm bg-orange-500 shrink-0" />
                  <span className="text-slate-600">Underserved (40-59)</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-sm bg-red-500 shrink-0" />
                  <span className="text-slate-600">Critical Gap (&lt;40)</span>
                </div>
              </div>
            </div>
          )}

          {/* Service Category Icons with Actual Logos */}
          <div className="grid grid-cols-2 gap-2 text-[10px]">
            <div className="flex items-center gap-1.5">
              <span
                className="w-4 h-4 rounded-full bg-red-500 text-white flex items-center justify-center shrink-0 shadow-xs p-0.5"
                dangerouslySetInnerHTML={{ __html: CATEGORY_CONFIG.healthcare.icon }}
              />
              <span className="text-slate-700 font-medium">Healthcare</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span
                className="w-4 h-4 rounded-full bg-blue-500 text-white flex items-center justify-center shrink-0 shadow-xs p-0.5"
                dangerouslySetInnerHTML={{ __html: CATEGORY_CONFIG.education.icon }}
              />
              <span className="text-slate-700 font-medium">Education</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span
                className="w-4 h-4 rounded-full bg-amber-500 text-white flex items-center justify-center shrink-0 shadow-xs p-0.5"
                dangerouslySetInnerHTML={{ __html: CATEGORY_CONFIG.transport.icon }}
              />
              <span className="text-slate-700 font-medium">Transport</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span
                className="w-4 h-4 rounded-full bg-cyan-500 text-white flex items-center justify-center shrink-0 shadow-xs p-0.5"
                dangerouslySetInnerHTML={{ __html: CATEGORY_CONFIG.water.icon }}
              />
              <span className="text-slate-700 font-medium">Water Points</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span
                className="w-4 h-4 rounded-full bg-emerald-500 text-white flex items-center justify-center shrink-0 shadow-xs p-0.5"
                dangerouslySetInnerHTML={{ __html: CATEGORY_CONFIG.market.icon }}
              />
              <span className="text-slate-700 font-medium">Food Markets</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-4 h-4 rounded-full bg-purple-600 text-white flex items-center justify-center shrink-0 shadow-xs p-0.5">
                <Sparkles className="w-2.5 h-2.5 text-white" />
              </span>
              <span className="text-slate-700 font-medium">Interventions</span>
            </div>
          </div>
        </div>

        {/* Data Mode & Attribution Indicator (Bottom-Right) */}
        <div className="absolute bottom-6 right-4 z-[1000] bg-white/90 backdrop-blur-md px-3 py-1.5 rounded-xl shadow border border-slate-200 text-[10px] flex items-center gap-2">
          <span
            className={`w-2 h-2 rounded-full ${dataStatus.isLive ? 'bg-emerald-500 animate-pulse' : 'bg-blue-500'}`}
          />
          <span className="font-semibold text-slate-700">
            {dataStatus.isLive ? 'Live API Connected' : 'Deterministic Demo Mode'}
          </span>
          <span className="text-slate-400">|</span>
          <span className="text-slate-500">{displayedServices.length} Facilities Active</span>
          {overpassFacilities.length > 0 && (
            <>
              <span className="text-slate-400">|</span>
              <span className="bg-indigo-100 text-indigo-800 font-bold px-1.5 py-0.5 rounded text-[9px]">
                {overpassFacilities.length} OSM Live
              </span>
            </>
          )}
          <span className="text-slate-400">|</span>
          <span className="text-slate-400 font-normal">
            &copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener noreferrer" className="underline hover:text-slate-600">OpenStreetMap contributors</a>
          </span>
        </div>
      </div>
    </div>
  );
};
