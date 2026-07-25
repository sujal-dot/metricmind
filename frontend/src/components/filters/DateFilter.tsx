'use client';

import React from 'react';

interface DateFilterProps {
  dateFrom: string;
  dateTo: string;
  onDateFromChange: (value: string) => void;
  onDateToChange: (value: string) => void;
  className?: string;
}

export default function DateFilter({
  dateFrom,
  dateTo,
  onDateFromChange,
  onDateToChange,
  className = '',
}: DateFilterProps) {
  const presets = [
    { label: 'Last 7 days', days: 7 },
    { label: 'Last 30 days', days: 30 },
    { label: 'Last 90 days', days: 90 },
    { label: 'Last 12 months', days: 365 },
  ];

  const applyPreset = (days: number) => {
    const to = new Date();
    const from = new Date();
    from.setDate(from.getDate() - days);
    onDateFromChange(from.toISOString().split('T')[0]);
    onDateToChange(to.toISOString().split('T')[0]);
  };

  const clearDates = () => {
    onDateFromChange('');
    onDateToChange('');
  };

  return (
    <div className={`flex flex-col gap-3 ${className}`}>
      <label className="block">
        <span className="text-sm font-medium text-gray-700">Date Range</span>
        <div className="mt-1 flex flex-col sm:flex-row gap-2">
          <div className="flex items-center gap-2">
            <input
              type="date"
              value={dateFrom}
              onChange={(e) => onDateFromChange(e.target.value)}
              className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              aria-label="From date"
            />
            <span className="text-gray-500 text-sm">to</span>
            <input
              type="date"
              value={dateTo}
              onChange={(e) => onDateToChange(e.target.value)}
              className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              aria-label="To date"
            />
          </div>
          {(dateFrom || dateTo) && (
            <button
              type="button"
              onClick={clearDates}
              className="px-3 py-2 text-sm text-gray-600 hover:text-gray-800 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            >
              Clear
            </button>
          )}
        </div>
      </label>
      <div className="flex flex-wrap gap-2">
        {presets.map((preset) => (
          <button
            key={preset.label}
            type="button"
            onClick={() => applyPreset(preset.days)}
            className="px-3 py-1.5 text-xs font-medium text-blue-600 bg-blue-50 rounded-full hover:bg-blue-100 transition-colors"
          >
            {preset.label}
          </button>
        ))}
      </div>
    </div>
  );
}
