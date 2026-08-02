'use client';

import React from 'react';
import { ArrowUpRight, ArrowDownRight, Minus } from 'lucide-react';

interface DashboardKpiCardProps {
  title: string;
  value: string;
  changePct?: number;
  changeLabel?: string;
  icon: React.ReactNode;
  iconBgColor: string;
  sparklineColor: string;
  sparklineData: number[];
  isLoading?: boolean;
}

export default function DashboardKpiCard({
  title,
  value,
  changePct = 0,
  changeLabel = 'vs Last Month',
  icon,
  iconBgColor,
  sparklineColor,
  sparklineData,
  isLoading = false,
}: DashboardKpiCardProps) {
  const isPositive = changePct > 0;
  const isNegative = changePct < 0;

  // Generate SVG path string from array of numbers
  const min = Math.min(...sparklineData, 0);
  const max = Math.max(...sparklineData, 1);
  const range = max - min || 1;
  const width = 180;
  const height = 40;

  const points = sparklineData.map((val, idx) => {
    const x = (idx / (sparklineData.length - 1)) * width;
    const y = height - ((val - min) / range) * (height - 8) - 4;
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  });

  const pathD = `M ${points.join(' L ')}`;
  const areaD = `M 0,${height} L ${points.join(' L ')} L ${width},${height} Z`;

  if (isLoading) {
    return (
      <div className="bg-white rounded-xl border border-gray-200 p-5 space-y-4 animate-pulse">
        <div className="flex items-center justify-between">
          <div className="h-4 w-24 bg-gray-200 rounded" />
          <div className="w-10 h-10 rounded-xl bg-gray-200" />
        </div>
        <div className="h-8 w-32 bg-gray-300 rounded" />
        <div className="h-4 w-20 bg-gray-200 rounded" />
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5 hover:shadow-md transition-shadow relative overflow-hidden flex flex-col justify-between">
      <div>
        <div className="flex items-center justify-between mb-3">
          <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
            {title}
          </span>
          <div className={`p-2.5 rounded-xl ${iconBgColor} text-white shadow-sm`}>
            {icon}
          </div>
        </div>

        <div className="flex items-baseline justify-between mb-2">
          <h3 className="text-2xl font-bold text-gray-900 tracking-tight">{value}</h3>
        </div>

        <div className="flex items-center gap-1.5 text-xs font-medium mb-3">
          {isPositive ? (
            <span className="inline-flex items-center px-1.5 py-0.5 rounded text-emerald-700 bg-emerald-50 font-semibold">
              <ArrowUpRight className="w-3.5 h-3.5 mr-0.5" />
              ▲ {Math.abs(changePct).toFixed(1)}%
            </span>
          ) : isNegative ? (
            <span className="inline-flex items-center px-1.5 py-0.5 rounded text-rose-700 bg-rose-50 font-semibold">
              <ArrowDownRight className="w-3.5 h-3.5 mr-0.5" />
              ▼ {Math.abs(changePct).toFixed(1)}%
            </span>
          ) : (
            <span className="inline-flex items-center px-1.5 py-0.5 rounded text-gray-600 bg-gray-100 font-semibold">
              <Minus className="w-3.5 h-3.5 mr-0.5" />
              0.0%
            </span>
          )}
          <span className="text-gray-400 font-normal">{changeLabel}</span>
        </div>
      </div>

      {/* Embedded Sparkline Chart */}
      <div className="w-full h-10 mt-1">
        <svg className="w-full h-full overflow-visible" viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none">
          <defs>
            <linearGradient id={`gradient-${title.replace(/\s+/g, '-')}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={sparklineColor} stopOpacity="0.25" />
              <stop offset="100%" stopColor={sparklineColor} stopOpacity="0.0" />
            </linearGradient>
          </defs>
          <path d={areaD} fill={`url(#gradient-${title.replace(/\s+/g, '-')})`} />
          <path d={pathD} fill="none" stroke={sparklineColor} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </div>
    </div>
  );
}
