'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import {
  ArrowRight, Sparkles, Loader2, type LucideIcon,
} from 'lucide-react';
import { useAuthStore } from '@/stores/authStore';
import { onboardingService, type OnboardingNextAction, type OnboardingStatus } from '@/services/onboarding/onboardingService';
import { getOnboardingIcon } from '@/lib/onboardingIcons';
import { Card, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { cn } from '@/lib/utils';

interface SmartEmptyStateProps {
  context?: 'datasets' | 'dashboards' | 'reports' | 'analytics' | 'general';
  title?: string;
  description?: string;
  className?: string;
}

export function SmartEmptyState({
  context = 'general',
  title,
  description,
  className,
}: SmartEmptyStateProps) {
  const router = useRouter();
  const { user } = useAuthStore();
  const [status, setStatus] = useState<OnboardingStatus | null>(null);
  const [nextAction, setNextAction] = useState<OnboardingNextAction | null>(null);
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

  if (loading) {
    return (
      <div className="flex items-center justify-center py-16">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  // If onboarding is complete, show a simpler empty state
  const showOnboarding = status && !status.is_complete && !status.skipped;

  const contextTitles: Record<string, string> = {
    datasets: 'No datasets yet',
    dashboards: 'No dashboards yet',
    reports: 'No reports yet',
    analytics: 'No analytics available',
    general: 'Nothing here yet',
  };

  const contextDescriptions: Record<string, string> = {
    datasets: 'Upload your first dataset to start analyzing data.',
    dashboards: 'Create a dashboard to visualize your data.',
    reports: 'Generate a report from your analyzed data.',
    analytics: 'Once you have data, analytics will appear here.',
    general: 'Get started by completing the steps below.',
  };

  const displayTitle = title || contextTitles[context];
  const displayDescription = description || contextDescriptions[context];

  return (
    <div className={cn('flex flex-col items-center justify-center py-16 text-center', className)}>
      <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-primary/10 text-primary">
        <Sparkles size={32} />
      </div>
      <h3 className="text-xl font-semibold">{displayTitle}</h3>
      <p className="mt-2 max-w-sm text-sm text-muted-foreground">{displayDescription}</p>

      {/* Onboarding progress card */}
      {showOnboarding && status && (
        <Card className="mt-6 max-w-md border-2">
          <CardContent className="p-6">
            <div className="mb-4">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">{status.flow.title}</span>
                <span className="text-xs text-muted-foreground">
                  {status.completed_count}/{status.total_steps}
                </span>
              </div>
              <div className="mt-2 h-2 overflow-hidden rounded-full bg-muted">
                <div
                  className="h-full rounded-full bg-primary transition-all duration-300"
                  style={{ width: `${status.percentage}%` }}
                />
              </div>
            </div>

            {/* Step list */}
            <div className="space-y-2">
              {status.flow.steps.map((step, i) => {
                const isCompleted = status.completed_steps.includes(step.key);
                const isCurrent = i === status.current_step_index;
                const Icon = getOnboardingIcon(step.icon);
                return (
                  <div
                    key={step.key}
                    className={cn(
                      'flex items-center gap-3 rounded-lg p-2 transition-colors',
                      isCurrent && 'bg-primary/5 border border-primary/20',
                      !isCurrent && !isCompleted && 'opacity-50',
                    )}
                  >
                    <div
                      className={cn(
                        'flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-xs font-bold',
                        isCompleted
                          ? 'bg-green-500 text-white'
                          : isCurrent
                            ? 'bg-primary text-primary-foreground'
                            : 'bg-muted text-muted-foreground',
                      )}
                    >
                      {isCompleted ? '✓' : i + 1}
                    </div>
                    <div className="flex-1 text-left">
                      <p className={cn('text-sm font-medium', isCompleted && 'line-through text-muted-foreground')}>
                        {step.title}
                      </p>
                    </div>
                    {isCurrent && (
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => router.push(step.href)}
                        className="gap-1"
                      >
                        <Icon size={14} />
                        {step.action_label}
                      </Button>
                    )}
                  </div>
                );
              })}
            </div>

            {/* Next action CTA */}
            {nextAction && (
              <Button
                className="mt-4 w-full gap-2"
                onClick={() => router.push(nextAction.href)}
              >
                {nextAction.action_label}
                <ArrowRight size={16} />
              </Button>
            )}
          </CardContent>
        </Card>
      )}

      {/* For completed onboarding users with no data */}
      {!showOnboarding && context !== 'general' && (
        <div className="mt-6">
          <Button
            variant="outline"
            onClick={() => {
              if (context === 'datasets') router.push('/datasets');
              else if (context === 'dashboards') router.push('/dashboard/builder');
              else if (context === 'reports') router.push('/reports');
              else if (context === 'analytics') router.push('/analytics');
            }}
            className="gap-2"
          >
            Get Started <ArrowRight size={16} />
          </Button>
        </div>
      )}
    </div>
  );
}
