"use client";

import { apiClient } from "@/services/api/client";

// ─── Types ──────────────────────────────────────────────────────

export interface FileRecord {
  id: number;
  file_id: string;
  organization_id: number;
  filename: string;
  storage_backend: string;
  storage_bucket: string | null;
  storage_key: string;
  storage_url: string | null;
  mime_type: string | null;
  file_size: number | null;
  checksum: string | null;
  metadata: Record<string, unknown> | null;
  uploaded_by: number | null;
  is_public: boolean;
  created_at: string | null;
  accessed_at: string | null;
  deleted_at: string | null;
}

export interface FileListResponse {
  files: FileRecord[];
  count: number;
  total: number;
}

export interface FileUrlResponse {
  url: string;
  expires_in: number;
}

// ─── Service ────────────────────────────────────────────────────

const BASE = "/api/files";

export const fileService = {
  upload: (file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return apiClient.upload<FileRecord>(`${BASE}/upload`, formData);
  },

  list: (params?: { limit?: number; offset?: number }) =>
    apiClient.get<FileListResponse>(BASE, { params }),

  getMetadata: (fileId: string) => apiClient.get<FileRecord>(`${BASE}/${fileId}`),

  downloadUrl: (fileId: string) => `${apiClient.getApiUrl()}${BASE}/${fileId}/download`,

  getUrl: (fileId: string, expires?: number) =>
    apiClient.get<FileUrlResponse>(`${BASE}/${fileId}/url`, {
      params: expires ? { expires } : undefined,
    }),

  delete: (fileId: string) => apiClient.delete<{ deleted: boolean; file_id: string }>(`${BASE}/${fileId}`),
};
