'use client';

import { useEffect, useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import {
  CheckCircle2, ArrowRight, ArrowLeft, X, Sparkles, Loader2,
} from 'lucide-react';
import { useAuthStore } from '@/stores/authStore';
import { onboardingService, type OnboardingStatus } from '@/services/onboarding/onboardingService';
import { getOnboardingIcon } from '@/lib/onboardingIcons';
import { Button } from '@/components/ui/Button';
import { Card, CardContent } from '@/components/ui/Card';
import { cn } from '@/lib/utils';

interface GuidedOnboardingProps {
  onComplete?: () => void;
  onSkip?: () => void;
}

export function GuidedOnboarding({ onComplete, onSkip }: GuidedOnboardingProps) {
  const router = useRouter();
  const { user } = useAuthStore();
  const [status, setStatus] = useState<OnboardingStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [completing, setCompleting] = useState(false);
  const [currentStepIdx, setCurrentStepIdx] = useState(0);

  const loadStatus = useCallback(async () => {
    try {
      const s = await onboardingService.getStatus();
      setStatus(s);
      setCurrentStepIdx(s.current_step_index);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadStatus();
  }, [loadStatus]);

  const handleCompleteStep = async (stepKey: string) => {
    setCompleting(true);
    try {
      const updated = await onboardingService.completeStep(stepKey);
      setStatus(updated);
      if (updated.is_complete) {
        onComplete?.();
        router.push('/dashboard');
        return;
      }
      setCurrentStepIdx(updated.current_step_index);
    } catch {
      // ignore
    } finally {
      setCompleting(false);
    }
  };

  const handleSkip = async () => {
    try {
      await onboardingService.skipOnboarding();
    } catch {
      // ignore
    }
    onSkip?.();
    router.push('/dashboard');
  };

  const handleNavigate = (href: string, stepKey: string) => {
    router.push(href);
  };

  if (loading || !status || !user) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (status.is_complete) {
    onComplete?.();
    return null;
  }

  const flow = status.flow;
  const step = flow.steps[currentStepIdx];
  const isLastStep = currentStepIdx === flow.steps.length - 1;
  const progress = ((currentStepIdx + 1) / flow.steps.length) * 100;
  const StepIcon = getOnboardingIcon(step.icon);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-950 dark:to-slate-900">
      {/* Progress bar */}
      <div className="border-b border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
        <div className="mx-auto flex max-w-2xl items-center gap-2 px-6 py-4">
          <span className="text-sm font-medium text-slate-700 dark:text-slate-300">
            {flow.title}
          </span>
          <div className="flex-1" />
          <span className="text-xs text-slate-400">
            {status.completed_count}/{status.total_steps} completed
          </span>
          <button
            onClick={handleSkip}
            className="flex items-center gap-1 text-xs text-slate-400 hover:text-slate-600 dark:hover:text-slate-300"
          >
            Skip <X className="h-3 w-3" />
          </button>
        </div>
        <div className="h-1 bg-slate-200 dark:bg-slate-700">
          <div
            className="h-full bg-primary transition-all duration-300"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      <div className="mx-auto max-w-2xl px-6 py-12">
        {/* Step indicator */}
        <div className="mb-8 flex items-center justify-center gap-2">
          {flow.steps.map((s, i) => {
            const isCompleted = status.completed_steps.includes(s.key);
            const Icon = getOnboardingIcon(s.icon);
            return (
              <div
                key={s.key}
                className={cn(
                  'flex h-10 w-10 items-center justify-center rounded-full text-xs font-bold transition-all',
                  isCompleted
                    ? 'bg-green-500 text-white'
                    : i === currentStepIdx
                      ? 'bg-primary text-primary-foreground scale-110 shadow-md'
                      : 'bg-slate-200 text-slate-400 dark:bg-slate-700 dark:text-slate-500',
                )}
              >
                {isCompleted ? (
                  <CheckCircle2 size={18} />
                ) : (
                  <Icon size={16} />
                )}
              </div>
            );
          })}
        </div>

        {/* Current step content */}
        <Card className="border-2">
          <CardContent className="p-8 text-center">
            <div className="mx-auto mb-6 flex h-20 w-20 items-center justify-center rounded-2xl bg-primary/10 text-primary">
              <StepIcon size={36} />
            </div>
            <h2 className="text-2xl font-bold text-slate-900 dark:text-slate-100">
              {step.title}
            </h2>
            <p className="mx-auto mt-3 max-w-md text-slate-500 dark:text-slate-400">
              {step.description}
            </p>

            <div className="mt-8 flex flex-col items-center gap-3">
              <Button
                size="lg"
                onClick={() => handleNavigate(step.href, step.key)}
                className="gap-2"
              >
                {step.action_label || `Go to ${step.title}`}
                <ArrowRight size={18} />
              </Button>
              <Button
                variant="outline"
                onClick={() => handleCompleteStep(step.key)}
                disabled={completing}
                className="gap-2"
              >
                {completing ? (
                  <Loader2 size={16} className="animate-spin" />
                ) : (
                  <CheckCircle2 size={16} />
                )}
                Mark as Done
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Navigation */}
        <div className="mt-8 flex items-center justify-between">
          <Button
            variant="outline"
            onClick={() => setCurrentStepIdx((s) => Math.max(0, s - 1))}
            disabled={currentStepIdx === 0}
            className="gap-2"
          >
            <ArrowLeft size={16} /> Back
          </Button>
          <div className="text-xs text-slate-400">
            Step {currentStepIdx + 1} of {flow.steps.length}
          </div>
          {!isLastStep ? (
            <Button
              variant="outline"
              onClick={() => setCurrentStepIdx((s) => Math.min(flow.steps.length - 1, s + 1))}
              className="gap-2"
            >
              Next <ArrowRight size={16} />
            </Button>
          ) : (
            <Button onClick={handleSkip} className="gap-2">
              <Sparkles size={16} /> Finish
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
