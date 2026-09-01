"use client";

import { apiClient, getAccessToken } from "@/services/api/client";

// ─── Types ──────────────────────────────────────────────────────

export interface CertificateType {
  key: string;
  label: string;
  industry: string;
  keywords: string[];
  fields: {
    name: string;
    label: string;
    data_type: string;
    required: boolean;
    keywords: string[];
  }[];
}

export interface CertificateField {
  id: number;
  field_name: string;
  field_label: string;
  data_type: string;
  value: string | null;
  raw_value: string | null;
  confidence_score: number;
  is_low_confidence: boolean;
  was_corrected: boolean;
  is_valid: boolean;
  validation_message: string | null;
}

export interface Certificate {
  id: number;
  batch_id: number | null;
  filename: string;
  file_type: string;
  status: string;
  error_message: string | null;
  document_type: string | null;
  document_type_label: string | null;
  classification_confidence: number | null;
  overall_confidence: number | null;
  needs_type_confirmation: boolean;
  verification_status: string;
  verification_method: string | null;
  verified_at: string | null;
  duplicate_of_id: number | null;
  is_duplicate: boolean;
  created_at: string | null;
  processed_at: string | null;
  approved_at: string | null;
  student_name?: string | null;
  course?: string | null;
  institution?: string | null;
  date_awarded?: string | null;
  certificate_number?: string | null;
  fields?: CertificateField[];
}

export interface CertificateDashboard {
  total: number;
  processed: number;
  processing: number;
  review_required: number;
  approved: number;
  rejected: number;
  failed: number;
  duplicates: number;
  verified: number;
  not_verified: number;
  verification_pending: number;
  verification_failed: number;
  by_type: Record<string, number>;
  by_status: Record<string, number>;
  by_verification: Record<string, number>;
  by_institution: Record<string, number>;
  by_year: Record<string, number>;
}

export interface CertificateSearchResult {
  certificates: Certificate[];
  total: number;
  limit: number;
  offset: number;
}

export interface CertificateUploadResult {
  batch_id: number;
  batch_name: string;
  total: number;
  succeeded: number;
  failed: number;
  duplicates: number;
  review_required: number;
  certificates: Certificate[];
}

export interface VerificationResult {
  document_id: number;
  verification_status: string;
  method: string;
  status: string;
  verification_id: number;
  notes: string | null;
}

// ─── Service ────────────────────────────────────────────────────

const BASE = "/api/certificates";

