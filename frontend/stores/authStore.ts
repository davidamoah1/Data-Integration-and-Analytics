'use client';

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { User } from '@/types';
import { authService, type SignupPayload } from '@/services/auth/authService';
import { getAccessToken, clearTokens } from '@/services/api/client';

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  login: (email: string, password: string, rememberMe?: boolean) => Promise<void>;
  signup: (payload: SignupPayload) => Promise<void>;
  fetchProfile: () => Promise<void>;
  logout: () => Promise<void>;
  clearError: () => void;
  hasPermission: (permission: string) => boolean;
  hasRole: (role: string) => boolean;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      login: async (email, password, rememberMe) => {
        set({ isLoading: true, error: null });
        try {
          const result = await authService.login({ email, password, remember_me: rememberMe });
          set({
            user: result.user,
            isAuthenticated: true,
            isLoading: false,
          });
        } catch (err) {
          const message = err instanceof Error ? err.message : 'Login failed';
          set({ isLoading: false, error: message });
          throw err;
        }
      },

      signup: async (payload) => {
        set({ isLoading: true, error: null });
        try {
          const result = await authService.signup(payload);
          set({
            user: result.user,
            isAuthenticated: true,
            isLoading: false,
          });
        } catch (err) {
          const message = err instanceof Error ? err.message : 'Sign up failed';
          set({ isLoading: false, error: message });
          throw err;
        }
      },

      fetchProfile: async () => {
        const token = getAccessToken();
        if (!token) {
          set({ isAuthenticated: false, user: null });
          return;
        }
        set({ isLoading: true });
        try {
          const profile = await authService.getProfile();
          set({ user: profile, isAuthenticated: true, isLoading: false });
        } catch {
          clearTokens();
          set({ user: null, isAuthenticated: false, isLoading: false });
        }
      },

      logout: async () => {
        await authService.logout();
        clearTokens();
        set({ user: null, isAuthenticated: false });
      },

      clearError: () => set({ error: null }),

      hasPermission: (permission) => {
        const { user } = get();
        if (!user) return false;
        if (user.roles.includes('super_admin')) return true;
        return user.permissions.includes(permission);
      },

      hasRole: (role) => {
        const { user } = get();
        if (!user) return false;
        return user.roles.includes(role);
      },
    }),
    {
      name: 'dataflow-auth',
      partialize: (state) => ({
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
    },
  ),
);
