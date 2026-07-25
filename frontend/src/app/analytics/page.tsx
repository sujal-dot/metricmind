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
import type { AnalyticsFilters } from '@/types/analytics';

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

const DEMO_DATA = {
  monthlyRevenue: [12000, 15000, 18000, 22000, 19000, 24000, 28000, 26000, 32000, 35000, 40000, 42000],
  monthlyProfit: [3000, 3750, 4500, 5500, 4750, 6000, 7000, 6500, 8000, 8750, 10000, 10500],
  monthlyOrders: [120, 150, 180, 220, 190, 240, 280, 260, 320, 350, 400, 420],
  regions: [
    { name: 'North America', value: 168000 },
    { name: 'Europe', value: 126000 },
    { name: 'Asia Pacific', value: 95000 },
    { name: 'Latin America', value: 52000 },
    { name: 'Middle East', value: 38000 },
    { name: 'Africa', value: 21000 },
  ],
  categories: [
    { name: 'Technology', value: 189000 },
    { name: 'Office Supplies', value: 147000 },
    { name: 'Furniture', value: 105000 },
    { name: 'Consumer Electronics', value: 52000 },
    { name: 'Apparel', value: 42000 },
    { name: 'Home & Kitchen', value: 31000 },
  ],
  topProducts: [
    { name: 'Product A', value: 52000 },
    { name: 'Product B', value: 48000 },
    { name: 'Product C', value: 41000 },
    { name: 'Product D', value: 36000 },
    { name: 'Product E', value: 29000 },
    { name: 'Product F', value: 22000 },
  ],
  topCustomers: [
    { name: 'Customer A', value: 62000 },
    { name: 'Customer B', value: 55000 },
    { name: 'Customer C', value: 48000 },
    { name: 'Customer D', value: 39000 },
    { name: 'Customer E', value: 31000 },
  ],
};

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
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="lg:col-span-2">
            <DateFilter
              dateFrom={dateFrom}
              dateTo={dateTo}
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
        >
          <LineChart
            labels={MONTHS}
            series={[
              {
                name: 'Revenue',
                data: DEMO_DATA.monthlyRevenue,
                color: '#3b82f6',
                smooth: true,
              },
              {
                name: 'Profit',
                data: DEMO_DATA.monthlyProfit,
                color: '#10b981',
                smooth: true,
              },
            ]}
            yAxisFormatter={(v) => formatCurrency(v)}
          />
        </ChartContainer>

        <ChartContainer
          title="Sales Trend (Orders)"
          subtitle="Monthly order volume"
        >
          <LineChart
            labels={MONTHS}
            series={[
              {
                name: 'Orders',
                data: DEMO_DATA.monthlyOrders,
                color: '#8b5cf6',
                smooth: true,
              },
            ]}
          />
        </ChartContainer>

        <ChartContainer
          title="Sales by Category"
          subtitle="Revenue broken down by product category"
        >
          <BarChart
            labels={DEMO_DATA.categories.map((c) => c.name)}
            data={DEMO_DATA.categories.map((c) => c.value)}
            name="Revenue"
            color="#8b5cf6"
            orientation="vertical"
            yAxisFormatter={(v) => formatCurrency(v)}
          />
        </ChartContainer>

        <ChartContainer
          title="Sales by Region"
          subtitle="Revenue broken down by geographic region"
        >
          <BarChart
            labels={DEMO_DATA.regions.map((r) => r.name)}
            data={DEMO_DATA.regions.map((r) => r.value)}
            name="Revenue"
            color="#10b981"
            orientation="horizontal"
            xAxisFormatter={(v) => formatCurrency(v)}
          />
        </ChartContainer>

        <ChartContainer
          title="Revenue by Category Distribution"
          subtitle="Percentage share of revenue across categories"
        >
          <PieChart data={DEMO_DATA.categories} showPercentage={true} />
        </ChartContainer>

        <ChartContainer
          title="Revenue by Region Distribution"
          subtitle="Percentage share of revenue across regions"
        >
          <PieChart data={DEMO_DATA.regions} showPercentage={true} />
        </ChartContainer>

        <ChartContainer
          title="Top Products by Sales"
          subtitle="Highest revenue-generating products"
          className="xl:col-span-2"
        >
          <BarChart
            labels={DEMO_DATA.topProducts.map((p) => p.name)}
            data={DEMO_DATA.topProducts.map((p) => p.value)}
            name="Revenue"
            color="#f59e0b"
            orientation="horizontal"
            xAxisFormatter={(v) => formatCurrency(v)}
            height="360px"
          />
        </ChartContainer>

        <ChartContainer
          title="Top Customers by Revenue"
          subtitle="Highest value customers"
          className="xl:col-span-2"
        >
          <BarChart
            labels={DEMO_DATA.topCustomers.map((c) => c.name)}
            data={DEMO_DATA.topCustomers.map((c) => c.value)}
            name="Revenue"
            color="#06b6d4"
            orientation="horizontal"
            xAxisFormatter={(v) => formatCurrency(v)}
            height="340px"
          />
        </ChartContainer>
      </div>
    </div>
  );
}
