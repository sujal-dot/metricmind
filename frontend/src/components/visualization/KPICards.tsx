'use client';

import type { KPIMetric } from '@/types/visualization';
import { formatCurrency, formatNumber, formatPercent } from '@/lib/chartUtils';

interface Props {
  data: KPIMetric[];
}

function formatMetricValue(metric: KPIMetric): string {
  switch (metric.format) {
    case 'currency':
      return formatCurrency(metric.value);
    case 'percent':
      return formatPercent(metric.value);
    case 'number':
    default:
      return formatNumber(metric.value);
  }
}

export default function KPICards({ data }: Props) {
  const cards = Array.isArray(data) ? data : [];
  const cols =
    cards.length <= 2
      ? 'grid-cols-1 sm:grid-cols-2'
      : cards.length <= 3
        ? 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3'
        : 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3';

  if (cards.length === 0) {
    return (
      <div className="rounded-xl border border-gray-200 bg-gray-50 p-6 text-center">
        <p className="text-sm text-gray-500">No KPI data to display.</p>
      </div>
    );
  }

  return (
    <div className={`grid gap-4 ${cols}`}>
      {cards.map((metric, idx) => (
        <div
          key={`${metric.label}-${idx}`}
          className="rounded-xl border border-gray-200 bg-white p-5"
        >
          <p className="text-sm font-medium text-gray-600">{metric.label}</p>
          <p className="mt-2 text-2xl font-bold text-gray-900">
            {formatMetricValue(metric)}
          </p>
          {metric.trend && metric.trendValue && (
            <div className="mt-2 flex items-center gap-1">
              <span
                className={`text-xs font-medium ${
                  metric.trend === 'up'
                    ? 'text-green-600'
                    : metric.trend === 'down'
                      ? 'text-red-600'
                      : 'text-gray-500'
                }`}
              >
                {metric.trend === 'up' ? '↑' : metric.trend === 'down' ? '↓' : '→'}{' '}
                {metric.trendValue}
              </span>
              {metric.description && (
                <span className="text-xs text-gray-500">{metric.description}</span>
              )}
            </div>
          )}
          {!metric.trend && metric.description && (
            <p className="mt-1 text-xs text-gray-500">{metric.description}</p>
          )}
        </div>
      ))}
    </div>
  );
}
