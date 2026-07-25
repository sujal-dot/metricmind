'use client';

import { useMemo } from 'react';
import { buildVisualizationPayload } from '@/components/visualization/VisualizationEngine';
import type { VisualizationPayload } from '@/types/visualization';
import LineChart from './LineChart';
import BarChart from './BarChart';
import PieChart from './PieChart';
import KPICards from './KPICards';
import EmptyVisualization from './EmptyVisualization';
import { getChartLabel } from '@/lib/visualization';

interface ChartRouterProps {
  question: string;
  cubeResponse?: Record<string, unknown> | null;
  className?: string;
}

export default function ChartRouter({
  question,
  cubeResponse,
  className = '',
}: ChartRouterProps) {
  const payload = useMemo<VisualizationPayload>(
    () => buildVisualizationPayload(question, cubeResponse ?? null, true),
    [question, cubeResponse]
  );

  if (!question.trim()) {
    return (
      <EmptyVisualization
        message="Ask a question to generate a visualization"
        reason="No question provided."
      />
    );
  }

  if (payload.errorMessage) {
    return (
      <EmptyVisualization
        message="Could not generate visualization"
        reason={payload.errorMessage}
      />
    );
  }

  return (
    <div className={`space-y-4 ${className}`}>
      <div className="flex flex-wrap items-center gap-2">
        <span className="inline-flex items-center gap-1 rounded-full bg-blue-50 px-2.5 py-1 text-xs font-medium text-blue-700 ring-1 ring-inset ring-blue-700/10">
          <svg
            className="h-3 w-3"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M13 10V3L4 14h7v7l9-11h-7z"
            />
          </svg>
          {getChartLabel(payload.chartType)}
        </span>
        {payload.intent.confidence > 0 && (
          <span className="text-xs text-gray-500">
            Confidence: {Math.round(payload.intent.confidence * 100)}%
            {payload.intent.timePeriod ? ` · time: ${payload.intent.timePeriod}` : ''}
            {payload.intent.dimensions.length > 0
              ? ` · dims: ${payload.intent.dimensions.join(', ')}`
              : ''}
            {payload.intent.metrics.length > 0
              ? ` · metrics: ${payload.intent.metrics.join(', ')}`
              : ''}
          </span>
        )}
      </div>

      {payload.chartType === 'line' && payload.line ? (
        <div className="rounded-xl border border-gray-200 bg-white p-5">
          <LineChart data={payload.line} />
        </div>
      ) : null}

      {payload.chartType === 'bar' && payload.bar ? (
        <div className="rounded-xl border border-gray-200 bg-white p-5">
          <BarChart data={payload.bar} />
        </div>
      ) : null}

      {payload.chartType === 'pie' && payload.pie ? (
        <div className="rounded-xl border border-gray-200 bg-white p-5">
          <PieChart data={payload.pie} />
        </div>
      ) : null}

      {payload.chartType === 'kpi' && payload.kpis ? (
        <KPICards data={payload.kpis} />
      ) : null}

      {payload.chartType === 'none' ? (
        <EmptyVisualization
          message="No visualization was selected for this question"
          reason="Try including trend, comparison, share/distribution, or KPI keywords."
        />
      ) : null}
    </div>
  );
}
