import { apiClient } from '../api/client';
import type {
  ComposedDashboard,
  ComposedWidget,
  DashboardTemplate,
  WidgetData,
  WidgetTypeMeta,
} from '@/types';

export const dashboardCompositionService = {
  async listWidgets(industry?: string, widgetType?: string): Promise<ComposedWidget[]> {
    const params = new URLSearchParams();
    if (industry) params.set('industry', industry);
    if (widgetType) params.set('widget_type', widgetType);
    const qs = params.toString() ? `?${params.toString()}` : '';
    return apiClient.get<ComposedWidget[]>(`/api/dashboards/widgets${qs}`);
  },

  async listWidgetTypes(): Promise<WidgetTypeMeta[]> {
    return apiClient.get<WidgetTypeMeta[]>('/api/dashboards/widgets/types');
  },

  async listWidgetsByIndustry(industry: string): Promise<ComposedWidget[]> {
    return apiClient.get<ComposedWidget[]>(`/api/dashboards/widgets/industry/${industry}`);
  },

  async listTemplates(): Promise<DashboardTemplate[]> {
    return apiClient.get<DashboardTemplate[]>('/api/dashboards/templates');
  },

  async composeDashboard(payload: {
    name: string;
    industry: string;
    widget_keys?: string[];
    description?: string;
  }): Promise<ComposedDashboard> {
    return apiClient.post<ComposedDashboard>('/api/dashboards/compose', payload);
  },

  async getDashboard(dashboardId: string): Promise<ComposedDashboard> {
    return apiClient.get<ComposedDashboard>(`/api/dashboards/${dashboardId}`);
  },

  async listDashboards(industry?: string): Promise<ComposedDashboard[]> {
    const qs = industry ? `?industry=${industry}` : '';
    return apiClient.get<ComposedDashboard[]>(`/api/dashboards${qs}`);
  },

  async addWidget(dashboardId: string, widgetKey: string): Promise<ComposedDashboard> {
    return apiClient.post<ComposedDashboard>(`/api/dashboards/${dashboardId}/widgets`, {
      widget_key: widgetKey,
    });
  },

  async removeWidget(dashboardId: string, widgetKey: string): Promise<ComposedDashboard> {
    return apiClient.delete<ComposedDashboard>(`/api/dashboards/${dashboardId}/widgets/${widgetKey}`);
  },

  async getWidgetData(dashboardId: string, widgetKey: string): Promise<WidgetData> {
    return apiClient.get<WidgetData>(`/api/dashboards/${dashboardId}/data/${widgetKey}`);
  },
};
