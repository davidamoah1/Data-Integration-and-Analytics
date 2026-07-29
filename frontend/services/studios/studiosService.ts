/** Studios API service — Data Intelligence Operating System. */

import { apiClient } from '../api/client';

// ─── Types ──────────────────────────────────────────────────────

export interface DataWorkspace {
  id: number;
  name: string;
  description?: string;
  dataset_id?: number;
  columns_config?: any[];
  filters?: any[];
  sort_config?: any[];
  conditional_formatting?: any[];
  pivot_config?: any;
  created_at?: string;
  updated_at?: string;
}

export interface CleaningJob {
  id: number;
  dataset_id: number;
  status: string;
  issues_found?: any[];
  transformations?: any[];
  summary?: any;
  created_at?: string;
}

export interface StatisticalAnalysis {
  id: number;
  dataset_id: number;
  analysis_type: string;
  test_name?: string;
  parameters?: any;
  results?: any;
  interpretation?: string;
  assumptions?: string[];
  limitations?: string;
  created_at?: string;
}

export interface MLExperiment {
  id: number;
  name: string;
  dataset_id: number;
  task_type: string;
  algorithm?: string;
  features?: string[];
  target?: string;
  metrics?: any;
  feature_importance?: Record<string, number>;
  model_summary?: string;
  status: string;
  created_at?: string;
}

export interface ResearchProject {
  id: number;
  title: string;
  research_question?: string;
  methodology?: string;
  status: string;
  industry?: string;
  created_at?: string;
}

export interface Presentation {
  id: number;
  title: string;
  source_type: string;
  source_id?: number;
  slides?: any[];
  template: string;
  format: string;
  is_generated: boolean;
  created_at?: string;
}

export interface IndustryOverview {
  industry: string;
  kpi_count: number;
  template_count: number;
  kpis: any[];
  templates: any[];
}

export interface ChartRecommendation {
  chart_type: string;
  chart_category: string;
  title: string;
  reasoning: string;
  config: any;
  data_summary?: any;
}

export interface MentorProfile {
  mentor_type: string;
  name: string;
  description: string;
  capabilities: string[];
  suggested_questions: string[];
}

export interface MentorSession {
  id: number;
  mentor_type: string;
  title: string;
  created_at?: string;
}

// ─── Workspace ──────────────────────────────────────────────────

export const workspaceService = {
  list: () => apiClient.get<{ workspaces: DataWorkspace[] }>('/api/studios/workspaces'),
  get: (id: number) => apiClient.get<DataWorkspace>(`/api/studios/workspaces/${id}`),
  create: (data: { name: string; dataset_id?: number; description?: string }) =>
    apiClient.post<{ id: number; name: string }>('/api/studios/workspaces', data),
  updateConfig: (id: number, data: any) =>
    apiClient.put<{ updated: boolean }>(`/api/studios/workspaces/${id}/config`, data),
  addCalculatedColumn: (id: number, data: { column_name: string; formula: string; data_type?: string }) =>
    apiClient.post<{ id: number; column_name: string }>(`/api/studios/workspaces/${id}/columns`, data),
  aiSuggestFormula: (description: string, available_columns: string[]) =>
    apiClient.post<{ suggestions: any[] }>('/api/studios/workspaces/ai-suggest-formula', { description, available_columns }),
};

// ─── Cleaning ───────────────────────────────────────────────────

export const cleaningService = {
  list: () => apiClient.get<{ jobs: CleaningJob[] }>('/api/studios/cleaning/jobs'),
  get: (id: number) => apiClient.get<CleaningJob>(`/api/studios/cleaning/jobs/${id}`),
  create: (dataset_id: number) =>
    apiClient.post<{ id: number; status: string }>('/api/studios/cleaning/jobs', { dataset_id }),
};

// ─── Statistics ─────────────────────────────────────────────────

export const statisticsService = {
  list: (dataset_id?: number) =>
    apiClient.get<{ analyses: StatisticalAnalysis[] }>(`/api/studios/statistics/analyses${dataset_id ? `?dataset_id=${dataset_id}` : ''}`),
  get: (id: number) => apiClient.get<StatisticalAnalysis>(`/api/studios/statistics/analyses/${id}`),
};

// ─── ML Lab ─────────────────────────────────────────────────────

export const mlLabService = {
  list: (dataset_id?: number) =>
    apiClient.get<{ experiments: MLExperiment[] }>(`/api/studios/ml/experiments${dataset_id ? `?dataset_id=${dataset_id}` : ''}`),
  get: (id: number) => apiClient.get<MLExperiment>(`/api/studios/ml/experiments/${id}`),
  create: (data: {
    dataset_id: number;
    name: string;
    task_type: string;
    features?: string[];
    target?: string;
    algorithm?: string;
  }) => apiClient.post<{ id: number; name: string; status: string }>('/api/studios/ml/experiments', data),
};

