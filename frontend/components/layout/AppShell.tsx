'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/stores/authStore';
import { Sidebar } from '@/components/layout/Sidebar';
import { TopNav } from '@/components/layout/TopNav';

export function AppShell({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const { isAuthenticated, isLoading, fetchProfile } = useAuthStore();

  useEffect(() => {
    const token = localStorage.getItem('dataflow_access_token');
    if (!token) {
      router.push('/login');
      return;
    }
    if (!isAuthenticated) {
      fetchProfile();
    }
  }, [router, isAuthenticated, fetchProfile]);

  if (!isAuthenticated) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="animate-pulse text-muted-foreground">Loading...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <Sidebar />
      <div className="ml-64">
        <TopNav />
        <main className="p-6">{children}</main>
      </div>
    </div>
  );
}
