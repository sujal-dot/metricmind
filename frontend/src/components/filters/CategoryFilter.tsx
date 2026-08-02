'use client';

import React, { useEffect } from 'react';

interface CategoryFilterProps {
  value: string;
  onChange: (value: string) => void;
  categories?: string[];
  className?: string;
}

const DEFAULT_CATEGORIES = [
  'Technology',
  'Office Supplies',
  'Furniture',
];

export default function CategoryFilter({
  value,
  onChange,
  categories = DEFAULT_CATEGORIES,
  className = '',
}: CategoryFilterProps) {
  const isDefaultCategories = categories === DEFAULT_CATEGORIES;

  useEffect(() => {
    // Only auto-clear if the categories array actually changed to a new reference
    // that doesn't include the value.
    if (!isDefaultCategories && value && !categories.includes(value)) {
      onChange('');
    }
  }, [categories, onChange, value, isDefaultCategories]);

  return (
    <div className={className}>
      <label className="block">
        <span className="text-sm font-medium text-gray-700">Category</span>
        <select
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed"
          disabled={categories.length === 0}
        >
          <option value="">All Categories</option>
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
