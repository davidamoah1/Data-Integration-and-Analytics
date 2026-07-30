'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { CheckCircle2, ArrowRight, ArrowLeft, X } from 'lucide-react';
import { useAuthStore } from '@/stores/authStore';
import { getOnboardingFlowForRoles } from '@/lib/onboarding';
import { Button } from '@/components/ui/Button';
import { cn } from '@/lib/utils';

interface AdaptiveOnboardingProps {
  onComplete?: () => void;
  onSkip?: () => void;
}

export function AdaptiveOnboarding({ onComplete, onSkip }: AdaptiveOnboardingProps) {
  const router = useRouter();
  const { user } = useAuthStore();
  const [currentStep, setCurrentStep] = useState(0);
  const [completed, setCompleted] = useState<Set<string>>(new Set());

  if (!user) return null;

  const flow = getOnboardingFlowForRoles(user.roles);
  const step = flow.steps[currentStep];
  const isLastStep = currentStep === flow.steps.length - 1;
  const progress = ((currentStep + 1) / flow.steps.length) * 100;

  const handleNext = () => {
    if (isLastStep) {
      onComplete?.();
      router.push('/dashboard');
      return;
    }
    setCompleted((prev) => new Set(prev).add(step.id));
    setCurrentStep((s) => s + 1);
  };

  const handleBack = () => {
    setCurrentStep((s) => Math.max(0, s - 1));
  };

  const handleSkip = () => {
    onSkip?.();
    router.push('/dashboard');
  };

  const StepIcon = step.icon;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-950 dark:to-slate-900">
      {/* Progress bar */}
      <div className="border-b border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
        <div className="mx-auto flex max-w-2xl items-center gap-2 px-6 py-4">
          <span className="text-sm font-medium text-slate-700 dark:text-slate-300">
            {flow.title}
          </span>
          <div className="flex-1" />
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
          {flow.steps.map((s, i) => (
            <div
              key={s.id}
              className={cn(
                'flex h-8 w-8 items-center justify-center rounded-full text-xs font-bold transition-colors',
                i < currentStep || completed.has(s.id)
                  ? 'bg-green-500 text-white'
                  : i === currentStep
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-slate-200 text-slate-400 dark:bg-slate-700 dark:text-slate-500'
              )}
            >
              {i < currentStep || completed.has(s.id) ? (
                <CheckCircle2 size={16} />
              ) : (
                i + 1
              )}
            </div>
          ))}
        </div>

        {/* Current step content */}
        <div className="text-center">
          <div className="mx-auto mb-6 flex h-20 w-20 items-center justify-center rounded-2xl bg-primary/10 text-primary">
            <StepIcon size={36} />
          </div>
          <h2 className="text-2xl font-bold text-slate-900 dark:text-slate-100">
            {step.title}
          </h2>
          <p className="mx-auto mt-3 max-w-md text-slate-500 dark:text-slate-400">
            {step.description}
          </p>

          {step.href && !isLastStep && (
            <div className="mt-6">
              <Button
                onClick={() => router.push(step.href!)}
                variant="outline"
                className="gap-2"
              >
                Go to {step.title} <ArrowRight size={16} />
              </Button>
            </div>
          )}
        </div>

        {/* Navigation */}
        <div className="mt-12 flex items-center justify-between">
          <Button
            variant="outline"
            onClick={handleBack}
            disabled={currentStep === 0}
            className="gap-2"
          >
            <ArrowLeft size={16} /> Back
          </Button>
          <div className="text-xs text-slate-400">
            Step {currentStep + 1} of {flow.steps.length}
          </div>
          <Button onClick={handleNext} className="gap-2">
            {isLastStep ? (
              <>
                Get Started <CheckCircle2 size={16} />
              </>
            ) : (
              <>
                Continue <ArrowRight size={16} />
              </>
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}
