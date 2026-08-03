"use client";

import { apiClient } from "@/services/api/client";

// ─── Types ──────────────────────────────────────────────────────

export interface AuditLogEntry {
  id: number;
  user_id: number | null;
  organization_id: number | null;
  action: string;
  resource_type: string | null;
  resource_id: number | null;
  old_values: Record<string, unknown> | null;
  new_values: Record<string, unknown> | null;
  metadata: Record<string, unknown> | null;
  ip_address: string | null;
  user_agent: string | null;
  request_id: string | null;
  created_at: string | null;
}

export interface AuditLogListResponse {
  logs: AuditLogEntry[];
  total: number;
  limit: number;
  offset: number;
}

export interface SecurityLogEntry {
  id: number;
  user_id: number | null;
  organization_id: number | null;
  event_type: string;
  ip_address: string | null;
  user_agent: string | null;
  resource: string | null;
  severity: string;
  details: Record<string, unknown> | null;
  created_at: string | null;
}

export interface SecurityLogListResponse {
  logs: SecurityLogEntry[];
  total: number;
  limit: number;
  offset: number;
}

export interface AuditStats {
  action_counts: Record<string, number>;
  daily_counts: { date: string; count: number }[];
  top_users: { user_id: number; count: number }[];
  total: number;
}

export interface AuditFilters {
  actions: string[];
  resource_types: string[];
}

export interface AuditLogQueryParams {
  [key: string]: string | number | boolean | null | undefined;
  user_id?: number;
  action?: string;
  resource_type?: string;
  resource_id?: number;
  ip_address?: string;
  start_date?: string;
  end_date?: string;
  limit?: number;
  offset?: number;
}

// ─── Service ────────────────────────────────────────────────────

const BASE = "/api/audit";

export const auditService = {
  listLogs: (params?: AuditLogQueryParams) =>
    apiClient.get<AuditLogListResponse>(`${BASE}/logs`, { params }),

  getLog: (id: number) => apiClient.get<AuditLogEntry>(`${BASE}/logs/${id}`),

  exportLogs: (format: "csv" | "json", params?: AuditLogQueryParams) => {
    const queryParams = new URLSearchParams({ format });
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          queryParams.append(key, String(value));
        }
      });
    }
    return `${apiClient.getApiUrl()}${BASE}/logs/export?${queryParams.toString()}`;
  },

  getStats: (params?: { start_date?: string; end_date?: string }) =>
    apiClient.get<AuditStats>(`${BASE}/stats`, { params }),

  getFilters: () => apiClient.get<AuditFilters>(`${BASE}/filters`),

  listSecurityLogs: (params?: {
    severity?: string;
    event_type?: string;
    limit?: number;
    offset?: number;
  }) => apiClient.get<SecurityLogListResponse>(`${BASE}/security`, { params }),

  getUserActivity: (userId: number, params?: { limit?: number; offset?: number }) =>
    apiClient.get<{ activities: unknown[]; total: number }>(`${BASE}/activity/${userId}`, { params }),
};
