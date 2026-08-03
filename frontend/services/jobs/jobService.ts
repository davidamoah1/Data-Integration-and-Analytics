"use client";

import { apiClient } from "@/services/api/client";

// ─── Types ──────────────────────────────────────────────────────

export type JobStatus = "pending" | "running" | "completed" | "failed" | "cancelled";
export type JobType = "etl_run" | "ocr_batch" | "report_gen" | "data_import" | "export" | "custom";

export interface Job {
  id: number;
  organization_id: number;
  user_id: number | null;
  job_type: string;
  name: string;
  description: string | null;
  status: JobStatus;
  progress: number;
  progress_message: string | null;
  payload: Record<string, unknown> | null;
  result: Record<string, unknown> | null;
  error: string | null;
  retries: number;
  max_retries: number;
  queue_task_id: string | null;
  created_at: string | null;
  started_at: string | null;
  completed_at: string | null;
  duration_seconds: number | null;
}

export interface JobPollResponse {
  id: number;
  status: JobStatus;
  progress: number;
  progress_message: string | null;
  error: string | null;
}

export interface JobSummary {
  total: number;
  pending: number;
  running: number;
  completed: number;
  failed: number;
  cancelled: number;
}

export interface JobListResponse {
  jobs: Job[];
  count: number;
}

export interface CreateJobPayload {
  job_type: string;
  name: string;
  description?: string;
  payload?: Record<string, unknown>;
  max_retries?: number;
}

// ─── Service ────────────────────────────────────────────────────

const BASE = "/api/jobs";

export const jobService = {
  listJobs: (params?: {
    status?: JobStatus;
    job_type?: string;
    limit?: number;
    offset?: number;
  }) => apiClient.get<JobListResponse>(BASE, { params }),

  getJob: (jobId: number) => apiClient.get<Job>(`${BASE}/${jobId}`),

  pollJob: (jobId: number) => apiClient.get<JobPollResponse>(`${BASE}/${jobId}/poll`),

  createJob: (payload: CreateJobPayload) => apiClient.post<Job>(BASE, payload),

  cancelJob: (jobId: number) => apiClient.post<Job>(`${BASE}/${jobId}/cancel`),

  retryJob: (jobId: number) => apiClient.post<Job>(`${BASE}/${jobId}/retry`),

  listActiveJobs: () => apiClient.get<JobListResponse>(`${BASE}/active`),

  getSummary: () => apiClient.get<JobSummary>(`${BASE}/summary`),

  getJobTypes: () => apiClient.get<{ types: string[] }>(`${BASE}/types`),
};
