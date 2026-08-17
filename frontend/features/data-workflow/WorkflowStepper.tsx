'use client';

import { CheckCircle2, Upload, Search, Sparkles, BarChart3, LayoutDashboard, FileText, Presentation } from 'lucide-react';
import { cn } from '@/lib/utils';

export type WorkflowStep =
  | 'upload'
  | 'understand'
  | 'clean'
  | 'analyze'
  | 'visualize'
  | 'report'
  | 'present';

export type StepStatus = 'pending' | 'active' | 'completed' | 'error';

interface StepConfig {
  key: WorkflowStep;
  label: string;
  icon: React.ReactNode;
}

const STEPS: StepConfig[] = [
  { key: 'upload', label: 'Upload', icon: <Upload className="h-4 w-4" /> },
  { key: 'understand', label: 'Understand', icon: <Search className="h-4 w-4" /> },
  { key: 'clean', label: 'Clean', icon: <Sparkles className="h-4 w-4" /> },
  { key: 'analyze', label: 'Analyze', icon: <BarChart3 className="h-4 w-4" /> },
  { key: 'visualize', label: 'Visualize', icon: <LayoutDashboard className="h-4 w-4" /> },
  { key: 'report', label: 'Report', icon: <FileText className="h-4 w-4" /> },
  { key: 'present', label: 'Present', icon: <Presentation className="h-4 w-4" /> },
];

interface Props {
  currentStep: WorkflowStep;
  stepStatuses: Partial<Record<WorkflowStep, StepStatus>>;
  onStepClick?: (step: WorkflowStep) => void;
}

export function WorkflowStepper({ currentStep, stepStatuses, onStepClick }: Props) {
  const currentIdx = STEPS.findIndex((s) => s.key === currentStep);

  return (
    <nav aria-label="Data workflow progress" className="w-full">
      <ol className="flex items-center justify-between">
        {STEPS.map((step, idx) => {
          const status = stepStatuses[step.key] || 'pending';
          const isActive = step.key === currentStep;
          const isCompleted = status === 'completed';
          const isClickable = isCompleted || isActive;

          return (
            <li key={step.key} className="flex flex-1 items-center">
              <button
                type="button"
                onClick={() => isClickable && onStepClick?.(step.key)}
                disabled={!isClickable}
                className={cn(
                  'flex flex-col items-center gap-1.5 transition-colors w-full group',
                  isClickable ? 'cursor-pointer' : 'cursor-default',
                )}
                aria-current={isActive ? 'step' : undefined}
              >
                <div
                  className={cn(
                    'flex h-10 w-10 items-center justify-center rounded-full border-2 transition-all',
                    isCompleted && 'border-green-600 bg-green-600 text-white',
                    isActive && !isCompleted && 'border-primary bg-primary text-primary-foreground shadow-md shadow-primary/25',
                    status === 'error' && 'border-red-500 bg-red-50 text-red-600 dark:bg-red-950',
                    status === 'pending' && !isActive && 'border-muted-foreground/30 text-muted-foreground/50',
                  )}
                >
                  {isCompleted ? <CheckCircle2 className="h-5 w-5" /> : step.icon}
                </div>
                <span
                  className={cn(
                    'text-xs font-medium transition-colors',
                    isActive && 'text-primary',
                    isCompleted && 'text-green-700 dark:text-green-400',
                    status === 'pending' && !isActive && 'text-muted-foreground/60',
                  )}
                >
                  {step.label}
                </span>
              </button>

              {idx < STEPS.length - 1 && (
                <div
                  className={cn(
                    'h-0.5 flex-1 mx-1 mt-[-1.25rem]',
                    idx < currentIdx ? 'bg-green-600' : 'bg-muted-foreground/20',
                  )}
                  aria-hidden="true"
                />
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
