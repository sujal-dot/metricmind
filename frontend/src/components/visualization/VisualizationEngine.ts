import { classifyIntent } from './IntentClassifier';
import type {
  DetectedIntent,
  VisualizationPayload,
  LineChartData,
  BarChartData,
  PieChartData,
  KPIMetric,
  ChartType,
} from '@/types/visualization';

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

const LINE_DEMO_DATASETS: Record<string, LineChartData> = {
  default: {
    labels: MONTHS,
    series: [
      { name: 'Revenue', data: [12000, 15000, 18000, 22000, 19000, 24000, 28000, 26000, 32000, 35000, 40000, 42000], color: '#3b82f6', smooth: true },
      { name: 'Profit', data: [3000, 3750, 4500, 5500, 4750, 6000, 7000, 6500, 8000, 8750, 10000, 10500], color: '#10b981', smooth: true },
    ],
    yAxisFormatter: 'currency',
  },
  orders: {
    labels: MONTHS,
    series: [
      { name: 'Orders', data: [120, 150, 180, 220, 190, 240, 280, 260, 320, 350, 400, 420], color: '#8b5cf6', smooth: true },
    ],
    yAxisFormatter: 'number',
  },
  customers: {
    labels: MONTHS,
    series: [
      { name: 'Customers', data: [48, 60, 72, 88, 76, 96, 112, 104, 128, 140, 160, 168], color: '#06b6d4', smooth: true },
    ],
    yAxisFormatter: 'number',
  },
};

const BAR_DEMO_DATASETS: Record<string, BarChartData> = {
  region: {
    labels: ['North America', 'Europe', 'Asia Pacific', 'Latin America', 'Middle East', 'Africa'],
    data: [168000, 126000, 95000, 52000, 38000, 21000],
    name: 'Revenue by Region',
    orientation: 'horizontal',
    color: '#10b981',
    axisFormatter: 'currency',
  },
  category: {
    labels: ['Technology', 'Office Supplies', 'Furniture', 'Consumer Electronics', 'Apparel', 'Home & Kitchen'],
    data: [189000, 147000, 105000, 52000, 42000, 31000],
    name: 'Revenue by Category',
    orientation: 'vertical',
    color: '#8b5cf6',
    axisFormatter: 'currency',
  },
  product: {
    labels: ['Product A', 'Product B', 'Product C', 'Product D', 'Product E', 'Product F', 'Product G', 'Product H', 'Product I', 'Product J'],
    data: [52000, 48000, 41000, 36000, 29000, 22000, 18000, 15000, 12000, 9000],
    name: 'Top Products',
    orientation: 'horizontal',
    color: '#f59e0b',
    axisFormatter: 'currency',
  },
  customer: {
    labels: ['Customer A', 'Customer B', 'Customer C', 'Customer D', 'Customer E', 'Customer F', 'Customer G', 'Customer H', 'Customer I', 'Customer J'],
    data: [62000, 55000, 48000, 39000, 31000, 26000, 22000, 18000, 14000, 11000],
    name: 'Top Customers',
    orientation: 'horizontal',
    color: '#06b6d4',
    axisFormatter: 'currency',
  },
  default: {
    labels: ['Technology', 'Office Supplies', 'Furniture'],
    data: [189000, 147000, 105000],
    name: 'Revenue',
    orientation: 'vertical',
    color: '#3b82f6',
    axisFormatter: 'currency',
  },
};

const PIE_DEMO_DATASETS: Record<string, PieChartData[]> = {
  category: [
    { name: 'Technology', value: 189000 },
    { name: 'Office Supplies', value: 147000 },
    { name: 'Furniture', value: 105000 },
    { name: 'Consumer Electronics', value: 52000 },
    { name: 'Apparel', value: 42000 },
    { name: 'Home & Kitchen', value: 31000 },
  ],
  region: [
    { name: 'North America', value: 168000 },
    { name: 'Europe', value: 126000 },
    { name: 'Asia Pacific', value: 95000 },
    { name: 'Latin America', value: 52000 },
    { name: 'Middle East', value: 38000 },
    { name: 'Africa', value: 21000 },
  ],
  default: [
    { name: 'Technology', value: 45000 },
    { name: 'Office Supplies', value: 35000 },
    { name: 'Furniture', value: 25000 },
    { name: 'Other', value: 20000 },
  ],
};

const KPI_DEFAULTS: KPIMetric[] = [
  { label: 'Total Revenue', value: 500000, format: 'currency', trend: 'up', trendValue: '12.4%', description: 'vs prior period' },
  { label: 'Total Profit', value: 125000, format: 'currency', trend: 'up', trendValue: '8.1%', description: 'vs prior period' },
  { label: 'Profit Margin', value: 0.25, format: 'percent', trend: 'neutral', trendValue: '0.3%', description: 'vs prior period' },
  { label: 'Total Orders', value: 3030, format: 'number', trend: 'up', trendValue: '5.7%', description: 'vs prior period' },
  { label: 'Total Customers', value: 1284, format: 'number', trend: 'up', trendValue: '9.2%', description: 'vs prior period' },
  { label: 'Average Order Value', value: 165, format: 'currency', trend: 'up', trendValue: '3.4%', description: 'vs prior period' },
];

