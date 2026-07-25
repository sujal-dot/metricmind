'use client';

import React from 'react';

type TrendDirection = 'up' | 'down' | 'neutral';

interface KPICardProps {
  title: string;
  value: string | number;
  icon?: React.ReactNode;
  trend?: TrendDirection;
  trendValue?: string;
  description?: string;
  isLoading?: boolean;
  error?: string | null;
}

export default function KPICard({
  title,
  value,
  icon,
  trend,
  trendValue,
  description,
  isLoading = false,
  error = null,
}: KPICardProps) {
  const trendColors: Record<TrendDirection, string> = {
    up: 'text-green-600',
    down: 'text-red-600',
    neutral: 'text-gray-500',
  };

  const trendIcons: Record<TrendDirection, string> = {
    up: '↑',
    down: '↓',
    neutral: '→',
  };

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6">
      {isLoading ? (
        <div className="space-y-3">
          <div className="h-4 w-1/2 bg-gray-200 rounded animate-pulse" />
          <div className="h-10 w-3/4 bg-gray-200 rounded animate-pulse" />
          <div className="h-4 w-1/3 bg-gray-200 rounded animate-pulse" />
        </div>
      ) : error ? (
        <div>
          <p className="text-gray-600 font-medium mb-2">{title}</p>
          <p className="text-sm text-red-500">{error}</p>
        </div>
      ) : (
        <>
          <div className="flex items-center justify-between mb-2">
            <p className="text-gray-600 font-medium">{title}</p>
            {icon && <div className="text-gray-400">{icon}</div>}
          </div>
          <p className="text-3xl font-bold text-gray-900 mb-2">{value}</p>
          {trend && trendValue && (
            <div className="flex items-center gap-1">
              <span className={`text-sm ${trendColors[trend]}`}>
                {trendIcons[trend]} {trendValue}
              </span>
            </div>
          )}
          {description && <p className="text-sm text-gray-500 mt-1">{description}</p>}
        </>
      )}
    </div>
  );
}
