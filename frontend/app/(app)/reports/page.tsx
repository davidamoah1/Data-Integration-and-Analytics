'use client';

import { FileText } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { EmptyState } from '@/components/ui/EmptyState';

export default function ReportsPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Reports</h1>
      <Card>
        <CardHeader>
          <CardTitle>Generated Reports</CardTitle>
          <CardDescription>View and export AI-generated reports</CardDescription>
        </CardHeader>
        <CardContent>
          <EmptyState
            icon={<FileText className="h-10 w-10" />}
            title="No reports yet"
            description="Generate a report from your data using the AI Copilot."
          />
        </CardContent>
      </Card>
    </div>
  );
}
