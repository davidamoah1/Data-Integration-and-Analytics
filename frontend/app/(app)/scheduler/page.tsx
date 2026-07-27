'use client';

import { CalendarClock } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { EmptyState } from '@/components/ui/EmptyState';

export default function SchedulerPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Scheduler</h1>
      <Card>
        <CardHeader>
          <CardTitle>Scheduled Reports</CardTitle>
          <CardDescription>Manage automated report schedules</CardDescription>
        </CardHeader>
        <CardContent>
          <EmptyState
            icon={<CalendarClock className="h-10 w-10" />}
            title="No scheduled reports"
            description="Schedule reports to run automatically on a recurring basis."
          />
        </CardContent>
      </Card>
    </div>
  );
}
