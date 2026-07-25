'use client';

import React from 'react';

interface ChartContainerProps {
  title: string;
  subtitle?: string;
  children: React.ReactNode;
  className?: string;
  isLoading?: boolean;
  error?: string | null;
}

export default function ChartContainer({
  title,
  subtitle,
  children,
  className = '',
  isLoading = false,
  error = null,
}: ChartContainerProps) {
  return (
    <div className={`bg-white rounded-xl border border-gray-200 p-6 ${className}`}>
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
        {subtitle && <p className="text-sm text-gray-500 mt-1">{subtitle}</p>}
      </div>
      {isLoading ? (
        <div className="flex items-center justify-center h-80 bg-gray-50 rounded-lg animate-pulse" />
      ) : error ? (
        <div className="flex items-center justify-center h-80 bg-red-50 rounded-lg p-4 text-center">
          <div>
            <p className="text-red-600 font-medium">Error loading data</p>
            <p className="text-sm text-red-500 mt-1">{error}</p>
          </div>
        </div>
      ) : (
        children
      )}
    </div>
  );
}
