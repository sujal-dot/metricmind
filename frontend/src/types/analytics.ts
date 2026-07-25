export interface KPIMetrics {
  total_revenue: number;
  total_profit: number;
  profit_margin: number;
  total_orders: number;
  total_customers: number;
  average_order_value: number;
}

export interface AnalyticsFilters {
  date_from?: string;
  date_to?: string;
  region?: string;
  category?: string;
  [key: string]: string | undefined;
}

export interface ChartDataPoint {
  label: string;
  value: number;
  category?: string;
}

export interface PieDataPoint {
  name: string;
  value: number;
  percentage?: number;
}

export interface LineChartSeries {
  name: string;
  data: number[];
  color?: string;
  smooth?: boolean;
}
