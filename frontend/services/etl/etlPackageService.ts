import { apiClient, getAccessToken } from '../api/client';

export interface ETLPackage {
  id: number;
  filename: string;
  status: string;
  current_stage: string | null;
  total_files: number;
  completed_files: number;
  failed_files: number;
  duplicate_files: number;
  unsupported_files: number;
  file_size_bytes: number;
  overall_quality_score: number | null;
  created_at: string;
  completed_at: string | null;
}

export interface ETLPackageProgress {
  package_id: number;
  filename: string;
  status: string;
  current_stage: string | null;
  total_files: number;
  discovered_files: number;
  queued_files: number;
  processing_files: number;
  completed_files: number;
  failed_files: number;
  duplicate_files: number;
  skipped_files: number;
  unsupported_files: number;
  percentage: number;
  total_rows_extracted: number;
  total_rows_loaded: number;
  total_rows_rejected: number;
  overall_quality_score: number | null;
  started_at: string | null;
  completed_at: string | null;
  error_message: string | null;
}

export interface ETLPackageFile {
  id: number;
  filename: string;
  original_path: string;
  extension: string;
  size: number | null;
  status: string;
  stage: string | null;
  row_count: number | null;
  column_count: number | null;
  quality_score: number | null;
  error_message: string | null;
  error_stage: string | null;
  retry_count: number;
  target_table: string | null;
  rows_loaded: number | null;
  completed_at: string | null;
}

export interface ETLPackageError {
  file_id: number;
  filename: string;
  original_path: string;
  error_message: string;
  error_stage: string | null;
  retry_count: number;
}

export interface ETLPackageQualityReport {
  package_id: number;
  filename: string;
  total_files: number;
  successful: number;
  failed: number;
  duplicates: number;
  unsupported: number;
  datasets_created: number;
  rows_processed: number;
  rows_loaded: number;
  data_quality_score: number | null;
  transformations_applied: string;
  warnings: string[];
  errors: Array<{ file: string; error: string }>;
}

export interface ETLPackageUploadResponse {
  package_id: number;
  job_id: number;
  filename: string;
  status: string;
  file_count: number;
  checksum: string;
  message: string;
}

export const etlPackageService = {
  async upload(file: File, onProgress?: (percent: number) => void): Promise<ETLPackageUploadResponse> {
    const formData = new FormData();
    formData.append('file', file);
    return apiClient.uploadWithProgress('/api/etl/packages', formData, onProgress, {
      timeout: 300000, // 5 min — upload only, not processing
    });
  },

  async list(
    limit = 50,
    offset = 0,
    filters?: { status?: string; search?: string },
  ): Promise<{ packages: ETLPackage[]; count: number }> {
    const params = new URLSearchParams();
    params.set('limit', String(limit));
    params.set('offset', String(offset));
    if (filters?.status) params.set('status', filters.status);
    if (filters?.search) params.set('search', filters.search);
    return apiClient.get(`/api/etl/packages?${params.toString()}`);
  },

  async get(packageId: number): Promise<ETLPackage> {
    return apiClient.get(`/api/etl/packages/${packageId}`);
  },

  async getProgress(packageId: number): Promise<ETLPackageProgress> {
    return apiClient.get(`/api/etl/packages/${packageId}/progress`, {
      timeout: 15000, // Short timeout for polling — fail fast to trigger backoff
    });
  },

  async getFiles(
    packageId: number,
    filters?: { status?: string; limit?: number; offset?: number },
  ): Promise<{ files: ETLPackageFile[]; count: number }> {
    const params = new URLSearchParams();
    if (filters?.status) params.set('status', filters.status);
    if (filters?.limit) params.set('limit', String(filters.limit));
    if (filters?.offset) params.set('offset', String(filters.offset));
    const qs = params.toString();
    return apiClient.get(`/api/etl/packages/${packageId}/files${qs ? `?${qs}` : ''}`);
  },

  async getErrors(packageId: number): Promise<{ package_id: number; errors: ETLPackageError[]; count: number }> {
    return apiClient.get(`/api/etl/packages/${packageId}/errors`);
  },

  async getQualityReport(packageId: number): Promise<ETLPackageQualityReport> {
    return apiClient.get(`/api/etl/packages/${packageId}/quality`);
  },

  async retryFailed(packageId: number): Promise<{ package_id: number; retried: number }> {
    return apiClient.post(`/api/etl/packages/${packageId}/retry-failed`);
  },

  async cancel(packageId: number): Promise<{ package_id: number; cancelled: boolean }> {
    return apiClient.post(`/api/etl/packages/${packageId}/cancel`);
  },

  getDownloadUrl(packageId: number): string {
    return apiClient.getApiUrl() + `/api/etl/packages/${packageId}/download`;
  },

  async download(packageId: number): Promise<Blob> {
    const token = getAccessToken();
    const url = apiClient.getApiUrl() + `/api/etl/packages/${packageId}/download`;
    const response = await fetch(url, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    if (!response.ok) {
      throw new Error(`Download failed: ${response.status}`);
    }
    return response.blob();
  },
};
