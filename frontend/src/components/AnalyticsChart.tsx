'use client';

import ReactECharts from 'echarts-for-react';
import { Card } from '@tremor/react';

interface AnalyticsChartProps {
  title?: string;
  options: any;
}

export default function AnalyticsChart({ title, options }: AnalyticsChartProps) {
  return (
    <Card className="p-6">
      {title && <h3 className="text-lg font-semibold text-gray-900 mb-4">{title}</h3>}
      <ReactECharts
        option={options}
        style={{ height: '400px' }}
        notMerge={true}
        lazyUpdate={true}
      />
    </Card>
  );
}
