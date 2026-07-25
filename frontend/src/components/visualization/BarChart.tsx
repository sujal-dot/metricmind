'use client';

import ReactECharts from 'echarts-for-react';
import type { EChartsOption } from 'echarts';
import { useMemo } from 'react';
import type { BarChartData } from '@/types/visualization';
import { formatCurrency, formatNumber, formatPercent, getChartColors } from '@/lib/chartUtils';

interface Props {
  data: BarChartData;
  height?: string;
}

export default function BarChart({ data, height = '340px' }: Props) {
  const colors = getChartColors();
  const color = data.color || colors[0];
  const formatterKind = data.axisFormatter;

  const option = useMemo<EChartsOption>(
    () => {
      const formatValue = (value: number): string => {
        switch (formatterKind) {
          case 'currency':
            return formatCurrency(value);
          case 'percent':
            return formatPercent(value);
          case 'number':
          default:
            return formatNumber(value);
        }
      };
      const isHorizontal = data.orientation === 'horizontal';
      return {
        tooltip: {
          trigger: 'axis',
          axisPointer: { type: 'shadow' },
          valueFormatter: (v) => (typeof v === 'number' ? formatValue(v) : String(v)),
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '3%',
          top: '10%',
          containLabel: true,
        },
        toolbox: { feature: { restore: {} } },
        color: colors,
        xAxis: isHorizontal
          ? {
              type: 'value',
              axisLabel: {
                formatter: (value) =>
                  typeof value === 'number' ? formatValue(value) : String(value),
              },
            }
          : {
              type: 'category',
              data: data.labels,
              axisLabel: { rotate: 30, interval: 0 },
            },
        yAxis: isHorizontal
          ? { type: 'category', data: data.labels }
          : {
              type: 'value',
              axisLabel: {
                formatter: (value) =>
                  typeof value === 'number' ? formatValue(value) : String(value),
              },
            },
        series: [
          {
            name: data.name,
            type: 'bar',
            data: data.data,
            itemStyle: {
              color,
              borderRadius: isHorizontal ? [0, 4, 4, 0] : [4, 4, 0, 0],
            },
            emphasis: {
              itemStyle: {
                shadowBlur: 10,
                shadowColor: 'rgba(0,0,0,0.2)',
              },
            },
          },
        ],
        animationDuration: 800,
      };
    },
    [data, colors, color, formatterKind]
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
