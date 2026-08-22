'use client';

import { useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { ArrowLeft, ArrowRight, CheckCircle2, Circle } from 'lucide-react';
import { WORKFLOWS } from '@/lib/workflows';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { toast } from '@/components/ui/Toaster';

export default function WorkflowRunnerPage() {
  const params = useParams();
  const router = useRouter();
  const workflowId = params.id as string;
  const workflow = WORKFLOWS.find((w) => w.id === workflowId);

  const [currentStep, setCurrentStep] = useState(0);
  const [completedSteps, setCompletedSteps] = useState<Set<number>>(new Set());

  if (!workflow) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold">Workflow not found</h1>
          <p className="mt-2 text-muted-foreground">The workflow you are looking for does not exist.</p>
          <Link href="/dashboard" className="mt-4 inline-block text-primary hover:underline">
            ← Back to Dashboard
          </Link>
        </div>
      </div>
    );
  }

  const Icon = workflow.icon;
  const step = workflow.steps[currentStep];
  const StepIcon = step.icon;
  const isLastStep = currentStep === workflow.steps.length - 1;
  const progress = Math.round(((completedSteps.size) / workflow.steps.length) * 100);

  const handleComplete = () => {
    setCompletedSteps((prev) => new Set(prev).add(currentStep));
    if (step.href) {
      window.open(step.href, '_blank');
    }
    toast.success(`${step.label} completed!`);

    if (!isLastStep) {
      setCurrentStep((c) => c + 1);
    } else {
      toast.success('Workflow complete! Great job.');
    }
  };

  const handleSkip = () => {
    if (!isLastStep) {
      setCurrentStep((c) => c + 1);
    }
  };

  const handleFinish = () => {
    toast.success('Workflow completed successfully!');
    router.push('/dashboard');
  };

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link href="/dashboard" className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground">
          <ArrowLeft size={16} /> Back
        </Link>
      </div>

      <div className="flex items-center gap-4">
        <div className={`flex h-14 w-14 items-center justify-center rounded-2xl ${workflow.color} text-white shadow-lg`}>
          <Icon className="h-7 w-7" />
        </div>
        <div>
          <h1 className="text-2xl font-bold">{workflow.title}</h1>
          <p className="text-sm text-muted-foreground">{workflow.description}</p>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="space-y-2">
        <div className="flex items-center justify-between text-sm">
          <span className="font-medium">Progress</span>
          <span className="text-muted-foreground">{completedSteps.size} of {workflow.steps.length} steps</span>
        </div>
        <div className="h-2 overflow-hidden rounded-full bg-muted">
          <div
            className="h-full rounded-full bg-primary transition-all duration-500"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      {/* Steps Overview */}
      <div className="space-y-1">
        {workflow.steps.map((s, idx) => {
          const SIcon = s.icon;
          const isCompleted = completedSteps.has(idx);
          const isCurrent = idx === currentStep;
          return (
            <div
              key={idx}
              className={`flex items-center gap-3 rounded-lg border p-3 transition-all ${
                isCurrent ? 'border-primary bg-primary/5 shadow-sm' : isCompleted ? 'border-green-200 bg-green-50' : 'border-border'
              }`}
            >
              <div className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${
                isCompleted ? 'bg-green-500 text-white' : isCurrent ? 'bg-primary text-primary-foreground' : 'bg-muted text-muted-foreground'
              }`}>
                {isCompleted ? <CheckCircle2 className="h-5 w-5" /> : <span className="text-xs font-bold">{idx + 1}</span>}
              </div>
              <div className="flex-1">
                <p className={`text-sm font-medium ${isCompleted ? 'text-green-700' : isCurrent ? 'text-foreground' : 'text-muted-foreground'}`}>
                  {s.label}
                </p>
                {isCurrent && (
                  <p className="mt-0.5 text-xs text-muted-foreground">{s.description}</p>
                )}
              </div>
              {isCurrent && s.href && (
                <Link href={s.href} target="_blank" className="text-xs text-primary hover:underline">
                  Open →
                </Link>
              )}
            </div>
          );
        })}
      </div>

      {/* Current Step Action */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <StepIcon className="h-5 w-5 text-primary" />
            Step {currentStep + 1}: {step.label}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm text-muted-foreground">{step.description}</p>

          <div className="flex items-center gap-3">
            {isLastStep ? (
              <Button onClick={handleFinish} className="gap-2">
                <CheckCircle2 className="h-4 w-4" />
                Finish Workflow
              </Button>
            ) : (
              <>
                <Button onClick={handleComplete} className="gap-2">
                  <CheckCircle2 className="h-4 w-4" />
                  Complete & Continue
                </Button>
                <Button variant="ghost" onClick={handleSkip} className="gap-2">
                  Skip <ArrowRight className="h-4 w-4" />
                </Button>
              </>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