// ─── Research ───────────────────────────────────────────────────

export const researchService = {
  list: () => apiClient.get<{ projects: ResearchProject[] }>('/api/studios/research/projects'),
  get: (id: number) => apiClient.get<ResearchProject>(`/api/studios/research/projects/${id}`),
  create: (data: { title: string; research_question?: string; industry?: string }) =>
    apiClient.post<{ id: number; title: string }>('/api/studios/research/projects', data),
  createHypothesis: (projectId: number, data: { hypothesis: string; test_type?: string }) =>
    apiClient.post<{ id: number }>(`/api/studios/research/projects/${projectId}/hypotheses`, data),
  suggestDesign: (research_question: string, industry?: string) =>
    apiClient.post<any>('/api/studios/research/suggest-design', { research_question, industry }),
  generateHypotheses: (research_question: string, variables: string[]) =>
    apiClient.post<{ hypotheses: any[] }>('/api/studios/research/generate-hypotheses', { research_question, variables }),
};

// ─── Presentations ──────────────────────────────────────────────

export const presentationService = {
  list: () => apiClient.get<{ presentations: Presentation[] }>('/api/studios/presentations'),
  get: (id: number) => apiClient.get<Presentation>(`/api/studios/presentations/${id}`),
  create: (data: { title: string; source_type: string; source_id?: number; template?: string }) =>
    apiClient.post<{ id: number; title: string }>('/api/studios/presentations', data),
};

// ─── Industry Intelligence ──────────────────────────────────────

export const industryService = {
  list: () => apiClient.get<{ industries: string[] }>('/api/studios/industries'),
  overview: (industry: string) =>
    apiClient.get<IndustryOverview>(`/api/studios/industries/${industry}/overview`),
  kpis: (industry: string) =>
    apiClient.get<{ kpis: any[] }>(`/api/studios/industries/${industry}/kpis`),
  templates: (industry: string) =>
    apiClient.get<{ templates: any[] }>(`/api/studios/industries/${industry}/templates`),
  recommend: (industry: string, available_columns: string[]) =>
    apiClient.post<{ recommendations: any[] }>('/api/studios/industries/recommend', { industry, available_columns }),
};

// ─── Visualization ──────────────────────────────────────────────

export const visualizationService = {
  recommend: (data: any[], columns?: string[], intent?: string) =>
    apiClient.post<ChartRecommendation>('/api/studios/visualizations/recommend', { data, columns, intent }),
  recommendMultiple: (data: any[], max_charts?: number) =>
    apiClient.post<{ recommendations: ChartRecommendation[] }>('/api/studios/visualizations/recommend-multiple', { data, max_charts }),
};

// ─── AI Mentors ─────────────────────────────────────────────────

export const mentorService = {
  list: () => apiClient.get<{ mentors: MentorProfile[] }>('/api/studios/mentors'),
  getProfile: (mentor_type: string) =>
    apiClient.get<MentorProfile>(`/api/studios/mentors/${mentor_type}`),
  createSession: (mentor_type: string, title?: string, context?: any) =>
    apiClient.post<{ id: number; title: string }>('/api/studios/mentors/sessions', { mentor_type, title, context }),
  listSessions: () =>
    apiClient.get<{ sessions: MentorSession[] }>('/api/studios/mentors/sessions'),
  sendMessage: (session_id: number, content: string) =>
    apiClient.post<{ response: string; messages: any[] }>(`/api/studios/mentors/sessions/${session_id}/messages`, { content }),
};

// ─── Collaboration ──────────────────────────────────────────────

export const collaborationService = {
  addComment: (data: {
    resource_type: string;
    resource_id: number;
    content: string;
    parent_id?: number;
  }) => apiClient.post<{ id: number }>('/api/studios/collaboration/comments', data),
  listComments: (resource_type: string, resource_id: number) =>
    apiClient.get<{ comments: any[] }>(`/api/studios/collaboration/comments?resource_type=${resource_type}&resource_id=${resource_id}`),
  share: (data: {
    resource_type: string;
    resource_id: number;
    shared_with_user_id?: number;
    shared_with_role?: string;
    permission?: string;
  }) => apiClient.post<{ id: number }>('/api/studios/collaboration/share', data),
  listShares: (resource_type: string, resource_id: number) =>
    apiClient.get<{ shares: any[] }>(`/api/studios/collaboration/shares?resource_type=${resource_type}&resource_id=${resource_id}`),
};
