'use client';

import React, { useMemo } from 'react';
import ReactECharts from 'echarts-for-react';
import type { EChartsOption } from 'echarts';

interface CategoryDataPoint {
  name: string;
  value: number;
}

interface CategoryDonutChartProps {
  data: CategoryDataPoint[];
  totalRevenueFormatted: string;
  isLoading?: boolean;
}

const CATEGORY_COLORS: Record<string, string> = {
  Technology: '#3b82f6',
  Furniture: '#10b981',
  'Office Supplies': '#f59e0b',
};

export default function CategoryDonutChart({
  data,
  totalRevenueFormatted,
  isLoading = false,
}: CategoryDonutChartProps) {
  const totalSum = useMemo(() => data.reduce((acc, curr) => acc + curr.value, 0) || 1, [data]);

  const option = useMemo<EChartsOption>(() => {
    return {
      tooltip: {
        trigger: 'item',
        formatter: (params: any) => {
          const valFormatted = new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
            maximumFractionDigits: 0,
          }).format(params.value);
          return `<div class="font-sans text-xs">
            <span class="font-semibold">${params.name}</span><br/>
            ${valFormatted} (${params.percent}%)
          </div>`;
        },
      },
      series: [
        {
          name: 'Sales by Category',
          type: 'pie',
          radius: ['62%', '82%'],
          center: ['35%', '50%'],
          avoidLabelOverlap: false,
          itemStyle: {
            borderRadius: 6,
            borderColor: '#ffffff',
            borderWidth: 3,
          },
          label: {
            show: false,
          },
          emphasis: {
            scale: true,
            scaleSize: 6,
          },
          data: data.map((item) => ({
            name: item.name,
            value: item.value,
            itemStyle: {
              color: CATEGORY_COLORS[item.name] || '#8b5cf6',
            },
          })),
        },
      ],
    };
  }, [data]);

  if (isLoading) {
    return (
      <div className="h-64 flex items-center justify-center bg-gray-50 rounded-xl animate-pulse">
        <div className="w-36 h-36 rounded-full border-8 border-gray-200" />
      </div>
    );
  }

  return (
    <div className="flex flex-col sm:flex-row items-center justify-between gap-4 h-full">
      {/* Donut Chart with Center Text */}
      <div className="relative w-full sm:w-1/2 h-64 flex items-center justify-center">
        <ReactECharts option={option} style={{ height: '100%', width: '100%' }} notMerge={true} />
        <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none text-center">
          <span className="text-2xl font-extrabold text-gray-900 tracking-tight">
            {totalRevenueFormatted}
          </span>
          <span className="text-xs font-medium text-gray-500 uppercase tracking-wider mt-0.5">
            Total Revenue
          </span>
        </div>
      </div>

      {/* Legend List */}
      <div className="w-full sm:w-1/2 space-y-3.5 pl-0 sm:pl-4 border-t sm:border-t-0 sm:border-l border-gray-100 pt-4 sm:pt-0">
        {data.map((item) => {
          const pct = ((item.value / totalSum) * 100).toFixed(1);
          const color = CATEGORY_COLORS[item.name] || '#8b5cf6';
          const formattedVal = new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
            maximumFractionDigits: 0,
          }).format(item.value);

          return (
            <div key={item.name} className="flex items-center justify-between text-sm">
              <div className="flex items-center gap-2.5">
                <span className="w-3 h-3 rounded-full flex-shrink-0" style={{ backgroundColor: color }} />
                <span className="font-semibold text-gray-800">{item.name}</span>
              </div>
              <div className="text-right font-medium text-gray-700">
                <span>{formattedVal}</span>
                <span className="text-xs text-gray-400 ml-1">({pct}%)</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
