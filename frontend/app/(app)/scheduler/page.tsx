'use client';

import { useRouter } from 'next/navigation';
import { CalendarClock, Plus, ArrowRight, FileText } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';

export default function SchedulerPage() {
  const router = useRouter();

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Scheduler</h1>
          <p className="text-sm text-muted-foreground">Manage automated report schedules</p>
        </div>
        <Button onClick={() => router.push('/reports')} className="gap-2">
          <Plus className="h-4 w-4" /> New Schedule
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Scheduled Reports</CardTitle>
          <CardDescription>Automate recurring report generation and delivery</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <CalendarClock className="mb-4 h-12 w-12 text-muted-foreground/50" />
            <h3 className="text-lg font-semibold">No scheduled reports</h3>
            <p className="mt-1 max-w-sm text-sm text-muted-foreground">
              Schedule reports to run automatically on a daily, weekly, or monthly basis.
              Generated reports will be delivered to your notifications.
            </p>
            <Button
              onClick={() => router.push('/reports')}
              variant="outline"
              className="mt-4 gap-2"
            >
              <FileText className="h-4 w-4" />
              Go to Reports <ArrowRight className="h-4 w-4" />
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
