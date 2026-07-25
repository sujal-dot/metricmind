'use client';

import KPICard from './KPICard';
import { useMetrics } from '@/lib/hooks';
import { formatCurrency, formatPercent, formatNumber } from '@/lib/chartUtils';
import type { AnalyticsFilters } from '@/types/analytics';

interface KPIGridProps {
  filters?: AnalyticsFilters;
}

export default function KPIGrid({ filters = {} }: KPIGridProps) {
  const { data, isLoading, error } = useMetrics(filters);

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
      <KPICard
        title="Total Revenue"
        value={data ? formatCurrency(data.total_revenue) : 0}
        isLoading={isLoading}
        error={error?.message || null}
      />
      <KPICard
        title="Total Profit"
        value={data ? formatCurrency(data.total_profit) : 0}
        isLoading={isLoading}
        error={error?.message || null}
      />
      <KPICard
        title="Profit Margin"
        value={data ? formatPercent(data.profit_margin) : '0%'}
        isLoading={isLoading}
        error={error?.message || null}
      />
      <KPICard
        title="Total Orders"
        value={data ? formatNumber(data.total_orders) : 0}
        isLoading={isLoading}
        error={error?.message || null}
      />
      <KPICard
        title="Total Customers"
        value={data ? formatNumber(data.total_customers) : 0}
        isLoading={isLoading}
        error={error?.message || null}
      />
      <KPICard
        title="Average Order Value"
        value={data ? formatCurrency(data.average_order_value) : 0}
        isLoading={isLoading}
        error={error?.message || null}
      />
    </div>
  );
}
