import type {
  DetectedIntent,
  ComparisonType,
  ChartType,
} from '@/types/visualization';

const TREND_KEYWORDS: string[] = [
  'trend',
  'growth',
  'over time',
  'monthly',
  'yearly',
  'daily',
  'timeline',
  'compare months',
  'compare years',
  'quarterly',
  'weekly',
  'trends',
  'over the',
  'across months',
  'across years',
  'period',
  'grew',
];

const BAR_STRONG_KEYWORDS: string[] = [
  'top',
  'ranking',
  'compare',
  'highest',
  'lowest',
  'best',
  'worst',
  'rank',
  'leaderboard',
  'top 10',
  'top 5',
  'top 3',
  'best-selling',
  'bestselling',
  'top selling',
];

const BAR_DIMENSION_KEYWORDS: string[] = [
  'region',
  'category',
  'product',
  'customer',
  'which',
  'employee',
  'segment',
];

const PIE_KEYWORDS: string[] = [
  'share',
  'percentage',
  'distribution',
  'composition',
  'contribution',
  'breakdown',
  'proportion',
  'mix',
  'market share',
  'percent',
  'percent of',
  'fraction',
  'split',
  'part of',
  'how much of',
  'what portion',
];

const KPI_KEYWORDS: string[] = [
  'total revenue',
  'total profit',
  'total orders',
  'customers',
  'average order value',
  'aov',
  'margin',
  'kpi',
  'how much revenue',
  'how much profit',
  'number of orders',
  'number of customers',
  'count of orders',
  'count of customers',
  'overall revenue',
  'overall profit',
  'profit margin',
  'gross margin',
  'summary',
  'totals',
  'what is the total',
  'what is total',
];

const METRIC_KEYWORDS: string[] = [
  'revenue',
  'profit',
  'sales',
  'orders',
  'customers',
  'margin',
  'aov',
  'average order value',
  'quantity',
  'discount',
];

const DIMENSION_KEYWORDS: string[] = [
  'region',
  'category',
  'product',
  'customer',
  'employee',
  'segment',
  'channel',
  'country',
  'city',
  'state',
];

const TIME_PERIOD_PATTERNS: Array<{ pattern: RegExp; value: string }> = [
  { pattern: /\b20\d{2}\b/g, value: 'year' },
  { pattern: /\b(january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|jun|jul|aug|sep|oct|nov|dec)\b/gi, value: 'month' },
  { pattern: /\b(q[1-4]|quarter)\b/gi, value: 'quarter' },
  { pattern: /\b(yearly|year|annually|annual)\b/gi, value: 'year' },
  { pattern: /\b(monthly|month)\b/gi, value: 'month' },
  { pattern: /\b(weekly|week)\b/gi, value: 'week' },
  { pattern: /\b(daily|day)\b/gi, value: 'day' },
];

function countMatches(text: string, keywords: string[]): number {
  const lower = text.toLowerCase();
  let count = 0;
  for (const keyword of keywords) {
    if (lower.includes(keyword.toLowerCase())) {
      count += 1;
    }
  }
  return count;
}

function extractKeywords(text: string, keywords: string[]): string[] {
  const lower = text.toLowerCase();
  const found: string[] = [];
  for (const keyword of keywords) {
    if (lower.includes(keyword.toLowerCase())) {
      found.push(keyword);
    }
  }
  return Array.from(new Set(found));
}

function detectTimePeriod(text: string): string | null {
  for (const { pattern, value } of TIME_PERIOD_PATTERNS) {
    if (pattern.test(text)) {
      return value;
    }
  }
  return null;
}

export function classifyIntent(question: string): DetectedIntent {
  const raw = question.trim();
  const lower = raw.toLowerCase();

  if (!raw) {
    return {
      rawQuestion: raw,
      comparisonType: 'unknown',
      chartType: 'none',
      metrics: [],
      dimensions: [],
      timePeriod: null,
      isSupported: false,
      confidence: 0,
    };
  }

  const trendCount = countMatches(lower, TREND_KEYWORDS);
  const barStrongCount = countMatches(lower, BAR_STRONG_KEYWORDS);
  const barDimCount = countMatches(lower, BAR_DIMENSION_KEYWORDS);
  const pieCount = countMatches(lower, PIE_KEYWORDS);
  const kpiCount = countMatches(lower, KPI_KEYWORDS);

  let comparisonType: ComparisonType = 'unknown';
  let chartType: ChartType = 'none';
  let confidence = 0;

  const scores: Array<{ type: ComparisonType; chart: ChartType; score: number }> = [
    { type: 'trend', chart: 'line', score: trendCount * 2.5 },
    { type: 'comparison', chart: 'bar', score: barStrongCount * 3 + barDimCount * 1.2 },
    { type: 'distribution', chart: 'pie', score: pieCount * 4 },
    { type: 'kpi', chart: 'kpi', score: kpiCount * 2.2 },
  ];

  scores.sort((a, b) => b.score - a.score);
  const best = scores[0];

  if (best && best.score > 0) {
    if (pieCount > 0 && barDimCount > 0 && barStrongCount === 0) {
      comparisonType = 'distribution';
      chartType = 'pie';
    } else {
      comparisonType = best.type;
      chartType = best.chart;
    }
    const total = scores.reduce((acc, s) => acc + s.score, 0);
    confidence = total === 0 ? 0 : Math.min(1, best.score / Math.max(1, total));
    if (pieCount > 0 && barDimCount > 0 && barStrongCount === 0) {
      confidence = Math.min(1, confidence + 0.1);
    }
  }

  if (comparisonType === 'unknown') {
    if (lower.includes('?') || METRIC_KEYWORDS.some((m) => lower.includes(m))) {
      comparisonType = 'kpi';
      chartType = 'kpi';
      confidence = 0.35;
    }
  }

  const metrics = extractKeywords(lower, METRIC_KEYWORDS);
  const dimensions = extractKeywords(lower, DIMENSION_KEYWORDS);
  const timePeriod = detectTimePeriod(lower);

  const isSupported =
    chartType === 'line' ||
    chartType === 'bar' ||
    chartType === 'pie' ||
    chartType === 'kpi';

  return {
    rawQuestion: raw,
    comparisonType,
    chartType,
    metrics,
    dimensions,
    timePeriod,
    isSupported,
    confidence,
  };
}

export const IntentClassifier = {
  classify: classifyIntent,
  TREND_KEYWORDS,
  BAR_STRONG_KEYWORDS,
  BAR_DIMENSION_KEYWORDS,
  PIE_KEYWORDS,
  KPI_KEYWORDS,
  METRIC_KEYWORDS,
  DIMENSION_KEYWORDS,
};

export type { ComparisonType, ChartType };
