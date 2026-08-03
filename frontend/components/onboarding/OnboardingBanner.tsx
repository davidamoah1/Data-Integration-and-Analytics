'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { ArrowRight, X, Sparkles } from 'lucide-react';
import { onboardingService, type OnboardingStatus, type OnboardingNextAction } from '@/services/onboarding/onboardingService';
import { getOnboardingIcon } from '@/lib/onboardingIcons';
import { Button } from '@/components/ui/Button';
import { cn } from '@/lib/utils';

export function OnboardingBanner() {
  const router = useRouter();
  const [status, setStatus] = useState<OnboardingStatus | null>(null);
  const [nextAction, setNextAction] = useState<OnboardingNextAction | null>(null);
  const [dismissed, setDismissed] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [s, action] = await Promise.all([
          onboardingService.getStatus(),
          onboardingService.getNextAction(),
        ]);
        setStatus(s);
        setNextAction(action);
      } catch {
        // ignore
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading || !status || status.is_complete || status.skipped || dismissed) {
    return null;
  }

  const NextIcon = nextAction ? getOnboardingIcon(nextAction.icon) : Sparkles;

  return (
    <div className={cn(
      'relative overflow-hidden rounded-xl border-2 border-primary/20 bg-gradient-to-r from-primary/5 to-primary/10 p-4',
      'mb-6'
    )}>
      <button
        onClick={() => setDismissed(true)}
        className="absolute right-3 top-3 text-muted-foreground hover:text-foreground"
      >
        <X className="h-4 w-4" />
      </button>

      <div className="flex items-center gap-4">
        <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-primary/10 text-primary">
          <NextIcon size={24} />
        </div>

        <div className="flex-1">
          <div className="flex items-center gap-2">
            <h3 className="text-sm font-semibold">
              {nextAction ? nextAction.title : 'Complete your setup'}
            </h3>
            <span className="rounded-full bg-primary/10 px-2 py-0.5 text-xs font-medium text-primary">
              {status.completed_count}/{status.total_steps} steps
            </span>
          </div>
          <p className="mt-0.5 text-sm text-muted-foreground">
            {nextAction ? nextAction.description : status.flow.description}
          </p>

          {/* Progress bar */}
          <div className="mt-2 h-1.5 max-w-xs overflow-hidden rounded-full bg-muted">
            <div
              className="h-full rounded-full bg-primary transition-all duration-300"
              style={{ width: `${status.percentage}%` }}
            />
          </div>
        </div>

        {nextAction && (
          <Button
            onClick={() => router.push(nextAction.href)}
            className="shrink-0 gap-2"
          >
            {nextAction.action_label}
            <ArrowRight size={16} />
          </Button>
        )}
      </div>
    </div>
  );
}
