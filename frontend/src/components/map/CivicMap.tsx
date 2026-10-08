import React, { useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import { ServiceFacility, CommunityReport } from '../../types/models';

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
  center?: [number, number];
  zoom?: number;
  activeLayer?: 'none' | 'accessibility' | 'gap' | 'equity';
}

export const CivicMap: React.FC<CivicMapProps> = ({ 
  facilities = [], 
  reports = [],
  center = [51.505, -0.09], // Default London
  zoom = 13,
  activeLayer = 'none'
}) => {
  return (
    <div className="w-full h-full min-h-[500px] relative rounded-xl overflow-hidden border border-slate-200 shadow-sm z-0">
      <MapContainer center={center} zoom={zoom} style={{ height: '100%', width: '100%' }}>
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors | CivicPulse'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        
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

        {/* Placeholder for GeoJSON / Heatmap layers which will be integrated in later stages when API delivers them */}
      </MapContainer>

      {/* Map Controls Overlay */}
      <div className="absolute top-4 right-4 z-[1000] bg-white p-2 rounded-lg shadow-md border border-slate-200">
        <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Active Layer</h4>
        <div className="flex flex-col gap-1 text-sm">
          <label className="flex items-center gap-2 cursor-pointer">
            <input type="radio" name="layer" checked={activeLayer === 'none'} readOnly className="text-blue-600" /> None
          </label>
          <label className="flex items-center gap-2 cursor-pointer">
            <input type="radio" name="layer" checked={activeLayer === 'accessibility'} readOnly className="text-blue-600" /> Accessibility Heatmap
          </label>
          <label className="flex items-center gap-2 cursor-pointer">
            <input type="radio" name="layer" checked={activeLayer === 'gap'} readOnly className="text-blue-600" /> Service Gap
          </label>
        </div>
      </div>
    </div>
  );
};
