import { apiClient, ApiError, getAccessToken } from "@/services/api/client";
import type {
  WorkflowState,
  DatasetProfile,
  QualityReport,
  QualityFinding,
  IndustryResult,
  InsightsResult,
  DashboardRecommendation,
  AnalysisSummary,
  AutoDashboardSpec,
  AutoPresentationSpec,
  ChartExplanation,
  CleanPreviewData,
  ProAnalysisResult,
  ReportConfig,
} from "@/types/workflow";

const BASE = "/api/dataset-workflow";
const JOBS_BASE = "/api/jobs";
const POLL_INTERVAL_MS = 2000;
const MAX_POLL_ATTEMPTS = 450; // 450 * 2s = 15 min max — enough for large datasets
const MAX_CONSECUTIVE_ERRORS = 5; // Stop after 5 consecutive network errors

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

const _INTERNAL_ERROR_PATTERNS = [
  /OperationalError/i,
  /SQLAlchemy/i,
  /PyMySQL/i,
  /psycopg2/i,
  /sqlite3/i,
  /IntegrityError/i,
  /ProgrammingError/i,
  /DBAPIError/i,
  /Traceback/i,
  /File "[^"]+"/i,
  /line \d+/i,
];

function _sanitizeErrorMessage(raw: string | null | undefined): string {
  if (!raw) return "Workflow processing failed. Please try again.";

  // Check if the error contains internal details
  const hasInternalDetails = _INTERNAL_ERROR_PATTERNS.some((p) => p.test(raw));
  if (hasInternalDetails) {
    return "We couldn't process this dataset. Please try again or contact your administrator.";
  }

  // Truncate very long errors
  if (raw.length > 200) {
    return raw.substring(0, 200) + "...";
  }

  return raw;
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
    let consecutiveErrors = 0;
    let lastProgress = 0;
    let lastProgressMessage = '';

    if (onProgress) {
      onProgress("Your dataset is waiting for a background worker.", 0);
    }

    while (attempts < MAX_POLL_ATTEMPTS) {
      attempts++;
      await new Promise((resolve) => setTimeout(resolve, POLL_INTERVAL_MS));

      let job: JobDetailResponse;
      try {
        job = await apiClient.get<JobDetailResponse>(`${JOBS_BASE}/${jobId}`);
        consecutiveErrors = 0; // Reset on successful response
      } catch (err) {
        consecutiveErrors++;

        // For auth errors (401/403), stop immediately — don't keep polling
        if (err instanceof ApiError && (err.status === 401 || err.status === 403)) {
          throw new Error("Your session has expired. Please log in again.");
        }

        // For 404, the job doesn't exist — stop polling
        if (err instanceof ApiError && err.status === 404) {
          throw new Error("The processing job could not be found. Please try uploading again.");
        }

        // If we get too many consecutive errors, show a useful message
        if (consecutiveErrors >= MAX_CONSECUTIVE_ERRORS) {
          if (onProgress) {
            onProgress(
              "Unable to check processing status. Please try again.",
              lastProgress,
            );
          }
          const errDetail = err instanceof ApiError
            ? ` (HTTP ${err.status})`
            : err instanceof Error
              ? ` (${err.message.slice(0, 80)})`
              : "";
          throw new Error(
            `Unable to check processing status after ${consecutiveErrors} attempts${errDetail}. The server may be unreachable. Please try again.`,
          );
        }

        // For server errors (500/502/503), continue polling but warn
        if (consecutiveErrors === 1 && onProgress) {
          onProgress(
            "Checking processing status... (experiencing connectivity issues)",
            lastProgress,
          );
        }
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
        const userError = _sanitizeErrorMessage(job.error || job.progress_message);
        throw new Error(userError);
      }

      if (job.status === "cancelled") {
        throw new Error("Workflow was cancelled");
      }

      // Still pending or running — report progress and continue polling
      if (job.progress > lastProgress || job.progress_message !== lastProgressMessage) {
        lastProgress = job.progress;
        lastProgressMessage = job.progress_message || '';
      }
      if (onProgress) {
        const message = job.progress_message || (
          job.status === "pending"
            ? "Your dataset is waiting for a background worker."
            : "Processing your dataset..."
        );
        onProgress(message, job.progress);
      }

      // If pending for more than 5 minutes (150 attempts), warn the user
      if (job.status === "pending" && attempts === 150) {
        if (onProgress) {
          onProgress(
            "Processing is taking longer than expected. We are checking the background processing service.",
            job.progress,
          );
        }
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

  async undoCleaningTransformation(
    workflowId: string,
    transformationId: string,
  ): Promise<{ success: boolean; message: string }> {
    return await apiClient.post(`${BASE}/${workflowId}/clean/undo`, {
      transformation_id: transformationId,
    });
  },

  async applyAllCleaningTransformations(
    workflowId: string,
    findings?: QualityFinding[],
  ): Promise<{ applied_count: number; transformations: Array<Record<string, unknown>> }> {
    return await apiClient.post(`${BASE}/${workflowId}/clean/apply-all`, {
      findings: findings || null,
    });
  },

  async getCleaningPreview(
    workflowId: string,
    limit = 20,
  ): Promise<CleanPreviewData> {
    return await apiClient.get<CleanPreviewData>(
      `${BASE}/${workflowId}/clean/preview?limit=${limit}`,
    );
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
  ): Promise<any> {
    return await apiClient.post(`${BASE}/${workflowId}/analyze`, payload);
  },

  async runProAnalysis(
    workflowId: string,
    analysisType: string,
    columns?: string[],
    groupColumn?: string,
    targetColumn?: string,
  ): Promise<ProAnalysisResult> {
    const res = await apiClient.post<{ mode: string; analysis_type: string; result: ProAnalysisResult }>(
      `${BASE}/${workflowId}/analyze`,
      {
        mode: "pro",
        analysis_type: analysisType,
        columns,
        group_column: groupColumn,
        target_column: targetColumn,
      },
    );
    return res.result;
  },

  async askDatasetQuestion(
    workflowId: string,
    question: string,
  ): Promise<{ question: string; answer: string; insights: InsightsResult["insights"] }> {
    return await apiClient.post(`${BASE}/${workflowId}/analyze`, {
      mode: "easy",
      question,
    });
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

  async generateReportPdf(
    workflowId: string,
    config?: ReportConfig,
    autoDownload = true,
  ): Promise<Blob> {
    const apiUrl = apiClient.getApiUrl();
    const token = getAccessToken();
    const response = await fetch(`${apiUrl}${BASE}/${workflowId}/report`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify(config || {}),
    });

    if (!response.ok) {
      const errText = await response.text().catch(() => "");
      throw new Error(`Report generation failed (${response.status}): ${errText || response.statusText}`);
    }

    const blob = await response.blob();
    if (autoDownload && typeof window !== "undefined") {
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      const safeTitle = (config?.title || "Dataset_Analysis").replace(/[^a-zA-Z0-9_-]/g, "_");
      a.download = `${safeTitle}_Audit_Report.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    }
    return blob;
  },

  async generatePresentation(
    workflowId: string,
    template: string = "executive",
    title?: string,
    autoDownload = true,
  ): Promise<Blob> {
    const apiUrl = apiClient.getApiUrl();
    const token = getAccessToken();
    const response = await fetch(`${apiUrl}${BASE}/${workflowId}/presentation`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({ template, title }),
    });

    if (!response.ok) {
      const errText = await response.text().catch(() => "");
      throw new Error(`Presentation generation failed (${response.status}): ${errText || response.statusText}`);
    }

    const blob = await response.blob();
    if (autoDownload && typeof window !== "undefined") {
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      const safeTitle = (title || "Dataset_Presentation").replace(/[^a-zA-Z0-9_-]/g, "_");
      a.download = `${safeTitle}_Presentation.pptx`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    }
    return blob;
  },
};
