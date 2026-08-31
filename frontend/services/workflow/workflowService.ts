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
const JOBS_BASE = "/api/jobs";
const POLL_INTERVAL_MS = 2000;
const MAX_POLL_ATTEMPTS = 60; // 60 * 2s = 120s max

interface AsyncJobResponse {
  job_id: number;
  status: string;
  status_url: string;
}

interface JobPollResponse {
  id: number;
  status: string;
  progress: number;
  progress_message: string | null;
  error: string | null;
}

interface JobDetailResponse {
  id: number;
  status: string;
  progress: number;
  progress_message: string | null;
  error: string | null;
  result: Record<string, unknown> | null;
}

function isAsyncJobResponse(data: unknown): data is AsyncJobResponse {
  return (
    typeof data === "object" &&
    data !== null &&
    "job_id" in data &&
    !("workflow_id" in data)
  );
}

export const workflowService = {
  async runWorkflow(
    file: File,
    adminConfirmed = false,
    onProgress?: (message: string, progress: number) => void,
  ): Promise<WorkflowState> {
    const formData = new FormData();
    formData.append("file", file);
    const result = await apiClient.upload<WorkflowState | AsyncJobResponse>(
      `${BASE}/run?admin_confirmed=${adminConfirmed}`,
      formData,
    );

    // If the backend returned a full workflow state (synchronous mode), use it directly
    if (!isAsyncJobResponse(result)) {
      return result;
    }

    // Async mode — poll the job until it completes, then extract the workflow state
    const jobId = result.job_id;
    let attempts = 0;

    if (onProgress) {
      onProgress("Workflow queued for background processing...", 0);
    }

    while (attempts < MAX_POLL_ATTEMPTS) {
      attempts++;
      await new Promise((resolve) => setTimeout(resolve, POLL_INTERVAL_MS));

      let job: JobDetailResponse;
      try {
        job = await apiClient.get<JobDetailResponse>(`${JOBS_BASE}/${jobId}`);
      } catch {
        // Network error — keep polling
        continue;
      }

      if (job.status === "completed" && job.result) {
        if (onProgress) {
          onProgress("Workflow completed, loading results...", 1.0);
        }
        // The job result contains the full workflow state dict
        const workflowState = job.result as unknown as WorkflowState;
        if (workflowState.workflow_id) {
          return workflowState;
        }
        throw new Error("Workflow completed but no workflow_id was returned");
      }

      if (job.status === "failed") {
        throw new Error(job.error || job.progress_message || "Workflow processing failed");
      }

      if (job.status === "cancelled") {
        throw new Error("Workflow was cancelled");
      }

      // Still pending or running — report progress and continue polling
      if (onProgress && job.progress_message) {
        onProgress(job.progress_message, job.progress);
      }
    }

    throw new Error(
      `Workflow processing timed out after ${Math.round(MAX_POLL_ATTEMPTS * POLL_INTERVAL_MS / 1000)}s. The dataset may be too large or the server is overloaded.`,
    );
  },

  async getJobStatus(jobId: number): Promise<JobPollResponse> {
    return await apiClient.get<JobPollResponse>(`${JOBS_BASE}/${jobId}/poll`);
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
