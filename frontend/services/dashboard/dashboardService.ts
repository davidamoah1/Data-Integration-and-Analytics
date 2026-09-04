import { apiClient } from '../api/client';
import type { Dashboard, KPI, Widget } from '@/types';

export const dashboardService = {
  async listDashboards(): Promise<Dashboard[]> {
    return apiClient.get('/analytics/dashboards');
  },

  async getDashboard(dashboardId: number): Promise<Dashboard> {
    return apiClient.get(`/analytics/dashboards/${dashboardId}`);
  },

  async createDashboard(payload: { name: string; description?: string; is_public?: boolean }): Promise<{ id: number; name: string; version: number }> {
    return apiClient.post('/analytics/dashboards', payload);
  },

  async updateDashboard(dashboardId: number, payload: Partial<Dashboard>): Promise<{ id: number; name: string; version: number }> {
    return apiClient.put(`/analytics/dashboards/${dashboardId}`, payload);
  },

  async deleteDashboard(dashboardId: number): Promise<void> {
    await apiClient.delete(`/analytics/dashboards/${dashboardId}`);
  },

  async toggleFavorite(dashboardId: number): Promise<void> {
    await apiClient.post(`/analytics/dashboards/${dashboardId}/favorite`);
  },

  async addWidget(dashboardId: number, widget: Omit<Widget, 'id'>): Promise<{ id: number; widget_type: string; title: string }> {
    return apiClient.post(`/analytics/dashboards/${dashboardId}/widgets`, widget);
  },

  async removeWidget(dashboardId: number, widgetId: number): Promise<void> {
    await apiClient.delete(`/analytics/dashboards/${dashboardId}/widgets/${widgetId}`);
  },

  async listKPIs(category?: string): Promise<KPI[]> {
    const qs = category ? `?category=${category}` : '';
    return apiClient.get(`/analytics/kpis${qs}`);
  },

  async getKPI(kpiId: number): Promise<KPI> {
    return apiClient.get(`/analytics/kpis/${kpiId}`);
  },

  async createKPI(payload: { name: string; category: string; target?: number; unit?: string }): Promise<{ id: number; name: string }> {
    return apiClient.post('/analytics/kpis', payload);
  },

  async recordKPI(kpiId: number, value: number): Promise<{ id: number; value: number; status: string }> {
    return apiClient.post(`/analytics/kpis/${kpiId}/record`, { value });
  },

  async deleteKPI(kpiId: number): Promise<void> {
    await apiClient.delete(`/analytics/kpis/${kpiId}`);
  },

  async getEtlDashboard(): Promise<unknown> {
    return apiClient.get('/etl/dashboard');
  },

  async getOverview(): Promise<EnterpriseOverview> {
    return apiClient.get('/analytics/overview');
  },
};

export interface OverviewDashboard {
  id: number;
  name: string;
  description: string;
  theme: string;
  widget_count: number;
  widgets: Array<{ id: number; type: string; title: string }>;
  is_public: boolean;
  created_at: string | null;
  updated_at: string | null;
}

export interface OverviewWorkflow {
  id: number;
  workflow_id: string;
  dataset_name: string;
  row_count: number;
  column_count: number;
  quality_score: number;
  status: string;
  created_at: string | null;
}

export interface OverviewActivity {
  id: number;
  action: string;
  resource_type: string;
  created_at: string | null;
}

export interface EnterpriseOverview {
  members_count: number;
  departments_count: number;
  datasets_count: number;
  dashboards_count: number;
  total_widgets_count: number;
  kpis_count: number;
  total_rows_processed: number;
  storage_usage_bytes: number;
  storage_usage_formatted: string;
  system_health: string;
  security_tier: string;
  recent_dashboards: OverviewDashboard[];
  recent_workflows: OverviewWorkflow[];
  recent_activity: OverviewActivity[];
}

