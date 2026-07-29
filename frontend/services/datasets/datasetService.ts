import { apiClient } from '../api/client';
import type { Dataset, DatasetPreview, DatasetSchema } from '@/types';

export const datasetService = {
  async list(filters?: { tier?: string; industry?: string; limit?: number }): Promise<{ datasets: Dataset[]; count: number }> {
    const params = new URLSearchParams();
    if (filters?.tier) params.set('tier', filters.tier);
    if (filters?.industry) params.set('industry', filters.industry);
    if (filters?.limit) params.set('limit', String(filters.limit));
    const qs = params.toString();
    return apiClient.get(`/datasets/${qs ? `?${qs}` : ''}`);
  },

  async get(datasetId: string): Promise<Dataset> {
    return apiClient.get(`/datasets/${datasetId}`);
  },

  async preview(datasetId: string, rows = 10): Promise<DatasetPreview> {
    return apiClient.get(`/datasets/${datasetId}/preview?rows=${rows}`);
  },

  async schema(datasetId: string): Promise<DatasetSchema> {
    return apiClient.get(`/datasets/${datasetId}/schema`);
  },

  async registerUpload(payload: {
    name: string;
    description?: string;
    industry?: string;
    file_path: string;
    row_count: number;
    column_count: number;
  }): Promise<Dataset> {
    return apiClient.post('/datasets/production/upload', payload);
  },

  async remove(datasetId: string): Promise<void> {
    await apiClient.delete(`/datasets/${datasetId}`);
  },

  async listIndustries(): Promise<{ industries: { key: string; name: string }[] }> {
    return apiClient.get('/datasets/industries/list');
  },

  async listTiers(): Promise<{ tiers: { key: string; name: string }[] }> {
    return apiClient.get('/datasets/tiers/list');
  },

  async uploadFile(file: File): Promise<unknown> {
    const formData = new FormData();
    formData.append('file', file);
    return apiClient.upload('/etl/import/upload', formData);
  },

  async semanticAnalyze(file: File): Promise<unknown> {
    const formData = new FormData();
    formData.append('file', file);
    return apiClient.upload('/semantic/analyze', formData);
  },

  async semanticAnalyzeWithOverrides(
    file: File,
    overrides?: Record<string, string>,
    adminConfirmed?: boolean,
    forceIndustry?: string,
  ): Promise<unknown> {
    const formData = new FormData();
    formData.append('file', file);
    if (overrides) formData.append('overrides', JSON.stringify(overrides));
    if (forceIndustry) formData.append('force_industry', forceIndustry);
    const params = new URLSearchParams();
    if (adminConfirmed) params.set('admin_confirmed', 'true');
    const qs = params.toString();
    return apiClient.upload(`/semantic/analyze-with-overrides${qs ? `?${qs}` : ''}`, formData);
  },

  async detectIndustry(file: File): Promise<unknown> {
    const formData = new FormData();
    formData.append('file', file);
    return apiClient.upload('/semantic/detect-industry', formData);
  },

  async validateFile(file: File): Promise<unknown> {
    const formData = new FormData();
    formData.append('file', file);
    return apiClient.upload('/validation/run', formData);
  },

  async persistAnalysis(payload: {
    table_name: string;
    industry?: string;
    dashboard_config?: Record<string, unknown> | null;
    kpis?: Array<Record<string, unknown>>;
    recommendations?: string[];
    alerts?: Array<Record<string, unknown>>;
  }): Promise<{ dashboard_id: number | null; kpi_ids: number[]; report_id: number | null; message: string }> {
    return apiClient.post('/semantic/persist-analysis', payload);
  },
};
