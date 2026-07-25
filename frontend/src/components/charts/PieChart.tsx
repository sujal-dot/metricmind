'use client';

import ReactECharts from 'echarts-for-react';
import type { EChartsOption } from 'echarts';
import { useMemo } from 'react';
import { getChartColors } from '@/lib/chartUtils';

interface PieChartProps {
  data: { name: string; value: number }[];
  title?: string;
  radius?: string | [string, string];
  showLegend?: boolean;
  showPercentage?: boolean;
  height?: string;
}

export default function PieChart({
  data,
  title,
  radius = '65%',
  showLegend = true,
  showPercentage = true,
  height = '400px',
}: PieChartProps) {
  const colors = getChartColors();

  const option = useMemo<EChartsOption>(
    () => ({
      title: title
        ? {
            text: title,
            left: 'center',
            top: 0,
            textStyle: { fontSize: 14, fontWeight: 600, color: '#111827' },
          }
        : undefined,
      tooltip: {
        trigger: 'item',
        formatter: showPercentage
          ? '{b}: {c} ({d}%)'
          : '{b}: {c}',
      },
      legend: showLegend
        ? {
            orient: 'horizontal',
            bottom: 0,
            type: 'scroll',
          }
        : undefined,
      color: colors,
      series: [
        {
          name: title || 'Distribution',
          type: 'pie',
          radius,
          avoidLabelOverlap: true,
          itemStyle: {
            borderRadius: 8,
            borderColor: '#fff',
            borderWidth: 2,
          },
          label: {
            show: true,
            formatter: showPercentage ? '{b}\n{d}%' : '{b}\n{c}',
            fontSize: 12,
          },
          emphasis: {
            label: {
              show: true,
              fontSize: 14,
              fontWeight: 'bold',
            },
            itemStyle: {
              shadowBlur: 10,
              shadowOffsetX: 0,
              shadowColor: 'rgba(0, 0, 0, 0.2)',
            },
            scale: true,
            scaleSize: 6,
          },
          labelLine: {
            show: true,
            length: 15,
            length2: 10,
          },
          data,
        },
      ],
      animationDuration: 800,
      animationEasing: 'elasticOut',
    }),
    [data, title, radius, showLegend, showPercentage, colors]
  );

  return (
    <ReactECharts
      option={option}
      style={{ height }}
      notMerge={true}
      lazyUpdate={true}
    />
  );
}
