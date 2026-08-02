'use client';

import React from 'react';

interface RegionDataPoint {
  name: string;
  value: number;
}

interface RegionBreakdownCardProps {
  data: RegionDataPoint[];
  isLoading?: boolean;
}

const REGION_COLOR_MAP: Record<string, { color: string; bg: string }> = {
  West: { color: '#3b82f6', bg: 'bg-blue-500' },
  East: { color: '#10b981', bg: 'bg-emerald-500' },
  Central: { color: '#8b5cf6', bg: 'bg-purple-500' },
  South: { color: '#f97316', bg: 'bg-orange-500' },
};

export default function RegionBreakdownCard({ data, isLoading = false }: RegionBreakdownCardProps) {
  const total = data.reduce((acc, r) => acc + r.value, 0) || 1;

  if (isLoading) {
    return (
      <div className="h-64 flex items-center justify-center bg-gray-50 rounded-xl animate-pulse space-y-3">
        <div className="w-full space-y-3 px-4">
          <div className="h-4 bg-gray-200 rounded w-3/4" />
          <div className="h-4 bg-gray-200 rounded w-1/2" />
          <div className="h-4 bg-gray-200 rounded w-2/3" />
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col sm:flex-row items-center justify-between gap-6 h-full">
      {/* Map Illustration Graphic */}
      <div className="w-full sm:w-1/2 h-56 bg-slate-50 rounded-xl p-4 flex items-center justify-center relative overflow-hidden border border-slate-100">
        <svg className="w-full h-full text-slate-300" viewBox="0 0 400 240" fill="none">
          {/* Stylized Region Map Contours */}
          <path
            d="M40 60 Q 90 20, 160 50 T 260 40 T 360 80 Q 380 140, 320 180 T 180 200 T 50 160 Z"
            fill="#e2e8f0"
            stroke="#cbd5e1"
            strokeWidth="2"
          />
          {/* West Region Overlay */}
          <path d="M40 60 Q 90 20, 140 80 T 100 160 T 50 160 Z" fill="#3b82f6" fillOpacity="0.4" />
          {/* Central Region Overlay */}
          <path d="M140 80 Q 200 60, 240 100 T 200 180 T 100 160 Z" fill="#8b5cf6" fillOpacity="0.4" />
          {/* East Region Overlay */}
          <path d="M240 100 Q 300 40, 360 80 T 320 150 T 240 100 Z" fill="#10b981" fillOpacity="0.4" />
          {/* South Region Overlay */}
          <path d="M200 140 Q 260 140, 320 150 T 260 210 T 180 200 Z" fill="#f97316" fillOpacity="0.5" />
          
          {/* Region Location Pins */}
          <circle cx="90" cy="100" r="6" fill="#3b82f6" className="animate-ping opacity-75" />
          <circle cx="90" cy="100" r="5" fill="#2563eb" />

          <circle cx="280" cy="95" r="6" fill="#10b981" className="animate-ping opacity-75" />
          <circle cx="280" cy="95" r="5" fill="#059669" />

          <circle cx="190" cy="120" r="6" fill="#8b5cf6" className="animate-ping opacity-75" />
          <circle cx="190" cy="120" r="5" fill="#7c3aed" />

          <circle cx="250" cy="165" r="6" fill="#f97316" className="animate-ping opacity-75" />
          <circle cx="250" cy="165" r="5" fill="#ea580c" />
        </svg>
      </div>

      {/* Region Sales Stats List */}
      <div className="w-full sm:w-1/2 space-y-4">
        {data.map((item) => {
          const pct = ((item.value / total) * 100).toFixed(1);
          const style = REGION_COLOR_MAP[item.name] || { color: '#64748b', bg: 'bg-slate-500' };
          const formattedVal = new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
            maximumFractionDigits: 0,
          }).format(item.value);

          return (
            <div key={item.name} className="space-y-1.5">
              <div className="flex items-center justify-between text-sm">
                <div className="flex items-center gap-2">
                  <span className={`w-3 h-3 rounded-full ${style.bg}`} />
                  <span className="font-semibold text-gray-800">{item.name}</span>
                </div>
                <div className="text-right">
                  <span className="font-bold text-gray-900">{formattedVal}</span>
                  <span className="text-xs text-gray-500 ml-1">({pct}%)</span>
                </div>
              </div>
              {/* Progress bar */}
              <div className="w-full bg-gray-100 rounded-full h-2 overflow-hidden">
                <div
                  className="h-full rounded-full transition-all duration-500"
                  style={{ width: `${pct}%`, backgroundColor: style.color }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
