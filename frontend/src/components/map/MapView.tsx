import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { MapContainer, TileLayer, Marker, Popup, GeoJSON, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import {
  AlertTriangle,
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
    icon: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"/><path d="M12 5v14"/><path d="M5 12h14"/></svg>`,
  },
  education: {
    label: 'Education',
    color: '#3b82f6',
    bg: '#dbeafe',
    border: '#60a5fa',
    text: '#1d4ed8',
    icon: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M22 10v6M2 10l10-5 10 5-10 5z"/><path d="M6 12v5c3 3 9 3 12 0v-5"/></svg>`,
  },
  transport: {
    label: 'Transport',
    color: '#f59e0b',
    bg: '#fef3c7',
    border: '#fbbf24',
    text: '#b45309',
    icon: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><rect width="16" height="16" x="4" y="3" rx="2"/><path d="M4 11h16"/><path d="M8 15h.01"/><path d="M16 15h.01"/><path d="m6 19-2 2"/><path d="m18 19 2 2"/></svg>`,
  },
  water: {
    label: 'Water & Sanitation',
    color: '#06b6d4',
    bg: '#cffafe',
    border: '#22d3ee',
    text: '#0e7490',
    icon: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M12 22a7 7 0 0 0 7-7c0-2-1-3.9-3-5.5s-3.5-4-4-6.5c-.5 2.5-2 4.9-4 6.5C6 11.1 5 13 5 15a7 7 0 0 0 7 7z"/></svg>`,
  },
  market: {
    label: 'Markets & Food',
    color: '#10b981',
    bg: '#d1fae5',
    border: '#34d399',
    text: '#047857',
    icon: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="m2 7 4.41-4.41A2 2 0 0 1 7.83 2h8.34a2 2 0 0 1 1.42.59L22 7"/><path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8"/><path d="M15 22v-4a2 2 0 0 0-2-2h-2a2 2 0 0 0-2 2v4"/><path d="M2 7h20"/></svg>`,
  },
};

