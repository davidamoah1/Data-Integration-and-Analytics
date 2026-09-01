import { apiClient } from '../api/client';

export interface KPIMetric {
  label: string;
  value: string | number;
  unit?: string;
  trend?: string;
  trend_value?: string;
  target?: string | number | null;
  color?: string;
}

export interface ChartDefinition {
  title: string;
  chart_type: string;
  data?: Record<string, unknown>[];
  x_axis?: string;
  y_axis?: string;
  series?: Record<string, unknown>[];
  config?: Record<string, unknown>;
}

export interface TableDefinition {
  title: string;
  columns: string[];
  rows: unknown[][];
  summary?: string;
}

export interface Insight {
  title: string;
  description: string;
  severity?: string;
  metric?: string;
  impact?: string;
}

export interface Recommendation {
  title: string;
  description: string;
  priority?: string;
  action?: string;
  expected_impact?: string;
  timeline?: string;
}

export interface ReportSection {
  section_type: string;
  title: string;
  content?: string;
  kpis?: KPIMetric[];
  charts?: ChartDefinition[];
  tables?: TableDefinition[];
  insights?: Insight[];
  recommendations?: Recommendation[];
  order: number;
  page_break?: boolean;
}

export interface ReportComposition {
  report_id: string;
  title: string;
  subtitle?: string;
  organization_name?: string;
  author_name?: string;
  template: string;
  industry?: string;
  dataset_id?: number | null;
  analysis_id?: number | null;
  sections: ReportSection[];
  created_at?: string;
  tags?: string[];
  executive_summary?: string;
}

export interface ReportListItem {
  report_id: string;
  title: string;
  subtitle?: string;
  template: string;
  industry?: string;
  section_count: number;
  created_at?: string;
  tags?: string[];
}

export interface SlideData {
  slide_number: number;
  layout: string;
  title: string;
  subtitle?: string;
  content?: string;
  kpis?: { label: string; value: string; trend?: string; trend_value?: string }[];
  chart_type?: string;
  chart_data?: Record<string, unknown>[];
  x_axis?: string;
  y_axis?: string;
  columns?: string[];
  rows?: unknown[][];
  speaker_notes?: string;
}

export interface PresentationData {
  report_id: string;
  title: string;
  slides: SlideData[];
}

export interface TemplateInfo {
  key: string;
  name: string;
  description: string;
}

export const reportEngineService = {
  async createReport(req: {
    title: string;
    template?: string;
    organization_name?: string;
    author_name?: string;
    industry?: string;
    dataset_id?: number;
    analysis_id?: number;
  }): Promise<ReportComposition> {
    return apiClient.post('/api/reports', req);
  },

  async listReports(): Promise<ReportListItem[]> {
    return apiClient.get('/api/reports');
  },

  async getReport(reportId: string): Promise<ReportComposition> {
    return apiClient.get(`/api/reports/${reportId}`);
  },

  async deleteReport(reportId: string): Promise<{ deleted: boolean }> {
    return apiClient.delete(`/api/reports/${reportId}`);
  },

  async addSection(reportId: string, section: Partial<ReportSection>): Promise<ReportComposition> {
    return apiClient.post(`/api/reports/${reportId}/sections`, section);
  },

  async updateSection(reportId: string, sectionOrder: number, updates: Partial<ReportSection>): Promise<ReportComposition> {
    return apiClient.put(`/api/reports/${reportId}/sections/${sectionOrder}`, updates);
  },

  async removeSection(reportId: string, sectionOrder: number): Promise<ReportComposition> {
    return apiClient.delete(`/api/reports/${reportId}/sections/${sectionOrder}`);
  },

  async addKPIs(reportId: string, sectionOrder: number, kpis: KPIMetric[]): Promise<ReportComposition> {
    return apiClient.post(`/api/reports/${reportId}/sections/${sectionOrder}/kpis`, { kpis });
  },

  async addChart(reportId: string, sectionOrder: number, chart: ChartDefinition): Promise<ReportComposition> {
    return apiClient.post(`/api/reports/${reportId}/sections/${sectionOrder}/charts`, chart);
  },

  async addTable(reportId: string, sectionOrder: number, table: TableDefinition): Promise<ReportComposition> {
    return apiClient.post(`/api/reports/${reportId}/sections/${sectionOrder}/tables`, table);
  },

  async addInsights(reportId: string, sectionOrder: number, insights: Insight[]): Promise<ReportComposition> {
    return apiClient.post(`/api/reports/${reportId}/sections/${sectionOrder}/insights`, { insights });
  },

  async addRecommendations(reportId: string, sectionOrder: number, recommendations: Recommendation[]): Promise<ReportComposition> {
    return apiClient.post(`/api/reports/${reportId}/sections/${sectionOrder}/recommendations`, { recommendations });
  },

  async getExecutiveSummary(reportId: string): Promise<{ report_id: string; executive_summary: string }> {
    return apiClient.get(`/api/reports/${reportId}/executive-summary`);
  },

  exportReportUrl(reportId: string, format: string = 'pdf'): string {
    const baseUrl = apiClient.getApiUrl();
    return `${baseUrl}/api/reports/${reportId}/export?format=${format}`;
  },

  async getPresentation(reportId: string): Promise<PresentationData> {
    return apiClient.get(`/api/reports/${reportId}/presentation`);
  },

  exportPresentationUrl(reportId: string, format: string = 'pptx'): string {
    const baseUrl = apiClient.getApiUrl();
    return `${baseUrl}/api/reports/${reportId}/presentation/export?format=${format}`;
  },

  async listTemplates(): Promise<{ templates: TemplateInfo[] }> {
    return apiClient.get('/api/reports/templates/list');
  },

  async listSectionTypes(): Promise<{ section_types: { key: string; name: string }[] }> {
    return apiClient.get('/api/reports/section-types/list');
  },

  async listChartTypes(): Promise<{ chart_types: { key: string; name: string }[] }> {
    return apiClient.get('/api/reports/chart-types/list');
  },

  async autoGenerateReport(file: File, options?: {
    title?: string;
    template?: string;
    industry?: string;
    organization_name?: string;
    author_name?: string;
  }): Promise<ReportComposition & { auto_generated: boolean; chart_count: number; kpi_count: number; insight_count: number }> {
    const formData = new FormData();
    formData.append('file', file);
    const params = new URLSearchParams();
    if (options?.title) params.set('title', options.title);
    if (options?.template) params.set('template', options.template);
    if (options?.industry) params.set('industry', options.industry);
    if (options?.organization_name) params.set('organization_name', options.organization_name);
    if (options?.author_name) params.set('author_name', options.author_name);
    const queryString = params.toString();
    const url = `/api/reports/auto-generate${queryString ? `?${queryString}` : ''}`;
    return apiClient.post(url, formData);
  },
};
