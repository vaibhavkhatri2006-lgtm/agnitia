import React, { useState } from 'react';
import { CivicMap } from '../components/map/CivicMap';
import { SimulationPanel } from '../components/simulation/SimulationPanel';
import { Compass, Sparkles } from 'lucide-react';
import { Marker, Popup } from 'react-leaflet';
import L from 'leaflet';

export const SimulationPage = () => {
  const [selectedLocation, setSelectedLocation] = useState<{lat: number, lng: number} | null>(null);
  const [simulationResult, setSimulationResult] = useState<any>(null);

  const handleMapClick = (lat: number, lng: number) => {
    setSelectedLocation({ lat, lng });
    setSimulationResult(null); // Reset result on new click
  };

  const handleSimulateComplete = (res: any) => {
    setSimulationResult(res);
  };

  return (
    <div className="h-full flex flex-col p-4 md:p-6 lg:p-8 max-w-[1600px] mx-auto space-y-6">
      {/* Header section */}
      <div className="flex flex-col justify-between items-start border-b border-slate-200 pb-5">
        <div className="flex items-center gap-2 mb-1">
          <span className="px-2 py-0.5 rounded text-[11px] font-bold uppercase tracking-wider bg-purple-50 text-purple-700 border border-purple-200 flex items-center gap-1">
            <Sparkles className="w-3 h-3 text-purple-600" />
            Intervention Simulation
          </span>
          <span className="px-2 py-0.5 rounded text-[11px] font-bold uppercase tracking-wider bg-blue-50 text-blue-700 border border-blue-200 flex items-center gap-1">
            <Compass className="w-3 h-3 text-blue-600" />
            Spatial Intelligence
          </span>
        </div>
        <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">Scenario Lab</h1>
        <p className="text-slate-500 mt-1 text-sm">
          Simulate civic facility placement and predict impact on accessibility and service gaps.
        </p>
      </div>

      {/* Main Layout */}
      <div className="flex flex-col lg:flex-row gap-6 flex-1 min-h-[650px]">
        {/* Left Panel - Simulation Control */}
        <div className="w-full lg:w-[400px] xl:w-[450px] shrink-0">
          <SimulationPanel 
            selectedLocation={selectedLocation} 
            onSimulateComplete={handleSimulateComplete} 
          />
        </div>

        {/* Right Panel - Map */}
        <div className="flex-1 bg-white p-2 rounded-2xl shadow-sm border border-slate-200 relative overflow-hidden">
          <CivicMap
            className="w-full h-full rounded-xl"
            onMapClick={handleMapClick}
            simulationPin={selectedLocation}
            activeLayer={simulationResult ? 'accessibility' : 'services'}
          />
        </div>
      </div>
    </div>
  );
};
