import React from 'react';
import { MapContainer, TileLayer, Marker, Popup, GeoJSON } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import { ServiceFacility, CommunityReport } from '../../types/models';
import { MapPinOff } from 'lucide-react';

// Fix for default marker icons in React-Leaflet
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

interface CivicMapProps {
  facilities?: ServiceFacility[];
  reports?: CommunityReport[];
  boundaries?: GeoJSON.FeatureCollection; // Real geojson data
  center?: [number, number];
  zoom?: number;
  activeLayer?: 'none' | 'accessibility' | 'gap' | 'equity';
}

export const CivicMap: React.FC<CivicMapProps> = ({ 
  facilities = [], 
  reports = [],
  boundaries,
  center = [51.505, -0.09], // Default London
  zoom = 13,
  activeLayer = 'none'
}) => {
  // Requirement: "If geographic data is unavailable, create a clear empty state and identify the missing data instead of fabricating a map."
  if (!boundaries || boundaries.features.length === 0) {
    return (
      <div className="w-full h-full min-h-[500px] flex flex-col items-center justify-center bg-slate-50 border-2 border-dashed border-slate-200 rounded-2xl p-8 text-center">
        <div className="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mb-4 border border-slate-200">
          <MapPinOff className="w-8 h-8 text-slate-400" />
        </div>
        <h3 className="text-xl font-bold text-slate-900 mb-2">Geographic Data Unavailable</h3>
        <p className="text-sm text-slate-500 max-w-md mx-auto leading-relaxed mb-4">
          The neighbourhood service-gap map cannot be rendered because we are missing real boundary data (GeoJSON Polygons) and verified service coordinates.
        </p>
        <div className="flex flex-col gap-2 text-xs font-mono text-left bg-white p-4 rounded-xl border border-slate-200 w-full max-w-sm">
          <div className="flex justify-between">
            <span className="text-slate-500">Neighbourhood Boundaries:</span>
            <span className="text-red-600 font-bold">Missing</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-500">Facility Coordinates:</span>
            <span className="text-red-600 font-bold">Missing</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-500">Service API Integration:</span>
            <span className="text-amber-600 font-bold">Pending</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full h-full min-h-[500px] relative rounded-2xl overflow-hidden border border-slate-200 shadow-sm z-0">
      <MapContainer center={center} zoom={zoom} style={{ height: '100%', width: '100%' }}>
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors | CivicPulse'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        
        {boundaries && (
          <GeoJSON 
            data={boundaries}
            style={() => ({
              color: '#3b82f6',
              weight: 2,
              fillColor: '#93c5fd',
              fillOpacity: 0.2
            })}
          />
        )}

        {facilities.map(facility => (
          <Marker key={facility.id} position={facility.coordinates}>
            <Popup>
              <div className="font-sans">
                <h4 className="font-bold text-slate-900">{facility.name}</h4>
                <p className="text-sm text-slate-600">{facility.type}</p>
                <div className="mt-2 text-xs">
                  <span className="bg-slate-100 px-2 py-1 rounded">Pressure: {facility.pressureScore}/100</span>
                </div>
              </div>
            </Popup>
          </Marker>
        ))}

        {reports.map(report => (
          <Marker key={report.id} position={report.coordinates}>
            <Popup>
              <div className="font-sans">
                <h4 className="font-bold text-red-700">Community Report</h4>
                <p className="text-sm font-semibold">{report.issueType}</p>
                <p className="text-xs text-slate-600 mt-1">{report.description}</p>
                <p className="text-xs mt-2 italic">Status: {report.status}</p>
              </div>
            </Popup>
          </Marker>
        ))}
      </MapContainer>

      {/* Map Controls Overlay */}
      <div className="absolute top-4 right-4 z-[1000] bg-white/90 backdrop-blur-sm p-4 rounded-xl shadow-lg border border-slate-200">
        <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-3">Active Map Layer</h4>
        <div className="flex flex-col gap-2 text-sm font-medium text-slate-700">
          <label className="flex items-center gap-2 cursor-pointer hover:text-blue-700 transition-colors">
            <input type="radio" name="layer" checked={activeLayer === 'none'} readOnly className="text-blue-600 focus:ring-blue-500" /> 
            Default View
          </label>
          <label className="flex items-center gap-2 cursor-pointer hover:text-blue-700 transition-colors">
            <input type="radio" name="layer" checked={activeLayer === 'accessibility'} readOnly className="text-blue-600 focus:ring-blue-500" /> 
            Accessibility Heatmap
          </label>
          <label className="flex items-center gap-2 cursor-pointer hover:text-blue-700 transition-colors">
            <input type="radio" name="layer" checked={activeLayer === 'gap'} readOnly className="text-blue-600 focus:ring-blue-500" /> 
            Service Gap Severity
          </label>
        </div>
      </div>
    </div>
  );
};
