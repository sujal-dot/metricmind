export type JsonPrimitive = string | number | boolean | null;
export type JsonValue = JsonPrimitive | JsonObject | JsonValue[];
export interface JsonObject {
  [key: string]: JsonValue;
}

export interface MetricsResponse {
  total_revenue: number;
  total_profit: number;
  profit_margin: number;
  total_orders: number;
  total_customers: number;
  average_order_value: number;
}

export interface SalesItem {
  order_id: string;
  sales: number;
  quantity: number;
  profit: number;
  discount: number;
}

export interface SalesListResponse {
  items: SalesItem[];
  total: number;
  limit: number;
  offset: number;
}

export interface BIQuestionRequest {
  question: string;
}

export interface BIAnswerResponse {
  question: string;
  answer: string;
  source: string;
  provider: string;
}

export interface SemanticSearchRequest {
  question: string;
}

export interface SemanticSearchIntent {
  metrics: string[];
  dimensions: string[];
  time_period: JsonObject | null;
  filters: JsonObject;
  ordering: Record<string, string> | null;
  limit: number | null;
}

export interface SemanticSearchResponse {
  question: string;
  intent: SemanticSearchIntent;
  cube_response: JsonObject;
  explanation: string;
  provider: string;
}

export interface HistoryItem {
  id: string;
  timestamp: string;
  userQuestion: string;
  aiResponse: string;
  status: 'success' | 'error';
}
