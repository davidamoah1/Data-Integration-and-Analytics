import { apiClient, setTokens, clearTokens } from '../api/client';
import type { LoginRequest, LoginResponse, RefreshResponse, User } from '@/types';

export const authService = {
  async login(credentials: LoginRequest): Promise<LoginResponse> {
    const data = await apiClient.post<LoginResponse>('/auth/login', credentials, {
      skipAuth: true,
    });
    setTokens(data.access_token, data.refresh_token);
    return data;
  },

  async signup(payload: {
    email: string;
    password: string;
    full_name: string;
    organization_name?: string;
  }): Promise<{ id: number; email: string; full_name: string }> {
    return apiClient.post('/auth/signup', payload, { skipAuth: true });
  },

  async logout(): Promise<void> {
    const refreshToken = localStorage.getItem('dataflow_refresh_token');
    if (refreshToken) {
      try {
        await apiClient.post('/auth/logout', { refresh_token: refreshToken });
      } catch {
        // ignore — we clear tokens anyway
      }
    }
    clearTokens();
  },

  async getProfile(): Promise<User> {
    return apiClient.get<User>('/auth/profile');
  },

  async updateProfile(payload: Partial<User>): Promise<User> {
    return apiClient.put<User>('/auth/profile', payload);
  },

  async changePassword(currentPassword: string, newPassword: string): Promise<void> {
    await apiClient.post('/auth/change-password', {
      current_password: currentPassword,
      new_password: newPassword,
    });
  },

  async forgotPassword(email: string): Promise<void> {
    await apiClient.post('/auth/forgot-password', { email }, { skipAuth: true });
  },

  async resetPassword(token: string, newPassword: string): Promise<void> {
    await apiClient.post('/auth/reset-password', { token, new_password: newPassword }, { skipAuth: true });
  },

  async getSessions(): Promise<unknown[]> {
    return apiClient.get('/auth/sessions');
  },

  async revokeSession(sessionId: number): Promise<void> {
    await apiClient.delete(`/auth/sessions/${sessionId}`);
  },

  async getLoginHistory(): Promise<unknown[]> {
    return apiClient.get('/auth/login-history');
  },
};
