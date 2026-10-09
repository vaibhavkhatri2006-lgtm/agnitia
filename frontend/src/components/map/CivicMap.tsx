import React from 'react';
import { MapView, MapLayerType } from './MapView';
import { LocalityProperties } from '../../services/deterministicData';
import { ServiceFacility, CommunityReport } from '../../types/models';

export interface CivicMapProps {
  facilities?: ServiceFacility[];
  reports?: CommunityReport[];
  boundaries?: GeoJSON.FeatureCollection;
  center?: [number, number];
  zoom?: number;
  activeLayer?: 'none' | 'accessibility' | 'gap' | 'equity' | 'services' | 'reports' | 'recommendations';
  onLocalitySelect?: (loc: LocalityProperties | null) => void;
  className?: string;
  initialCategory?: string;
  initialCity?: 'indore' | 'bengaluru';
}

export const CivicMap: React.FC<CivicMapProps> = ({
  center,
  zoom,
  activeLayer = 'services',
  onLocalitySelect,
  className = 'w-full h-full min-h-[500px]',
  initialCategory = 'all',
  initialCity = 'indore',
}) => {
  // Normalize layer name for MapView
  let mappedLayer: MapLayerType = 'services';
  if (activeLayer === 'accessibility') {
    mappedLayer = 'accessibility';
  } else if (activeLayer === 'gap' || activeLayer === 'equity') {
    mappedLayer = 'gap';
  } else if (activeLayer === 'reports') {
    mappedLayer = 'reports';
  } else if (activeLayer === 'recommendations') {
    mappedLayer = 'recommendations';
  }

  return (
    <MapView
      center={center}
      zoom={zoom}
      activeLayer={mappedLayer}
      className={className}
      onLocalitySelect={onLocalitySelect}
      initialCategory={initialCategory}
      initialCity={initialCity}
    />
  );
};

export default CivicMap;