export const certificateService = {
  getTypes: () =>
    apiClient.get<{ certificate_types: CertificateType[] }>(`${BASE}/types`),

  getDashboard: () =>
    apiClient.get<CertificateDashboard>(`${BASE}/dashboard`),

  search: (params?: {
    q?: string;
    certificate_type?: string;
    verification_status?: string;
    review_status?: string;
    institution?: string;
    year?: number;
    limit?: number;
    offset?: number;
  }) =>
    apiClient.get<CertificateSearchResult>(`${BASE}/search`, { params }),

  upload: (files: File[], batchName?: string, onProgress?: (percent: number) => void) => {
    const formData = new FormData();
    files.forEach((file) => formData.append("files", file));
    if (batchName) formData.append("batch_name", batchName);
    return apiClient.uploadWithProgress<CertificateUploadResult>(
      `${BASE}/upload`,
      formData,
      onProgress,
      { timeout: 120000 },
    );
  },

  exportCsv: async (params?: {
    certificate_type?: string;
    review_status?: string;
    verification_status?: string;
  }) => {
    const apiUrl = apiClient.getApiUrl();
    const token = getAccessToken();
    const query = new URLSearchParams();
    if (params?.certificate_type) query.set("certificate_type", params.certificate_type);
    if (params?.review_status) query.set("review_status", params.review_status);
    if (params?.verification_status) query.set("verification_status", params.verification_status);
    const qs = query.toString();
    const response = await fetch(
      `${apiUrl}${BASE}/export/csv${qs ? `?${qs}` : ""}`,
      {
        headers: { Authorization: `Bearer ${token}` },
      }
    );
    if (!response.ok) throw new Error(`Export failed: ${response.status}`);
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "certificates_export.csv";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  },

  exportXlsx: async (params?: {
    certificate_type?: string;
    review_status?: string;
    verification_status?: string;
  }) => {
    const apiUrl = apiClient.getApiUrl();
    const token = getAccessToken();
    const query = new URLSearchParams();
    if (params?.certificate_type) query.set("certificate_type", params.certificate_type);
    if (params?.review_status) query.set("review_status", params.review_status);
    if (params?.verification_status) query.set("verification_status", params.verification_status);
    const qs = query.toString();
    const response = await fetch(
      `${apiUrl}${BASE}/export/xlsx${qs ? `?${qs}` : ""}`,
      {
        headers: { Authorization: `Bearer ${token}` },
      }
    );
    if (!response.ok) throw new Error(`Export failed: ${response.status}`);
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "certificates_export.xlsx";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  },

  verify: (documentId: number, payload: {
    method: string;
    status: "pending" | "verified" | "failed" | "inconclusive";
    verification_source?: string;
    reference_number?: string;
    notes?: string;
    verified_fields?: Record<string, string>;
  }) =>
    apiClient.post<VerificationResult>(`${BASE}/${documentId}/verify`, payload),

  listVerifications: (documentId: number) =>
    apiClient.get<{ document_id: number; current_status: string; verifications: any[] }>(
      `${BASE}/${documentId}/verifications`
    ),

  toDataset: (datasetName?: string) =>
    apiClient.post<{
      dataset_name: string;
      csv_path: string;
      row_count: number;
      field_count: number;
      message: string;
    }>(`${BASE}/to-dataset`, datasetName ? { dataset_name: datasetName } : undefined),

  getStatus: (documentId: number) =>
    apiClient.get<{
      id: number;
      status: string;
      error_message: string | null;
      document_type: string | null;
      document_type_label: string | null;
      overall_confidence: number | null;
      classification_confidence: number | null;
    }>(`${BASE}/${documentId}/status`),

  getDetail: (documentId: number) =>
    apiClient.get<{
      certificate: Certificate;
      fields: CertificateField[];
      analysis: {
        document_type: string | null;
        document_type_label: string | null;
        classification_confidence: number | null;
        overall_confidence: number | null;
        summary: string;
        verification_status: string;
        is_duplicate: boolean;
        duplicate_of_id: number | null;
        completeness: {
          total_fields: number;
          required_fields: number;
          required_filled: number;
          optional_fields: number;
          optional_filled: number;
          completeness_pct: number;
          overall_pct: number;
          missing_required: string[];
          missing_optional: string[];
        };
        consistency_checks: {
          check_name: string;
          description: string;
          passed: boolean;
          severity: string;
          detail: string;
        }[];
        academic_performance: {
          gpa: string | null;
          grade: string | null;
          qualification: string | null;
          programme: string | null;
          has_performance_data: boolean;
          summary: string;
        };
        anomalies: {
          anomaly_type: string;
          field_name: string | null;
          description: string;
          severity: string;
        }[];
        recommendations: {
          action: string;
          description: string;
          priority: string;
        }[];
        field_analysis: {
          field_name: string;
          field_label: string;
          value: string | null;
          raw_value: string | null;
          confidence: number;
          is_low_confidence: boolean;
          is_present: boolean;
          is_required: boolean;
          is_valid: boolean;
          validation_message: string | null;
          was_corrected: boolean;
        }[];
      };
    }>(`${BASE}/${documentId}/detail`),

  getBatchAnalytics: (batchId: number) =>
    apiClient.get<{
      batch_id: number;
      total: number;
      by_type: Record<string, number>;
      by_verification: Record<string, number>;
      by_completeness_tier: Record<string, number>;
      avg_completeness: number;
      avg_confidence: number;
      total_anomalies: number;
      total_duplicates: number;
      common_anomalies: Record<string, number>;
      institutions: Record<string, number>;
      qualifications: Record<string, number>;
      summary: string;
      certificates: {
        id: number;
        filename: string;
        document_type: string | null;
        document_type_label: string | null;
        status: string;
        verification_status: string;
        overall_confidence: number | null;
        duplicate_of_id: number | null;
      }[];
    }>(`${BASE}/batch/${batchId}/analytics`),

  correctField: (documentId: number, fieldId: number, value: string) =>
    apiClient.patch<{
      document_id: number;
      field_id: number;
      field_name: string;
      old_value: string | null;
      new_value: string;
      confidence_score: number;
      was_corrected: boolean;
      is_valid: boolean;
      validation_message: string | null;
    }>(`${BASE}/${documentId}/fields/${fieldId}`, { value }),

  getReport: (params?: {
    certificate_type?: string;
    verification_status?: string;
    review_status?: string;
  }) =>
    apiClient.get<{
      title: string;
      organization_id: number;
      generated_at: string;
      generated_by: number;
      filters: Record<string, string | null>;
      executive_summary: string;
      metrics: {
        total_certificates: number;
        avg_completeness: number;
        avg_confidence: number;
        total_anomalies: number;
        total_duplicates: number;
      };
      breakdowns: {
        by_type: Record<string, number>;
        by_verification: Record<string, number>;
        by_completeness_tier: Record<string, number>;
        by_institution: Record<string, number>;
        by_qualification: Record<string, number>;
      };
      anomaly_summary: Record<string, number>;
      certificates: any[];
    }>(`${BASE}/report`, { params }),

  downloadPresentation: async (params?: {
    certificate_type?: string;
    verification_status?: string;
    review_status?: string;
  }) => {
    const apiUrl = apiClient.getApiUrl();
    const token = getAccessToken();
    const query = new URLSearchParams();
    if (params?.certificate_type) query.set("certificate_type", params.certificate_type);
    if (params?.verification_status) query.set("verification_status", params.verification_status);
    if (params?.review_status) query.set("review_status", params.review_status);
    const qs = query.toString();
    const response = await fetch(
      `${apiUrl}${BASE}/presentation${qs ? `?${qs}` : ""}`,
      { headers: { Authorization: `Bearer ${token}` } }
    );
    if (!response.ok) throw new Error(`Download failed: ${response.status}`);
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "certificate_intelligence.pptx";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  },
};
