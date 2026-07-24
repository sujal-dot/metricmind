'use client';

import StatCard from '@/components/StatCard';
import Loading from '@/components/Loading';
import { useMetrics } from '@/lib/hooks';

export default function DashboardPage() {
  const { data: metrics, isLoading, isError } = useMetrics();

  if (isLoading) return <Loading text="Loading dashboard..." />;
  if (isError)
    return (
      <div className="text-center p-12">
        <p className="text-red-500">Error loading metrics: Please check backend connection</p>
      </div>
    );

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-6">
        <StatCard
          title="Total Revenue"
          value={`$${metrics?.total_revenue.toLocaleString() ?? 0}`}
          trend="up"
          trendValue="12%"
        />
        <StatCard
          title="Total Profit"
          value={`$${metrics?.total_profit.toLocaleString() ?? 0}`}
          trend="up"
          trendValue="8%"
        />
        <StatCard
          title="Total Orders"
          value={metrics?.total_orders.toLocaleString() ?? 0}
        />
        <StatCard
          title="Total Customers"
          value={metrics?.total_customers.toLocaleString() ?? 0}
        />
        <StatCard
          title="Profit Margin"
          value={`${((metrics?.profit_margin ?? 0) * 100).toFixed(1)}%`}
        />
      </div>
    </div>
  );
}
