'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import {
  ArrowLeft,
  Package,
  CheckCircle,
  XCircle,
  AlertCircle,
  RefreshCw,
  Loader2,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Alert, AlertDescription } from '@/components/ui/Alert';
import { Table, TableRow, TableCell } from '@/components/ui/Table';
import { SkeletonTable } from '@/components/ui/Skeleton';
import { ErrorState } from '@/components/ui/ErrorState';
import { toast } from '@/components/ui/Toaster';
import {
  etlPackageService,
  type ETLPackageProgress,
  type ETLPackageFile,
  type ETLPackageError,
} from '@/services/etl/etlPackageService';
import { formatNumber, formatDate } from '@/lib/utils';

type Tab = 'overview' | 'files' | 'errors';

export default function PackageDetailsPage() {
  const params = useParams();
  const router = useRouter();
  const packageId = Number(params?.id);

  const [progress, setProgress] = useState<ETLPackageProgress | null>(null);
  const [files, setFiles] = useState<ETLPackageFile[]>([]);
  const [errors, setErrors] = useState<ETLPackageError[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState<Tab>('overview');
  const [isPolling, setIsPolling] = useState(false);

  useEffect(() => {
    if (!packageId) return;
    loadData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [packageId]);

  useEffect(() => {
    if (!progress) return;
    const isActive = ['uploaded', 'extracting', 'discovering', 'processing'].includes(
      progress.status,
    );
    if (isActive && !isPolling) {
      setIsPolling(true);
      const interval = setInterval(async () => {
        try {
          const p = await etlPackageService.getProgress(packageId);
          setProgress(p);
          if (['completed', 'completed_with_errors', 'failed', 'cancelled'].includes(p.status)) {
            clearInterval(interval);
            setIsPolling(false);
            loadFiles();
            loadErrors();
          }
        } catch {
          // ignore
        }
      }, 3000);
      return () => {
        clearInterval(interval);
        setIsPolling(false);
      };
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [progress, packageId, isPolling]);

  async function loadData() {
    try {
      setLoading(true);
      const p = await etlPackageService.getProgress(packageId);
      setProgress(p);
      await loadFiles();
      await loadErrors();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load package');
    } finally {
      setLoading(false);
    }
  }

  async function loadFiles() {
    try {
      const res = await etlPackageService.getFiles(packageId, { limit: 500 });
      setFiles(res.files);
    } catch {
      // ignore
    }
  }

  async function loadErrors() {
    try {
      const res = await etlPackageService.getErrors(packageId);
      setErrors(res.errors);
    } catch {
      // ignore
    }
  }

  async function handleRetry() {
    try {
      const result = await etlPackageService.retryFailed(packageId);
      toast.success(`Retrying ${result.retried} failed files`);
      loadData();
    } catch {
      toast.error('Failed to retry');
    }
  }

  if (loading) {
    return (
      <div className="container mx-auto py-6">
        <SkeletonTable rows={5} />
      </div>
    );
  }

  if (error || !progress) {
    return (
      <div className="container mx-auto py-6">
        <ErrorState
          title="Package Not Found"
          message={error || 'The requested package could not be found.'}
          onRetry={() => router.push('/datasets/etl-packages')}
        />
      </div>
    );
  }

  const isActive = ['uploaded', 'extracting', 'discovering', 'processing'].includes(
    progress.status,
  );

  const statusIcon = {
    completed: <CheckCircle className="h-6 w-6 text-green-600" />,
    completed_with_errors: <AlertCircle className="h-6 w-6 text-yellow-600" />,
    failed: <XCircle className="h-6 w-6 text-red-600" />,
    cancelled: <XCircle className="h-6 w-6 text-gray-500" />,
    uploaded: <Package className="h-6 w-6 text-blue-600" />,
    extracting: <Loader2 className="h-6 w-6 text-blue-600 animate-spin" />,
    discovering: <Loader2 className="h-6 w-6 text-blue-600 animate-spin" />,
    processing: <Loader2 className="h-6 w-6 text-blue-600 animate-spin" />,
  };

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="sm" onClick={() => router.push('/datasets/etl-packages')}>
          <ArrowLeft className="h-4 w-4 mr-1" /> Back
        </Button>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              {statusIcon[progress.status as keyof typeof statusIcon] || (
                <Package className="h-6 w-6 text-gray-400" />
              )}
              <div>
                <CardTitle className="text-xl">{progress.filename}</CardTitle>
                <CardDescription>
                  Package #{packageId} • {progress.status.replace(/_/g, ' ')}
                </CardDescription>
              </div>
            </div>
            <div className="flex gap-2">
              {progress.failed_files > 0 && !isActive && (
                <Button variant="outline" size="sm" onClick={handleRetry}>
                  <RefreshCw className="h-4 w-4 mr-1" /> Retry Failed
                </Button>
              )}
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {isActive && (
            <div className="mb-4">
              <div className="flex justify-between text-sm mb-1">
                <span className="text-gray-600 capitalize">
                  {progress.current_stage || progress.status}
                </span>
                <span className="font-medium">{progress.percentage}%</span>
              </div>
              <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                <div
                  className="h-full bg-blue-600 transition-all duration-500"
                  style={{ width: `${progress.percentage}%` }}
                />
              </div>
            </div>
          )}

          <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
            <StatBox label="Total Files" value={progress.total_files} />
            <StatBox label="Completed" value={progress.completed_files} color="green" />
            <StatBox label="Failed" value={progress.failed_files} color="red" />
            <StatBox label="Duplicates" value={progress.duplicate_files} color="yellow" />
            <StatBox label="Unsupported" value={progress.unsupported_files} color="gray" />
          </div>

          {(progress.total_rows_loaded > 0 || progress.total_rows_extracted > 0) && (
            <div className="grid grid-cols-3 gap-3 mt-3">
              <StatBox label="Rows Extracted" value={progress.total_rows_extracted} />
              <StatBox label="Rows Loaded" value={progress.total_rows_loaded} color="green" />
              <StatBox label="Rows Rejected" value={progress.total_rows_rejected} color="red" />
            </div>
          )}

          {progress.overall_quality_score !== null && (
            <div className="mt-3 flex items-center gap-2">
              <Badge variant="secondary">
                Quality Score: {progress.overall_quality_score}/100
              </Badge>
              {progress.started_at && (
                <Badge variant="outline">
                  Started: {formatDate(progress.started_at)}
                </Badge>
              )}
              {progress.completed_at && (
                <Badge variant="outline">
                  Completed: {formatDate(progress.completed_at)}
                </Badge>
              )}
            </div>
          )}

          {progress.error_message && (
            <Alert variant="destructive" className="mt-4">
              <AlertDescription>{progress.error_message}</AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>

      <div className="flex gap-2 border-b">
        <TabButton active={tab === 'overview'} onClick={() => setTab('overview')}>
          Overview
        </TabButton>
        <TabButton active={tab === 'files'} onClick={() => setTab('files')}>
          Files ({files.length})
        </TabButton>
        <TabButton active={tab === 'errors'} onClick={() => setTab('errors')}>
          Errors ({errors.length})
        </TabButton>
      </div>

      {tab === 'overview' && (
        <Card>
          <CardContent className="py-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
              <InfoRow label="Filename" value={progress.filename} />
              <InfoRow label="Status" value={progress.status.replace(/_/g, ' ')} />
              <InfoRow
                label="Current Stage"
                value={progress.current_stage || 'N/A'}
              />
              <InfoRow label="Total Files" value={String(progress.total_files)} />
              <InfoRow
                label="Rows Extracted"
                value={formatNumber(progress.total_rows_extracted)}
              />
              <InfoRow
                label="Rows Loaded"
                value={formatNumber(progress.total_rows_loaded)}
              />
              <InfoRow
                label="Quality Score"
                value={progress.overall_quality_score !== null
                  ? `${progress.overall_quality_score}/100`
                  : 'N/A'}
              />
              <InfoRow
                label="Started"
                value={progress.started_at ? formatDate(progress.started_at) : 'N/A'}
              />
              <InfoRow
                label="Completed"
                value={progress.completed_at ? formatDate(progress.completed_at) : 'N/A'}
              />
            </div>
          </CardContent>
        </Card>
      )}

      {tab === 'files' && (
        <Card>
          <CardContent className="py-4">
            {files.length === 0 ? (
              <p className="text-center text-gray-500 py-8">No files discovered yet.</p>
            ) : (
              <div className="overflow-x-auto">
                <Table headers={['Filename', 'Type', 'Rows', 'Quality', 'Status']}>
                    {files.map((f) => (
                      <TableRow key={f.id}>
                        <TableCell className="font-medium">{f.filename}</TableCell>
                        <TableCell>
                          <Badge variant="outline">{f.extension}</Badge>
                        </TableCell>
                        <TableCell className="text-right">
                          {f.row_count !== null ? formatNumber(f.row_count) : '-'}
                        </TableCell>
                        <TableCell className="text-right">
                          {f.quality_score !== null ? `${f.quality_score}` : '-'}
                        </TableCell>
                        <TableCell>
                          <FileStatusBadge status={f.status} />
                        </TableCell>
                      </TableRow>
                    ))}
                </Table>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {tab === 'errors' && (
        <Card>
          <CardContent className="py-4">
            {errors.length === 0 ? (
              <p className="text-center text-gray-500 py-8">No errors recorded.</p>
            ) : (
              <div className="space-y-3">
                {errors.map((e) => (
                  <div
                    key={e.file_id}
                    className="flex items-start gap-3 p-3 rounded-lg border border-red-200 bg-red-50"
                  >
                    <XCircle className="h-5 w-5 text-red-600 mt-0.5 flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <div className="font-medium text-sm">{e.filename}</div>
                      <div className="text-xs text-gray-600 mt-1">{e.error_message}</div>
                      {e.error_stage && (
                        <Badge variant="outline" className="mt-1">
                          Stage: {e.error_stage}
                        </Badge>
                      )}
                    </div>
                    {e.retry_count > 0 && (
                      <Badge variant="secondary">Retried {e.retry_count}x</Badge>
                    )}
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function StatBox({
  label,
  value,
  color = 'blue',
}: {
  label: string;
  value: number;
  color?: 'blue' | 'green' | 'red' | 'yellow' | 'gray';
}) {
  const colors = {
    blue: 'bg-blue-50 text-blue-700',
    green: 'bg-green-50 text-green-700',
    red: 'bg-red-50 text-red-700',
    yellow: 'bg-yellow-50 text-yellow-700',
    gray: 'bg-gray-50 text-gray-700',
  };
  return (
    <div className={`rounded-lg p-3 text-center ${colors[color]}`}>
      <div className="text-xl font-bold">{formatNumber(value)}</div>
      <div className="text-xs mt-1 opacity-80">{label}</div>
    </div>
  );
}

function TabButton({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      onClick={onClick}
      className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
        active
          ? 'border-blue-600 text-blue-600'
          : 'border-transparent text-gray-500 hover:text-gray-700'
      }`}
    >
      {children}
    </button>
  );
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between border-b pb-2">
      <span className="text-gray-500">{label}</span>
      <span className="font-medium">{value}</span>
    </div>
  );
}

function FileStatusBadge({ status }: { status: string }) {
  const variants: Record<string, 'default' | 'secondary' | 'destructive' | 'outline'> = {
    completed: 'default',
    failed: 'destructive',
    duplicate: 'secondary',
    unsupported: 'outline',
    processing: 'secondary',
    discovered: 'outline',
    queued: 'outline',
    skipped: 'outline',
  };
  return <Badge variant={variants[status] || 'outline'}>{status}</Badge>;
}
