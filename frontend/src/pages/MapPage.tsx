import React, { useState } from 'react';
import { CivicMap } from '../components/map/CivicMap';
import { LocalityProperties } from '../services/deterministicData';
import { Compass, MapPin, Activity } from 'lucide-react';

export const MapPage = () => {
  const [selectedLocality, setSelectedLocality] = useState<LocalityProperties | null>(null);

  return (
    <div className="h-full flex flex-col p-4 md:p-6 lg:p-8 max-w-7xl mx-auto space-y-6">
      {/* Header section */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-4 border-b border-slate-200 pb-5">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2 py-0.5 rounded text-[11px] font-bold uppercase tracking-wider bg-blue-50 text-blue-700 border border-blue-200 flex items-center gap-1">
              <Compass className="w-3 h-3 text-blue-600" />
              Spatial Intelligence
            </span>
            <span className="px-2 py-0.5 rounded text-[11px] font-bold uppercase tracking-wider bg-emerald-50 text-emerald-700 border border-emerald-200 flex items-center gap-1">
              <Activity className="w-3 h-3 text-emerald-600" />
              OpenStreetMap + Civic Engine
            </span>
          </div>
          <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">Civic Geospatial Map</h1>
          <p className="text-slate-500 mt-1 text-sm">
            Interactive multi-modal accessibility, verified service infrastructure, and real-time community report visualization.
          </p>
        </div>

        {selectedLocality && (
          <div className="bg-blue-50/80 border border-blue-200 px-3 py-1.5 rounded-xl text-xs flex items-center gap-2">
            <MapPin className="w-3.5 h-3.5 text-blue-600 shrink-0" />
            <span className="text-blue-900 font-semibold">Active Focus: {selectedLocality.name}</span>
            <button
              onClick={() => setSelectedLocality(null)}
              className="text-blue-500 hover:text-blue-700 ml-1 font-bold"
            >
              ×
            </button>
          </div>
        )}
      </div>

      {/* Main Map Container */}
      <div className="flex-1 w-full bg-white p-2 rounded-2xl shadow-sm border border-slate-200 min-h-[620px]">
        <CivicMap
          className="w-full h-full min-h-[600px]"
          onLocalitySelect={setSelectedLocality}
        />
      </div>
    </div>
  );
};
