'use client';

import { useEffect, type ReactNode } from 'react';
import { useAuthStore } from '@/stores/authStore';

export function AuthProvider({ children }: { children: ReactNode }) {
  const fetchProfile = useAuthStore((s) => s.fetchProfile);
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);

  useEffect(() => {
    if (isAuthenticated) return;
    // Only fetch profile if we have a token in localStorage
    const token = localStorage.getItem('dataflow_access_token');
    if (token) {
      fetchProfile();
    }
  }, [fetchProfile, isAuthenticated]);

  return <>{children}</>;
}
