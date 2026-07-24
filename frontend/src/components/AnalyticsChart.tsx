'use client';

import type { EChartsOption } from 'echarts';
import ReactECharts from 'echarts-for-react';

interface AnalyticsChartProps {
  title?: string;
  options: EChartsOption;
}

export default function AnalyticsChart({ title, options }: AnalyticsChartProps) {
  return (
    <div className="bg-white p-6 rounded-xl border border-gray-200">
      {title && <h3 className="text-lg font-semibold text-gray-900 mb-4">{title}</h3>}
      <ReactECharts
        option={options}
        style={{ height: '400px' }}
        notMerge={true}
        lazyUpdate={true}
      />
    </div>
  );
}
