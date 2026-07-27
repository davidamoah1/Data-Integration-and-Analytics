export interface WorkflowStageResult {
  stage: string;
  status: "pending" | "running" | "completed" | "failed" | "skipped";
  started_at: string;
  completed_at: string;
  duration_seconds: number;
  result: Record<string, unknown>;
  error: string | null;
  retries: number;
}

export interface WorkflowState {
  workflow_id: string;
  dataset_name: string;
  current_stage: string;
  stages: Record<string, WorkflowStageResult>;
  created_at: string;
  updated_at: string;
  is_complete: boolean;
  has_errors: boolean;
}

export interface ColumnProfile {
  name: string;
  dtype: string;
  count: number;
  null_count: number;
  null_percentage: number;
  unique_count: number;
  uniqueness: number;
  cardinality: string;
  min_value: number | null;
  max_value: number | null;
  mean_value: number | null;
  median_value: number | null;
  std_value: number | null;
  q1: number | null;
  q3: number | null;
  iqr: number | null;
  outlier_count: number;
  skewness: number | null;
  kurtosis: number | null;
  date_range: string[] | null;
  top_values: Record<string, number>;
  value_distribution: Record<string, number>;
  pattern: string;
  pattern_consistency: number;
  completeness: number;
  consistency: number;
  validity: number;
  quality_score: number;
  is_sensitive: boolean;
  sensitive_type: string;
  pk_score: number;
}

export interface DatasetProfile {
  source_name: string;
  profiled_at: string;
  row_count: number;
  column_count: number;
  duplicate_rows: number;
  duplicate_percentage: number;
  total_missing: number;
  missing_percentage: number;
  total_outliers: number;
  memory_mb: number;
  overall_completeness: number;
  overall_consistency: number;
  overall_uniqueness: number;
  overall_validity: number;
  overall_quality_score: number;
  columns: ColumnProfile[];
  correlations: Array<{
    column_1: string;
    column_2: string;
    correlation: number;
    strength: string;
    direction: string;
  }>;
  sensitive_columns: string[];
  candidate_primary_keys: string[];
  quality_issues: Array<{
    column: string;
    severity: string;
    issue: string;
    detail: string;
    recommended_fix: string;
  }>;
  distribution_summary: Record<string, {
    mean: number;
    median: number;
    std: number;
    skewness: number;
    kurtosis: number;
    distribution_type: string;
  }>;
}

export interface QualityFinding {
  check_name: string;
  category: string;
  severity: string;
  column: string | null;
  affected_rows: number;
  affected_pct: number;
  message: string;
  suggested_fix: string;
  business_impact: string;
  sample_values: unknown[];
}

export interface QualityReport {
  findings: QualityFinding[];
  drift: unknown;
  schema_changes: unknown;
  score: {
    completeness: number;
    validity: number;
    uniqueness: number;
    consistency: number;
    timeliness: number;
    overall: number;
    traffic_light: string;
    grade: string;
  } | null;
  summary: string;
  recommendations: string[];
  error_count: number;
  warning_count: number;
  info_count: number;
  checked_at: string;
}

export interface IndustryResult {
  industry: string;
  confidence: number;
  detected_entities: string[];
  alternative_candidates: Array<{ industry: string; votes: number }>;
  needs_confirmation: boolean;
}

export interface Insight {
  type: string;
  severity: string;
  title: string;
  description: string;
  metric: string | null;
  value: number | null;
  recommendation: string;
}

export interface InsightsResult {
  insights: Insight[];
  executive_summary: string;
  total_insights: number;
}

export interface DashboardRecommendation {
  recommended: boolean;
  needs_confirmation: boolean;
  confirmation_reason: string;
  industry: string;
  industry_confidence: number;
  reasoning: string;
  available_measures: Array<{ column: string; entity: string; display: string; confidence: number }>;
  available_dimensions: Array<{ column: string; entity: string; display: string; confidence: number }>;
  time_fields: Array<{ column: string; display: string; is_datetime: boolean }>;
  geo_fields: Array<{ column: string; entity: string; display: string }>;
  available_templates: Array<{ industry: string; name: string; kpi_count: number; chart_count: number }>;
  recommended_charts: Array<{
    type: string;
    title: string;
    reasoning: string;
    [key: string]: unknown;
  }>;
  dashboard_config: Record<string, unknown> | null;
  actions: Record<string, string>;
}

export interface AnalysisSummary {
  dataset_name: string;
  row_count: number;
  column_count: number;
  quality_score: number;
  industry: string;
  industry_confidence: number;
  total_insights: number;
  dashboard_recommended: boolean;
  dashboard_title: string;
}
