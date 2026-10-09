// Deterministic seed datasets for CivicPulse map visualization
// Grounded in backend seed data for Metro City, ensuring deterministic presentation in demo mode.

export interface GeoJSONFeature<G = any, P = any> {
  type: 'Feature';
  id?: string | number;
  geometry: G;
  properties: P;
}

export interface GeoJSONFeatureCollection<G = any, P = any> {
  type: 'FeatureCollection';
  features: GeoJSONFeature<G, P>[];
}

export interface LocalityProperties {
  id: number;
  name: string;
  area_type: 'city' | 'ward' | 'neighbourhood';
  parent_id?: number | null;
  population: number;
  accessibility_score?: number;
  gap_score?: number;
  desert_classification?: string;
  categories_evaluated?: number;
  main_gap?: string;
  nearest_service?: string;
  travel_time?: string;
  data_confidence?: number;
}

export interface ServiceFacilityProperties {
  id: number;
  name: string;
  category_id?: number;
  category_code: 'healthcare' | 'education' | 'transport' | 'water' | 'market';
  category_name: string;
  area_id?: number;
  area_name?: string;
  latitude: number;
  longitude: number;
  status: 'operational' | 'degraded' | 'temporarily_unavailable' | 'closed';
  source_type: string;
  verification_status: 'verified' | 'pending' | 'unverified';
  confidence_score: number;
  capacity?: number | null;
  current_load?: number | null;
  operating_hours?: string | null;
  osm_id?: number;
  osm_type?: string;
  is_demo_data?: boolean;
  tags?: Record<string, string>;
}

export interface CommunityReportItem {
  id: number;
  title: string;
  description: string;
  category_code?: string;
  category_name?: string;
  area_name?: string;
  latitude: number;
  longitude: number;
  severity: 'low' | 'medium' | 'high' | 'critical';
  status: string;
  verification_status: string;
  confidence_score: number;
  source_type: string;
  created_at: string;
}

export interface RecommendationCandidateItem {
  candidate_id: string;
  service_type: string;
  rank: number;
  recommendation_score: number;
  latitude: number;
  longitude: number;
  area_id: number;
  area_name: string;
  population: number;
  strategy: string;
  confidence: number;
  reasons: string[];
}

export const INDORE_CITY_CENTER: [number, number] = [22.7196, 75.8577];
export const INDORE_CITY_DEFAULT_ZOOM = 13;
export const INDORE_BBOX: [number, number, number, number] = [22.65, 75.78, 22.78, 75.92];

export const BENGALURU_CITY_CENTER: [number, number] = [12.9716, 77.5946];
export const BENGALURU_CITY_DEFAULT_ZOOM = 13;
export const BENGALURU_BBOX: [number, number, number, number] = [12.935, 77.56, 13.015, 77.645];

// Primary default city center: Indore, Madhya Pradesh
export const METRO_CITY_CENTER: [number, number] = INDORE_CITY_CENTER;
export const METRO_CITY_DEFAULT_ZOOM = 13;

export interface CityProfile {
  id: 'indore' | 'bengaluru';
  name: string;
  fullName: string;
  state: string;
  center: [number, number];
  zoom: number;
  bbox: [number, number, number, number];
  description: string;
}

export const CITIES: Record<string, CityProfile> = {
  indore: {
    id: 'indore',
    name: 'Indore',
    fullName: 'Indore, Madhya Pradesh',
    state: 'Madhya Pradesh',
    center: INDORE_CITY_CENTER,
    zoom: 13,
    bbox: INDORE_BBOX,
    description: "India's cleanest city and primary civic planning hub",
  },
  bengaluru: {
    id: 'bengaluru',
    name: 'Bengaluru',
    fullName: 'Bengaluru (Test Bed)',
    state: 'Karnataka',
    center: BENGALURU_CITY_CENTER,
    zoom: 13,
    bbox: BENGALURU_BBOX,
    description: 'Stage 1 benchmark test suite reference environment',
  },
};

