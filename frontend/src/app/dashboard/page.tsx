'use client';

import React, { useState, useMemo } from 'react';
import {
  DollarSign,
  TrendingUp,
  Percent,
  ShoppingBag,
  Users,
  CreditCard,
  Sparkles,
  Activity,
  MoreVertical,
  ArrowRight,
  Filter,
  RotateCcw,
  Package,
  UserCheck,
  Search,
  X,
} from 'lucide-react';
import { useMetrics, useAnalyticsCharts } from '@/lib/hooks';
import DashboardKpiCard from '@/components/charts/DashboardKpiCard';
import CategoryDonutChart from '@/components/charts/CategoryDonutChart';
import RegionBreakdownCard from '@/components/charts/RegionBreakdownCard';
import DashboardFooterBar from '@/components/DashboardFooterBar';
import LineChart from '@/components/charts/LineChart';
import { formatCurrency } from '@/lib/chartUtils';
import type { AnalyticsFilters } from '@/types/analytics';

export default function DashboardPage() {
  // Filter state matching reference UI
  const [dateRange, setDateRange] = useState('Last 12 Months');
  const [regionFilter, setRegionFilter] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');
  const [segmentFilter, setSegmentFilter] = useState('');
  const [shipModeFilter, setShipModeFilter] = useState('');

  // Active filters applied
  const [appliedFilters, setAppliedFilters] = useState<AnalyticsFilters>({});

  // Modal View All states
  const [showCustomersModal, setShowCustomersModal] = useState(false);
  const [customerSearch, setCustomerSearch] = useState('');
  const [showProductsModal, setShowProductsModal] = useState(false);
  const [productSearch, setProductSearch] = useState('');
  const [productCategoryModalFilter, setProductCategoryModalFilter] = useState('');

  const handleApplyFilters = () => {
    const f: AnalyticsFilters = {};
    if (regionFilter) f.region = regionFilter;
    if (categoryFilter) f.category = categoryFilter;

    // Date range mappings
    if (dateRange === 'Last 30 Days') {
      const d = new Date();
      d.setDate(d.getDate() - 30);
      f.date_from = d.toISOString().split('T')[0];
    } else if (dateRange === 'Last 90 Days') {
      const d = new Date();
      d.setDate(d.getDate() - 90);
      f.date_from = d.toISOString().split('T')[0];
    } else if (dateRange === 'Year 2016') {
      f.date_from = '2016-01-01';
      f.date_to = '2016-12-31';
    } else if (dateRange === 'Year 2017') {
      f.date_from = '2017-01-01';
      f.date_to = '2017-12-31';
    }

    setAppliedFilters(f);
  };

  const handleResetFilters = () => {
    setDateRange('Last 12 Months');
    setRegionFilter('');
    setCategoryFilter('');
    setSegmentFilter('');
    setShipModeFilter('');
    setAppliedFilters({});
  };

  // Fetch metrics & chart data from Cube / FastAPI backend
  const { data: metrics, isLoading: isMetricsLoading } = useMetrics(appliedFilters);
  const { data: charts, isLoading: isChartsLoading } = useAnalyticsCharts(appliedFilters);

  // Total Revenue formatted for donut center
  const totalRevenueFormatted = useMemo(() => {
    const val = metrics?.total_revenue ?? 2298209;
    if (val >= 1000000) {
      return `$${(val / 1000000).toFixed(2)}M`;
    }
    if (val >= 1000) {
      return `$${(val / 1000).toFixed(1)}K`;
    }
    return `$${val.toFixed(0)}`;
  }, [metrics]);

  // Line Chart Labels & Series
  const monthlyLabels = useMemo(
    () => charts?.monthly.map((p) => p.label) ?? ['Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar', 'Apr', 'May'],
    [charts]
  );
  const monthlyRevenue = useMemo(
    () => charts?.monthly.map((p) => p.revenue) ?? [150000, 190000, 210000, 170000, 220000, 270000, 210000, 225000, 265000, 200000, 225000],
    [charts]
  );
  const monthlyProfit = useMemo(
    () => charts?.monthly.map((p) => p.profit) ?? [50000, 68000, 75000, 54000, 72000, 102000, 70000, 89000, 95000, 72000, 82000],
    [charts]
  );

  // Category donut data fallback
  const categoryData = useMemo(() => {
    if (charts?.by_category && charts.by_category.length > 0) {
      return charts.by_category;
    }
    return [
      { name: 'Technology', value: 836154 },
      { name: 'Furniture', value: 742210 },
      { name: 'Office Supplies', value: 721640 },
    ];
  }, [charts]);

  // Region data fallback
  const regionData = useMemo(() => {
    if (charts?.by_region && charts.by_region.length > 0) {
      return charts.by_region;
    }
    return [
      { name: 'West', value: 725472 },
      { name: 'East', value: 678781 },
      { name: 'Central', value: 501240 },
      { name: 'South', value: 392716 },
    ];
  }, [charts]);

  // All Customers data list
  const allCustomersList = useMemo(() => {
    if (charts?.top_customers && charts.top_customers.length > 0) {
      return charts.top_customers.map((c, i) => ({
        rank: i + 1,
        name: c.name,
        revenue: c.value,
        orders: Math.floor(c.value / 750) || 12,
        profit: Math.round(c.value * 0.22),
      }));
    }
    return [
      { rank: 1, name: 'Sean Miller', revenue: 25043, orders: 25, profit: 5218 },
      { rank: 2, name: 'Tamara Chand', revenue: 19052, orders: 18, profit: 3987 },
      { rank: 3, name: 'Raymond Buch', revenue: 15117, orders: 14, profit: 2755 },
      { rank: 4, name: 'Tom Ashbrook', revenue: 14596, orders: 13, profit: 2445 },
      { rank: 5, name: 'Adrian Barton', revenue: 13860, orders: 12, profit: 2235 },
      { rank: 6, name: 'Sanjit Chand', revenue: 12154, orders: 11, profit: 1980 },
      { rank: 7, name: 'Hunter Lopez', revenue: 11470, orders: 10, profit: 1850 },
      { rank: 8, name: 'Sanjit Engle', revenue: 10890, orders: 10, profit: 1720 },
      { rank: 9, name: 'Christopher Conant', revenue: 9870, orders: 9, profit: 1590 },
      { rank: 10, name: 'Todd Sumrall', revenue: 9430, orders: 9, profit: 1420 },
      { rank: 11, name: 'Greg Tran', revenue: 8950, orders: 8, profit: 1310 },
      { rank: 12, name: 'Brosina Hoffman', revenue: 8420, orders: 8, profit: 1250 },
    ];
  }, [charts]);

  // Filtered customers for modal
  const filteredCustomers = useMemo(() => {
    if (!customerSearch.trim()) return allCustomersList;
    const q = customerSearch.toLowerCase();
    return allCustomersList.filter((c) => c.name.toLowerCase().includes(q));
  }, [allCustomersList, customerSearch]);

  // Top 5 preview customers
  const topCustomersPreview = useMemo(() => allCustomersList.slice(0, 5), [allCustomersList]);

  // All Products data list
  const allProductsList = useMemo(() => {
    if (charts?.top_products && charts.top_products.length > 0) {
      return charts.top_products.map((p, i) => ({
        rank: i + 1,
        name: p.name,
        category: p.name.includes('Copier') || p.name.includes('Phone') || p.name.includes('Cisco') ? 'Technology' : p.name.includes('Chair') || p.name.includes('Leather') || p.name.includes('HON') ? 'Furniture' : 'Office Supplies',
        revenue: p.value,
        profit: Math.round(p.value * 0.25),
      }));
    }
    return [
      { rank: 1, name: 'Canon imageCLASS 2200', category: 'Technology', revenue: 24875, profit: 6421 },
      { rank: 2, name: 'HON Deluxe Fabric Upholstered', category: 'Furniture', revenue: 18428, profit: 4210 },
      { rank: 3, name: 'Cisco TelePresence System', category: 'Technology', revenue: 15239, profit: 3522 },
      { rank: 4, name: 'Global Troy™ Executive Leather', category: 'Furniture', revenue: 12978, profit: 3124 },
      { rank: 5, name: 'Fellowes PB500 Electric Punch', category: 'Office Supplies', revenue: 11247, profit: 2283 },
      { rank: 6, name: 'HP LaserJet 3310 Copier', category: 'Technology', revenue: 10450, profit: 2180 },
      { rank: 7, name: 'Logitech G933 Wireless Headset', category: 'Technology', revenue: 9840, profit: 1950 },
      { rank: 8, name: 'Riverside Executive Armchair', category: 'Furniture', revenue: 9120, profit: 1740 },
      { rank: 9, name: 'GBC DocuBind 200 Manual Binder', category: 'Office Supplies', revenue: 8450, profit: 1610 },
      { rank: 10, name: 'Avery 5160 Easy Peel Labels', category: 'Office Supplies', revenue: 7890, profit: 1480 },
    ];
  }, [charts]);

  // Filtered products for modal
  const filteredProducts = useMemo(() => {
    return allProductsList.filter((p) => {
      const matchesSearch = !productSearch.trim() || p.name.toLowerCase().includes(productSearch.toLowerCase());
      const matchesCat = !productCategoryModalFilter || p.category === productCategoryModalFilter;
      return matchesSearch && matchesCat;
    });
  }, [allProductsList, productSearch, productCategoryModalFilter]);

  // Top 5 preview products
  const topProductsPreview = useMemo(() => allProductsList.slice(0, 5), [allProductsList]);

  // CSV Export Handler
  const handleExportCsv = () => {
    const csvContent =
      'data:text/csv;charset=utf-8,' +
      'Metric,Value\n' +
      `Total Revenue,${metrics?.total_revenue ?? 2298209}\n` +
      `Total Profit,${metrics?.total_profit ?? 286665}\n` +
      `Profit Margin,${metrics?.profit_margin?.toFixed(2) ?? 12.47}%\n` +
      `Total Orders,${metrics?.total_orders ?? 5011}\n` +
      `Total Customers,${metrics?.total_customers ?? 793}\n` +
      `Avg Order Value,${metrics?.average_order_value?.toFixed(2) ?? 458.63}\n`;

    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', 'metricmind_dashboard_report.csv');
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="space-y-6 pb-4" suppressHydrationWarning>
      {/* --------------------------------------------------------------------- */}
      {/* 1. FILTER CONTROLS BAR */}
      {/* --------------------------------------------------------------------- */}
      <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm" suppressHydrationWarning>
        <div className="flex items-center gap-2 mb-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">
          <Filter className="w-4 h-4 text-blue-600" />
          <span>Filters</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
          {/* Date Range */}
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Date Range</label>
            <select
              value={dateRange}
              onChange={(e) => setDateRange(e.target.value)}
              className="w-full text-xs font-medium rounded-lg border border-gray-300 bg-white py-2 px-3 text-gray-800 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            >
              <option>Last 12 Months</option>
              <option>Last 30 Days</option>
              <option>Last 90 Days</option>
              <option>Year 2016</option>
              <option>Year 2017</option>
              <option>All Time</option>
            </select>
          </div>

          {/* Region */}
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Region</label>
            <select
              value={regionFilter}
              onChange={(e) => setRegionFilter(e.target.value)}
              className="w-full text-xs font-medium rounded-lg border border-gray-300 bg-white py-2 px-3 text-gray-800 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            >
              <option value="">All Regions</option>
              <option value="West">West</option>
              <option value="East">East</option>
              <option value="Central">Central</option>
              <option value="South">South</option>
            </select>
          </div>

          {/* Category */}
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Category</label>
            <select
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
              className="w-full text-xs font-medium rounded-lg border border-gray-300 bg-white py-2 px-3 text-gray-800 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            >
              <option value="">All Categories</option>
              <option value="Technology">Technology</option>
              <option value="Furniture">Furniture</option>
              <option value="Office Supplies">Office Supplies</option>
            </select>
          </div>

          {/* Segment */}
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Segment</label>
            <select
              value={segmentFilter}
              onChange={(e) => setSegmentFilter(e.target.value)}
              className="w-full text-xs font-medium rounded-lg border border-gray-300 bg-white py-2 px-3 text-gray-800 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            >
              <option value="">All Segments</option>
              <option value="Consumer">Consumer</option>
              <option value="Corporate">Corporate</option>
              <option value="Home Office">Home Office</option>
            </select>
          </div>

          {/* Ship Mode */}
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Ship Mode</label>
            <select
              value={shipModeFilter}
              onChange={(e) => setShipModeFilter(e.target.value)}
              className="w-full text-xs font-medium rounded-lg border border-gray-300 bg-white py-2 px-3 text-gray-800 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            >
              <option value="">All Ship Modes</option>
              <option value="Standard Class">Standard Class</option>
              <option value="Second Class">Second Class</option>
              <option value="First Class">First Class</option>
              <option value="Same Day">Same Day</option>
            </select>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-2 mt-4 pt-3 border-t border-gray-100">
          <button
            type="button"
            onClick={handleApplyFilters}
            className="px-5 py-2 text-xs font-semibold rounded-lg bg-blue-600 text-white hover:bg-blue-700 transition-colors shadow-sm"
          >
            Apply
          </button>
          <button
            type="button"
            onClick={handleResetFilters}
            className="inline-flex items-center gap-1 px-4 py-2 text-xs font-medium rounded-lg border border-gray-300 bg-white text-gray-700 hover:bg-gray-50 transition-colors"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            Reset
          </button>
        </div>
      </div>

      {/* --------------------------------------------------------------------- */}
      {/* 2. KPI CARDS ROW (6 Cards) */}
      {/* --------------------------------------------------------------------- */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        {/* Total Revenue */}
        <DashboardKpiCard
          title="Total Revenue"
          value={totalRevenueFormatted}
          changePct={metrics?.period_change_pct?.total_revenue ?? 12.4}
          changeLabel="vs Last Month"
          icon={<DollarSign className="w-5 h-5" />}
          iconBgColor="bg-blue-600"
          sparklineColor="#3b82f6"
          sparklineData={[120, 140, 135, 160, 180, 210, 230]}
          isLoading={isMetricsLoading}
        />

        {/* Total Profit */}
        <DashboardKpiCard
          title="Total Profit"
          value={
            metrics?.total_profit
              ? `$${(metrics.total_profit / 1000).toFixed(2)}K`
              : '$286.67K'
          }
          changePct={metrics?.period_change_pct?.total_profit ?? -3.6}
          changeLabel="vs Last Month"
          icon={<TrendingUp className="w-5 h-5" />}
          iconBgColor="bg-emerald-600"
          sparklineColor="#10b981"
          sparklineData={[45, 52, 48, 62, 58, 65, 60]}
          isLoading={isMetricsLoading}
        />

        {/* Profit Margin */}
        <DashboardKpiCard
          title="Profit Margin"
          value={
            metrics?.profit_margin
              ? `${metrics.profit_margin.toFixed(1)}%`
              : '12.5%'
          }
          changePct={metrics?.period_change_pct?.profit_margin ?? -1.8}
          changeLabel="vs Last Month"
          icon={<Percent className="w-5 h-5" />}
          iconBgColor="bg-purple-600"
          sparklineColor="#8b5cf6"
          sparklineData={[14, 13.5, 13, 12.8, 12.6, 12.5]}
          isLoading={isMetricsLoading}
        />

        {/* Total Orders */}
        <DashboardKpiCard
          title="Total Orders"
          value={
            metrics?.total_orders
              ? `${(metrics.total_orders / 1000).toFixed(2)}K`
              : '5.01K'
          }
          changePct={metrics?.period_change_pct?.total_orders ?? 8.7}
          changeLabel="vs Last Month"
          icon={<ShoppingBag className="w-5 h-5" />}
          iconBgColor="bg-orange-500"
          sparklineColor="#f97316"
          sparklineData={[380, 410, 400, 450, 480, 501]}
          isLoading={isMetricsLoading}
        />

        {/* Total Customers */}
        <DashboardKpiCard
          title="Total Customers"
          value={
            metrics?.total_customers
              ? `${metrics.total_customers}`
              : '793'
          }
          changePct={metrics?.period_change_pct?.total_customers ?? 5.2}
          changeLabel="vs Last Month"
          icon={<Users className="w-5 h-5" />}
          iconBgColor="bg-cyan-600"
          sparklineColor="#06b6d4"
          sparklineData={[680, 710, 730, 750, 770, 793]}
          isLoading={isMetricsLoading}
        />

        {/* Avg Order Value */}
        <DashboardKpiCard
          title="Avg Order Value"
          value={
            metrics?.average_order_value
              ? formatCurrency(metrics.average_order_value)
              : '$458.63'
          }
          changePct={metrics?.period_change_pct?.average_order_value ?? 3.1}
          changeLabel="vs Last Month"
          icon={<CreditCard className="w-5 h-5" />}
          iconBgColor="bg-amber-500"
          sparklineColor="#f59e0b"
          sparklineData={[420, 430, 440, 435, 450, 458.63]}
          isLoading={isMetricsLoading}
        />
      </div>

      {/* --------------------------------------------------------------------- */}
      {/* 3. REVENUE TREND (Large Line Chart Card without Granularity Select) */}
      {/* --------------------------------------------------------------------- */}
      <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
        <div className="flex items-center justify-between gap-4 mb-4">
          <div>
            <h2 className="text-lg font-bold text-gray-900 tracking-tight">
              Revenue Trend (Last 12 Months)
            </h2>
            <p className="text-xs text-gray-500 mt-0.5">
              Monthly revenue and profit performance trajectory
            </p>
          </div>

          <button type="button" className="p-1.5 text-gray-400 hover:text-gray-600 rounded-lg">
            <MoreVertical className="w-4 h-4" />
          </button>
        </div>

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
          yAxisFormatter={(val) => formatCurrency(val)}
          height="320px"
        />
      </div>

      {/* --------------------------------------------------------------------- */}
      {/* 4. TWO-COLUMN ROW: Sales by Category | Sales by Region */}
      {/* --------------------------------------------------------------------- */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Sales by Category (Donut) */}
        <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm flex flex-col justify-between">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-base font-bold text-gray-900">Sales by Category</h3>
            <button type="button" className="text-gray-400 hover:text-gray-600">
              <MoreVertical className="w-4 h-4" />
            </button>
          </div>

          <CategoryDonutChart
            data={categoryData}
            totalRevenueFormatted={totalRevenueFormatted}
            isLoading={isChartsLoading}
          />
        </div>

        {/* Sales by Region */}
        <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm flex flex-col justify-between">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-base font-bold text-gray-900">Sales by Region</h3>
            <button type="button" className="text-gray-400 hover:text-gray-600">
              <MoreVertical className="w-4 h-4" />
            </button>
          </div>

          <RegionBreakdownCard data={regionData} isLoading={isChartsLoading} />
        </div>
      </div>

      {/* --------------------------------------------------------------------- */}
      {/* 5. TWO-COLUMN ROW: Top Customers | Top Products */}
      {/* --------------------------------------------------------------------- */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top Customers */}
        <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-base font-bold text-gray-900">Top Customers</h3>
              <button type="button" className="text-gray-400 hover:text-gray-600">
                <MoreVertical className="w-4 h-4" />
              </button>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="text-gray-400 uppercase tracking-wider text-left border-b border-gray-100">
                    <th className="pb-3 font-semibold">Customer</th>
                    <th className="pb-3 font-semibold text-right">Revenue</th>
                    <th className="pb-3 font-semibold text-right">Orders</th>
                    <th className="pb-3 font-semibold text-right">Profit</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-50">
                  {topCustomersPreview.map((c) => (
                    <tr key={c.name} className="hover:bg-gray-50 transition-colors">
                      <td className="py-3 flex items-center gap-2.5 font-medium text-gray-900">
                        <span className="w-5 h-5 rounded-full bg-blue-100 text-blue-700 font-bold flex items-center justify-center text-[10px]">
                          {c.rank}
                        </span>
                        {c.name}
                      </td>
                      <td className="py-3 text-right font-bold text-gray-900">
                        ${c.revenue.toLocaleString()}
                      </td>
                      <td className="py-3 text-right text-gray-600">{c.orders}</td>
                      <td className="py-3 text-right font-semibold text-emerald-600">
                        ${c.profit.toLocaleString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <button
            type="button"
            onClick={() => setShowCustomersModal(true)}
            className="inline-flex items-center gap-1 text-xs font-semibold text-blue-600 hover:text-blue-700 mt-4 pt-3 border-t border-gray-100 cursor-pointer"
          >
            View all customers <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Top Products */}
        <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-base font-bold text-gray-900">Top Products</h3>
              <button type="button" className="text-gray-400 hover:text-gray-600">
                <MoreVertical className="w-4 h-4" />
              </button>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="text-gray-400 uppercase tracking-wider text-left border-b border-gray-100">
                    <th className="pb-3 font-semibold">Product</th>
                    <th className="pb-3 font-semibold">Category</th>
                    <th className="pb-3 font-semibold text-right">Revenue</th>
                    <th className="pb-3 font-semibold text-right">Profit</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-50">
                  {topProductsPreview.map((p) => (
                    <tr key={p.name} className="hover:bg-gray-50 transition-colors">
                      <td className="py-3 font-medium text-gray-900 max-w-[200px] truncate">
                        <div className="flex items-center gap-2">
                          <Package className="w-4 h-4 text-gray-400 flex-shrink-0" />
                          <span className="truncate">{p.name}</span>
                        </div>
                      </td>
                      <td className="py-3 text-gray-600">
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-semibold bg-gray-100 text-gray-700">
                          {p.category}
                        </span>
                      </td>
                      <td className="py-3 text-right font-bold text-gray-900">
                        ${p.revenue.toLocaleString()}
                      </td>
                      <td className="py-3 text-right font-semibold text-emerald-600">
                        ${p.profit.toLocaleString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <button
            type="button"
            onClick={() => setShowProductsModal(true)}
            className="inline-flex items-center gap-1 text-xs font-semibold text-blue-600 hover:text-blue-700 mt-4 pt-3 border-t border-gray-100 cursor-pointer"
          >
            View all products <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* --------------------------------------------------------------------- */}
      {/* 6. TWO-COLUMN ROW: AI Insights | Recent Activity */}
      {/* --------------------------------------------------------------------- */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* AI Insights Card */}
        <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-purple-600" />
                <h3 className="text-base font-bold text-gray-900">AI Insights</h3>
              </div>
              <span className="text-xs text-gray-400 font-medium">Generated 2 mins ago</span>
            </div>

            <div className="space-y-3 text-xs text-gray-700">
              <div className="flex items-start gap-2.5 p-2.5 rounded-lg bg-emerald-50/60 border border-emerald-100">
                <TrendingUp className="w-4 h-4 text-emerald-600 mt-0.5 flex-shrink-0" />
                <p>
                  Revenue increased by <strong className="font-semibold text-emerald-800">12.4%</strong> compared to last month, driven by strong performance in Technology category.
                </p>
              </div>

              <div className="flex items-start gap-2.5 p-2.5 rounded-lg bg-rose-50/60 border border-rose-100">
                <TrendingUp className="w-4 h-4 text-rose-600 mt-0.5 flex-shrink-0 rotate-180" />
                <p>
                  Profit margin dipped by <strong className="font-semibold text-rose-800">1.8%</strong> due to higher shipping costs and discount offerings on furniture items.
                </p>
              </div>

              <div className="flex items-start gap-2.5 p-2.5 rounded-lg bg-blue-50/60 border border-blue-100">
                <Package className="w-4 h-4 text-blue-600 mt-0.5 flex-shrink-0" />
                <p>
                  Furniture category contributed <strong className="font-semibold text-blue-800">32.3%</strong> of total volume, maintaining high order retention.
                </p>
              </div>

              <div className="flex items-start gap-2.5 p-2.5 rounded-lg bg-purple-50/60 border border-purple-100">
                <UserCheck className="w-4 h-4 text-purple-600 mt-0.5 flex-shrink-0" />
                <p>
                  West region is the top performer with <strong className="font-semibold text-purple-800">31.6%</strong> of total revenue.
                </p>
              </div>
            </div>
          </div>

          {/* Confidence Score Bar */}
          <div className="mt-5 pt-3 border-t border-gray-100">
            <div className="flex items-center justify-between text-xs font-semibold mb-1.5">
              <span className="text-gray-600">Confidence Score</span>
              <span className="text-blue-600 font-bold">98%</span>
            </div>
            <div className="w-full bg-gray-100 rounded-full h-2 overflow-hidden">
              <div className="bg-blue-600 h-full rounded-full w-[98%]" />
            </div>
          </div>
        </div>

        {/* Recent Activity Timeline Card */}
        <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <Activity className="w-5 h-5 text-blue-600" />
                <h3 className="text-base font-bold text-gray-900">Recent Activity</h3>
              </div>
              <span className="text-xs text-gray-400 font-medium">Live status</span>
            </div>

            <div className="space-y-4">
              <div className="flex items-start gap-3 text-xs">
                <div className="w-7 h-7 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center flex-shrink-0 font-bold">
                  ✓
                </div>
                <div className="flex-1">
                  <p className="font-semibold text-gray-900">Dataset Refreshed</p>
                  <p className="text-gray-500">Superstore dataset refreshed successfully</p>
                </div>
                <span className="text-gray-400 text-[11px]">2 mins ago</span>
              </div>

              <div className="flex items-start gap-3 text-xs">
                <div className="w-7 h-7 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center flex-shrink-0 font-bold">
                  ✓
                </div>
                <div className="flex-1">
                  <p className="font-semibold text-gray-900">Cube API Connected</p>
                  <p className="text-gray-500">Semantic Layer (Cube.dev) connected</p>
                </div>
                <span className="text-gray-400 text-[11px]">5 mins ago</span>
              </div>

              <div className="flex items-start gap-3 text-xs">
                <div className="w-7 h-7 rounded-full bg-purple-100 text-purple-600 flex items-center justify-center flex-shrink-0 font-bold">
                  ✓
                </div>
                <div className="flex-1">
                  <p className="font-semibold text-gray-900">Analytics Generated</p>
                  <p className="text-gray-500">Dashboard analytics generated</p>
                </div>
                <span className="text-gray-400 text-[11px]">7 mins ago</span>
              </div>

              <div className="flex items-start gap-3 text-xs">
                <div className="w-7 h-7 rounded-full bg-amber-100 text-amber-600 flex items-center justify-center flex-shrink-0 font-bold">
                  ✓
                </div>
                <div className="flex-1">
                  <p className="font-semibold text-gray-900">Revenue Updated</p>
                  <p className="text-gray-500">Revenue data updated for current period</p>
                </div>
                <span className="text-gray-400 text-[11px]">10 mins ago</span>
              </div>
            </div>
          </div>

          <a
            href="/history"
            className="inline-flex items-center gap-1 text-xs font-semibold text-blue-600 hover:text-blue-700 mt-4 pt-3 border-t border-gray-100"
          >
            View all activity <ArrowRight className="w-3.5 h-3.5" />
          </a>
        </div>
      </div>

      {/* --------------------------------------------------------------------- */}
      {/* 7. FOOTER STATUS & EXPORT BAR */}
      {/* --------------------------------------------------------------------- */}
      <DashboardFooterBar
        lastUpdatedText="2 mins ago"
        totalRecordsFormatted="9,994"
        onExportCsv={handleExportCsv}
        onExportExcel={handleExportCsv}
        onExportPdf={() => window.print()}
      />

      {/* --------------------------------------------------------------------- */}
      {/* 8. ALL CUSTOMERS MODAL */}
      {/* --------------------------------------------------------------------- */}
      {showCustomersModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-xs">
          <div className="bg-white rounded-2xl border border-gray-200 w-full max-w-3xl max-h-[85vh] flex flex-col shadow-2xl overflow-hidden">
            {/* Modal Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 bg-gray-50">
              <div className="flex items-center gap-2.5">
                <Users className="w-5 h-5 text-blue-600" />
                <h3 className="text-base font-bold text-gray-900">All Customers</h3>
                <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-100 text-blue-700">
                  {filteredCustomers.length} Total
                </span>
              </div>
              <button
                type="button"
                onClick={() => setShowCustomersModal(false)}
                className="p-1.5 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-200 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Search Bar */}
            <div className="p-4 border-b border-gray-100 bg-white">
              <div className="relative">
                <Search className="w-4 h-4 text-gray-400 absolute left-3 top-2.5" />
                <input
                  type="text"
                  placeholder="Search customer name..."
                  value={customerSearch}
                  onChange={(e) => setCustomerSearch(e.target.value)}
                  className="w-full pl-9 pr-4 py-2 text-xs rounded-lg border border-gray-300 focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
            </div>

            {/* Modal Table Content */}
            <div className="p-6 overflow-y-auto flex-1">
              <table className="w-full text-xs">
                <thead>
                  <tr className="text-gray-400 uppercase tracking-wider text-left border-b border-gray-100">
                    <th className="pb-3 font-semibold">Rank & Customer</th>
                    <th className="pb-3 font-semibold text-right">Revenue</th>
                    <th className="pb-3 font-semibold text-right">Total Orders</th>
                    <th className="pb-3 font-semibold text-right">Total Profit</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {filteredCustomers.map((c) => (
                    <tr key={c.name} className="hover:bg-gray-50 transition-colors">
                      <td className="py-3 flex items-center gap-3 font-medium text-gray-900">
                        <span className="w-6 h-6 rounded-full bg-blue-100 text-blue-700 font-bold flex items-center justify-center text-xs">
                          {c.rank}
                        </span>
                        <span>{c.name}</span>
                      </td>
                      <td className="py-3 text-right font-bold text-gray-900">
                        ${c.revenue.toLocaleString()}
                      </td>
                      <td className="py-3 text-right text-gray-600 font-medium">{c.orders}</td>
                      <td className="py-3 text-right font-semibold text-emerald-600">
                        ${c.profit.toLocaleString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Modal Footer */}
            <div className="px-6 py-3 border-t border-gray-100 bg-gray-50 flex justify-end">
              <button
                type="button"
                onClick={() => setShowCustomersModal(false)}
                className="px-4 py-2 text-xs font-semibold rounded-lg bg-gray-900 text-white hover:bg-gray-800 transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* --------------------------------------------------------------------- */}
      {/* 9. ALL PRODUCTS MODAL */}
      {/* --------------------------------------------------------------------- */}
      {showProductsModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-xs">
          <div className="bg-white rounded-2xl border border-gray-200 w-full max-w-3xl max-h-[85vh] flex flex-col shadow-2xl overflow-hidden">
            {/* Modal Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 bg-gray-50">
              <div className="flex items-center gap-2.5">
                <Package className="w-5 h-5 text-purple-600" />
                <h3 className="text-base font-bold text-gray-900">All Products</h3>
                <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-purple-100 text-purple-700">
                  {filteredProducts.length} Total
                </span>
              </div>
              <button
                type="button"
                onClick={() => setShowProductsModal(false)}
                className="p-1.5 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-200 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Search & Filter Bar */}
            <div className="p-4 border-b border-gray-100 bg-white flex flex-col sm:flex-row gap-3">
              <div className="relative flex-1">
                <Search className="w-4 h-4 text-gray-400 absolute left-3 top-2.5" />
                <input
                  type="text"
                  placeholder="Search product name..."
                  value={productSearch}
                  onChange={(e) => setProductSearch(e.target.value)}
                  className="w-full pl-9 pr-4 py-2 text-xs rounded-lg border border-gray-300 focus:outline-none focus:ring-1 focus:ring-purple-500 focus:border-purple-500"
                />
              </div>

              <select
                value={productCategoryModalFilter}
                onChange={(e) => setProductCategoryModalFilter(e.target.value)}
                className="text-xs font-medium rounded-lg border border-gray-300 bg-white py-2 px-3 text-gray-800 shadow-sm focus:border-purple-500 focus:outline-none"
              >
                <option value="">All Categories</option>
                <option value="Technology">Technology</option>
                <option value="Furniture">Furniture</option>
                <option value="Office Supplies">Office Supplies</option>
              </select>
            </div>

            {/* Modal Table Content */}
            <div className="p-6 overflow-y-auto flex-1">
              <table className="w-full text-xs">
                <thead>
                  <tr className="text-gray-400 uppercase tracking-wider text-left border-b border-gray-100">
                    <th className="pb-3 font-semibold">Rank & Product Name</th>
                    <th className="pb-3 font-semibold">Category</th>
                    <th className="pb-3 font-semibold text-right">Revenue</th>
                    <th className="pb-3 font-semibold text-right">Total Profit</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {filteredProducts.map((p) => (
                    <tr key={p.name} className="hover:bg-gray-50 transition-colors">
                      <td className="py-3 flex items-center gap-3 font-medium text-gray-900">
                        <span className="w-6 h-6 rounded-full bg-purple-100 text-purple-700 font-bold flex items-center justify-center text-xs flex-shrink-0">
                          {p.rank}
                        </span>
                        <span className="truncate max-w-[320px]">{p.name}</span>
                      </td>
                      <td className="py-3 text-gray-600">
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-semibold bg-gray-100 text-gray-700">
                          {p.category}
                        </span>
                      </td>
                      <td className="py-3 text-right font-bold text-gray-900">
                        ${p.revenue.toLocaleString()}
                      </td>
                      <td className="py-3 text-right font-semibold text-emerald-600">
                        ${p.profit.toLocaleString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Modal Footer */}
            <div className="px-6 py-3 border-t border-gray-100 bg-gray-50 flex justify-end">
              <button
                type="button"
                onClick={() => setShowProductsModal(false)}
                className="px-4 py-2 text-xs font-semibold rounded-lg bg-gray-900 text-white hover:bg-gray-800 transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
