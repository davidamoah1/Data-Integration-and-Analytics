import { apiClient } from '../api/client';
import type { ChatRequest, ChatResponse, Conversation } from '@/types';

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

  async getInsights(): Promise<unknown[]> {
    return apiClient.get('/ai/insights');
  },

  async generateForecast(payload: { metric: string; periods: number }): Promise<unknown> {
    return apiClient.post('/ai/forecast', payload);
  },

  async detectAnomalies(payload: { metric: string }): Promise<unknown> {
    return apiClient.post('/ai/anomaly/detect', payload);
  },
};
