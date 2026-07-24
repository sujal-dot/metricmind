'use client';

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
    <div className="bg-white p-6 rounded-xl border border-gray-200">
      <div className="flex items-center justify-between mb-2">
        <p className="text-gray-600 font-medium">{title}</p>
        {icon && <div className="text-gray-400">{icon}</div>}
      </div>
      <p className="text-3xl font-bold text-gray-900 mb-2">{value}</p>
      {trend && trendValue && (
        <div className="flex items-center gap-1">
          <p
            className={`text-sm ${
              trend === 'up'
                ? 'text-green-600'
                : trend === 'down'
                ? 'text-red-600'
                : 'text-gray-500'
            }`}
          >
            {trend === 'up' ? '↑' : trend === 'down' ? '↓' : ''} {trendValue}
          </p>
        </div>
      )}
      {description && <p className="text-sm text-gray-500 mt-1">{description}</p>}
    </div>
  );
}
