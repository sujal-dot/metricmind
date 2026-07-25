'use client';

import ReactECharts from 'echarts-for-react';
import type { EChartsOption } from 'echarts';
import { useMemo } from 'react';
import type { PieChartData } from '@/types/visualization';
import { getChartColors } from '@/lib/chartUtils';

interface Props {
  data: PieChartData[];
  title?: string;
  height?: string;
}

export default function PieChart({ data, title, height = '340px' }: Props) {
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
        formatter: '{b}: {c} ({d}%)',
      },
      legend: {
        orient: 'horizontal',
        bottom: 0,
        type: 'scroll',
      },
      color: colors,
      series: [
        {
          name: title || 'Distribution',
          type: 'pie',
          radius: '65%',
          avoidLabelOverlap: true,
          itemStyle: {
            borderRadius: 8,
            borderColor: '#fff',
            borderWidth: 2,
          },
          label: {
            show: true,
            formatter: '{b}\n{d}%',
            fontSize: 12,
          },
          emphasis: {
            label: { show: true, fontSize: 14, fontWeight: 'bold' },
            itemStyle: {
              shadowBlur: 10,
              shadowOffsetX: 0,
              shadowColor: 'rgba(0, 0, 0, 0.2)',
            },
            scale: true,
            scaleSize: 6,
          },
          labelLine: { show: true, length: 15, length2: 10 },
          data,
        },
      ],
      animationDuration: 800,
      animationEasing: 'elasticOut',
    }),
    [data, title, colors]
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
