// ─── Auth Types ──────────────────────────────────────────────

export interface User {
  id: number;
  email: string;
  full_name: string;
  avatar_url?: string;
  phone?: string;
  organization_id?: number;
  organization_name?: string;
  roles: string[];
  permissions: string[];
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
