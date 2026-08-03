'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import {
  Database, BarChart3, Lightbulb, FileText, Presentation as PresentationIcon,
  ArrowRight, Check, Loader2,
} from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Card, CardContent } from '@/components/ui/Card';
import { cn } from '@/lib/utils';
import { reportEngineService } from '@/services/reports/reportEngineService';
import { toast } from '@/components/ui/Toaster';

const STEPS = [
  {
    key: 'dataset',
    label: 'Dataset',
    icon: Database,
    description: 'Select or upload a dataset',
    href: '/datasets',
  },
  {
    key: 'analysis',
    label: 'Analysis',
    icon: BarChart3,
    description: 'Run statistical analysis on your data',
    href: '/analytics',
  },
  {
    key: 'insights',
    label: 'Insights',
    icon: Lightbulb,
    description: 'Review AI-generated insights',
    href: '/insights',
  },
  {
    key: 'report',
    label: 'Report',
    icon: FileText,
    description: 'Generate an executive-ready report',
    href: '/reports/builder',
  },
  {
    key: 'presentation',
    label: 'Presentation',
    icon: PresentationIcon,
    description: 'Export as a PowerPoint presentation',
    href: '/reports/builder',
  },
];

export function ReportWorkflow() {
  const router = useRouter();
  const [currentStep, setCurrentStep] = useState(0);
  const [completed, setCompleted] = useState<Set<string>>(new Set());
  const [creating, setCreating] = useState(false);

  const handleStepClick = (stepIndex: number) => {
    const step = STEPS[stepIndex];
    if (step.href) {
      router.push(step.href);
    }
  };

  const handleComplete = (stepIndex: number) => {
    const step = STEPS[stepIndex];
    setCompleted((prev) => new Set([...prev, step.key]));
    if (stepIndex < STEPS.length - 1) {
      setCurrentStep(stepIndex + 1);
    }
  };

  const handleCreateReport = async () => {
    setCreating(true);
    try {
      const report = await reportEngineService.createReport({
        title: 'Executive Report',
        template: 'executive',
      });
      toast.success('Report created successfully');
      router.push(`/reports/builder?id=${report.report_id}`);
    } catch {
      toast.error('Failed to create report');
    } finally {
      setCreating(false);
    }
  };

  return (
    <Card>
      <CardContent className="p-6">
        <h3 className="mb-1 text-lg font-semibold">Report Generation Workflow</h3>
        <p className="mb-6 text-sm text-muted-foreground">
          Follow these steps to create executive-ready reports and presentations
        </p>

        {/* Workflow steps */}
        <div className="flex items-center justify-between">
          {STEPS.map((step, i) => {
            const isCompleted = completed.has(step.key);
            const isCurrent = i === currentStep;
            const Icon = step.icon;

            return (
              <div key={step.key} className="flex flex-1 items-center">
                <button
                  onClick={() => handleStepClick(i)}
                  className="group flex flex-col items-center gap-2"
                >
                  <div
                    className={cn(
                      'flex h-12 w-12 items-center justify-center rounded-full border-2 transition-all',
                      isCompleted
                        ? 'border-green-500 bg-green-500 text-white'
                        : isCurrent
                          ? 'border-primary bg-primary text-primary-foreground scale-110 shadow-md'
                          : 'border-slate-200 bg-white text-slate-400 dark:border-slate-700 dark:bg-slate-800'
                    )}
                  >
                    {isCompleted ? <Check size={20} /> : <Icon size={20} />}
                  </div>
                  <span
                    className={cn(
                      'text-xs font-medium',
                      isCurrent ? 'text-primary' : isCompleted ? 'text-green-600' : 'text-muted-foreground'
                    )}
                  >
                    {step.label}
                  </span>
                </button>
                {i < STEPS.length - 1 && (
                  <div className={cn(
                    'mx-2 h-0.5 flex-1 transition-colors',
                    completed.has(STEPS[i].key) ? 'bg-green-500' : 'bg-slate-200 dark:bg-slate-700'
                  )} />
                )}
              </div>
            );
          })}
        </div>

        {/* Current step detail */}
        <div className="mt-6 rounded-lg border bg-muted/30 p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-semibold">{STEPS[currentStep].label}</p>
              <p className="text-xs text-muted-foreground">{STEPS[currentStep].description}</p>
            </div>
            <div className="flex gap-2">
              <Button
                size="sm"
                variant="outline"
                onClick={() => handleStepClick(currentStep)}
                className="gap-1"
              >
                Go to {STEPS[currentStep].label} <ArrowRight size={14} />
              </Button>
              <Button
                size="sm"
                onClick={() => handleComplete(currentStep)}
                className="gap-1"
              >
                <Check size={14} /> Mark Done
              </Button>
            </div>
          </div>
        </div>

        {/* Quick create */}
        {currentStep >= 3 && (
          <div className="mt-4 flex justify-end">
            <Button onClick={handleCreateReport} disabled={creating} className="gap-2">
              {creating ? <Loader2 size={16} className="animate-spin" /> : <FileText size={16} />}
              Create Executive Report
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