export const DETERMINISTIC_AREAS_GEOJSON: GeoJSONFeatureCollection<any, LocalityProperties> = {
  type: 'FeatureCollection',
  features: [
    {
      type: 'Feature',
      id: 6,
      geometry: {
        type: 'Polygon',
        coordinates: [
          [
            [77.5850, 12.9700],
            [77.6050, 12.9700],
            [77.6050, 12.9850],
            [77.5850, 12.9850],
            [77.5850, 12.9700]
          ]
        ]
      },
      properties: {
        id: 6,
        name: 'Downtown Core',
        area_type: 'neighbourhood',
        parent_id: 2,
        population: 25000,
        accessibility_score: 82.8,
        gap_score: 17.2,
        desert_classification: 'Well Served',
        main_gap: 'Capacity Congestion (82% Peak Load)',
        nearest_service: 'Central Metro Hospital (0.4 km)',
        travel_time: '5 mins walk',
        data_confidence: 96
      }
    },
    {
      type: 'Feature',
      id: 7,
      geometry: {
        type: 'Polygon',
        coordinates: [
          [
            [77.5800, 12.9650],
            [77.5850, 12.9650],
            [77.5850, 12.9850],
            [77.5800, 12.9850],
            [77.5800, 12.9650]
          ]
        ]
      },
      properties: {
        id: 7,
        name: 'West End',
        area_type: 'neighbourhood',
        parent_id: 2,
        population: 12000,
        accessibility_score: 83.2,
        gap_score: 16.8,
        desert_classification: 'Well Served',
        main_gap: 'None (High Baseline Coverage)',
        nearest_service: 'West End Community Clinic (0.3 km)',
        travel_time: '4 mins walk',
        data_confidence: 94
      }
    },
    {
      type: 'Feature',
      id: 8,
      geometry: {
        type: 'Polygon',
        coordinates: [
          [
            [77.5900, 12.9900],
            [77.6150, 12.9900],
            [77.6150, 13.0080],
            [77.5900, 13.0080],
            [77.5900, 12.9900]
          ]
        ]
      },
      properties: {
        id: 8,
        name: 'Riverside Commons',
        area_type: 'neighbourhood',
        parent_id: 3,
        population: 18000,
        accessibility_score: 69.7,
        gap_score: 30.3,
        desert_classification: 'Adequate',
        main_gap: 'Health Center Capacity Overloaded (120%)',
        nearest_service: 'Riverside Health Center (0.6 km)',
        travel_time: '8 mins walk',
        data_confidence: 92
      }
    },
    {
      type: 'Feature',
      id: 9,
      geometry: {
        type: 'Polygon',
        coordinates: [
          [
            [77.6120, 12.9680],
            [77.6380, 12.9680],
            [77.6380, 12.9880],
            [77.6120, 12.9880],
            [77.6120, 12.9680]
          ]
        ]
      },
      properties: {
        id: 9,
        name: 'Highlands Valley',
        area_type: 'neighbourhood',
        parent_id: 4,
        population: 22000,
        accessibility_score: 52.5,
        gap_score: 47.5,
        desert_classification: 'Underserved',
        main_gap: 'Critical Healthcare Desert (Zero Clinics in Boundary)',
        nearest_service: 'Downtown Central Academy (2.4 km)',
        travel_time: '32 mins transit',
        data_confidence: 89
      }
    },
    {
      type: 'Feature',
      id: 10,
      geometry: {
        type: 'Polygon',
        coordinates: [
          [
            [77.5680, 12.9420],
            [77.5980, 12.9420],
            [77.5980, 12.9630],
            [77.5680, 12.9630],
            [77.5680, 12.9420]
          ]
        ]
      },
      properties: {
        id: 10,
        name: 'South Hillside',
        area_type: 'neighbourhood',
        parent_id: 5,
        population: 15000,
        accessibility_score: 57.9,
        gap_score: 42.1,
        desert_classification: 'Underserved',
        main_gap: 'Degraded Water Well & Transit Landslide Disruption',
        nearest_service: 'South Hillside Primary (0.5 km)',
        travel_time: '18 mins walk',
        data_confidence: 87
      }
    }
  ]
};

