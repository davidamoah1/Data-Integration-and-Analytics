import { apiClient } from "@/services/api/client";
import type {
  WorkflowState,
  DatasetProfile,
  QualityReport,
  IndustryResult,
  InsightsResult,
  DashboardRecommendation,
  AnalysisSummary,
  AutoDashboardSpec,
  AutoPresentationSpec,
  ChartExplanation,
} from "@/types/workflow";

const BASE = "/api/dataset-workflow";

export const workflowService = {
  async runWorkflow(file: File, adminConfirmed = false): Promise<WorkflowState> {
    const formData = new FormData();
    formData.append("file", file);
    return await apiClient.upload<WorkflowState>(
      `${BASE}/run?admin_confirmed=${adminConfirmed}`,
      formData,
    );
  },

  async getStatus(workflowId: string): Promise<WorkflowState> {
    return await apiClient.get<WorkflowState>(`${BASE}/${workflowId}/status`);
  },

  async getProfile(workflowId: string): Promise<DatasetProfile> {
    return await apiClient.get<DatasetProfile>(`${BASE}/${workflowId}/profile`);
  },

  async getQuality(workflowId: string): Promise<QualityReport> {
    return await apiClient.get<QualityReport>(`${BASE}/${workflowId}/quality`);
  },

  async getIndustry(workflowId: string): Promise<IndustryResult> {
    return await apiClient.get<IndustryResult>(`${BASE}/${workflowId}/industry`);
  },

  async getInsights(workflowId: string): Promise<InsightsResult> {
    return await apiClient.get<InsightsResult>(`${BASE}/${workflowId}/insights`);
  },

  async getDashboard(workflowId: string): Promise<DashboardRecommendation> {
    return await apiClient.get<DashboardRecommendation>(`${BASE}/${workflowId}/dashboard`);
  },

  async getSummary(workflowId: string): Promise<AnalysisSummary> {
    return await apiClient.get<AnalysisSummary>(`${BASE}/${workflowId}/summary`);
  },

  async retryStage(workflowId: string, stage: string): Promise<WorkflowState> {
    return await apiClient.post<WorkflowState>(`${BASE}/${workflowId}/retry/${stage}`);
  },

  async applyCleaningTransformation(
    workflowId: string,
    payload: {
      check_name: string;
      column?: string;
      action: string;
      method?: string;
      value?: string;
    },
  ): Promise<{ id: string; description: string; affected_rows: number }> {
    return await apiClient.post(`${BASE}/${workflowId}/clean/apply`, payload);
  },

  async getCleaningHistory(
    workflowId: string,
  ): Promise<{ transformations: Array<{ id: string; timestamp: string; action: string; description: string; affected_rows: number; undone: boolean }>; total: number; active: number }> {
    return await apiClient.get(`${BASE}/${workflowId}/clean/history`);
  },

  async runAnalysis(
    workflowId: string,
    payload: {
      mode: 'easy' | 'pro';
      analysis_type?: string;
      columns?: string[];
      group_column?: string;
      target_column?: string;
      question?: string;
    },
  ): Promise<unknown> {
    return await apiClient.post(`${BASE}/${workflowId}/analyze`, payload);
  },

  async getUnderstanding(workflowId: string): Promise<Record<string, unknown>> {
    return await apiClient.get<Record<string, unknown>>(`${BASE}/${workflowId}/understanding`);
  },

  async getAutoDashboard(workflowId: string): Promise<AutoDashboardSpec> {
    return await apiClient.get<AutoDashboardSpec>(`${BASE}/${workflowId}/auto-dashboard`);
  },

  async getAutoPresentation(workflowId: string): Promise<AutoPresentationSpec> {
    return await apiClient.get<AutoPresentationSpec>(`${BASE}/${workflowId}/auto-presentation`);
  },

  async explainChart(workflowId: string, chartId: string): Promise<ChartExplanation> {
    return await apiClient.get<ChartExplanation>(`${BASE}/${workflowId}/charts/${chartId}/explain`);
  },

  async generatePresentation(
    workflowId: string,
    template: string = "executive",
    title?: string,
  ): Promise<Blob> {
    return await apiClient.post(`${BASE}/${workflowId}/presentation`, { template, title });
  },
};
