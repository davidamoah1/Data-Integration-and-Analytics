'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { FileText, Download, ChevronRight, BarChart3 } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Skeleton, SkeletonCard } from '@/components/ui/Skeleton';
import { ErrorState } from '@/components/ui/ErrorState';
import { EmptyState } from '@/components/ui/EmptyState';
import { reportService, type AIReport } from '@/services/reports/reportService';
import { formatDate } from '@/lib/utils';

export default function ReportsPage() {
  const router = useRouter();
  const [reports, setReports] = useState<AIReport[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        setLoading(true);
        const data = await reportService.listReports();
        setReports(data || []);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load reports');
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold">Reports</h1>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 3 }).map((_, i) => <SkeletonCard key={i} />)}
        </div>
      </div>
    );
  }

  if (error) return <ErrorState message={error} />;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Reports</h1>
        <Badge variant="secondary">{reports.length} report{reports.length !== 1 ? 's' : ''}</Badge>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Generated Reports</CardTitle>
          <CardDescription>View and export automated reports from your datasets</CardDescription>
        </CardHeader>
        <CardContent>
          {reports.length === 0 ? (
            <EmptyState
              icon={<FileText className="h-10 w-10" />}
              title="No reports yet"
              description="Upload a dataset and run semantic analysis to generate reports. You can also use the Analytics Assistant to generate custom reports."
            />
          ) : (
            <div className="space-y-2">
              {reports.map((report) => (
                <div
                  key={report.id}
                  className="flex items-center justify-between rounded-lg border p-4 hover:bg-accent cursor-pointer"
                  onClick={() => router.push(`/reports/${report.id}`)}
                >
                  <div className="flex items-center gap-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                      <BarChart3 className="h-5 w-5 text-primary" />
                    </div>
                    <div>
                      <p className="font-medium">{report.title}</p>
                      <div className="flex items-center gap-2 mt-0.5">
                        <Badge variant="outline" className="text-xs">{report.report_type}</Badge>
                        {report.created_at && (
                          <span className="text-xs text-muted-foreground">
                            {formatDate(report.created_at)}
                          </span>
                        )}
                      </div>
                      {report.summary && (
                        <p className="text-xs text-muted-foreground mt-1 line-clamp-2">{report.summary}</p>
                      )}
                    </div>
                  </div>
                  <ChevronRight className="h-5 w-5 text-muted-foreground" />
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
