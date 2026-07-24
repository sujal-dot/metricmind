'use client';

import type { EChartsOption } from 'echarts';

import AnalyticsChart from '@/components/AnalyticsChart';

const monthlyRevenueOptions: EChartsOption = {
  tooltip: {
    trigger: 'axis',
  },
  xAxis: {
    type: 'category',
    data: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
  },
  yAxis: {
    type: 'value',
    axisLabel: {
      formatter: '${value}',
    },
  },
  series: [
    {
      name: 'Revenue',
      type: 'line',
      smooth: true,
      data: [12000, 15000, 18000, 22000, 19000, 24000, 28000, 26000, 32000, 35000, 40000, 42000],
      itemStyle: {
        color: '#3b82f6',
      },
      areaStyle: {
        color: 'rgba(59, 130, 246, 0.1)',
      },
    },
  ],
};

const profitTrendOptions: EChartsOption = {
  tooltip: {
    trigger: 'axis',
  },
  xAxis: {
    type: 'category',
    data: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
  },
  yAxis: {
    type: 'value',
    axisLabel: {
      formatter: '${value}',
    },
  },
  series: [
    {
      name: 'Profit',
      type: 'bar',
      data: [3000, 3750, 4500, 5500, 4750, 6000, 7000, 6500, 8000, 8750, 10000, 10500],
      itemStyle: {
        color: '#10b981',
      },
    },
  ],
};

const salesByRegionOptions: EChartsOption = {
  tooltip: {
    trigger: 'item',
  },
  series: [
    {
      name: 'Sales',
      type: 'pie',
      radius: '50%',
      data: [
        { value: 40000, name: 'North America' },
        { value: 30000, name: 'Europe' },
        { value: 20000, name: 'Asia' },
        { value: 10000, name: 'Other' },
      ],
      emphasis: {
        itemStyle: {
          shadowBlur: 10,
          shadowOffsetX: 0,
          shadowColor: 'rgba(0, 0, 0, 0.5)',
        },
      },
    },
  ],
};

const salesByCategoryOptions: EChartsOption = {
  tooltip: {
    trigger: 'axis',
    axisPointer: {
      type: 'shadow',
    },
  },
  xAxis: {
    type: 'category',
    data: ['Technology', 'Office Supplies', 'Furniture'],
  },
  yAxis: {
    type: 'value',
  },
  series: [
    {
      type: 'bar',
      data: [45000, 35000, 25000],
      itemStyle: {
        color: '#8b5cf6',
      },
    },
  ],
};

const topCustomersOptions: EChartsOption = {
  tooltip: {
    trigger: 'axis',
    axisPointer: {
      type: 'shadow',
    },
  },
  xAxis: {
    type: 'value',
    axisLabel: {
      formatter: '${value}',
    },
  },
  yAxis: {
    type: 'category',
    data: ['Customer E', 'Customer D', 'Customer C', 'Customer B', 'Customer A'],
  },
  series: [
    {
      type: 'bar',
      data: [12000, 15000, 18000, 22000, 25000],
      itemStyle: {
        color: '#f59e0b',
      },
    },
  ],
};

export default function AnalyticsPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Analytics</h1>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <AnalyticsChart title="Monthly Revenue" options={monthlyRevenueOptions} />
        <AnalyticsChart title="Profit Trend" options={profitTrendOptions} />
        <AnalyticsChart title="Sales by Region" options={salesByRegionOptions} />
        <AnalyticsChart title="Sales by Category" options={salesByCategoryOptions} />
        <AnalyticsChart title="Top Customers" options={topCustomersOptions} />
      </div>
    </div>
  );
}
