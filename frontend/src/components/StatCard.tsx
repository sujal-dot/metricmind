'use client';

import { Card, Text } from '@tremor/react';

interface StatCardProps {
  title: string;
  value: string | number;
  icon?: React.ReactNode;
  trend?: 'up' | 'down' | 'neutral';
  trendValue?: string;
  description?: string;
}

export default function StatCard({
  title,
  value,
  icon,
  trend,
  trendValue,
  description,
}: StatCardProps) {
  return (
    <Card className="p-6">
      <div className="flex items-center justify-between mb-2">
        <Text className="text-gray-500 font-medium">{title}</Text>
        {icon && <div className="text-gray-400">{icon}</div>}
      </div>
      <Text className="text-3xl font-bold text-gray-900 mb-2">{value}</Text>
      {trend && trendValue && (
        <div className="flex items-center gap-1">
          <Text
            className={`text-sm ${
              trend === 'up'
                ? 'text-green-600'
                : trend === 'down'
                ? 'text-red-600'
                : 'text-gray-500'
            }`}
          >
            {trend === 'up' ? '↑' : trend === 'down' ? '↓' : ''} {trendValue}
          </Text>
        </div>
      )}
      {description && (
        <Text className="text-sm text-gray-500 mt-1">{description}</Text>
      )}
    </Card>
  );
}
