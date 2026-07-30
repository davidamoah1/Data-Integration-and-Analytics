import { apiClient, setTokens, clearTokens } from '../api/client';
import type { LoginRequest, LoginResponse, RefreshResponse, User } from '@/types';

export interface SignupPayload {
  email: string;
  password: string;
  full_name: string;
  organization_name?: string;
  country?: string;
  industry?: string;
  organization_type?: string;
}

export interface SignupResponse {
  id: number;
  email: string;
  full_name: string;
  organization_id: number | null;
  onboarding_completed: boolean;
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface OnboardingPayload {
  industry?: string;
  organization_type?: string;
  primary_goal?: string;
  country?: string;
  skip_dataset?: boolean;
}

export interface SignupV2Payload {
  email: string;
  password: string;
  full_name: string;
  registration_mode: 'create_organization' | 'join_organization' | 'personal';
  organization_name?: string;
  industry?: string;
  country?: string;
  organization_type?: string;
  invitation_token?: string;
}

export interface InvitationPayload {
  email: string;
  role_name: string;
  department_id?: number;
}

export const authService = {
  async login(credentials: LoginRequest): Promise<LoginResponse> {
    const data = await apiClient.post<LoginResponse>('/api/auth/login', credentials, {
      skipAuth: true,
    });
    setTokens(data.access_token, data.refresh_token);
    return data;
  },

  async signup(payload: SignupPayload): Promise<SignupResponse> {
    const data = await apiClient.post<SignupResponse>('/api/auth/signup', payload, {
      skipAuth: true,
    });
    if (data.access_token) {
      setTokens(data.access_token, data.refresh_token);
    }
    return data;
  },

  async signupV2(payload: SignupV2Payload): Promise<SignupResponse> {
    const data = await apiClient.post<SignupResponse>('/api/auth/signup-v2', payload, {
      skipAuth: true,
    });
    if (data.access_token) {
      setTokens(data.access_token, data.refresh_token);
    }
    return data;
  },

  async logout(): Promise<void> {
    const refreshToken = localStorage.getItem('dataflow_refresh_token');
    if (refreshToken) {
      try {
        await apiClient.post('/api/auth/logout', { refresh_token: refreshToken });
      } catch {
        // ignore — we clear tokens anyway
      }
    }
    clearTokens();
  },

  async getProfile(): Promise<User> {
    return apiClient.get<User>('/api/auth/profile');
  },

  async updateProfile(payload: Partial<User>): Promise<User> {
    return apiClient.put<User>('/api/auth/profile', payload);
  },

  async changePassword(currentPassword: string, newPassword: string): Promise<void> {
    await apiClient.post('/api/auth/change-password', {
      current_password: currentPassword,
      new_password: newPassword,
    });
  },

  async forgotPassword(email: string): Promise<void> {
    await apiClient.post('/api/auth/forgot-password', { email }, { skipAuth: true });
  },

  async resetPassword(token: string, newPassword: string): Promise<void> {
    await apiClient.post('/api/auth/reset-password', { token, new_password: newPassword }, { skipAuth: true });
  },

  async verifyEmail(token: string): Promise<void> {
    await apiClient.post('/api/auth/verify-email', { token }, { skipAuth: true });
  },

  async getOnboardingStatus(): Promise<{ onboarding_completed: boolean; onboarding_data: Record<string, unknown> }> {
    return apiClient.get('/api/auth/onboarding-status');
  },

  async completeOnboarding(payload: OnboardingPayload): Promise<{ onboarding_completed: boolean; onboarding_data: Record<string, unknown> }> {
    return apiClient.post('/api/auth/onboarding', payload);
  },

  async getSessions(): Promise<unknown[]> {
    return apiClient.get('/api/auth/sessions');
  },

  async revokeSession(sessionId: number): Promise<void> {
    await apiClient.delete(`/api/auth/sessions/${sessionId}`);
  },

  async getLoginHistory(): Promise<unknown[]> {
    return apiClient.get('/api/auth/login-history');
  },

  async getInvitationInfo(token: string): Promise<{ id: number; email: string; organization_name: string; organization_id: number; role_name: string; expires_at: string }> {
    return apiClient.get(`/api/invitations/info/${token}`, { skipAuth: true });
  },

  async acceptInvitation(token: string, fullName: string, password: string): Promise<SignupResponse> {
    const data = await apiClient.post<SignupResponse>('/api/invitations/accept', {
      token,
      full_name: fullName,
      password,
    }, { skipAuth: true });
    if (data.access_token) {
      setTokens(data.access_token, data.refresh_token);
    }
    return data;
  },

  async listInvitations(): Promise<unknown[]> {
    return apiClient.get('/api/invitations');
  },

  async sendInvitation(payload: InvitationPayload): Promise<unknown> {
    return apiClient.post('/api/invitations', payload);
  },

  async revokeInvitation(invitationId: number): Promise<void> {
    await apiClient.delete(`/api/invitations/${invitationId}`);
  },
};
