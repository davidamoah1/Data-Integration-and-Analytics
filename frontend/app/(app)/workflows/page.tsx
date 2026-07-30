'use client';

import { useRouter } from 'next/navigation';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { WORKFLOWS } from '@/lib/workflows';
import { ArrowRight } from 'lucide-react';

const categoryColors: Record<string, string> = {
  healthcare: 'bg-red-500',
  research: 'bg-purple-500',
  business: 'bg-blue-500',
  education: 'bg-amber-500',
  government: 'bg-emerald-500',
  general: 'bg-slate-500',
};

export default function WorkflowsPage() {
  const router = useRouter();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Guided Workflows</h1>
        <p className="text-sm text-muted-foreground">
          Follow step-by-step workflows tailored to your industry and use case.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {WORKFLOWS.map((wf) => {
          const Icon = wf.icon;
          return (
            <Card
              key={wf.id}
              className="cursor-pointer transition-all hover:shadow-md hover:border-primary/50"
              onClick={() => router.push(`/workflows/${wf.id}`)}
            >
              <CardHeader>
                <div className="flex items-center gap-3">
                  <div className={`flex h-10 w-10 items-center justify-center rounded-lg ${categoryColors[wf.category] || 'bg-slate-500'} text-white`}>
                    <Icon className="h-5 w-5" />
                  </div>
                  <div>
                    <CardTitle className="text-base">{wf.title}</CardTitle>
                    <Badge variant="outline" className="mt-1 capitalize">{wf.category}</Badge>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <CardDescription>{wf.description}</CardDescription>
                <p className="mt-3 text-xs text-muted-foreground">{wf.steps.length} steps</p>
                <div className="mt-2 flex items-center gap-1 text-sm text-primary">
                  Start workflow <ArrowRight className="h-3 w-3" />
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
