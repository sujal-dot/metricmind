'use client';

import React from 'react';

interface DateFilterProps {
  dateFrom: string;
  dateTo: string;
  onDateFromChange: (value: string) => void;
  onDateToChange: (value: string) => void;
  maxDate?: string;
  className?: string;
}

export default function DateFilter({
  dateFrom,
  dateTo,
  onDateFromChange,
  onDateToChange,
  maxDate,
  className = '',
}: DateFilterProps) {
  const presets = [
    { label: 'Last 7 days', days: 7 },
    { label: 'Last 30 days', days: 30 },
    { label: 'Last 90 days', days: 90 },
    { label: 'Last 12 months', days: 365 },
  ];

  const applyPreset = (days: number) => {
    // Avoid time zone shifting: parse YYYY-MM-DD as UTC and do math in UTC
    const to = maxDate ? new Date(`${maxDate}T00:00:00Z`) : new Date(new Date().setUTCHours(0, 0, 0, 0));
    const from = new Date(to.getTime());
    from.setUTCDate(to.getUTCDate() - days);
    onDateFromChange(from.toISOString().split('T')[0]);
    onDateToChange(to.toISOString().split('T')[0]);
  };

  const clearDates = () => {
    onDateFromChange('');
    onDateToChange('');
  };

  const handleDateFromChange = (value: string) => {
    if (value && dateTo && value > dateTo) {
      onDateToChange(value);
    }
    onDateFromChange(value);
  };

  const handleDateToChange = (value: string) => {
    if (value && dateFrom && value < dateFrom) {
      onDateFromChange(value);
    }
    onDateToChange(value);
  };

  return (
    <div className={`flex flex-col gap-3 ${className}`}>
      <label className="block">
        <span className="text-sm font-medium text-gray-700">Date Range</span>
        <div className="mt-1 flex flex-col gap-2">
          <div className="grid grid-cols-[minmax(0,1fr)_auto_minmax(0,1fr)] items-center gap-2">
            <input
              type="date"
              value={dateFrom}
              max={dateTo || maxDate}
              onChange={(e) => handleDateFromChange(e.target.value)}
              className="w-full min-w-0 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              aria-label="From date"
            />
            <span className="text-gray-500 text-sm">to</span>
            <input
              type="date"
              value={dateTo}
              min={dateFrom}
              max={maxDate}
              onChange={(e) => handleDateToChange(e.target.value)}
              className="w-full min-w-0 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
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
