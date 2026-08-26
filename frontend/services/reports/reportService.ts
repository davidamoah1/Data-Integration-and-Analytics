import { apiClient } from '../api/client';

export interface AIReport {
  id: number;
  report_type: string;
  title: string;
  summary?: string;
  created_at?: string;
}

export interface AIReportDetail extends AIReport {
  content?: string;
  sections?: unknown;
  format?: string;
}

export const reportService = {
  async listReports(reportType?: string, limit = 20): Promise<AIReport[]> {
    const params = new URLSearchParams();
    if (reportType) params.set('report_type', reportType);
    params.set('limit', String(limit));
    return apiClient.get(`/ai/reports?${params.toString()}`);
  },

  async getReport(reportId: number): Promise<AIReportDetail> {
    return apiClient.get(`/ai/reports/${reportId}`);
  },

  async exportReportUrl(reportId: number, format = 'pdf'): Promise<string> {
    const baseUrl = apiClient.getApiUrl();
    return `${baseUrl}/api/ai/reports/${reportId}/export?format=${format}`;
  },
};
