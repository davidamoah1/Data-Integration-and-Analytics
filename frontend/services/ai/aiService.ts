import { apiClient } from '../api/client';
import type {
  ChatRequest,
  ChatResponse,
  Conversation,
  ExecutiveSummary,
  RootCauseAnalysis,
  ForecastResult,
  AnomalyResult,
  RecommendationResult,
  NLAnalyticsResult,
  ReportResult,
  AIInsight,
} from '@/types';

export const aiService = {
  async chat(request: ChatRequest): Promise<ChatResponse> {
    return apiClient.post('/ai/chat', request);
  },

  async listConversations(assistantType?: string): Promise<Conversation[]> {
    const qs = assistantType ? `?assistant_type=${assistantType}` : '';
    return apiClient.get(`/ai/conversations${qs}`);
  },

  async getConversationMessages(conversationId: number): Promise<unknown[]> {
    return apiClient.get(`/ai/conversations/${conversationId}/messages`);
  },

  async deleteConversation(conversationId: number): Promise<void> {
    await apiClient.delete(`/ai/conversations/${conversationId}`);
  },

  async searchConversations(query: string, limit = 20): Promise<Conversation[]> {
    return apiClient.get(`/ai/conversations/search?q=${encodeURIComponent(query)}&limit=${limit}`);
  },

  async listAssistants(): Promise<{ id: string; name: string; description?: string }[]> {
    return apiClient.get('/ai/assistants');
  },

  async messageFeedback(messageId: number, feedback: 'positive' | 'negative', comment?: string): Promise<void> {
    await apiClient.post(`/ai/messages/${messageId}/feedback`, { feedback, comment });
  },

  async getInsights(): Promise<AIInsight[]> {
    return apiClient.get('/ai/insights');
  },

  // ── Enterprise AI Endpoints ──────────────────────────

  async generateExecutiveSummary(payload: {
    dataset_id?: string;
    industry?: string;
    user_message?: string;
  }): Promise<ExecutiveSummary> {
    return apiClient.post('/ai/enterprise/executive-summary', payload);
  },

  async analyzeRootCause(payload: {
    question: string;
    dataset_id?: string;
    industry?: string;
  }): Promise<RootCauseAnalysis> {
    return apiClient.post('/ai/enterprise/root-cause', payload);
  },

  async generateForecast(payload: {
    metric: string;
    dataset_id?: string;
    industry?: string;
    horizon?: string | number;
    method?: string;
  }): Promise<ForecastResult> {
    return apiClient.post('/ai/enterprise/forecast', payload);
  },

  async detectAnomalies(payload: {
    metric: string;
    dataset_id?: string;
    industry?: string;
    sensitivity?: number;
  }): Promise<AnomalyResult> {
    return apiClient.post('/ai/enterprise/anomaly', payload);
  },

  async getRecommendations(payload: {
    dataset_id?: string;
    industry?: string;
  }): Promise<RecommendationResult> {
    return apiClient.post('/ai/enterprise/recommendations', payload);
  },

  async analyzeNaturalLanguage(payload: {
    question: string;
    dataset_id?: string;
    industry?: string;
  }): Promise<NLAnalyticsResult> {
    return apiClient.post('/ai/enterprise/nl-analytics', payload);
  },

  async generateReport(payload: {
    report_type?: string;
    title?: string;
    dataset_id?: string;
    industry?: string;
    format?: string;
  }): Promise<ReportResult> {
    return apiClient.post('/ai/enterprise/report', payload);
  },

  async listTaskTypes(): Promise<{ task_type: string; description: string; output_format: string }[]> {
    return apiClient.get('/ai/enterprise/task-types');
  },
};
