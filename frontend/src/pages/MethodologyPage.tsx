import React from 'react';
import { BookOpen } from 'lucide-react';

export const MethodologyPage = () => {
  return (
    <div className="p-4 md:p-8 max-w-4xl mx-auto space-y-8">
      <div className="mb-8 border-b border-slate-200 pb-8">
        <h1 className="text-3xl font-bold text-slate-900 tracking-tight flex items-center gap-3">
          <BookOpen className="w-8 h-8 text-blue-600" />
          Methodology & Why CivicPulse
        </h1>
        <p className="text-slate-500 mt-2 text-lg">
          Understanding the data, metrics, and mission behind our civic tech platform.
        </p>
      </div>

      <section className="space-y-4">
        <h2 className="text-2xl font-bold text-slate-800">Why CivicPulse?</h2>
        <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200 text-slate-700 leading-relaxed space-y-4">
          <p>
            CivicPulse bridges the gap between official urban planning data and the lived realities of citizens. Traditional planning often relies on outdated or incomplete data, leading to underserved communities and misallocated resources.
          </p>
          <p>
            By crowdsourcing community reports and combining them with official geospatial data, CivicPulse creates a dynamic, high-confidence map of city infrastructure. This empowers citizens to advocate for their needs and allows urban planners to prioritize investments equitably.
          </p>
        </div>
      </section>

      <section className="space-y-4">
        <h2 className="text-2xl font-bold text-slate-800">Core Metrics</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-white p-5 rounded-xl shadow-sm border border-slate-200">
            <h3 className="font-bold text-slate-900 mb-2">Accessibility Score</h3>
            <p className="text-sm text-slate-600">Calculates the ease of reaching essential services (healthcare, education) based on geographic proximity, transit links, and physical barriers.</p>
          </div>
          <div className="bg-white p-5 rounded-xl shadow-sm border border-slate-200">
            <h3 className="font-bold text-slate-900 mb-2">Equity Index</h3>
            <p className="text-sm text-slate-600">Measures the distribution of resources across demographics to ensure historically underserved areas receive prioritized intervention.</p>
          </div>
          <div className="bg-white p-5 rounded-xl shadow-sm border border-slate-200">
            <h3 className="font-bold text-slate-900 mb-2">Reality Gap</h3>
            <p className="text-sm text-slate-600">The delta between official capacity/status of a facility and the on-the-ground reality verified by community reports.</p>
          </div>
          <div className="bg-white p-5 rounded-xl shadow-sm border border-slate-200">
            <h3 className="font-bold text-slate-900 mb-2">Confidence Score</h3>
            <p className="text-sm text-slate-600">A dynamic score reflecting the reliability of data, weighted heavily by community verification and recent audit timelines.</p>
          </div>
        </div>
      </section>
      
      <section className="space-y-4">
        <h2 className="text-2xl font-bold text-slate-800">Data & Trust</h2>
        <div className="bg-blue-50 p-6 rounded-xl border border-blue-100 text-blue-900 leading-relaxed text-sm">
          <h4 className="font-bold mb-2">OpenStreetMap Attribution</h4>
          <p className="mb-4">
            Map data &copy; <a href="https://www.openstreetmap.org/copyright" className="underline hover:text-blue-700">OpenStreetMap contributors</a>. CivicPulse relies on open spatial data enriched by proprietary and community-sourced layers.
          </p>
          <h4 className="font-bold mb-2">Demo Data Disclaimer</h4>
          <p>
            Please note that the current environment may display <strong>Demo Data</strong> for illustrative purposes. This data is synthetically generated to showcase features and does not represent real-world civic deficiencies unless explicitly stated.
          </p>
        </div>
      </section>
    </div>
  );
};