export const DETERMINISTIC_SERVICES_GEOJSON: GeoJSONFeatureCollection<any, ServiceFacilityProperties> = {
  type: 'FeatureCollection',
  features: [
    // Healthcare
    {
      type: 'Feature',
      id: 1,
      geometry: { type: 'Point', coordinates: [77.5900, 12.9750] },
      properties: {
        id: 1,
        name: 'Central Metro Hospital',
        category_code: 'healthcare',
        category_name: 'Healthcare',
        area_id: 6,
        area_name: 'Downtown Core',
        latitude: 12.9750,
        longitude: 77.5900,
        status: 'operational',
        source_type: 'simulated_demo',
        verification_status: 'verified',
        confidence_score: 0.98,
        capacity: 500,
        current_load: 380,
        operating_hours: '24/7 Emergency & Inpatient'
      }
    },
    {
      type: 'Feature',
      id: 2,
      geometry: { type: 'Point', coordinates: [77.5820, 12.9720] },
      properties: {
        id: 2,
        name: 'West End Community Clinic',
        category_code: 'healthcare',
        category_name: 'Healthcare',
        area_id: 7,
        area_name: 'West End',
        latitude: 12.9720,
        longitude: 77.5820,
        status: 'operational',
        source_type: 'simulated_demo',
        verification_status: 'verified',
        confidence_score: 0.92,
        capacity: 80,
        current_load: 75,
        operating_hours: 'Mon-Sat 08:00-18:00'
      }
    },
    {
      type: 'Feature',
      id: 3,
      geometry: { type: 'Point', coordinates: [77.6020, 12.9980] },
      properties: {
        id: 3,
        name: 'Riverside Health Center',
        category_code: 'healthcare',
        category_name: 'Healthcare',
        area_id: 8,
        area_name: 'Riverside Commons',
        latitude: 12.9980,
        longitude: 77.6020,
        status: 'operational',
        source_type: 'simulated_demo',
        verification_status: 'verified',
        confidence_score: 0.95,
        capacity: 60,
        current_load: 72,
        operating_hours: 'Mon-Fri 08:00-20:00'
      }
    },

    // Education
    {
      type: 'Feature',
      id: 4,
      geometry: { type: 'Point', coordinates: [77.5960, 12.9780] },
      properties: {
        id: 4,
        name: 'Downtown Central Academy',
        category_code: 'education',
        category_name: 'Education',
        area_id: 6,
        area_name: 'Downtown Core',
        latitude: 12.9780,
        longitude: 77.5960,
        status: 'operational',
        source_type: 'simulated_demo',
        verification_status: 'verified',
        confidence_score: 0.99,
        capacity: 1200,
        current_load: 1100,
        operating_hours: 'Mon-Fri 08:00-16:00'
      }
    },
    {
      type: 'Feature',
      id: 5,
      geometry: { type: 'Point', coordinates: [77.6250, 12.9760] },
      properties: {
        id: 5,
        name: 'Highlands Public School',
        category_code: 'education',
        category_name: 'Education',
        area_id: 9,
        area_name: 'Highlands Valley',
        latitude: 12.9760,
        longitude: 77.6250,
        status: 'operational',
        source_type: 'simulated_demo',
        verification_status: 'verified',
        confidence_score: 0.94,
        capacity: 800,
        current_load: 780,
        operating_hours: 'Mon-Fri 08:30-15:30'
      }
    },
    {
      type: 'Feature',
      id: 6,
      geometry: { type: 'Point', coordinates: [77.5850, 12.9520] },
      properties: {
        id: 6,
        name: 'South Hillside Primary',
        category_code: 'education',
        category_name: 'Education',
        area_id: 10,
        area_name: 'South Hillside',
        latitude: 12.9520,
        longitude: 77.5850,
        status: 'operational',
        source_type: 'simulated_demo',
        verification_status: 'verified',
        confidence_score: 0.90,
        capacity: 450,
        current_load: 420,
        operating_hours: 'Mon-Fri 08:00-15:00'
      }
    },

    // Transport
    {
      type: 'Feature',
      id: 7,
      geometry: { type: 'Point', coordinates: [77.5920, 12.9730] },
      properties: {
        id: 7,
        name: 'Central Multimodal Transit Hub',
        category_code: 'transport',
        category_name: 'Transport',
        area_id: 6,
        area_name: 'Downtown Core',
        latitude: 12.9730,
        longitude: 77.5920,
        status: 'operational',
        source_type: 'simulated_demo',
        verification_status: 'verified',
        confidence_score: 0.99,
        capacity: 5000,
        current_load: 3200,
        operating_hours: '24/7 Operations'
      }
    },
    {
      type: 'Feature',
      id: 8,
      geometry: { type: 'Point', coordinates: [77.6050, 12.9950] },
      properties: {
        id: 8,
        name: 'Riverside Metro Station',
        category_code: 'transport',
        category_name: 'Transport',
        area_id: 8,
        area_name: 'Riverside Commons',
        latitude: 12.9950,
        longitude: 77.6050,
        status: 'operational',
        source_type: 'simulated_demo',
        verification_status: 'verified',
        confidence_score: 0.96,
        capacity: 2000,
        current_load: 1500,
        operating_hours: '05:30-23:30 Daily'
      }
    },
    {
      type: 'Feature',
      id: 9,
      geometry: { type: 'Point', coordinates: [77.5800, 12.9500] },
      properties: {
        id: 9,
        name: 'South Hillside Bus Hub',
        category_code: 'transport',
        category_name: 'Transport',
        area_id: 10,
        area_name: 'South Hillside',
        latitude: 12.9500,
        longitude: 77.5800,
        status: 'temporarily_unavailable',
        source_type: 'simulated_demo',
        verification_status: 'verified',
        confidence_score: 0.88,
        capacity: 800,
        current_load: 0,
        operating_hours: 'Out of Service due to landslide repair'
      }
    },

    // Water
    {
      type: 'Feature',
      id: 10,
      geometry: { type: 'Point', coordinates: [77.5880, 12.9790] },
      properties: {
        id: 10,
        name: 'Downtown Municipal Purification Facility',
        category_code: 'water',
        category_name: 'Water & Sanitation',
        area_id: 6,
        area_name: 'Downtown Core',
        latitude: 12.9790,
        longitude: 77.5880,
        status: 'operational',
        source_type: 'simulated_demo',
        verification_status: 'verified',
        confidence_score: 0.97,
        capacity: 10000,
        current_load: 7500,
        operating_hours: 'Continuous supply'
      }
    },
    {
      type: 'Feature',
      id: 11,
      geometry: { type: 'Point', coordinates: [77.6300, 12.9740] },
      properties: {
        id: 11,
        name: 'Highlands Spring Water Point',
        category_code: 'water',
        category_name: 'Water & Sanitation',
        area_id: 9,
        area_name: 'Highlands Valley',
        latitude: 12.9740,
        longitude: 77.6300,
        status: 'operational',
        source_type: 'simulated_demo',
        verification_status: 'verified',
        confidence_score: 0.89,
        capacity: 2500,
        current_load: 2400,
        operating_hours: '06:00-20:00 Daily'
      }
    },
    {
      type: 'Feature',
      id: 12,
      geometry: { type: 'Point', coordinates: [77.5750, 12.9480] },
      properties: {
        id: 12,
        name: 'South Hillside Community Well #4',
        category_code: 'water',
        category_name: 'Water & Sanitation',
        area_id: 10,
        area_name: 'South Hillside',
        latitude: 12.9480,
        longitude: 77.5750,
        status: 'degraded',
        source_type: 'simulated_demo',
        verification_status: 'pending',
        confidence_score: 0.72,
        capacity: 1500,
        current_load: 400,
        operating_hours: 'Intermittent supply'
      }
    },

    // Market
    {
      type: 'Feature',
      id: 13,
      geometry: { type: 'Point', coordinates: [77.5950, 12.9725] },
      properties: {
        id: 13,
        name: 'Grand Central Produce Market',
        category_code: 'market',
        category_name: 'Food & Market',
        area_id: 6,
        area_name: 'Downtown Core',
        latitude: 12.9725,
        longitude: 77.5950,
        status: 'operational',
        source_type: 'simulated_demo',
        verification_status: 'verified',
        confidence_score: 0.98,
        capacity: 1500,
        current_load: 1200,
        operating_hours: '06:00-21:00 Daily'
      }
    },
    {
      type: 'Feature',
      id: 14,
      geometry: { type: 'Point', coordinates: [77.6100, 12.9920] },
      properties: {
        id: 14,
        name: 'Riverside Farmers Market',
        category_code: 'market',
        category_name: 'Food & Market',
        area_id: 8,
        area_name: 'Riverside Commons',
        latitude: 12.9920,
        longitude: 77.6100,
        status: 'operational',
        source_type: 'simulated_demo',
        verification_status: 'verified',
        confidence_score: 0.93,
        capacity: 700,
        current_load: 550,
        operating_hours: 'Tue-Sun 07:00-19:00'
      }
    }
  ]
};

