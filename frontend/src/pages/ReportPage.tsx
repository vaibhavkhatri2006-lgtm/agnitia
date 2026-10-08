import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { ShieldAlert, CheckCircle2, MapPin, Camera } from 'lucide-react';

export const ReportPage = () => {
  const { user } = useAuth();
  const [submitted, setSubmitted] = useState(false);

  if (user?.role !== 'Citizen' && user?.role !== 'Community') {
    return (
      <div className="p-8 max-w-3xl mx-auto text-center">
        <h2 className="text-2xl font-bold text-red-600">Access Restricted</h2>
        <p className="mt-2 text-slate-600">Only Citizens and Community organizations can submit Reality Reports.</p>
      </div>
    );
  }

  if (submitted) {
    return (
      <div className="max-w-2xl mx-auto p-8 mt-12 bg-white rounded-2xl shadow-sm border border-emerald-100 text-center">
        <CheckCircle2 className="w-16 h-16 text-emerald-500 mx-auto mb-4" />
        <h2 className="text-2xl font-bold text-slate-900 mb-2">Report Submitted Successfully</h2>
        <p className="text-slate-600 mb-6">
          Your reality report has been securely logged. It is now pending verification by the community and authorities.
        </p>
        <button
          onClick={() => setSubmitted(false)}
          className="px-6 py-2 bg-slate-100 text-slate-700 font-medium rounded-lg hover:bg-slate-200 transition-colors"
        >
          Submit Another Report
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto p-4 md:p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-slate-900 tracking-tight flex items-center gap-3">
          <ShieldAlert className="w-8 h-8 text-blue-600" />
          Report Reality
        </h1>
        <p className="text-slate-500 mt-2">
          Help us close the data gap. Report on-the-ground realities about civic infrastructure and services in your area.
        </p>
      </div>

      <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
        <div className="p-6 md:p-8">
          <form className="space-y-6" onSubmit={(e) => { e.preventDefault(); setSubmitted(true); }}>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Issue Category</label>
                <select className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:ring-blue-500 focus:border-blue-500 bg-white">
                  <option>Healthcare Access</option>
                  <option>Education Quality</option>
                  <option>Public Transport</option>
                  <option>Infrastructure Damage</option>
                  <option>Safety Concern</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Location</label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <MapPin className="h-4 w-4 text-slate-400" />
                  </div>
                  <input
                    type="text"
                    className="w-full pl-10 border border-slate-300 rounded-lg px-3 py-2 text-sm focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Enter address or select on map"
                  />
                </div>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Description</label>
              <textarea
                rows={4}
                className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:ring-blue-500 focus:border-blue-500"
                placeholder="Describe what you see on the ground vs what is officially reported..."
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Photographic Evidence</label>
              <div className="mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-slate-300 border-dashed rounded-lg hover:bg-slate-50 transition-colors cursor-pointer">
                <div className="space-y-1 text-center">
                  <Camera className="mx-auto h-12 w-12 text-slate-400" />
                  <div className="flex text-sm text-slate-600 justify-center">
                    <span className="relative cursor-pointer bg-white rounded-md font-medium text-blue-600 hover:text-blue-500 focus-within:outline-none">
                      Upload a file
                    </span>
                    <p className="pl-1">or drag and drop</p>
                  </div>
                  <p className="text-xs text-slate-500">PNG, JPG, GIF up to 10MB</p>
                </div>
              </div>
            </div>

            <div className="bg-blue-50 rounded-lg p-4 flex gap-3 border border-blue-100">
              <ShieldAlert className="w-5 h-5 text-blue-600 shrink-0 mt-0.5" />
              <div className="text-sm text-blue-800">
                <strong>Trust Center:</strong> Your report will undergo a verification process. Validated reports contribute to the community's Civic Trust Score and help direct real investment.
              </div>
            </div>

            <div className="pt-4 flex justify-end">
              <button
                type="submit"
                className="bg-blue-600 text-white font-medium px-6 py-2.5 rounded-lg shadow-sm hover:bg-blue-700 transition-colors"
              >
                Submit Report
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};
