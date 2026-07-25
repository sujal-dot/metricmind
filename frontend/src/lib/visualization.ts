import { buildVisualizationPayload } from '@/components/visualization/VisualizationEngine';
import { classifyIntent } from '@/components/visualization/IntentClassifier';
import type {
  DetectedIntent,
  VisualizationPayload,
  ChartType,
  ComparisonType,
} from '@/types/visualization';

export { classifyIntent, buildVisualizationPayload };
export type { DetectedIntent, VisualizationPayload, ChartType, ComparisonType };

export function getChartLabel(chartType: ChartType): string {
  switch (chartType) {
    case 'line':
      return 'Line Chart';
    case 'bar':
      return 'Bar Chart';
    case 'pie':
      return 'Pie Chart';
    case 'kpi':
      return 'KPI Cards';
    case 'none':
    default:
      return 'No visualization';
  }
}