export const DETERMINISTIC_REPORTS: CommunityReportItem[] = [
  {
    id: 98,
    title: 'Hospital road blockage due to construction',
    description: 'Ambulances facing 20-minute delay due to unplanned utility trenching.',
    category_code: 'healthcare',
    category_name: 'Healthcare',
    area_name: 'Downtown Core',
    latitude: 12.973,
    longitude: 77.593,
    severity: 'high',
    status: 'OFFICIAL',
    verification_status: 'OFFICIAL',
    confidence_score: 1.0,
    source_type: 'community',
    created_at: '2026-10-09'
  },
  {
    id: 99,
    title: 'Well pump mechanical failure',
    description: 'Borehole pump offline; 400 households currently without potable water.',
    category_code: 'water',
    category_name: 'Water & Sanitation',
    area_name: 'South Hillside',
    latitude: 12.947,
    longitude: 77.576,
    severity: 'critical',
    status: 'COMMUNITY_VERIFIED',
    verification_status: 'COMMUNITY_VERIFIED',
    confidence_score: 0.92,
    source_type: 'community',
    created_at: '2026-10-08'
  },
  {
    id: 100,
    title: 'Highlands clinic commute hazard',
    description: 'No local clinic available; elderly residents travel over 45 minutes on unpaved connector.',
    category_code: 'healthcare',
    category_name: 'Healthcare',
    area_name: 'Highlands Valley',
    latitude: 12.977,
    longitude: 77.628,
    severity: 'high',
    status: 'AUTHORITY_VERIFIED',
    verification_status: 'AUTHORITY_VERIFIED',
    confidence_score: 0.95,
    source_type: 'community',
    created_at: '2026-10-07'
  }
];

