import React, { useState } from 'react';
import { CivicMap } from '../components/map/CivicMap';

export const MapPage = () => {
  const [activeLayer, setActiveLayer] = useState<'none' | 'accessibility' | 'gap' | 'equity'>('none');

  // Mock data for Stage 6 UI contract visualization
  const mockFacilities = [
    { id: '1', name: 'Central Hospital', type: 'Healthcare', coordinates: [51.505, -0.09] as [number, number], capacity: 500, pressureScore: 85 },
    { id: '2', name: 'Westside School', type: 'Education', coordinates: [51.51, -0.1] as [number, number], capacity: 1200, pressureScore: 60 }
  ];

  return (
    <div className="h-full flex flex-col p-4 md:p-6 lg:p-8 max-w-7xl mx-auto space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 tracking-tight">Civic Map</h1>
          <p className="text-slate-500 mt-1">Explore spatial data, accessibility, and community reports.</p>
        </div>
        <div className="flex gap-2">
          <select 
            className="border border-slate-300 rounded-lg px-3 py-2 text-sm focus:ring-blue-500 focus:border-blue-500 bg-white shadow-sm"
            value={activeLayer}
            onChange={(e) => setActiveLayer(e.target.value as any)}
          >
            <option value="none">No Layer</option>
            <option value="accessibility">Accessibility Heatmap</option>
            <option value="gap">Service Gap</option>
          </select>
          <select className="border border-slate-300 rounded-lg px-3 py-2 text-sm focus:ring-blue-500 focus:border-blue-500 bg-white shadow-sm">
            <option>All Services</option>
            <option>Healthcare</option>
            <option>Education</option>
          </select>
        </div>
      </div>
      
      <div className="flex-1 bg-white p-2 rounded-2xl shadow-sm border border-slate-200">
        <CivicMap facilities={mockFacilities} activeLayer={activeLayer} />
      </div>
    </div>
  );
};
