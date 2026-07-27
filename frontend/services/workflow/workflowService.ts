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
    const res = await apiClient.post(
      `${BASE}/run?admin_confirmed=${adminConfirmed}`,
      formData,
      { headers: { "Content-Type": "multipart/form-data" } }
    );
    return res.data as WorkflowState;
  },

  async getStatus(workflowId: string): Promise<WorkflowState> {
    const res = await apiClient.get(`${BASE}/${workflowId}/status`);
    return res.data as WorkflowState;
  },

  async getProfile(workflowId: string): Promise<DatasetProfile> {
    const res = await apiClient.get(`${BASE}/${workflowId}/profile`);
    return res.data as DatasetProfile;
  },

  async getQuality(workflowId: string): Promise<QualityReport> {
    const res = await apiClient.get(`${BASE}/${workflowId}/quality`);
    return res.data as QualityReport;
  },

  async getIndustry(workflowId: string): Promise<IndustryResult> {
    const res = await apiClient.get(`${BASE}/${workflowId}/industry`);
    return res.data as IndustryResult;
  },

  async getInsights(workflowId: string): Promise<InsightsResult> {
    const res = await apiClient.get(`${BASE}/${workflowId}/insights`);
    return res.data as InsightsResult;
  },

  async getDashboard(workflowId: string): Promise<DashboardRecommendation> {
    const res = await apiClient.get(`${BASE}/${workflowId}/dashboard`);
    return res.data as DashboardRecommendation;
  },

  async getSummary(workflowId: string): Promise<AnalysisSummary> {
    const res = await apiClient.get(`${BASE}/${workflowId}/summary`);
    return res.data as AnalysisSummary;
  },

  async retryStage(workflowId: string, stage: string): Promise<WorkflowState> {
    const res = await apiClient.post(`${BASE}/${workflowId}/retry/${stage}`);
    return res.data as WorkflowState;
  },
};
