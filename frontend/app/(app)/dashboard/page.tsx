'use client';

import { useAuthStore } from '@/stores/authStore';
import { AdaptiveDashboard } from '@/components/adaptive/AdaptiveDashboard';
import { OnboardingBanner } from '@/components/onboarding/OnboardingBanner';

export default function DashboardPage() {
  const { isAuthenticated } = useAuthStore();

  if (!isAuthenticated) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="animate-pulse text-muted-foreground">Loading...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <OnboardingBanner />
      <AdaptiveDashboard />
    </div>
  );
}