export const DETERMINISTIC_RECOMMENDATIONS: RecommendationCandidateItem[] = [
  {
    candidate_id: 'cand-healthcare-9-centroid',
    service_type: 'healthcare',
    rank: 1,
    recommendation_score: 80.6,
    latitude: 12.978,
    longitude: 77.625,
    area_id: 9,
    area_name: 'Highlands Valley',
    population: 22000,
    strategy: 'Centroid Optimal Allocation',
    confidence: 0.89,
    reasons: [
      'Severe healthcare accessibility gap (86.9%) in Highlands Valley',
      'Large affected population (22,000 residents)',
      'Estimated travel time deficit exceeds 30 minutes to nearest hospital',
      'Strong local demand supporting new primary health center'
    ]
  },
  {
    candidate_id: 'cand-water-10-well',
    service_type: 'water',
    rank: 2,
    recommendation_score: 76.4,
    latitude: 12.949,
    longitude: 77.578,
    area_id: 10,
    area_name: 'South Hillside',
    population: 15000,
    strategy: 'Infrastructure Redundancy Expansion',
    confidence: 0.87,
    reasons: [
      'Frequent well degradation and intermittency in South Hillside',
      '15,000 residents dependent on fragile single borehole',
      'High equity vulnerability index (0.74)'
    ]
  },
  {
    candidate_id: 'cand-transport-9-shuttle',
    service_type: 'transport',
    rank: 3,
    recommendation_score: 72.1,
    latitude: 12.975,
    longitude: 77.622,
    area_id: 9,
    area_name: 'Highlands Valley',
    population: 22000,
    strategy: 'Feeder Transit Corridor Link',
    confidence: 0.85,
    reasons: [
      'Connects underserved valley community to Metro Station',
      'Reduces transit travel time from 40 mins to 14 mins'
    ]
  }
];

