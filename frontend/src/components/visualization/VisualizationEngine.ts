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

type CubeRow = Record<string, unknown>;
type CubeResponse = { data: CubeRow[] } | Record<string, unknown>;

const PALETTE = [
  '#3b82f6',
  '#10b981',
  '#8b5cf6',
  '#f59e0b',
  '#06b6d4',
  '#f43f5e',
  '#64748b',
  '#84cc16',
  '#ec4899',
  '#6366f1',
];

const CURRENCY_KEYWORDS = ['revenue', 'profit', 'cost', 'discount', 'margin', 'aov', 'averageordervalue', 'amount'];
const TIME_GRANULARITIES = ['year', 'quarter', 'month', 'week', 'day'];
const FACT_PREFIX_PATTERN = /^Fact[A-Z]\w*\./;
const DIM_PREFIX_PATTERN = /^Dim[A-Z]\w*\./;

function _pickColor(i: number): string {
  return PALETTE[i % PALETTE.length];
}

// eslint-disable-next-line @typescript-eslint/no-unused-vars
function _formatCurrency(n: number): string {
  if (!isFinite(n)) return 'N/A';
  const abs = Math.abs(n);
  if (abs >= 1e9) {
    return `$${(n / 1e9).toFixed(1)}B`;
  }
  if (abs >= 1e6) {
    return `$${(n / 1e6).toFixed(1)}M`;
  }
  if (abs >= 1e3) {
    return `$${(n / 1e3).toFixed(1)}K`;
  }
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(n);
}

// eslint-disable-next-line @typescript-eslint/no-unused-vars
function _formatNumber(n: number): string {
  if (!isFinite(n)) return 'N/A';
  const abs = Math.abs(n);
  if (abs >= 1e9) {
    return `${(n / 1e9).toFixed(1)}B`;
  }
  if (abs >= 1e6) {
    return `${(n / 1e6).toFixed(1)}M`;
  }
  if (abs >= 1e3) {
    return `${(n / 1e3).toFixed(1)}K`;
  }
  return new Intl.NumberFormat('en-US').format(Math.round(n));
}

