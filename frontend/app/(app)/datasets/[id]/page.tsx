'use client';

import { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { ArrowLeft, Database, Table as TableIcon } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Skeleton, SkeletonTable } from '@/components/ui/Skeleton';
import { ErrorState } from '@/components/ui/ErrorState';
import { datasetService } from '@/services/datasets/datasetService';
import type { Dataset, DatasetPreview } from '@/types';
import { formatNumber, formatDate } from '@/lib/utils';

export default function DatasetDetailPage() {
  const router = useRouter();
  const params = useParams();
  const datasetId = params?.id as string;

  const [dataset, setDataset] = useState<Dataset | null>(null);
  const [preview, setPreview] = useState<DatasetPreview | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!datasetId) return;
    async function load() {
      try {
        setLoading(true);
        const [ds, prev] = await Promise.all([
          datasetService.get(datasetId),
          datasetService.preview(datasetId, 20).catch(() => null),
        ]);
        setDataset(ds);
        setPreview(prev);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load dataset');
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [datasetId]);

  if (loading) {
    return (
      <div className="space-y-6">
        <Button variant="ghost" onClick={() => router.push('/datasets')}>
          <ArrowLeft className="mr-2 h-4 w-4" /> Back
        </Button>
        <Skeleton className="h-12 w-full" />
        <SkeletonTable rows={5} />
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <Button variant="ghost" onClick={() => router.push('/datasets')}>
          <ArrowLeft className="mr-2 h-4 w-4" /> Back to Datasets
        </Button>
        <ErrorState message={error} onRetry={() => router.push('/datasets')} />
      </div>
    );
  }

  if (!dataset) {
    return (
      <div className="space-y-6">
        <Button variant="ghost" onClick={() => router.push('/datasets')}>
          <ArrowLeft className="mr-2 h-4 w-4" /> Back to Datasets
        </Button>
        <ErrorState title="Not Found" message="Dataset not found." />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Button variant="ghost" onClick={() => router.push('/datasets')}>
            <ArrowLeft className="mr-2 h-4 w-4" /> Back
          </Button>
          <div className="flex items-center gap-2">
            <Database className="h-5 w-5 text-primary" />
            <h1 className="text-2xl font-bold">{dataset.name}</h1>
          </div>
        </div>
        <div className="flex gap-2">
          <Badge variant="outline">{dataset.tier}</Badge>
          <Badge variant={dataset.status === 'ready' ? 'success' : dataset.status === 'failed' ? 'destructive' : 'warning'}>
            {dataset.status}
          </Badge>
        </div>
      </div>

      {/* Metadata */}
      <Card>
        <CardHeader>
          <CardTitle>Dataset Information</CardTitle>
          <CardDescription>{dataset.description || 'No description available'}</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <div>
              <p className="text-sm font-medium text-muted-foreground">Industry</p>
              <p className="mt-1">{dataset.industry || '—'}</p>
            </div>
            <div>
              <p className="text-sm font-medium text-muted-foreground">Rows</p>
              <p className="mt-1">{formatNumber(dataset.row_count)}</p>
            </div>
            <div>
              <p className="text-sm font-medium text-muted-foreground">Columns</p>
              <p className="mt-1">{formatNumber(dataset.column_count)}</p>
            </div>
            <div>
              <p className="text-sm font-medium text-muted-foreground">Quality Score</p>
              <p className="mt-1">
                {dataset.quality_score != null ? `${dataset.quality_score.toFixed(0)}%` : '—'}
              </p>
            </div>
            <div>
              <p className="text-sm font-medium text-muted-foreground">Owner</p>
              <p className="mt-1">{dataset.owner || '—'}</p>
            </div>
            <div>
              <p className="text-sm font-medium text-muted-foreground">Created</p>
              <p className="mt-1">{formatDate(dataset.created_at)}</p>
            </div>
            <div>
              <p className="text-sm font-medium text-muted-foreground">Updated</p>
              <p className="mt-1">{formatDate(dataset.updated_at)}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Data Preview */}
      {preview && (
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <TableIcon className="h-5 w-5" />
              <CardTitle>Data Preview</CardTitle>
            </div>
            <CardDescription>
              Showing {preview.rows.length} of {formatNumber(preview.total_rows)} rows
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="border-b bg-muted/50">
                  <tr>
                    {preview.columns.map((col) => (
                      <th key={col} className="p-2 text-left font-medium">{col}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {preview.rows.map((row, i) => (
                    <tr key={i} className="border-b">
                      {preview.columns.map((col) => (
                        <td key={col} className="p-2">{String(row[col] ?? '')}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
