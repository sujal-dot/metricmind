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

export interface MonthlyAnalyticsPoint {
  label: string;
  revenue: number;
  profit: number;
  orders: number;
}

export interface ChartDataPoint {
  label?: string;
  name?: string;
  value: number;
  category?: string;
}

export interface AnalyticsCharts {
  monthly: MonthlyAnalyticsPoint[];
  by_category: { name: string; value: number }[];
  by_region: { name: string; value: number }[];
  top_products: { name: string; value: number }[];
  top_customers: { name: string; value: number }[];
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