function _stripPrefix(key: string): string {
  const withoutFactOrDim = key.replace(/^(Fact[A-Z]\w*|Dim[A-Z]\w*)\./, '');
  const parts = withoutFactOrDim.split('.');
  const last = parts[parts.length - 1] || withoutFactOrDim;
  return last
    .replace(/([A-Z])/g, ' $1')
    .replace(/[_-]/g, ' ')
    .trim()
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

function _displayName(key: string): string {
  const name = _stripPrefix(key);
  const map: Record<string, string> = {
    Revenue: 'Revenue',
    Profit: 'Profit',
    Totalorders: 'Total Orders',
    Totalquantity: 'Total Quantity',
    Discountamount: 'Discount Amount',
    Averageordervalue: 'Average Order Value',
    Averageprofit: 'Average Profit per Order',
    Margin: 'Profit Margin',
    Totalcustomers: 'Total Customers',
    Count: 'Count',
  };
  const compact = name.replace(/\s+/g, '');
  return map[compact] || name;
}

function _isMeasureKey(key: string): boolean {
  return FACT_PREFIX_PATTERN.test(key);
}

function _isDimensionKey(key: string): boolean {
  return DIM_PREFIX_PATTERN.test(key);
}

// eslint-disable-next-line @typescript-eslint/no-unused-vars
function _extractByPrefix(rows: CubeRow[], prefix: string): string[] {
  const allKeys = new Set<string>();
  for (const row of rows) {
    for (const key of Object.keys(row)) {
      if (key.startsWith(prefix)) {
        allKeys.add(key);
      }
    }
  }
  return Array.from(allKeys);
}

function _extractKeysByPrefix(rows: CubeRow[], prefixPattern: RegExp): string[] {
  const allKeys = new Set<string>();
  for (const row of rows) {
    for (const key of Object.keys(row)) {
      if (prefixPattern.test(key)) {
        allKeys.add(key);
      }
    }
  }
  return Array.from(allKeys);
}

function _extractMeasureKeys(rows: CubeRow[]): string[] {
  return _extractKeysByPrefix(rows, FACT_PREFIX_PATTERN);
}

// eslint-disable-next-line @typescript-eslint/no-unused-vars
function _extractDimensionKeys(rows: CubeRow[]): string[] {
  return _extractKeysByPrefix(rows, DIM_PREFIX_PATTERN);
}

function _toNumber(val: unknown): number {
  if (typeof val === 'number') return val;
  if (typeof val === 'string') {
    const parsed = parseFloat(val);
    return isNaN(parsed) ? 0 : parsed;
  }
  return 0;
}

function _hasCurrencyMeasure(keys: string[]): boolean {
  return keys.some((k) => {
    const lower = k.toLowerCase();
    return CURRENCY_KEYWORDS.some((ck) => lower.includes(ck));
  });
}

function _isTimeKey(key: string): boolean {
  const lower = key.toLowerCase();
  if (lower.includes('createdat') || lower.includes('fulldate')) return true;
  return TIME_GRANULARITIES.some((g) => key.endsWith(`.${g}`) || lower.includes(`.${g}`));
}

function _detectTimeLabelKey(rows: CubeRow[]): string | null {
  if (rows.length === 0) return null;
  const firstRow = rows[0];
  const allKeys = Object.keys(firstRow);
  const timeKeys = allKeys.filter(_isTimeKey);
  if (timeKeys.length > 0) return timeKeys[0];
  for (const key of allKeys) {
    const val = firstRow[key];
    if (typeof val === 'string' && /^\d{4}-\d{2}-\d{2}/.test(val)) {
      return key;
    }
  }
  return null;
}

function _bestLabelKey(row: CubeRow, chartType: ChartType, dimensions: string[]): string | null {
  const allKeys = Object.keys(row);
  const dimKeys = allKeys.filter(_isDimensionKey);
  const dimLower = dimensions.map((d) => d.toLowerCase());
  for (const dim of dimLower) {
    const match = dimKeys.find((k) => k.toLowerCase().includes(dim));
    if (match) return match;
  }
  const nonMeasureKeys = allKeys.filter((k) => !_isMeasureKey(k));
  for (const k of nonMeasureKeys) {
    if (!_isTimeKey(k)) return k;
  }
  if (chartType === 'bar' || chartType === 'pie') {
    return nonMeasureKeys[0] || null;
  }
  return null;
}

function _formatTimeLabel(raw: string): string {
  if (!raw) return '';
  try {
    const date = new Date(raw);
    if (isNaN(date.getTime())) return raw;
    return new Intl.DateTimeFormat('en-US', {
      month: 'short',
      year: '2-digit',
    }).format(date);
  } catch {
    return raw;
  }
}

function _mapLineChart(
  rows: CubeRow[],
  _intent: DetectedIntent
): LineChartData {
  const timeLabelKey = _detectTimeLabelKey(rows);
  const measureKeys = _extractMeasureKeys(rows);
  const labels = timeLabelKey
    ? rows.map((r) => _formatTimeLabel(String(r[timeLabelKey] ?? '')))
    : rows.map((_, i) => String(i + 1));

  const series = measureKeys.map((key, i) => ({
    name: _displayName(key),
    data: rows.map((r) => _toNumber(r[key])),
    color: _pickColor(i),
    smooth: true,
  }));

  const yAxisFormatter = _hasCurrencyMeasure(measureKeys) ? 'currency' : 'number';

  return { labels, series, yAxisFormatter };
}

function _mapBarChart(
  rows: CubeRow[],
  intent: DetectedIntent
): BarChartData {
  const firstRow = rows[0] || {};
  const labelKey = _bestLabelKey(firstRow, 'bar', intent.dimensions);
  const measureKeys = _extractMeasureKeys(rows);
  const hasManyLabels = rows.length > 8;
  const orientation: 'horizontal' | 'vertical' = hasManyLabels ? 'horizontal' : 'vertical';
  const intentHints = intent.rawQuestion.toLowerCase();
  const forcedHorizontal = intentHints.includes('top 10') || intentHints.includes('top 5') || intentHints.includes('top ') || intentHints.includes('ranking');
  const finalOrientation = forcedHorizontal ? 'horizontal' : orientation;

  const labels = labelKey
    ? rows.map((r) => String(r[labelKey] ?? ''))
    : rows.map((_, i) => `Item ${i + 1}`);

  let valueKey = measureKeys[0] || '';
  const revenueKey = measureKeys.find((k) => k.toLowerCase().includes('revenue'));
  if (revenueKey && intent.dimensions.length < 2) {
    valueKey = revenueKey;
  }

  const data = rows.map((r) => _toNumber(r[valueKey]));
  const name = _displayName(valueKey) || 'Value';
  const color = _pickColor(0);
  const axisFormatter = _hasCurrencyMeasure([valueKey]) ? 'currency' : 'number';

  return { labels, data, name, orientation: finalOrientation, color, axisFormatter };
}

function _mapPieChart(
  rows: CubeRow[],
  intent: DetectedIntent
): PieChartData[] {
  const firstRow = rows[0] || {};
  const labelKey = _bestLabelKey(firstRow, 'pie', intent.dimensions);
  const measureKeys = _extractMeasureKeys(rows);
  let valueKey = measureKeys[0] || '';
  const revenueKey = measureKeys.find((k) => k.toLowerCase().includes('revenue'));
  if (revenueKey) valueKey = revenueKey;

  return rows.map((r) => ({
    name: labelKey ? String(r[labelKey] ?? '') : 'Unknown',
    value: _toNumber(r[valueKey]),
  }));
}

function _mapKPIs(
  rows: CubeRow[],
  _intent: DetectedIntent,
  deltas?: Record<string, number>
): KPIMetric[] {
  const firstRow = rows[0];
  if (!firstRow) {
    return [{
      label: 'No Data',
      value: 0,
      format: 'number',
      trend: 'neutral',
      description: 'No aggregate data available',
    }];
  }
  const measureKeys = _extractMeasureKeys(rows).slice(0, 4);
  if (measureKeys.length === 0) {
    return [{
      label: 'Analysis Result',
      value: 0,
      format: 'number',
      trend: 'neutral',
      description: 'No metrics found in Cube response',
    }];
  }
  return measureKeys.map((key, i) => {
    const rawValue = firstRow[key];
    const value = _toNumber(rawValue);
    const isCurrency = _hasCurrencyMeasure([key]);
    const name = _displayName(key);
    const isPercent = name.toLowerCase().includes('margin');
    let format: 'currency' | 'number' | 'percent' = 'number';
    if (isPercent) format = 'percent';
    else if (isCurrency) format = 'currency';
    let finalValue = value;
    if (format === 'percent' && Math.abs(value) <= 1) {
      finalValue = value * 100;
    }
    const deltaKey = key.toLowerCase();
    const delta = deltas?.[deltaKey] ?? 0;
    let trend: 'up' | 'down' | 'neutral' = 'neutral';
    let trendValue: string | undefined;
    if (delta > 0) {
      trend = 'up';
      trendValue = `+${delta.toFixed(1)}%`;
    } else if (delta < 0) {
      trend = 'down';
      trendValue = `${delta.toFixed(1)}%`;
    }
    return {
      label: name,
      value: finalValue,
      format,
      color: _pickColor(i),
      trend,
      trendValue,
      description: delta !== undefined ? 'vs prior period' : undefined,
    };
  });
}

function _emptyLineChart(): LineChartData {
  return {
    labels: ['—', '—', '—', '—', '—', '—'],
    series: [
      { name: 'Insufficient data', data: [0, 0, 0, 0, 0, 0], color: '#cbd5e1', smooth: true },
    ],
    yAxisFormatter: 'number',
  };
}

function _emptyBarChart(): BarChartData {
  return {
    labels: ['Waiting for Cube data'],
    data: [0],
    name: 'Insufficient data',
    orientation: 'vertical',
    color: '#cbd5e1',
    axisFormatter: 'number',
  };
}

function _emptyPieChart(): PieChartData[] {
  return [
    { name: 'Insufficient data', value: 1 },
  ];
}

function _emptyKPIs(): KPIMetric[] {
  return [
    {
      label: 'Insufficient data',
      value: 0,
      format: 'number',
      trend: 'neutral',
      description: 'Waiting for Cube response',
    },
  ];
}

function _waitingKPIs(): KPIMetric[] {
  return [
    {
      label: 'Analysis result',
      value: 0,
      format: 'number',
      trend: 'neutral',
      description: 'Waiting for Cube data',
    },
  ];
}

export function _mockCubePayloadFor(chartType: ChartType): CubeResponse {
  const months = [
    '2025-01-01T00:00:00.000',
    '2025-02-01T00:00:00.000',
    '2025-03-01T00:00:00.000',
    '2025-04-01T00:00:00.000',
    '2025-05-01T00:00:00.000',
    '2025-06-01T00:00:00.000',
    '2025-07-01T00:00:00.000',
    '2025-08-01T00:00:00.000',
    '2025-09-01T00:00:00.000',
    '2025-10-01T00:00:00.000',
    '2025-11-01T00:00:00.000',
    '2025-12-01T00:00:00.000',
  ];
  const baseRevenues = [12000, 15000, 18000, 22000, 19000, 24000, 28000, 26000, 32000, 35000, 40000, 42000];
  const baseProfits = [3000, 3750, 4500, 5500, 4750, 6000, 7000, 6500, 8000, 8750, 10000, 10500];

  if (chartType === 'line') {
    return {
      data: months.map((m, i) => ({
        'FactSales.revenue': baseRevenues[i],
        'FactSales.profit': baseProfits[i],
        'FactSales.createdAt.month': m,
      })),
    };
  }
  if (chartType === 'bar') {
    return {
      data: [
        { 'DimRegion.region': 'North America', 'FactSales.revenue': 168000 },
        { 'DimRegion.region': 'Europe', 'FactSales.revenue': 126000 },
        { 'DimRegion.region': 'Asia Pacific', 'FactSales.revenue': 95000 },
        { 'DimRegion.region': 'Latin America', 'FactSales.revenue': 52000 },
        { 'DimRegion.region': 'Middle East', 'FactSales.revenue': 38000 },
        { 'DimRegion.region': 'Africa', 'FactSales.revenue': 21000 },
      ],
    };
  }
  if (chartType === 'pie') {
    return {
      data: [
        { 'DimProduct.category': 'Technology', 'FactSales.revenue': 189000 },
        { 'DimProduct.category': 'Office Supplies', 'FactSales.revenue': 147000 },
        { 'DimProduct.category': 'Furniture', 'FactSales.revenue': 105000 },
        { 'DimProduct.category': 'Consumer Electronics', 'FactSales.revenue': 52000 },
        { 'DimProduct.category': 'Apparel', 'FactSales.revenue': 42000 },
        { 'DimProduct.category': 'Home & Kitchen', 'FactSales.revenue': 31000 },
      ],
    };
  }
  if (chartType === 'kpi') {
    return {
      data: [
        {
          'FactSales.revenue': 500000,
          'FactSales.profit': 125000,
          'FactSales.margin': 0.25,
          'FactSales.totalOrders': 3030,
        },
      ],
    };
  }
  return { data: [] };
}

function _getCubeRows(cubeResponse: unknown): CubeRow[] {
  if (!cubeResponse || typeof cubeResponse !== 'object') return [];
  const obj = cubeResponse as Record<string, unknown>;
  const data = obj.data;
  if (!Array.isArray(data)) return [];
  return data.filter((item): item is CubeRow => !!item && typeof item === 'object');
}

function _getDeltas(cubeResponse: unknown): Record<string, number> | undefined {
  if (!cubeResponse || typeof cubeResponse !== 'object') return undefined;
  const obj = cubeResponse as Record<string, unknown>;
  const deltas = obj._deltas_pct;
  if (deltas && typeof deltas === 'object') {
    const out: Record<string, number> = {};
    for (const [k, v] of Object.entries(deltas as Record<string, unknown>)) {
      out[k.toLowerCase()] = _toNumber(v);
    }
    return out;
  }
  return undefined;
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
      dataSource: 'semantic',
      errorMessage: fallbackData
        ? undefined
        : 'This question type is not yet supported for automatic visualization.',
    };
  }

  const chartType: ChartType = intent.chartType;
  const basePayload: VisualizationPayload = {
    intent,
    chartType,
    dataSource: 'semantic',
  };

  if (!_cubeResponse || _cubeResponse === null) {
    const waiting: VisualizationPayload = { ...basePayload };
    if (chartType === 'kpi') {
      waiting.kpis = _waitingKPIs();
    } else {
      waiting.kpis = _waitingKPIs();
      waiting.chartType = 'kpi';
    }
    return waiting;
  }

  try {
    const rows = _getCubeRows(_cubeResponse);
    const deltas = _getDeltas(_cubeResponse);

    if (rows.length === 0) {
      const empty: VisualizationPayload = { ...basePayload };
      switch (chartType) {
        case 'line':
          empty.line = _emptyLineChart();
          break;
        case 'bar':
          empty.bar = _emptyBarChart();
          break;
        case 'pie':
          empty.pie = _emptyPieChart();
          break;
        case 'kpi':
          empty.kpis = _emptyKPIs();
          break;
        default:
          empty.kpis = _emptyKPIs();
      }
      empty.errorMessage = 'Insufficient data returned from Cube';
      return empty;
    }

    const payload: VisualizationPayload = { ...basePayload };
    switch (chartType) {
      case 'line':
        payload.line = _mapLineChart(rows, intent);
        break;
      case 'bar':
        payload.bar = _mapBarChart(rows, intent);
        break;
      case 'pie':
        payload.pie = _mapPieChart(rows, intent);
        break;
      case 'kpi':
        payload.kpis = _mapKPIs(rows, intent, deltas);
        break;
      default:
        payload.kpis = _mapKPIs(rows, intent, deltas);
    }
    return payload;
  } catch (err) {
    console.error('[VisualizationEngine] Failed to render chart from Cube data:', err);
    const fallback: VisualizationPayload = { ...basePayload };
    fallback.errorMessage = 'Could not render chart from Cube data';
    switch (chartType) {
      case 'line':
        fallback.line = _emptyLineChart();
        break;
      case 'bar':
        fallback.bar = _emptyBarChart();
        break;
      case 'pie':
        fallback.pie = _emptyPieChart();
        break;
      case 'kpi':
        fallback.kpis = _emptyKPIs();
        break;
      default:
        fallback.kpis = _emptyKPIs();
    }
    return fallback;
  }
}

export const VisualizationEngine = {
  classify: classifyIntent,
  build: buildVisualizationPayload,
};