export const INDORE_AREAS_GEOJSON: GeoJSONFeatureCollection<any, LocalityProperties> = {
  type: 'FeatureCollection',
  features: [
    {
      type: 'Feature',
      id: 101,
      geometry: {
        type: 'Polygon',
        coordinates: [
          [
            [75.8500, 22.7130],
            [75.8650, 22.7130],
            [75.8650, 22.7250],
            [75.8500, 22.7250],
            [75.8500, 22.7130],
          ],
        ],
      },
      properties: {
        id: 101,
        name: 'Rajwada / Central Core',
        area_type: 'neighbourhood',
        parent_id: 1,
        population: 38000,
        accessibility_score: 84.5,
        gap_score: 15.5,
        desert_classification: 'Well Served',
        main_gap: 'Pedestrian Congestion at Heritage Bazaar',
        nearest_service: 'MY Hospital (0.9 km)',
        travel_time: '6 mins walk',
        data_confidence: 96,
      },
    },
    {
      type: 'Feature',
      id: 102,
      geometry: {
        type: 'Polygon',
        coordinates: [
          [
            [75.8850, 22.7450],
            [75.9080, 22.7450],
            [75.9080, 22.7650],
            [75.8850, 22.7650],
            [75.8850, 22.7450],
          ],
        ],
      },
      properties: {
        id: 102,
        name: 'Vijay Nagar / Scheme 54',
        area_type: 'neighbourhood',
        parent_id: 1,
        population: 46000,
        accessibility_score: 86.2,
        gap_score: 13.8,
        desert_classification: 'Well Served',
        main_gap: 'Peak-Hour Commercial Traffic',
        nearest_service: 'Bombay Hospital Indore (0.5 km)',
        travel_time: '5 mins walk',
        data_confidence: 95,
      },
    },
    {
      type: 'Feature',
      id: 103,
      geometry: {
        type: 'Polygon',
        coordinates: [
          [
            [75.8750, 22.7180],
            [75.8950, 22.7180],
            [75.8950, 22.7320],
            [75.8750, 22.7320],
            [75.8750, 22.7180],
          ],
        ],
      },
      properties: {
        id: 103,
        name: 'Palasia / Chhappan Dukan',
        area_type: 'neighbourhood',
        parent_id: 1,
        population: 29000,
        accessibility_score: 79.4,
        gap_score: 20.6,
        desert_classification: 'Adequate',
        main_gap: 'Public School Capacity Deficit',
        nearest_service: 'Greater Kailash Hospital (0.4 km)',
        travel_time: '7 mins walk',
        data_confidence: 93,
      },
    },
    {
      type: 'Feature',
      id: 104,
      geometry: {
        type: 'Polygon',
        coordinates: [
          [
            [75.8550, 22.6820],
            [75.8750, 22.6820],
            [75.8750, 22.7000],
            [75.8550, 22.7000],
            [75.8550, 22.6820],
          ],
        ],
      },
      properties: {
        id: 104,
        name: 'Bhawar Kuan / University Hub',
        area_type: 'neighbourhood',
        parent_id: 1,
        population: 34000,
        accessibility_score: 61.3,
        gap_score: 38.7,
        desert_classification: 'Underserved',
        main_gap: 'Primary Health Clinic Capacity Deficit',
        nearest_service: 'Choithram Hospital (1.6 km)',
        travel_time: '18 mins transit',
        data_confidence: 91,
      },
    },
    {
      type: 'Feature',
      id: 105,
      geometry: {
        type: 'Polygon',
        coordinates: [
          [
            [75.8200, 22.6900],
            [75.8450, 22.6900],
            [75.8450, 22.7100],
            [75.8200, 22.7100],
            [75.8200, 22.6900],
          ],
        ],
      },
      properties: {
        id: 105,
        name: 'Annapurna / Sudama Nagar',
        area_type: 'neighbourhood',
        parent_id: 1,
        population: 33000,
        accessibility_score: 54.8,
        gap_score: 45.2,
        desert_classification: 'Critical Desert',
        main_gap: 'Emergency Healthcare Transit Lag',
        nearest_service: 'Shubham Hospital (1.8 km)',
        travel_time: '24 mins transit',
        data_confidence: 89,
      },
    },
  ],
};

