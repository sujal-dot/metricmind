'use client';

import React from 'react';

export default function LoadingCharts() {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        {[...Array(6)].map((_, i) => (
          <div
            key={`kpi-skeleton-${i}`}
            className="bg-white rounded-xl border border-gray-200 p-6 space-y-3"
          >
            <div className="h-4 w-1/2 bg-gray-200 rounded animate-pulse" />
            <div className="h-10 w-3/4 bg-gray-200 rounded animate-pulse" />
            <div className="h-4 w-1/3 bg-gray-200 rounded animate-pulse" />
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {[...Array(4)].map((_, i) => (
          <div
            key={`chart-skeleton-${i}`}
            className="bg-white rounded-xl border border-gray-200 p-6"
          >
            <div className="h-5 w-1/3 bg-gray-200 rounded animate-pulse mb-4" />
            <div className="h-5 w-1/2 bg-gray-100 rounded animate-pulse mb-6" />
            <div className="h-80 bg-gray-50 rounded-lg animate-pulse" />
          </div>
        ))}
      </div>
    </div>
  );
}
