"use client";

import { apiClient } from "@/services/api/client";

// ─── Types ──────────────────────────────────────────────────────

export interface CaptureDocumentType {
  key: string;
  label: string;
  industry: string;
  fields: {
    name: string;
    label: string;
    data_type: string;
    required: boolean;
  }[];
}

export interface CaptureField {
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
  page_number: number;
}

export interface CaptureDocument {
  id: number;
  batch_id: number | null;
  filename: string;
  file_type: string;
  page_count: number;
  status: string;
  error_message: string | null;
  industry: string | null;
  document_type: string | null;
  document_type_label: string | null;
  classification_confidence: number | null;
  needs_type_confirmation: boolean;
  overall_confidence: number | null;
  duplicate_of_id: number | null;
  extracted_tables: any[] | null;
  created_at: string | null;
  processed_at: string | null;
  reviewed_at: string | null;
  approved_at: string | null;
  fields?: CaptureField[];
  raw_ocr_text?: string;
}

export interface CaptureBatch {
  id: number;
  name: string;
  industry: string | null;
  total_documents: number;
  processed_documents: number;
  failed_documents: number;
  status: string;
  created_at: string | null;
}

export interface CaptureAnalyticsSummary {
  total_documents: number;
  approved_documents: number;
  pending_review: number;
  failed_documents: number;
  average_confidence: number;
  by_status: Record<string, number>;
  by_document_type: Record<string, number>;
  by_industry: Record<string, number>;
}

export interface CaptureEngineStatus {
  ocr_available: boolean;
  supported_industries: string[];
}

// ─── Service ────────────────────────────────────────────────────

const BASE = "/api/capture";

export const captureService = {
  getStatus: () => apiClient.get<CaptureEngineStatus>(`${BASE}/status`),

  getDocumentTypes: (industry?: string) =>
    apiClient.get<{ document_types: CaptureDocumentType[] }>(`${BASE}/document-types`, {
      params: industry ? { industry } : undefined,
    }),

  uploadDocument: (file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return apiClient.upload<CaptureDocument>(`${BASE}/documents/upload`, formData);
  },

  uploadDocumentWithProgress: (file: File, onProgress?: (percent: number) => void) => {
    const formData = new FormData();
    formData.append("file", file);
    return apiClient.uploadWithProgress<CaptureDocument>(
      `${BASE}/documents/upload`,
      formData,
      onProgress,
      { timeout: 120000 },
    );
  },

  uploadZipBatch: (file: File, batchName?: string, industry?: string) => {
    const formData = new FormData();
    formData.append("file", file);
    const params: Record<string, string> = {};
    if (batchName) params.batch_name = batchName;
    if (industry) params.industry = industry;
    return apiClient.upload<{ batch_id: number; total_documents: number; status: string; documents: CaptureDocument[] }>(
      `${BASE}/batches/upload-zip`,
      formData,
      { params },
    );
  },

  listBatches: (limit = 50, offset = 0) =>
    apiClient.get<{ batches: CaptureBatch[] }>(`${BASE}/batches`, {
      params: { limit, offset },
    }),

  getBatch: (batchId: number) =>
    apiClient.get<{ id: number; name: string; status: string; total_documents: number; processed_documents: number; failed_documents: number; documents: CaptureDocument[] }>(
      `${BASE}/batches/${batchId}`,
    ),

  listDocuments: (filters?: { status?: string; document_type?: string; batch_id?: number; limit?: number; offset?: number }) =>
    apiClient.get<{ documents: CaptureDocument[] }>(`${BASE}/documents`, {
      params: filters as Record<string, string | number | undefined>,
    }),

  getDocument: (documentId: number) =>
    apiClient.get<CaptureDocument>(`${BASE}/documents/${documentId}`),

  updateField: (documentId: number, fieldId: number, value: string) =>
    apiClient.patch<CaptureField>(`${BASE}/documents/${documentId}/fields/${fieldId}`, { value }),

  setDocumentType: (documentId: number, documentType: string) =>
    apiClient.post<CaptureDocument>(`${BASE}/documents/${documentId}/document-type`, {
      document_type: documentType,
    }),

  approveDocument: (documentId: number) =>
    apiClient.post<CaptureDocument>(`${BASE}/documents/${documentId}/approve`),

  rejectDocument: (documentId: number, reason?: string) =>
    apiClient.post<CaptureDocument>(`${BASE}/documents/${documentId}/reject`, reason ? { reason } : undefined),

  saveDraft: (documentId: number) =>
    apiClient.post<CaptureDocument>(`${BASE}/documents/${documentId}/draft`),

  retryDocument: (documentId: number) =>
    apiClient.post<CaptureDocument>(`${BASE}/documents/${documentId}/retry`),

  deleteDocument: (documentId: number) =>
    apiClient.delete<{ success: boolean }>(`${BASE}/documents/${documentId}`),

  getAuditLog: (documentId: number) =>
    apiClient.get<{ logs: any[] }>(`${BASE}/documents/${documentId}/audit-log`),

  getAnalyticsSummary: () =>
    apiClient.get<CaptureAnalyticsSummary>(`${BASE}/analytics/summary`),

  exportToDataset: (documentId: number, datasetName?: string) =>
    apiClient.post<{ document_id: number; csv_path: string; dataset_name: string; row_count: number; field_count: number; fields_exported: string[] }>(
      `${BASE}/documents/${documentId}/export`,
      datasetName ? { dataset_name: datasetName } : undefined,
    ),

  bulkExportApproved: (documentType?: string, datasetName?: string) =>
    apiClient.post<{ csv_path: string; dataset_name: string; row_count: number; field_count: number; fields_exported: string[] }>(
      `${BASE}/documents/bulk-export`,
      { document_type: documentType, dataset_name: datasetName },
    ),
};
