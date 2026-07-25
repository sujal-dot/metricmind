export type ChartType = 'line' | 'bar' | 'pie' | 'kpi' | 'none';

export type ComparisonType =
  | 'trend'
  | 'comparison'
  | 'distribution'
  | 'kpi'
  | 'unknown';

export interface DetectedIntent {
  rawQuestion: string;
  comparisonType: ComparisonType;
  chartType: ChartType;
  metrics: string[];
  dimensions: string[];
  timePeriod: string | null;
  isSupported: boolean;
  confidence: number;
}

export interface LineChartData {
  labels: string[];
  series: Array<{
    name: string;
    data: number[];
    color?: string;
    smooth?: boolean;
  }>;
  yAxisFormatter?: 'currency' | 'number' | 'percent';
}

export interface BarChartData {
  labels: string[];
  data: number[];
  name: string;
  orientation?: 'horizontal' | 'vertical';
  color?: string;
  axisFormatter?: 'currency' | 'number' | 'percent';
}

export interface PieChartData {
  name: string;
  value: number;
}

export interface KPIMetric {
  label: string;
  value: number;
  format: 'currency' | 'number' | 'percent';
  trend?: 'up' | 'down' | 'neutral';
  trendValue?: string;
  description?: string;
}

export interface VisualizationPayload {
  intent: DetectedIntent;
  chartType: ChartType;
  line?: LineChartData;
  bar?: BarChartData;
  pie?: PieChartData[];
  kpis?: KPIMetric[];
  dataSource?: 'semantic' | 'metrics' | 'sales' | 'demo';
  errorMessage?: string;
}

export interface VisualizationContext {
  userQuestion: string;
  assistantAnswer: string;
  provider?: string;
}