// Create custom pin icons with Leaflet L.divIcon
function createCategoryPinIcon(categoryCode: string, isOverpass = false) {
  const cfg = CATEGORY_CONFIG[categoryCode.toLowerCase()] || CATEGORY_CONFIG.healthcare;
  const badgeHtml = `
    <div style="
      background-color: ${cfg.color};
      color: white;
      width: 28px;
      height: 28px;
      border-radius: 50% 50% 50% 0;
      transform: rotate(-45deg);
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 4px 8px rgba(0,0,0,0.25);
      border: 2px solid white;
      transition: transform 0.15s ease;
      cursor: pointer;
    ">
      <div style="transform: rotate(45deg); display: flex; align-items: center; justify-content: center;">
        ${cfg.icon}
      </div>
    </div>
    ${
      isOverpass
        ? `<div style="position: absolute; bottom: -4px; right: -4px; background: #6366f1; color: white; border-radius: 50%; width: 12px; height: 12px; font-size: 8px; font-weight: bold; display: flex; align-items: center; justify-content: center; border: 1px solid white;">OSM</div>`
        : ''
    }
  `;

  return L.divIcon({
    html: `<div style="position: relative; width: 28px; height: 28px;">${badgeHtml}</div>`,
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

const INITIAL_DATA_STATUS: DataFetchStatus = {
  source: 'demo',
  isLive: false,
  lastUpdated: new Date(0),
};

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

  // Telemetry & UI State
  const [dataStatus, setDataStatus] = useState<DataFetchStatus>({
    source: 'live',
    isLive: true,
    lastUpdated: new Date(),
  });
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

  // Synchronize external selection and pan map to locality
  const handleSelectLocality = useCallback(
    (loc: LocalityProperties | null) => {
      setSelectedLocality(loc);
      if (loc && (loc as any).geometry && (loc as any).geometry.type === 'Polygon') {
        const coords = (loc as any).geometry.coordinates[0];
        if (coords && coords.length > 0) {
          const avgLon = coords.reduce((acc: number, c: number[]) => acc + c[0], 0) / coords.length;
          const avgLat = coords.reduce((acc: number, c: number[]) => acc + c[1], 0) / coords.length;
          setMapTargetCenter([avgLat, avgLon]);
          setMapTargetZoom(14);
        }
      }
      if (onLocalitySelect) {
        onLocalitySelect(loc);
      }
    },
    [onLocalitySelect]
  );

  // Switch City Context
  const handleCityChange = (cityId: 'indore' | 'bengaluru') => {
    setSelectedCity(cityId);
    setSelectedLocality(null);
    setOverpassFacilities([]);
    setOsmNotice(null);
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
  const handleQueryOverpass = async (targetLocality?: LocalityProperties | null) => {
    setIsQueryingOverpass(true);
    const target = targetLocality || selectedLocality;
    const city = CITIES[selectedCity] || CITIES.indore;
    const locName = target ? target.name : city.name;

    setOsmNotice({
      type: 'loading',
      message: `Querying OpenStreetMap Overpass provider for ${selectedCategory === 'all' ? 'civic' : selectedCategory} amenities in ${locName}...`,
    });

    try {
      const res = await queryOverpassServices({
        localityName: target ? target.name : city.name,
        areaId: target ? target.id : undefined,
        bbox: target ? undefined : city.bbox,
        category: selectedCategory,
        forceLive: true,
        cityId: selectedCity,
      });

      setIsQueryingOverpass(false);

      if (res.status === 'empty' || res.facilities.length === 0) {
        setOverpassFacilities([]);
        setOsmNotice({
          type: 'empty',
          message: `No ${selectedCategory === 'all' ? 'civic' : selectedCategory} facilities found on OpenStreetMap for ${locName}.`,
        });
      } else if (res.status === 'timeout') {
        setOverpassFacilities(res.facilities);
        setOsmNotice({
          type: 'timeout',
          message: res.warning || `Overpass query timed out for ${locName}. Showing deterministic local fallback data.`,
        });
      } else if (res.status === 'error') {
        setOverpassFacilities(res.facilities);
        setOsmNotice({
          type: 'error',
          message: res.warning || res.error || `Overpass service encountered an issue. Preserving deterministic local data.`,
        });
      } else {
        setOverpassFacilities(res.facilities);
        setOsmNotice({
          type: 'success',
          message: `Retrieved ${res.facilities.length} ${selectedCategory === 'all' ? 'civic' : selectedCategory} facilities from OpenStreetMap (${res.cached ? 'from cache' : 'fresh Overpass query'}).`,
        });
      }
    } catch (err: any) {
      setIsQueryingOverpass(false);
      setOsmNotice({
        type: 'error',
        message: `OpenStreetMap query failed: ${err.message}. Operating in DEMO_MODE.`,
      });
    }
  };

  // GeoJSON style for locality boundaries
  const getLocalityStyle = useCallback(
    (feature: any) => {
      const props = feature?.properties as LocalityProperties;
      const isSelected = selectedLocality?.id === props?.id;

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
          color: isSelected ? '#1e293b' : strokeColor,
          weight: isSelected ? 3.5 : 1.5,
          fillColor,
          fillOpacity: isSelected ? 0.45 : 0.25,
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
          color: isSelected ? '#1e293b' : strokeColor,
          weight: isSelected ? 3.5 : 1.5,
          fillColor,
          fillOpacity: isSelected ? 0.45 : 0.25,
        };
      }

      // Default civic styling
      return {
        color: isSelected ? '#2563eb' : '#64748b',
        weight: isSelected ? 3 : 1.5,
        fillColor: isSelected ? '#3b82f6' : '#94a3b8',
        fillOpacity: isSelected ? 0.25 : 0.1,
        dashArray: isSelected ? undefined : '3, 4',
      };
    },
    [activeLayer, selectedLocality]
  );

  // GeoJSON feature interactions (hover, click)
  const onEachFeature = useCallback(
    (feature: any, layer: L.Layer) => {
      const props = feature.properties as LocalityProperties;
      layer.on({
        click: () => {
          handleSelectLocality(props);
        },
        mouseover: (e) => {
          const l = e.target;
          l.setStyle({ fillOpacity: 0.5 });
        },
        mouseout: (e) => {
          const l = e.target;
          l.setStyle(getLocalityStyle(feature));
        },
      });

      // Tooltip for quick identification
      layer.bindTooltip(
        `<strong>${props.name}</strong><br/>Pop: ${props.population.toLocaleString()}${
          props.accessibility_score ? `<br/>Access Score: ${props.accessibility_score}/100` : ''
        }`,
        { sticky: true, className: 'civic-map-tooltip' }
      );
    },
    [getLocalityStyle, handleSelectLocality]
  );

  // Filter facilities based on selected category
  const displayedServices = useMemo(() => {
    const list = selectedCategory === 'all' ? services : services.filter((s) => s.category_code === selectedCategory);
    return list;
  }, [services, selectedCategory]);

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

        {/* City Focus & Category Filter & Overpass OSM Search */}
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

          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="text-xs font-semibold bg-white border border-slate-200 rounded-lg px-2.5 py-1.5 text-slate-700 shadow-sm focus:ring-1 focus:ring-blue-500 focus:outline-none"
          >
            <option value="all">All Service Types</option>
            <option value="healthcare">Healthcare (Clinics/Hospitals)</option>
            <option value="education">Education (Schools/Colleges)</option>
            <option value="transport">Transport (Hubs/Stops)</option>
            <option value="water">Water & Sanitation</option>
            <option value="market">Essential Food Markets</option>
          </select>

          {/* Overpass Query Trigger */}
          <button
            onClick={() => handleQueryOverpass()}
            disabled={isQueryingOverpass}
            title="Query OpenStreetMap Overpass for live amenities in area"
            className="flex items-center gap-1.5 text-xs font-semibold bg-indigo-50 hover:bg-indigo-100 text-indigo-700 border border-indigo-200 px-3 py-1.5 rounded-lg transition-colors shadow-sm disabled:opacity-50"
          >
            {isQueryingOverpass ? (
              <RefreshCw className="w-3.5 h-3.5 animate-spin text-indigo-600" />
            ) : (
              <Search className="w-3.5 h-3.5 text-indigo-600" />
            )}
            <span>Query OSM</span>
          </button>
        </div>
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

          {/* Locality Boundaries Layer */}
          {areas && (
            <GeoJSON
              key={`areas-${activeLayer}-${selectedLocality?.id || 'none'}`}
              data={areas as any}
              style={getLocalityStyle}
              onEachFeature={onEachFeature}
            />
          )}

          {/* Service Facilities Markers */}
          {(activeLayer === 'services' || activeLayer === 'accessibility' || activeLayer === 'gap') && (
            <>
              {displayedServices.map((facility) => (
                <Marker
                  key={`srv-${facility.id}`}
                  position={[facility.latitude, facility.longitude]}
                  icon={createCategoryPinIcon(facility.category_code)}
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
              {overpassFacilities.map((facility) => (
                <Marker
                  key={`osm-${facility.id}`}
                  position={[facility.latitude, facility.longitude]}
                  icon={createCategoryPinIcon(facility.category_code, true)}
                >
                  <Popup className="civic-custom-popup">
                    <div className="font-sans min-w-[230px] p-1">
                      <div className="flex items-center justify-between gap-2 border-b border-slate-100 pb-2 mb-2">
                        <span className="text-[10px] font-bold bg-indigo-50 text-indigo-700 px-2 py-0.5 rounded uppercase tracking-wider">
                          {facility.category_name}
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
              ))}
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

        {/* Selected Locality Inspector Side Panel */}
        {selectedLocality && (
          <div className="absolute top-4 right-4 z-[1000] w-80 bg-white/95 backdrop-blur-md rounded-2xl p-5 shadow-xl border border-slate-200 animate-in fade-in slide-in-from-right-4 duration-300">
            <div className="flex items-start justify-between border-b border-slate-100 pb-3 mb-3">
              <div>
                <span className="text-[10px] font-bold uppercase tracking-wider text-blue-600 bg-blue-50 px-2 py-0.5 rounded">
                  {selectedLocality.area_type}
                </span>
                <h3 className="text-lg font-extrabold text-slate-900 mt-1 leading-tight">{selectedLocality.name}</h3>
              </div>
              <button
                onClick={() => handleSelectLocality(null)}
                className="text-slate-400 hover:text-slate-600 p-1 rounded-lg hover:bg-slate-100 transition-colors"
                title="Close inspector"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div className="flex justify-between items-center py-1 border-b border-slate-100">
                <span className="text-slate-500">Population:</span>
                <span className="font-bold text-slate-800">{selectedLocality.population.toLocaleString()} residents</span>
              </div>

              {selectedLocality.accessibility_score != null && (
                <div className="flex justify-between items-center py-1 border-b border-slate-100">
                  <span className="text-slate-500">Accessibility Score:</span>
                  <span
                    className={`font-bold px-2 py-0.5 rounded text-[11px] ${
                      selectedLocality.accessibility_score >= 80
                        ? 'bg-emerald-100 text-emerald-800'
                        : selectedLocality.accessibility_score >= 60
                        ? 'bg-amber-100 text-amber-800'
                        : 'bg-red-100 text-red-800'
                    }`}
                  >
                    {selectedLocality.accessibility_score} / 100
                  </span>
                </div>
              )}

              {selectedLocality.main_gap && (
                <div className="bg-red-50/70 border border-red-100 p-2.5 rounded-xl">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-red-600 block mb-0.5">
                    Primary Service Gap
                  </span>
                  <p className="font-semibold text-red-900 leading-snug">{selectedLocality.main_gap}</p>
                </div>
              )}

              {selectedLocality.nearest_service && (
                <div className="flex justify-between items-center py-1 border-b border-slate-100">
                  <span className="text-slate-500">Nearest Amenity:</span>
                  <span className="font-medium text-slate-800 text-right">{selectedLocality.nearest_service}</span>
                </div>
              )}

              {selectedLocality.travel_time && (
                <div className="flex justify-between items-center py-1 border-b border-slate-100">
                  <span className="text-slate-500">Est. Travel Time:</span>
                  <span className="font-semibold text-slate-800">{selectedLocality.travel_time}</span>
                </div>
              )}

              {selectedLocality.data_confidence != null && (
                <div className="flex justify-between items-center py-1">
                  <span className="text-slate-500">Data Confidence:</span>
                  <span className="font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded text-[11px]">
                    {selectedLocality.data_confidence}% Verified
                  </span>
                </div>
              )}
            </div>

            {/* Overpass Live Ingestion Quick Action */}
            <button
              onClick={() => handleQueryOverpass(selectedLocality)}
              disabled={isQueryingOverpass}
              className="w-full mt-3 flex items-center justify-center gap-1.5 text-xs font-bold bg-indigo-50 hover:bg-indigo-100 text-indigo-700 border border-indigo-200 py-2 px-3 rounded-xl transition-all shadow-xs disabled:opacity-50"
            >
              {isQueryingOverpass ? (
                <RefreshCw className="w-3.5 h-3.5 animate-spin text-indigo-600" />
              ) : (
                <Search className="w-3.5 h-3.5 text-indigo-600" />
              )}
              <span>Query OSM for {selectedLocality.name}</span>
            </button>

            <div className="mt-3 pt-3 border-t border-slate-100 flex items-center justify-between text-[10px] text-slate-400">
              <span className="flex items-center gap-1">
                <Compass className="w-3 h-3 text-slate-400" />
                {dataStatus.isLive ? 'Backend Live Engine' : 'Deterministic Seed Model'}
              </span>
              <button
                onClick={() => handleSelectLocality(null)}
                className="text-blue-600 hover:text-blue-800 font-semibold"
              >
                Clear Selection
              </button>
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

          {/* Service Category Icons */}
          <div className="grid grid-cols-2 gap-1.5 text-[10px]">
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-red-500 shrink-0" />
              <span className="text-slate-700 font-medium">Healthcare</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-blue-500 shrink-0" />
              <span className="text-slate-700 font-medium">Education</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-amber-500 shrink-0" />
              <span className="text-slate-700 font-medium">Transport</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-cyan-500 shrink-0" />
              <span className="text-slate-700 font-medium">Water Points</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 shrink-0" />
              <span className="text-slate-700 font-medium">Food Markets</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-purple-600 shrink-0" />
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
