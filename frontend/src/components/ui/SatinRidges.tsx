import React from 'react';

export const SatinRidges = ({ className }: { className?: string }) => {
  return (
    <div className={`absolute inset-0 z-0 overflow-hidden ${className || ''}`}>
      {/* Mocking the flowing satin folds catching soft highlights */}
      <div className="absolute inset-0 bg-gradient-to-br from-[#0a1b33] via-[#0f2d59] to-[#143668]">
        <svg xmlns="http://www.w3.org/2000/svg" width="100%" height="100%" preserveAspectRatio="none" viewBox="0 0 100 100">
          <defs>
            <linearGradient id="satin1" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#2563eb" stopOpacity="0.2" />
              <stop offset="50%" stopColor="#3b82f6" stopOpacity="0.1" />
              <stop offset="100%" stopColor="#2563eb" stopOpacity="0.0" />
            </linearGradient>
            <linearGradient id="satin2" x1="100%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#38bdf8" stopOpacity="0.15" />
              <stop offset="70%" stopColor="#0ea5e9" stopOpacity="0.0" />
            </linearGradient>
          </defs>
          <path d="M0,0 C30,40 70,10 100,50 L100,100 L0,100 Z" fill="url(#satin1)" />
          <path d="M0,100 C40,70 60,90 100,40 L100,0 L0,0 Z" fill="url(#satin2)" />
        </svg>
      </div>
      <div className="absolute inset-0 backdrop-blur-[2px] bg-black/10 mix-blend-overlay"></div>
    </div>
  );
};
