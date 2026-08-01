'use client';

import StatCard from '@/components/StatCard';
import { formatCurrency, formatNumber } from '@/lib/chartUtils';
import { useMetrics } from '@/lib/hooks';
import { useQueryClient } from '@tanstack/react-query';

type TrendDirection = 'up' | 'down' | 'neutral';

function DashboardStatSkeleton() {
  return (
    <div className="bg-white p-6 rounded-xl border border-gray-200 animate-pulse">
      <div className="h-5 bg-gray-200 rounded w-1/2 mb-2" />
      <div className="h-10 bg-gray-300 rounded w-3/4 mb-2" />
      <div className="h-4 bg-gray-200 rounded w-1/3" />
    </div>
  );
}

function formatMarginPct(value: number | null | undefined): string {
  if (value == null || !isFinite(value)) return '0.0%';
  return `${value.toFixed(1)}%`;
}

function formatTrendValue(delta: number | null | undefined): {
  trend: TrendDirection;
  trendValue: string;
} {
  if (delta == null || !isFinite(delta)) {
    return { trend: 'neutral', trendValue: '0.0%' };
  }
  const rounded = Math.round(delta * 10) / 10;
  const sign = rounded > 0 ? '+' : '';
  const trend: TrendDirection =
    rounded > 0 ? 'up' : rounded < 0 ? 'down' : 'neutral';
  return { trend, trendValue: `${sign}${rounded}%` };
}

function formatMarginDelta(delta: number | null | undefined): {
  trend: TrendDirection;
  trendValue: string;
} {
  if (delta == null || !isFinite(delta)) {
    return { trend: 'neutral', trendValue: '0.0pp' };
  }
  const rounded = Math.round(delta * 10) / 10;
  const sign = rounded > 0 ? '+' : '';
  const trend: TrendDirection =
    rounded > 0 ? 'up' : rounded < 0 ? 'down' : 'neutral';
  return { trend, trendValue: `${sign}${rounded}pp` };
}

export default function DashboardPage() {
  const { data: metrics, isLoading, isError, error } = useMetrics();
  const queryClient = useQueryClient();

  if (isLoading) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-6">
          <DashboardStatSkeleton />
          <DashboardStatSkeleton />
          <DashboardStatSkeleton />
          <DashboardStatSkeleton />
          <DashboardStatSkeleton />
          <DashboardStatSkeleton />
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>

      {isError && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4 flex items-center justify-between">
          <div>
            <p className="text-red-700 font-medium">
              Error loading dashboard metrics
            </p>
            <p className="text-red-600 text-sm">
              {error?.message || 'Please check backend connection'}
            </p>
          </div>
          <button
            onClick={() => queryClient.refetchQueries({ queryKey: ['metrics'] })}
            className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors text-sm font-medium"
          >
            Retry
          </button>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-6">
        <StatCard
          title="Total Revenue"
          value={formatCurrency(metrics?.total_revenue ?? 0)}
          {...formatTrendValue(metrics?.period_change_pct?.total_revenue)}
        />
        <StatCard
          title="Total Profit"
          value={formatCurrency(metrics?.total_profit ?? 0)}
          {...formatTrendValue(metrics?.period_change_pct?.total_profit)}
        />
        <StatCard
          title="Profit Margin"
          value={formatMarginPct(metrics?.profit_margin)}
          {...formatMarginDelta(metrics?.period_change_pct?.profit_margin)}
        />
        <StatCard
          title="Total Orders"
          value={formatNumber(metrics?.total_orders ?? 0)}
          {...formatTrendValue(metrics?.period_change_pct?.total_orders)}
        />
        <StatCard
          title="Total Customers"
          value={formatNumber(metrics?.total_customers ?? 0)}
          {...formatTrendValue(metrics?.period_change_pct?.total_customers)}
        />
        <StatCard
          title="Avg Order Value"
          value={formatCurrency(metrics?.average_order_value ?? 0)}
          {...formatTrendValue(metrics?.period_change_pct?.average_order_value)}
        />
      </div>
    </div>
  );
}
