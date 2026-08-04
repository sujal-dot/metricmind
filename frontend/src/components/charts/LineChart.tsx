'use client';

import React, { useMemo, useRef } from 'react';
import ReactECharts from 'echarts-for-react';
import type { EChartsOption } from 'echarts';

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
  showControls?: boolean;
}

export default function LineChart({
  labels,
  series,
  yAxisFormatter,
  height = '400px',
  showControls = true,
}: LineChartProps) {
  const echartsRef = useRef<ReactECharts>(null);

  const getEChartInstance = () => {
    return echartsRef.current?.getEchartsInstance();
  };

  const handleZoomIn = () => {
    const chart = getEChartInstance();
    if (!chart) return;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const option = chart.getOption() as any;
    const currentStart = option?.dataZoom?.[0]?.start ?? 0;
    const currentEnd = option?.dataZoom?.[0]?.end ?? 100;
    const range = currentEnd - currentStart;
    const step = Math.max(5, Math.round(range * 0.2));
    const nextStart = Math.min(currentStart + step, currentEnd - 10);
    const nextEnd = Math.max(currentEnd - step, nextStart + 10);
    chart.dispatchAction({
      type: 'dataZoom',
      start: nextStart,
      end: nextEnd,
    });
  };

  const handleZoomOut = () => {
    const chart = getEChartInstance();
    if (!chart) return;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const option = chart.getOption() as any;
    const currentStart = option?.dataZoom?.[0]?.start ?? 0;
    const currentEnd = option?.dataZoom?.[0]?.end ?? 100;
    const range = currentEnd - currentStart;
    const step = Math.max(5, Math.round(range * 0.25));
    const nextStart = Math.max(0, currentStart - step);
    const nextEnd = Math.min(100, currentEnd + step);
    chart.dispatchAction({
      type: 'dataZoom',
      start: nextStart,
      end: nextEnd,
    });
  };

  const handleResetZoom = () => {
    const chart = getEChartInstance();
    if (!chart) return;
    chart.dispatchAction({
      type: 'dataZoom',
      start: 0,
      end: 100,
    });
  };

  const handleRestore = () => {
    const chart = getEChartInstance();
    if (!chart) return;
    chart.dispatchAction({
      type: 'restore',
    });
    chart.dispatchAction({
      type: 'dataZoom',
      start: 0,
      end: 100,
    });
  };

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
        bottom: '12%',
        top: '15%',
        containLabel: true,
      },
      toolbox: {
        show: true,
        right: 10,
        top: 0,
        showTitle: false,
        feature: {
          dataZoom: {
            yAxisIndex: 'none',
            title: {
              zoom: 'Box Zoom',
              back: 'Reset Zoom',
            },
          },
          restore: {
            title: 'Restore',
          },
        },
      },
      dataZoom: [
        {
          type: 'inside',
          start: 0,
          end: 100,
        },
        {
          type: 'slider',
          show: true,
          start: 0,
          end: 100,
          height: 20,
          bottom: 5,
          borderColor: '#e2e8f0',
          backgroundColor: '#f8fafc',
          fillerColor: 'rgba(59, 130, 246, 0.15)',
          handleStyle: {
            color: '#3b82f6',
            borderColor: '#2563eb',
          },
          moveHandleStyle: {
            color: '#94a3b8',
          },
          textStyle: {
            color: '#64748b',
            fontSize: 11,
          },
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
    <div className="relative w-full">
      {showControls && (
        <div className="flex items-center justify-end gap-1.5 mb-2 px-1 text-xs text-gray-600">
          <button
            type="button"
            onClick={handleZoomIn}
            className="inline-flex items-center gap-1 rounded bg-gray-100 hover:bg-gray-200 px-2 py-1 font-medium transition-colors cursor-pointer"
            title="Zoom in on timeline"
          >
            <svg className="w-3.5 h-3.5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM10 7v6m3-3H7" />
            </svg>
            Zoom +
          </button>
          <button
            type="button"
            onClick={handleZoomOut}
            className="inline-flex items-center gap-1 rounded bg-gray-100 hover:bg-gray-200 px-2 py-1 font-medium transition-colors cursor-pointer"
            title="Zoom out on timeline"
          >
            <svg className="w-3.5 h-3.5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM13 10H7" />
            </svg>
            Zoom -
          </button>
          <button
            type="button"
            onClick={handleResetZoom}
            className="inline-flex items-center gap-1 rounded bg-gray-100 hover:bg-gray-200 px-2 py-1 font-medium transition-colors cursor-pointer"
            title="Reset timeline zoom to 100%"
          >
            <svg className="w-3.5 h-3.5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Reset Zoom
          </button>
          <button
            type="button"
            onClick={handleRestore}
            className="inline-flex items-center gap-1 rounded bg-gray-100 hover:bg-gray-200 px-2 py-1 font-medium transition-colors cursor-pointer"
            title="Restore original chart view"
          >
            <svg className="w-3.5 h-3.5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9" />
            </svg>
            Restore
          </button>
        </div>
      )}

      <ReactECharts
        ref={echartsRef}
        option={option}
        style={{ height }}
        notMerge={true}
        lazyUpdate={true}
      />
    </div>
  );
}
