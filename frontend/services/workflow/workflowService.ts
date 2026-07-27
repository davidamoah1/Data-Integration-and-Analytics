import { apiClient } from "@/services/api/client";
import type {
  WorkflowState,
  DatasetProfile,
  QualityReport,
  IndustryResult,
  InsightsResult,
  DashboardRecommendation,
  AnalysisSummary,
} from "@/types/workflow";

const BASE = "/dataset-workflow";

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
};
