import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { CivicScoreProvider } from './context/CivicScoreContext';
import { AppLayout } from './components/layout/AppLayout';
import { ProtectedRoute } from './components/layout/ProtectedRoute';
import { Login } from './pages/Login';
import { Dashboard } from './pages/Dashboard';
import { MapPage } from './pages/MapPage';
import { ReportPage } from './pages/ReportPage';
import { MethodologyPage } from './pages/MethodologyPage';
import { SimulationPage } from './pages/SimulationPage';

function App() {
  return (
    <AuthProvider>
      <CivicScoreProvider>
        <Router>
          <Routes>
            <Route path="/login" element={<Login />} />
            
            {/* Protected Routes */}
            <Route element={<ProtectedRoute />}>
              <Route element={<AppLayout />}>
                <Route path="/" element={<Navigate to="/dashboard" replace />} />
                <Route path="/dashboard" element={<Dashboard />} />
                <Route path="/map" element={<MapPage />} />
                <Route path="/scenario-lab" element={<SimulationPage />} />
                <Route path="/report" element={<ReportPage />} />
                <Route path="/methodology" element={<MethodologyPage />} />
              </Route>
            </Route>
            
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </Router>
      </CivicScoreProvider>
    </AuthProvider>
  );
}

export default App;
