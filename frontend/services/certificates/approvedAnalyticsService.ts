"use client";

import { apiClient, getAccessToken } from "@/services/api/client";

const BASE = "/api/certificates/approved-analytics";

export interface ApprovedKPIs {
  total_approved: number;
  unique_recipients: number;
  certificate_types: number;
  certificate_names: number;
  issuing_organizations: number;
  courses: number;
  avg_certs_per_person: number;
  completed_this_month: number;
  completed_this_year: number;
  latest_completion_date: string | null;
  earliest_completion_date: string | null;
}

export interface ApprovedDataQuality {
  total: number;
  recipient_identified: number;
  certificate_name_identified: number;
  completion_date_identified: number;
  institution_identified: number;
  certificate_number_identified: number;
  course_identified: number;
}

export interface ApprovedAnalyticsSummary {
  kpis: ApprovedKPIs;
  data_quality: ApprovedDataQuality;
  by_name: Record<string, number>;
  by_type: Record<string, number>;
  by_issuer: Record<string, number>;
  by_course: Record<string, number>;
  trends: Record<string, number>;
  recipients: { name: string; approved_certificates: number }[];
  certs_per_person: Record<string, number>;
  insights: string[];
  total: number;
}

export interface ApprovedCertificateRecord {
  id: number;
  recipient: string;
  certificate_name: string;
  certificate_type: string;
  course: string;
  issuing_organization: string;
  completion_date: string;
  certificate_number: string;
  verification_status: string;
  approved_at: string | null;
  batch_id: number | null;
  filename: string;
}

export interface ApprovedRecordsResult {
  records: ApprovedCertificateRecord[];
  total: number;
  limit: number;
  offset: number;
}

export interface ApprovedFilterOptions {
  certificate_names: string[];
  certificate_types: string[];
  issuing_organizations: string[];
  courses: string[];
  recipients: string[];
}

export interface ApprovedAnalyticsFilters {
  certificate_name?: string;
  certificate_type?: string;
  issuing_organization?: string;
  course?: string;
  recipient?: string;
  date_from?: string;
  date_to?: string;
  year?: number;
}

function buildParams(filters?: ApprovedAnalyticsFilters): Record<string, string> {
  const params: Record<string, string> = {};
  if (filters) {
    if (filters.certificate_name) params.certificate_name = filters.certificate_name;
    if (filters.certificate_type) params.certificate_type = filters.certificate_type;
    if (filters.issuing_organization) params.issuing_organization = filters.issuing_organization;
    if (filters.course) params.course = filters.course;
    if (filters.recipient) params.recipient = filters.recipient;
    if (filters.date_from) params.date_from = filters.date_from;
    if (filters.date_to) params.date_to = filters.date_to;
    if (filters.year) params.year = String(filters.year);
  }
  return params;
}

export const approvedAnalyticsService = {
  getSummary: (filters?: ApprovedAnalyticsFilters) =>
    apiClient.get<ApprovedAnalyticsSummary>(`${BASE}/summary`, { params: buildParams(filters) }),

  getRecords: (params?: ApprovedAnalyticsFilters & {
    search?: string;
    sort_by?: string;
    sort_order?: string;
    limit?: number;
    offset?: number;
  }) => {
    const p: Record<string, string> = buildParams(params);
    if (params?.search) p.search = params.search;
    if (params?.sort_by) p.sort_by = params.sort_by;
    if (params?.sort_order) p.sort_order = params.sort_order;
    if (params?.limit) p.limit = String(params.limit);
    if (params?.offset) p.offset = String(params.offset);
    return apiClient.get<ApprovedRecordsResult>(`${BASE}/records`, { params: p });
  },

  getFilters: () =>
    apiClient.get<ApprovedFilterOptions>(`${BASE}/filters`),

  exportCsv: async (filters?: ApprovedAnalyticsFilters) => {
    const apiUrl = apiClient.getApiUrl();
    const token = getAccessToken();
    const params = new URLSearchParams(buildParams(filters));
    const qs = params.toString();
    const response = await fetch(
      `${apiUrl}${BASE}/export/csv${qs ? `?${qs}` : ""}`,
      { headers: { Authorization: `Bearer ${token}` } }
    );
    if (!response.ok) throw new Error(`Export failed: ${response.status}`);
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "approved_certificates.csv";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  },

  exportXlsx: async (filters?: ApprovedAnalyticsFilters) => {
    const apiUrl = apiClient.getApiUrl();
    const token = getAccessToken();
    const params = new URLSearchParams(buildParams(filters));
    const qs = params.toString();
    const response = await fetch(
      `${apiUrl}${BASE}/export/xlsx${qs ? `?${qs}` : ""}`,
      { headers: { Authorization: `Bearer ${token}` } }
    );
    if (!response.ok) throw new Error(`Export failed: ${response.status}`);
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "approved_certificates.xlsx";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  },

  getReport: (filters?: ApprovedAnalyticsFilters) =>
    apiClient.get<ApprovedAnalyticsSummary & {
      title: string;
      organization_id: number;
      generated_at: string;
      generated_by: number;
      filters: Record<string, string | number | null>;
      breakdowns: {
        by_name: Record<string, number>;
        by_type: Record<string, number>;
        by_issuer: Record<string, number>;
        by_course: Record<string, number>;
        by_year: Record<string, number>;
      };
      certificates: ApprovedCertificateRecord[];
    }>(`${BASE}/report`, { params: buildParams(filters) }),

  downloadPresentation: async (filters?: ApprovedAnalyticsFilters) => {
    const apiUrl = apiClient.getApiUrl();
    const token = getAccessToken();
    const params = new URLSearchParams(buildParams(filters));
    const qs = params.toString();
    const response = await fetch(
      `${apiUrl}${BASE}/presentation${qs ? `?${qs}` : ""}`,
      { headers: { Authorization: `Bearer ${token}` } }
    );
    if (!response.ok) throw new Error(`Download failed: ${response.status}`);
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "approved_certificates.pptx";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  },
};
