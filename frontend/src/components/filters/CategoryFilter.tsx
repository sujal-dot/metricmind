'use client';

import React from 'react';

interface CategoryFilterProps {
  value: string;
  onChange: (value: string) => void;
  categories?: string[];
  className?: string;
}

const DEFAULT_CATEGORIES = [
  'All Categories',
  'Technology',
  'Office Supplies',
  'Furniture',
  'Consumer Electronics',
  'Apparel',
  'Home & Kitchen',
];

export default function CategoryFilter({
  value,
  onChange,
  categories = DEFAULT_CATEGORIES,
  className = '',
}: CategoryFilterProps) {
  return (
    <div className={className}>
      <label className="block">
        <span className="text-sm font-medium text-gray-700">Category</span>
        <select
          value={value}
          onChange={(e) =>
            onChange(e.target.value === 'All Categories' ? '' : e.target.value)
          }
          className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          aria-label="Filter by category"
        >
          {categories.map((category) => (
            <option key={category} value={category}>
              {category}
            </option>
          ))}
        </select>
      </label>
    </div>
  );
}
