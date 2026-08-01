'use client';

import { useState, useMemo } from 'react';

import KPIGrid from '@/components/charts/KPIGrid';
import ChartContainer from '@/components/charts/ChartContainer';
import LineChart from '@/components/charts/LineChart';
import BarChart from '@/components/charts/BarChart';
import PieChart from '@/components/charts/PieChart';
import DateFilter from '@/components/filters/DateFilter';
import RegionFilter from '@/components/filters/RegionFilter';
import CategoryFilter from '@/components/filters/CategoryFilter';
import { formatCurrency } from '@/lib/chartUtils';
import { useAnalyticsCharts } from '@/lib/hooks';
import type { AnalyticsFilters } from '@/types/analytics';

const DATASET_MAX_DATE = '2017-12-30';

function EmptyChart() {
  return (
    <div className="flex h-80 items-center justify-center rounded-lg bg-gray-50 text-sm text-gray-500">
      No data for the selected filters
    </div>
  );
}

export default function AnalyticsPage() {
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [region, setRegion] = useState('');
  const [category, setCategory] = useState('');

  const filters = useMemo<AnalyticsFilters>(() => {
    const f: AnalyticsFilters = {};
    if (dateFrom) f.date_from = dateFrom;
    if (dateTo) f.date_to = dateTo;
    if (region) f.region = region;
    if (category) f.category = category;
    return f;
  }, [dateFrom, dateTo, region, category]);

  const hasActiveFilters = dateFrom || dateTo || region || category;
  const {
    data: chartData,
    isLoading: chartsLoading,
    error: chartsError,
  } = useAnalyticsCharts(filters);

  const monthlyLabels = chartData?.monthly.map((point) => point.label) ?? [];
  const monthlyRevenue = chartData?.monthly.map((point) => point.revenue) ?? [];
  const monthlyProfit = chartData?.monthly.map((point) => point.profit) ?? [];
  const monthlyOrders = chartData?.monthly.map((point) => point.orders) ?? [];
  const chartError = chartsError?.message || null;

  const clearAllFilters = () => {
    setDateFrom('');
    setDateTo('');
    setRegion('');
    setCategory('');
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Analytics Dashboard</h1>
          <p className="text-sm text-gray-500 mt-1">
            Interactive charts and KPIs powered by MetricMind BI
          </p>
        </div>
        {hasActiveFilters && (
          <button
            type="button"
            onClick={clearAllFilters}
            className="self-start sm:self-auto px-4 py-2 text-sm font-medium text-red-600 bg-red-50 rounded-lg hover:bg-red-100 transition-colors border border-red-100"
          >
            Clear all filters
          </button>
        )}
      </div>

      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h2 className="text-sm font-semibold text-gray-700 mb-4">Filters</h2>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
          <div className="md:col-span-2">
            <DateFilter
              dateFrom={dateFrom}
              dateTo={dateTo}
              maxDate={DATASET_MAX_DATE}
              onDateFromChange={setDateFrom}
              onDateToChange={setDateTo}
            />
          </div>
          <RegionFilter value={region} onChange={setRegion} />
          <CategoryFilter value={category} onChange={setCategory} />
        </div>
      </div>

      <KPIGrid filters={filters} />

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <ChartContainer
          title="Monthly Revenue & Profit"
          subtitle="Revenue and profit trends over time"
          isLoading={chartsLoading}
          error={chartError}
        >
          {monthlyLabels.length ? (
            <LineChart
              labels={monthlyLabels}
              series={[
                {
                  name: 'Revenue',
                  data: monthlyRevenue,
                  color: '#3b82f6',
                  smooth: true,
                },
                {
                  name: 'Profit',
                  data: monthlyProfit,
                  color: '#10b981',
                  smooth: true,
                },
              ]}
              yAxisFormatter={(v) => formatCurrency(v)}
            />
          ) : (
            <EmptyChart />
          )}
        </ChartContainer>

        <ChartContainer
          title="Sales Trend (Orders)"
          subtitle="Monthly order volume"
          isLoading={chartsLoading}
          error={chartError}
        >
          {monthlyLabels.length ? (
            <LineChart
              labels={monthlyLabels}
              series={[
                {
                  name: 'Orders',
                  data: monthlyOrders,
                  color: '#8b5cf6',
                  smooth: true,
                },
              ]}
            />
          ) : (
            <EmptyChart />
          )}
        </ChartContainer>

        <ChartContainer
          title="Sales by Category"
          subtitle="Revenue broken down by product category"
          isLoading={chartsLoading}
          error={chartError}
        >
          {chartData?.by_category.length ? (
            <BarChart
              labels={chartData.by_category.map((c) => c.name)}
              data={chartData.by_category.map((c) => c.value)}
              name="Revenue"
              color="#8b5cf6"
              orientation="vertical"
              yAxisFormatter={(v) => formatCurrency(v)}
            />
          ) : (
            <EmptyChart />
          )}
        </ChartContainer>

        <ChartContainer
          title="Sales by Region"
          subtitle="Revenue broken down by geographic region"
          isLoading={chartsLoading}
          error={chartError}
        >
          {chartData?.by_region.length ? (
            <BarChart
              labels={chartData.by_region.map((r) => r.name)}
              data={chartData.by_region.map((r) => r.value)}
              name="Revenue"
              color="#10b981"
              orientation="horizontal"
              xAxisFormatter={(v) => formatCurrency(v)}
            />
          ) : (
            <EmptyChart />
          )}
        </ChartContainer>

        <ChartContainer
          title="Revenue by Category Distribution"
          subtitle="Percentage share of revenue across categories"
          isLoading={chartsLoading}
          error={chartError}
        >
          {chartData?.by_category.length ? (
            <PieChart data={chartData.by_category} showPercentage={true} />
          ) : (
            <EmptyChart />
          )}
        </ChartContainer>

        <ChartContainer
          title="Revenue by Region Distribution"
          subtitle="Percentage share of revenue across regions"
          isLoading={chartsLoading}
          error={chartError}
        >
          {chartData?.by_region.length ? (
            <PieChart data={chartData.by_region} showPercentage={true} />
          ) : (
            <EmptyChart />
          )}
        </ChartContainer>

        <ChartContainer
          title="Top Products by Sales"
          subtitle="Highest revenue-generating products"
          className="xl:col-span-2"
          isLoading={chartsLoading}
          error={chartError}
        >
          {chartData?.top_products.length ? (
            <BarChart
              labels={chartData.top_products.map((p) => p.name)}
              data={chartData.top_products.map((p) => p.value)}
              name="Revenue"
              color="#f59e0b"
              orientation="horizontal"
              xAxisFormatter={(v) => formatCurrency(v)}
              height="360px"
            />
          ) : (
            <EmptyChart />
          )}
        </ChartContainer>

        <ChartContainer
          title="Top Customers by Revenue"
          subtitle="Highest value customers"
          className="xl:col-span-2"
          isLoading={chartsLoading}
          error={chartError}
        >
          {chartData?.top_customers.length ? (
            <BarChart
              labels={chartData.top_customers.map((c) => c.name)}
              data={chartData.top_customers.map((c) => c.value)}
              name="Revenue"
              color="#06b6d4"
              orientation="horizontal"
              xAxisFormatter={(v) => formatCurrency(v)}
              height="340px"
            />
          ) : (
            <EmptyChart />
          )}
        </ChartContainer>
      </div>
    </div>
  );
}
