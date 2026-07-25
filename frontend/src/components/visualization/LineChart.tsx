'use client';

import ReactECharts from 'echarts-for-react';
import type { EChartsOption } from 'echarts';
import { useMemo } from 'react';
import type { LineChartData } from '@/types/visualization';
import { formatCurrency, formatNumber, formatPercent } from '@/lib/chartUtils';
import { getChartColors } from '@/lib/chartUtils';

interface Props {
  data: LineChartData;
  height?: string;
}

export default function LineChart({ data, height = '340px' }: Props) {
  const colors = getChartColors();
  const formatterKind = data.yAxisFormatter;

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
      return {
      tooltip: {
        trigger: 'axis',
        valueFormatter: (v) => (typeof v === 'number' ? formatValue(v) : String(v)),
      },
      legend: { top: 0 },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        top: '15%',
        containLabel: true,
      },
      toolbox: {
        feature: {
          dataZoom: { yAxisIndex: 'none' },
          restore: {},
        },
      },
      dataZoom: [{ type: 'inside', start: 0, end: 100 }],
      color: colors,
      xAxis: {
        type: 'category',
        boundaryGap: false,
        data: data.labels,
      },
      yAxis: {
        type: 'value',
        axisLabel: {
          formatter: (value) => (typeof value === 'number' ? formatValue(value) : String(value)),
        },
      },
      series: data.series.map((s, idx) => ({
        name: s.name,
        type: 'line',
        smooth: s.smooth ?? true,
        data: s.data,
        itemStyle: { color: s.color || colors[idx % colors.length] },
        lineStyle: {
          width: 3,
          color: s.color || colors[idx % colors.length],
        },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: `${s.color || colors[idx % colors.length]}33` },
              { offset: 1, color: `${s.color || colors[idx % colors.length]}00` },
            ],
          },
        },
      })),
      animationDuration: 800,
    };
    },
    [data, colors, formatterKind]
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
