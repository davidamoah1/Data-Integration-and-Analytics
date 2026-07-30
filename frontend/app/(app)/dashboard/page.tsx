'use client';

import { useAuthStore } from '@/stores/authStore';
import { AdaptiveDashboard } from '@/components/adaptive/AdaptiveDashboard';

export default function DashboardPage() {
  const { isAuthenticated } = useAuthStore();

  if (!isAuthenticated) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="animate-pulse text-muted-foreground">Loading...</div>
      </div>
    );
  }

  return <AdaptiveDashboard />;
}