export const INDORE_SERVICES_GEOJSON: GeoJSONFeatureCollection<any, ServiceFacilityProperties> = {
  type: 'FeatureCollection',
  features: [
    {
      type: 'Feature',
      id: 1001,
      geometry: { type: 'Point', coordinates: [75.8905, 22.7251] },
      properties: {
        id: 1001,
        name: 'Greater Kailash Hospital',
        category_code: 'healthcare',
        category_name: 'HEALTHCARE',
        latitude: 22.7251,
        longitude: 75.8905,
        status: 'operational',
        source_type: 'OpenStreetMap',
        verification_status: 'verified',
        confidence_score: 0.96,
        capacity: 180,
        current_load: 142,
        operating_hours: '24/7 Emergency',
        osm_id: 1001,
        osm_type: 'node',
        is_demo_data: false,
        tags: { amenity: 'hospital', emergency: 'yes', city: 'Indore' },
      },
    },
    {
      type: 'Feature',
      id: 1002,
      geometry: { type: 'Point', coordinates: [75.8702, 22.7165] },
      properties: {
        id: 1002,
        name: 'Maharaja Yeshwantrao Hospital (MYH)',
        category_code: 'healthcare',
        category_name: 'HEALTHCARE',
        latitude: 22.7165,
        longitude: 75.8702,
        status: 'operational',
        source_type: 'OpenStreetMap',
        verification_status: 'verified',
        confidence_score: 0.98,
        capacity: 950,
        current_load: 870,
        operating_hours: '24/7 Public Multi-Specialty',
        osm_id: 1002,
        osm_type: 'way',
        is_demo_data: false,
        tags: { amenity: 'hospital', operator: 'Government of MP', city: 'Indore' },
      },
    },
    {
      type: 'Feature',
      id: 1003,
      geometry: { type: 'Point', coordinates: [75.8965, 22.7562] },
      properties: {
        id: 1003,
        name: 'Bombay Hospital Indore',
        category_code: 'healthcare',
        category_name: 'HEALTHCARE',
        latitude: 22.7562,
        longitude: 75.8965,
        status: 'operational',
        source_type: 'OpenStreetMap',
        verification_status: 'verified',
        confidence_score: 0.95,
        capacity: 350,
        current_load: 280,
        operating_hours: '24/7 Super Specialty',
        osm_id: 1003,
        osm_type: 'way',
        is_demo_data: false,
        tags: { amenity: 'hospital', city: 'Indore' },
      },
    },
    {
      type: 'Feature',
      id: 1004,
      geometry: { type: 'Point', coordinates: [75.8340, 22.6885] },
      properties: {
        id: 1004,
        name: 'Choithram Hospital & Research Centre',
        category_code: 'healthcare',
        category_name: 'HEALTHCARE',
        latitude: 22.6885,
        longitude: 75.8340,
        status: 'operational',
        source_type: 'OpenStreetMap',
        verification_status: 'verified',
        confidence_score: 0.94,
        capacity: 260,
        current_load: 210,
        operating_hours: '24/7 Emergency Care',
        osm_id: 1004,
        osm_type: 'node',
        is_demo_data: false,
        tags: { amenity: 'hospital', city: 'Indore' },
      },
    },
    {
      type: 'Feature',
      id: 1005,
      geometry: { type: 'Point', coordinates: [75.8920, 22.7080] },
      properties: {
        id: 1005,
        name: 'Daly College Indore',
        category_code: 'education',
        category_name: 'EDUCATION',
        latitude: 22.7080,
        longitude: 75.8920,
        status: 'operational',
        source_type: 'OpenStreetMap',
        verification_status: 'verified',
        confidence_score: 0.97,
        capacity: 1200,
        current_load: 1050,
        operating_hours: '08:00 - 16:00',
        osm_id: 1005,
        osm_type: 'way',
        is_demo_data: false,
        tags: { amenity: 'school', city: 'Indore' },
      },
    },
    {
      type: 'Feature',
      id: 1006,
      geometry: { type: 'Point', coordinates: [75.8670, 22.6930] },
      properties: {
        id: 1006,
        name: 'Devi Ahilya Vishwavidyalaya (DAVV)',
        category_code: 'education',
        category_name: 'EDUCATION',
        latitude: 22.6930,
        longitude: 75.8670,
        status: 'operational',
        source_type: 'OpenStreetMap',
        verification_status: 'verified',
        confidence_score: 0.98,
        capacity: 8500,
        current_load: 7800,
        operating_hours: '09:00 - 18:00',
        osm_id: 1006,
        osm_type: 'way',
        is_demo_data: false,
        tags: { amenity: 'university', city: 'Indore' },
      },
    },
    {
      type: 'Feature',
      id: 1007,
      geometry: { type: 'Point', coordinates: [75.8830, 22.7210] },
      properties: {
        id: 1007,
        name: 'AICTSL iBus Geeta Bhawan Station',
        category_code: 'transport',
        category_name: 'TRANSPORT',
        latitude: 22.7210,
        longitude: 75.8830,
        status: 'operational',
        source_type: 'OpenStreetMap',
        verification_status: 'verified',
        confidence_score: 0.96,
        capacity: 500,
        current_load: 390,
        operating_hours: '06:00 - 23:00 BRTS Corridor',
        osm_id: 1007,
        osm_type: 'node',
        is_demo_data: false,
        tags: { highway: 'bus_stop', public_transport: 'platform', network: 'AICTSL iBus' },
      },
    },
    {
      type: 'Feature',
      id: 1008,
      geometry: { type: 'Point', coordinates: [75.8640, 22.7155] },
      properties: {
        id: 1008,
        name: 'Indore Junction Railway Station',
        category_code: 'transport',
        category_name: 'TRANSPORT',
        latitude: 22.7155,
        longitude: 75.8640,
        status: 'operational',
        source_type: 'OpenStreetMap',
        verification_status: 'verified',
        confidence_score: 0.99,
        capacity: 15000,
        current_load: 12200,
        operating_hours: '24/7 Central Railway',
        osm_id: 1008,
        osm_type: 'node',
        is_demo_data: false,
        tags: { railway: 'station', city: 'Indore' },
      },
    },
    {
      type: 'Feature',
      id: 1009,
      geometry: { type: 'Point', coordinates: [75.8812, 22.7245] },
      properties: {
        id: 1009,
        name: 'Chhappan Dukan Essential Market',
        category_code: 'market',
        category_name: 'MARKET',
        latitude: 22.7245,
        longitude: 75.8812,
        status: 'operational',
        source_type: 'OpenStreetMap',
        verification_status: 'verified',
        confidence_score: 0.97,
        capacity: 2500,
        current_load: 2100,
        operating_hours: '11:00 - 23:00 Clean Street Food Hub',
        osm_id: 1009,
        osm_type: 'node',
        is_demo_data: false,
        tags: { amenity: 'marketplace', tourism: 'attraction', city: 'Indore' },
      },
    },
    {
      type: 'Feature',
      id: 1010,
      geometry: { type: 'Point', coordinates: [75.8560, 22.7185] },
      properties: {
        id: 1010,
        name: 'Sarafa Bazaar Heritage Market',
        category_code: 'market',
        category_name: 'MARKET',
        latitude: 22.7185,
        longitude: 75.8560,
        status: 'operational',
        source_type: 'OpenStreetMap',
        verification_status: 'verified',
        confidence_score: 0.98,
        capacity: 4000,
        current_load: 3600,
        operating_hours: '10:00 - 02:00 Night Market',
        osm_id: 1010,
        osm_type: 'way',
        is_demo_data: false,
        tags: { amenity: 'marketplace', city: 'Indore' },
      },
    },
    {
      type: 'Feature',
      id: 1011,
      geometry: { type: 'Point', coordinates: [75.8400, 22.7200] },
      properties: {
        id: 1011,
        name: 'Yashwant Sagar Municipal Water Grid',
        category_code: 'water',
        category_name: 'WATER',
        latitude: 22.7200,
        longitude: 75.8400,
        status: 'operational',
        source_type: 'OpenStreetMap',
        verification_status: 'verified',
        confidence_score: 0.95,
        capacity: 50000,
        current_load: 42000,
        operating_hours: '24/7 Municipal Supply',
        osm_id: 1011,
        osm_type: 'node',
        is_demo_data: false,
        tags: { amenity: 'drinking_water', operator: 'Indore Municipal Corporation (IMC)' },
      },
    },
  ],
};
