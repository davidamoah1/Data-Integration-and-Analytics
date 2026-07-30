// ─── Auth Types ──────────────────────────────────────────────

export interface User {
  id: number;
  email: string;
  full_name: string;
  avatar_url?: string;
  phone?: string;
  organization_id?: number;
  organization_name?: string;
  department_id?: number;
  position?: string;
  language?: string;
  timezone?: string;
  roles: string[];
  permissions: string[];
  email_verified?: boolean;
  last_login_at?: string;
  created_at?: string;
}

export interface LoginRequest {
  email: string;
  password: string;
  remember_me?: boolean;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface RefreshResponse {
  access_token: string;
  refresh_token: string;
  expires_in: number;
}

// ─── API Response Types ──────────────────────────────────────

export interface ApiResponse<T = unknown> {
  success: boolean;
  data: T;
  message: string;
}

export interface PaginatedResponse<T = unknown> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

// ─── Dataset Types ───────────────────────────────────────────

export interface Dataset {
  id: string;
  name: string;
  description: string;
  tier: 'production' | 'demo' | 'test';
  industry: string;
  row_count: number;
  column_count: number;
  quality_score?: number;
  status: 'ready' | 'processing' | 'failed' | 'draft';
  owner?: string;
  created_at: string;
  updated_at: string;
}

export interface DatasetPreview {
  columns: string[];
  rows: Record<string, unknown>[];
  total_rows: number;
}

export interface DatasetSchema {
  columns: ColumnSchema[];
}

export interface ColumnSchema {
  name: string;
  dtype: string;
  nullable: boolean;
  unique_count: number;
  sample_values: unknown[];
}

// ─── Dashboard Types ─────────────────────────────────────────

export interface Dashboard {
  id: number;
  name: string;
  description?: string;
  is_public: boolean;
  is_favorite: boolean;
  version: number;
  widgets: Widget[];
  created_at: string;
  updated_at: string;
}

export interface Widget {
  id: number;
  widget_type: 'kpi' | 'chart' | 'table' | 'text' | 'filter';
  title: string;
  config: Record<string, unknown>;
  position: { x: number; y: number; w: number; h: number };
}

export interface KPI {
  id: number;
  name: string;
  category: string;
  value: number;
  target?: number;
  unit?: string;
  trend?: 'up' | 'down' | 'flat';
  trend_value?: number;
  status: 'good' | 'warning' | 'critical';
  is_active: boolean;
}

// ─── AI Copilot Types ────────────────────────────────────────

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  citations?: string[];
  confidence?: number;
  created_at: string;
}

export interface Conversation {
  id: number;
  title: string;
  assistant_type: string;
  message_count: number;
  created_at: string;
  updated_at: string;
}

export interface ChatRequest {
  message: string;
  assistant_type?: string;
  conversation_id?: number;
  context?: Record<string, unknown>;
}

export interface ChatResponse {
  response: string;
  conversation_id: number;
  citations?: string[];
  confidence_score?: number;
  follow_ups?: string[];
}

// ─── Enterprise AI Types ─────────────────────────────────────

export interface ExecutiveSummary {
  id?: number;
  title: string;
  executive_summary: string;
  kpi_highlights: KPIHighlight[];
  main_drivers: string[];
  risks: RiskItem[];
  opportunities: string[];
  forecast: {
    direction: string;
    expected_range: string;
    horizon: string;
    assumptions: string[];
  };
  recommended_actions: RecommendedAction[];
  confidence: {
    score: number;
    methodology: string;
    data_limitations: string[];
  };
  industry?: string;
  dataset?: string;
}

export interface KPIHighlight {
  metric: string;
  value: string;
  change: string;
  direction: 'up' | 'down' | 'stable';
}

export interface RiskItem {
  risk: string;
  severity: 'low' | 'medium' | 'high';
  evidence: string;
}

export interface RecommendedAction {
  action: string;
  priority: 'high' | 'medium' | 'low';
  expected_impact: string;
  feasibility: 'easy' | 'medium' | 'hard';
}

export interface RootCauseAnalysis {
  id?: number;
  observation: string;
  magnitude: string;
  root_causes: RootCause[];
  ruled_out: string[];
  conclusion: string;
  recommended_actions: string[];
  overall_confidence: number;
}

export interface RootCause {
  cause: string;
  evidence: string;
  contribution: string;
  confidence: number;
}

export interface ForecastResult {
  id?: number;
  metric: string;
  method: string;
  horizon: number;
  predictions: ForecastPrediction[];
  accuracy_score: number;
  confidence_level: number;
  assumptions: string[];
  model_limitations: string[];
  interpretation: string;
  confidence: {
    score: number;
    methodology: string;
    data_limitations: string[];
  };
}

export interface ForecastPrediction {
  date: string;
  value: number;
  lower_ci: number;
  upper_ci: number;
}

export interface AnomalyResult {
  alerts: AnomalyAlert[];
  total_anomalies: number;
  summary: string;
  explanations: AnomalyExplanation[];
  metric: string;
  sensitivity: number;
}

export interface AnomalyAlert {
  alert_type: string;
  severity: 'info' | 'warning' | 'critical';
  title: string;
  description: string;
  expected_value?: number;
  actual_value?: number;
  deviation_percentage?: number;
  explanation: string;
}

export interface AnomalyExplanation {
  alert_type: string;
  title: string;
  explanation: string;
  impact: string;
}

export interface RecommendationResult {
  recommendations: RecommendedAction[];
  industry: string;
  triggers_detected: Trigger[];
  confidence: number;
}

export interface Trigger {
  trigger: string;
  evidence: string;
}

export interface NLAnalyticsResult {
  intent: string;
  query_interpretation: string;
  analysis: {
    method: string;
    results: string;
    data_points: string[];
  };
  explanation: string;
  visualizations: {
    type: string;
    rationale: string;
  }[];
  confidence: number;
}

export interface ReportResult {
  id?: number;
  report_type: string;
  title: string;
  content: string;
  summary: string;
  sections: string[];
  methodology: string;
  appendix: string;
  format: string;
  exported?: {
    format: string;
    content?: string;
    error?: string;
  };
  created_at: string;
}

export interface AIInsight {
  id: number;
  insight_type: string;
  title: string;
  summary: string;
  details: Record<string, unknown>;
  key_findings: unknown[];
  recommendations: string[];
  risks: string[];
  opportunities: string[];
  confidence_score?: number;
  created_at: string;
}

// ─── ETL Types ───────────────────────────────────────────────

export interface Pipeline {
  id: number;
  name: string;
  description?: string;
  status: 'idle' | 'running' | 'completed' | 'failed';
  version: number;
  created_at: string;
  updated_at: string;
}

export interface PipelineJob {
  id: number;
  pipeline_id: number;
  status: 'pending' | 'running' | 'completed' | 'failed';
  started_at: string;
  completed_at?: string;
  rows_extracted: number;
  rows_transformed: number;
  rows_loaded: number;
  error_message?: string;
}

// ─── Notification Types ──────────────────────────────────────

export interface Notification {
  id: number;
  title: string;
  message: string;
  type: 'info' | 'success' | 'warning' | 'error';
  is_read: boolean;
  created_at: string;
}

// ─── Semantic Types ──────────────────────────────────────────

export interface Industry {
  key: string;
  name: string;
  description: string;
  icon?: string;
}

export interface SemanticAnalysisResult {
  industry: string;
  industry_confidence: number;
  business_entities: Record<string, unknown>;
  column_mappings: Record<string, unknown>[];
  kpi_definitions: unknown[];
  recommendations: string[];
}
