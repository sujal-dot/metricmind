export type JsonPrimitive = string | number | boolean | null;
export type JsonValue = JsonPrimitive | JsonObject | JsonValue[];
export interface JsonObject {
  [key: string]: JsonValue;
}

export interface MetricsBase {
  total_revenue: number;
  total_profit: number;
  profit_margin: number;
  total_orders: number;
  total_customers: number;
  average_order_value: number;
}

export interface MetricsResponse extends MetricsBase {
  prior_metrics?: MetricsBase | null;
  period_change_pct: Record<string, number | null>;
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
  cube_trace?: CubeTrace | null;
  cube_json?: JsonObject | null;
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
  cube_trace?: CubeTrace | null;
  cube_json?: JsonObject | null;
}

export interface HistoryItem {
  id: string;
  timestamp: string;
  userQuestion: string;
  aiResponse: string;
  status: 'success' | 'error';
}

// ---------------------------------------------------------------------------
// Governance / Transparency - Day 16
// ---------------------------------------------------------------------------

export interface CubeTrace {
  endpoint: string;
  method: string;
  request_payload: JsonObject;
  query_parameters: JsonObject;
  execution_time_ms: number;
  response_status: number;
  response_size_bytes: number;
}

export interface GovernanceValidationRequest {
  question: string;
  route?: string;
}

export interface SecurityDecision {
  allowed: boolean;
  block_reason?: string | null;
  block_code?: 'sql_injection' | 'sql_request' | 'expensive' | string | null;
  suggested_filters?: string[];
  has_sql_injection?: boolean;
  has_sql_request?: boolean;
  is_expensive?: boolean;
  matched_reasons?: string[];
}

export interface GovernanceValidationResponse {
  question: string;
  decision: SecurityDecision;
  cube_trace?: CubeTrace | null;
  cube_json?: JsonObject | null;
}

export interface ExplainResponse {
  question: string;
  summary: ExplainSummary;
  possible_reasons: string[];
  confidence: number;
  confidence_breakdown: JsonObject;
  recommendations: string[];
  provider: string;
  data_source: string;
  narrative?: string | null;
  cube_trace?: CubeTrace | null;
  cube_json?: JsonObject | null;
}

export interface ExplainSummary {
  region: string;
  period?: string | null;
  revenue: number;
  cost: number;
  shipping_cost: number;
  discount_amount: number;
  profit: number;
  margin: number;
  orders: number;
  customers: number;
  aov: number;
  primary_metric: string;
  direction_hint: string;
  period_deltas_pct: JsonObject;
  period_deltas_abs: JsonObject;
}