function resolveBarDataset(intent: DetectedIntent): BarChartData {
  const dims = intent.dimensions.map((d) => d.toLowerCase());
  if (dims.includes('region')) return BAR_DEMO_DATASETS.region;
  if (dims.includes('category')) return BAR_DEMO_DATASETS.category;
  if (dims.includes('product')) return BAR_DEMO_DATASETS.product;
  if (dims.includes('customer')) return BAR_DEMO_DATASETS.customer;
  if (intent.rawQuestion.toLowerCase().includes('top 10 customer') || intent.rawQuestion.toLowerCase().includes('top customer')) {
    return BAR_DEMO_DATASETS.customer;
  }
  if (intent.rawQuestion.toLowerCase().includes('top') || intent.rawQuestion.toLowerCase().includes('best-selling')) {
    return BAR_DEMO_DATASETS.product;
  }
  return BAR_DEMO_DATASETS.default;
}

function resolvePieDataset(intent: DetectedIntent): PieChartData[] {
  const lower = intent.rawQuestion.toLowerCase();
  if (lower.includes('region')) return PIE_DEMO_DATASETS.region;
  if (lower.includes('category')) return PIE_DEMO_DATASETS.category;
  if (lower.includes('customer')) return PIE_DEMO_DATASETS.default;
  return PIE_DEMO_DATASETS.default;
}

function resolveLineDataset(intent: DetectedIntent): LineChartData {
  const metrics = intent.metrics.map((m) => m.toLowerCase());
  if (metrics.includes('orders') && !metrics.includes('revenue') && !metrics.includes('profit')) {
    return LINE_DEMO_DATASETS.orders;
  }
  if (metrics.includes('customers') || lowerIncludes(intent.rawQuestion, ['customer', 'growth'])) {
    return LINE_DEMO_DATASETS.customers;
  }
  return LINE_DEMO_DATASETS.default;
}

function lowerIncludes(text: string, needles: string[]): boolean {
  const l = text.toLowerCase();
  return needles.some((n) => l.includes(n.toLowerCase()));
}

function resolveKPIs(intent: DetectedIntent): KPIMetric[] {
  const lower = intent.rawQuestion.toLowerCase();
  if (lower.includes('total profit') || lower.includes('profit') && !lower.includes('revenue')) {
    return [
      { label: 'Total Profit', value: 125000, format: 'currency', trend: 'up', trendValue: '8.1%', description: 'vs prior period' },
    ];
  }
  if (lower.includes('total revenue') || (lowerIncludes(lower, ['revenue']) && !lowerIncludes(lower, ['profit', 'orders', 'customers', 'aov', 'average order value', 'margin']))) {
    return [
      { label: 'Total Revenue', value: 500000, format: 'currency', trend: 'up', trendValue: '12.4%', description: 'vs prior period' },
    ];
  }
  if (lowerIncludes(lower, ['total orders', 'number of orders', 'count of orders'])) {
    return [
      { label: 'Total Orders', value: 3030, format: 'number', trend: 'up', trendValue: '5.7%', description: 'vs prior period' },
    ];
  }
  if (lowerIncludes(lower, ['customers', 'number of customers', 'count of customers'])) {
    return [
      { label: 'Total Customers', value: 1284, format: 'number', trend: 'up', trendValue: '9.2%', description: 'vs prior period' },
    ];
  }
  if (lowerIncludes(lower, ['average order value', 'aov'])) {
    return [
      { label: 'Average Order Value', value: 165, format: 'currency', trend: 'up', trendValue: '3.4%', description: 'vs prior period' },
    ];
  }
  if (lowerIncludes(lower, ['margin', 'profit margin', 'gross margin'])) {
    return [
      { label: 'Profit Margin', value: 0.25, format: 'percent', trend: 'neutral', trendValue: '0.3%', description: 'vs prior period' },
    ];
  }
  return KPI_DEFAULTS;
}

export function buildVisualizationPayload(
  question: string,
  _cubeResponse?: Record<string, unknown> | null,
  fallbackData = true
): VisualizationPayload {
  const intent = classifyIntent(question);

  if (!intent.isSupported) {
    return {
      intent,
      chartType: 'none',
      dataSource: 'demo',
      errorMessage: fallbackData
        ? undefined
        : 'This question type is not yet supported for automatic visualization.',
    };
  }

  const chartType: ChartType = intent.chartType;
  const payload: VisualizationPayload = {
    intent,
    chartType,
    dataSource: 'demo',
  };

  switch (chartType) {
    case 'line':
      payload.line = resolveLineDataset(intent);
      break;
    case 'bar':
      payload.bar = resolveBarDataset(intent);
      break;
    case 'pie':
      payload.pie = resolvePieDataset(intent);
      break;
    case 'kpi':
      payload.kpis = resolveKPIs(intent);
      break;
    default:
      break;
  }

  return payload;
}

export const VisualizationEngine = {
  classify: classifyIntent,
  build: buildVisualizationPayload,
};
