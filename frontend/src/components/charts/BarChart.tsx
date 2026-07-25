'use client';

import ReactECharts from 'echarts-for-react';
import type { EChartsOption } from 'echarts';
import { useMemo } from 'react';

type BarOrientation = 'horizontal' | 'vertical';

interface BarChartProps {
  labels: string[];
  data: number[];
  name: string;
  color?: string;
  orientation?: BarOrientation;
  yAxisFormatter?: (value: number) => string;
  xAxisFormatter?: (value: number) => string;
  height?: string;
}

export default function BarChart({
  labels,
  data,
  name,
  color = '#3b82f6',
  orientation = 'vertical',
  yAxisFormatter,
  xAxisFormatter,
  height = '400px',
}: BarChartProps) {
  const option = useMemo<EChartsOption>(
    () => {
      const isHorizontal = orientation === 'horizontal';
      return {
        tooltip: {
          trigger: 'axis',
          axisPointer: {
            type: 'shadow',
          },
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '3%',
          top: '10%',
          containLabel: true,
        },
        toolbox: {
          feature: {
            restore: {},
          },
        },
        xAxis: isHorizontal
          ? {
              type: 'value',
              axisLabel: { formatter: xAxisFormatter },
            }
          : {
              type: 'category',
              data: labels,
              axisLabel: { rotate: 30, interval: 0 },
            },
        yAxis: isHorizontal
          ? {
              type: 'category',
              data: labels,
            }
          : {
              type: 'value',
              axisLabel: { formatter: yAxisFormatter },
            },
        series: [
          {
            name,
            type: 'bar',
            data,
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
    [labels, data, name, color, orientation, yAxisFormatter, xAxisFormatter]
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
