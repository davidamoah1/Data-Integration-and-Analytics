'use client';

import { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { ArrowLeft, Download, FileText, Loader2 } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Skeleton } from '@/components/ui/Skeleton';
import { ErrorState } from '@/components/ui/ErrorState';
import { EmptyState } from '@/components/ui/EmptyState';
import { reportService, type AIReportDetail } from '@/services/reports/reportService';
import { getAccessToken } from '@/services/api/client';
import { formatDate } from '@/lib/utils';

export default function ReportDetailPage() {
  const router = useRouter();
  const params = useParams();
  const reportId = Number(params.id);

  const [report, setReport] = useState<AIReportDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [downloading, setDownloading] = useState<string | null>(null);

  useEffect(() => {
    if (!reportId) return;
    async function load() {
      try {
        setLoading(true);
        const data = await reportService.getReport(reportId);
        setReport(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load report');
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [reportId]);

  async function handleDownload(format: 'pdf' | 'csv' | 'xlsx') {
    if (!reportId) return;
    setDownloading(format);
    try {
      const url = await reportService.exportReportUrl(reportId, format);
      const token = getAccessToken();
      const response = await fetch(url, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (!response.ok) throw new Error('Download failed');
      const blob = await response.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = downloadUrl;
      a.download = `report_${reportId}.${format}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(downloadUrl);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Download failed');
    } finally {
      setDownloading(null);
    }
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <Button variant="ghost" size="sm" onClick={() => router.push('/reports')}>
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to Reports
        </Button>
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-4 w-96" />
        <Skeleton className="h-96 w-full" />
      </div>
    );
  }

  if (error) return <ErrorState message={error} onRetry={() => router.push('/reports')} />;

  if (!report) {
    return (
      <div className="space-y-6">
        <Button variant="ghost" size="sm" onClick={() => router.push('/reports')}>
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to Reports
        </Button>
        <EmptyState
          icon={<FileText className="h-10 w-10" />}
          title="Report not found"
          description="This report may have been deleted."
        />
      </div>
    );
  }

  const sections = Array.isArray(report.sections) ? report.sections as string[] : [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="sm" onClick={() => router.push('/reports')}>
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back
          </Button>
          <div>
            <h1 className="text-2xl font-bold">{report.title}</h1>
            <div className="flex items-center gap-2 mt-1">
              <Badge variant="outline">{report.report_type}</Badge>
              {report.created_at && (
                <span className="text-xs text-muted-foreground">{formatDate(report.created_at)}</span>
              )}
            </div>
          </div>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => handleDownload('pdf')}
            disabled={downloading !== null}
          >
            {downloading === 'pdf' ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Download className="mr-2 h-4 w-4" />}
            PDF
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => handleDownload('csv')}
            disabled={downloading !== null}
          >
            {downloading === 'csv' ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Download className="mr-2 h-4 w-4" />}
            CSV
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => handleDownload('xlsx')}
            disabled={downloading !== null}
          >
            {downloading === 'xlsx' ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Download className="mr-2 h-4 w-4" />}
            Excel
          </Button>
        </div>
      </div>

      {/* Summary */}
      {report.summary && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Summary</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">{report.summary}</p>
          </CardContent>
        </Card>
      )}

      {/* Sections */}
      {sections.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Sections</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {sections.map((section, i) => (
                <Badge key={i} variant="secondary">{section}</Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Content */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Report Content</CardTitle>
          <CardDescription>Full report details in markdown format</CardDescription>
        </CardHeader>
        <CardContent>
          {report.content ? (
            <div className="prose prose-sm max-w-none dark:prose-invert">
              <pre className="whitespace-pre-wrap text-sm font-sans leading-relaxed text-foreground">
                {report.content}
              </pre>
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">No content available.</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
