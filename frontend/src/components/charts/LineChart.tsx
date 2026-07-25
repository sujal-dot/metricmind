'use client';

import ReactECharts from 'echarts-for-react';
import type { EChartsOption } from 'echarts';
import { useMemo } from 'react';

interface LineChartProps {
  labels: string[];
  series: {
    name: string;
    data: number[];
    color?: string;
    smooth?: boolean;
  }[];
  yAxisFormatter?: (value: number) => string;
  height?: string;
}

export default function LineChart({
  labels,
  series,
  yAxisFormatter,
  height = '400px',
}: LineChartProps) {
  const option = useMemo<EChartsOption>(
    () => ({
      tooltip: {
        trigger: 'axis',
      },
      legend: {
        top: 0,
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        top: '15%',
        containLabel: true,
      },
      toolbox: {
        feature: {
          dataZoom: {
            yAxisIndex: 'none',
          },
          restore: {},
        },
      },
      dataZoom: [
        {
          type: 'inside',
          start: 0,
          end: 100,
        },
      ],
      xAxis: {
        type: 'category',
        boundaryGap: false,
        data: labels,
      },
      yAxis: {
        type: 'value',
        axisLabel: {
          formatter: yAxisFormatter,
        },
      },
      series: series.map((s) => ({
        name: s.name,
        type: 'line',
        smooth: s.smooth ?? true,
        data: s.data,
        itemStyle: { color: s.color },
        lineStyle: { width: 3, color: s.color },
        areaStyle: s.color
          ? {
              color: {
                type: 'linear',
                x: 0,
                y: 0,
                x2: 0,
                y2: 1,
                colorStops: [
                  { offset: 0, color: `${s.color}33` },
                  { offset: 1, color: `${s.color}00` },
                ],
              },
            }
          : undefined,
      })),
      animationDuration: 800,
    }),
    [labels, series, yAxisFormatter]
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
