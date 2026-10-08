// CivicPulse Frontend Data Models
// These represent the expected API contracts from the backend (Person 2)

export type Role = 'Citizen' | 'Community' | 'Authority' | 'Admin';

export interface User {
  id: string;
  name: string;
  email: string;
  role: Role;
}

export interface Metric {
  id: string;
  name: string;
  value: number;
  label: string;
  confidence?: number;
  explanation?: string;
}

export interface ServiceFacility {
  id: string;
  name: string;
  type: string; // e.g., 'Hospital', 'School', 'Park'
  coordinates: [number, number];
  capacity: number;
  pressureScore: number;
}

export interface CommunityReport {
  id: string;
  userId: string;
  facilityId?: string;
  issueType: string;
  description: string;
  coordinates: [number, number];
  evidenceUrl?: string; // e.g., Photo URL
  status: 'Pending' | 'Verified' | 'Rejected';
  timestamp: string;
}

export interface Scenario {
  id: string;
  name: string;
  description: string;
  interventions: Intervention[];
  impactScore: number;
  budgetRequired: number;
}

export interface Intervention {
  id: string;
  type: 'NewFacility' | 'UpgradeFacility' | 'PolicyChange';
  targetLocation: [number, number];
  cost: number;
  expectedBenefit: Metric[];
}

export interface GeospatialAnalysis {
  regionId: string;
  scale: 'Local' | 'Neighbourhood' | 'District' | 'City' | 'Region' | 'Country' | 'Global';
  accessibilityHeatmap: [number, number, number][]; // lat, lng, weight
  gapScore: number;
  equityScore: number;
}
