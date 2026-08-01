'use client';

import React, { useEffect } from 'react';

interface RegionFilterProps {
  value: string;
  onChange: (value: string) => void;
  regions?: string[];
  className?: string;
}

const DEFAULT_REGIONS = [
  'Central',
  'East',
  'South',
  'West',
];

export default function RegionFilter({
  value,
  onChange,
  regions = DEFAULT_REGIONS,
  className = '',
}: RegionFilterProps) {
  useEffect(() => {
    if (value && !regions.includes(value)) {
      onChange('');
    }
  }, [onChange, regions, value]);

  return (
    <div className={className}>
      <label className="block">
        <span className="text-sm font-medium text-gray-700">Region</span>
        <select
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          aria-label="Filter by region"
        >
          <option value="">All Regions</option>
          {regions.map((region) => (
            <option key={region} value={region}>
              {region}
            </option>
          ))}
        </select>
      </label>
    </div>
  );
}
