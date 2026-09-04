'use client';

import { useState, useCallback, useRef, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import {
  Upload,
  FileArchive,
  CheckCircle,
  XCircle,
  Loader2,
  Package,
  AlertCircle,
  RefreshCw,
  X,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Alert, AlertDescription } from '@/components/ui/Alert';
import { toast } from '@/components/ui/Toaster';
import { etlPackageService, type ETLPackageProgress } from '@/services/etl/etlPackageService';
import { cn, formatNumber } from '@/lib/utils';

type UploadStage = 'idle' | 'uploading' | 'processing' | 'done' | 'error';

type ErrorType = 'upload_failed' | 'processing_failed' | 'backend_unavailable' | 'unknown';

const POLL_INITIAL_DELAY_MS = 2000;
const POLL_MAX_DELAY_MS = 30000;
const POLL_MAX_CONSECUTIVE_ERRORS = 10;

export function ETLPackageUpload() {
  const router = useRouter();
  const [stage, setStage] = useState<UploadStage>('idle');
  const [uploadProgress, setUploadProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [errorType, setErrorType] = useState<ErrorType | null>(null);
  const [packageId, setPackageId] = useState<number | null>(null);
  const [progress, setProgress] = useState<ETLPackageProgress | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const [connectionLost, setConnectionLost] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const pollRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const consecutiveErrorsRef = useRef(0);
  const pollDelayRef = useRef(POLL_INITIAL_DELAY_MS);

  useEffect(() => {
    return () => {
      if (pollRef.current) clearTimeout(pollRef.current);
    };
  }, []);

  const startPolling = useCallback((id: number) => {
    if (pollRef.current) clearTimeout(pollRef.current);
    consecutiveErrorsRef.current = 0;
    pollDelayRef.current = POLL_INITIAL_DELAY_MS;
    setConnectionLost(false);

    const poll = async () => {
      try {
        const p = await etlPackageService.getProgress(id);
        setProgress(p);
        consecutiveErrorsRef.current = 0;
        pollDelayRef.current = POLL_INITIAL_DELAY_MS;
        setConnectionLost(false);

        if (['completed', 'completed_with_errors', 'failed', 'cancelled'].includes(p.status)) {
          pollRef.current = null;
          setStage('done');
          return;
        }

        // Schedule next poll with reset delay
        pollRef.current = setTimeout(poll, pollDelayRef.current);
      } catch {
        consecutiveErrorsRef.current += 1;

        if (consecutiveErrorsRef.current >= POLL_MAX_CONSECUTIVE_ERRORS) {
          // Too many consecutive errors — show connection lost but DON'T
          // change the stage. The package may still be processing.
          setConnectionLost(true);
        }

        // Exponential backoff: double the delay, cap at max
        pollDelayRef.current = Math.min(
          pollDelayRef.current * 2,
          POLL_MAX_DELAY_MS,
        );
        pollRef.current = setTimeout(poll, pollDelayRef.current);
      }
    };

    pollRef.current = setTimeout(poll, pollDelayRef.current);
  }, []);

  const handleFile = useCallback(
    async (file: File) => {
      if (!file.name.toLowerCase().endsWith('.zip')) {
        setError('Please select a ZIP file (.zip)');
        toast.error('Please select a ZIP file');
        return;
      }

      setError(null);
      setStage('uploading');
      setUploadProgress(0);
      setProgress(null);

      try {
        const result = await etlPackageService.upload(file, (percent) => {
          setUploadProgress(percent);
        });

        setPackageId(result.package_id);
        setStage('processing');
        toast.success('Package uploaded. Processing started in background.');
        startPolling(result.package_id);
      } catch (err) {
        const msg = err instanceof Error ? err.message : 'Upload failed';
        // Distinguish upload errors from backend unavailable
        if (msg.includes('Unable to connect to the server') || msg.includes('timed out')) {
          setErrorType('backend_unavailable');
        } else {
          setErrorType('upload_failed');
        }
        setError(msg);
        setStage('error');
        toast.error(msg);
      }
    },
    [startPolling],
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragOver(false);
      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    },
    [handleFile],
  );

  const handleCancel = useCallback(async () => {
    if (!packageId) return;
    try {
      await etlPackageService.cancel(packageId);
      toast.success('Package processing cancelled');
      if (pollRef.current) {
        clearTimeout(pollRef.current);
        pollRef.current = null;
      }
      setStage('idle');
      setPackageId(null);
      setProgress(null);
    } catch {
      toast.error('Failed to cancel package');
    }
  }, [packageId]);

  const handleRetry = useCallback(async () => {
    if (!packageId) return;
    try {
      const result = await etlPackageService.retryFailed(packageId);
      toast.success(`Retrying ${result.retried} failed files`);
      setStage('processing');
      startPolling(packageId);
    } catch {
      toast.error('Failed to retry');
    }
  }, [packageId, startPolling]);

  const handleReset = useCallback(() => {
    setStage('idle');
    setUploadProgress(0);
    setPackageId(null);
    setProgress(null);
    setError(null);
    setErrorType(null);
    setConnectionLost(false);
  }, []);

  const processingPercentage = progress?.percentage ?? 0;
  const isProcessing = stage === 'processing' || stage === 'uploading';

  const handleRetryConnection = useCallback(() => {
    if (!packageId) return;
    setConnectionLost(false);
    consecutiveErrorsRef.current = 0;
    pollDelayRef.current = POLL_INITIAL_DELAY_MS;
    startPolling(packageId);
  }, [packageId, startPolling]);

  return (
    <div className="w-full max-w-3xl mx-auto">
      {stage === 'idle' && (
        <Card
          className={cn(
            'border-2 border-dashed transition-colors cursor-pointer',
            dragOver ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-gray-400',
          )}
          onDragOver={(e) => {
            e.preventDefault();
            setDragOver(true);
          }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
        >
          <CardContent className="flex flex-col items-center justify-center py-16 text-center">
            <div className="mb-4 rounded-full bg-blue-100 p-4">
              <Package className="h-10 w-10 text-blue-600" />
            </div>
            <h3 className="text-lg font-semibold">Upload ZIP Package</h3>
            <p className="mt-1 text-sm text-gray-500">
              Drop a ZIP file here or click to browse
            </p>
            <p className="mt-2 text-xs text-gray-400">
              Supports CSV, Excel, JSON, XML files inside the ZIP
            </p>
            <input
              ref={fileInputRef}
              type="file"
              accept=".zip"
              className="hidden"
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file) handleFile(file);
              }}
            />
          </CardContent>
        </Card>
      )}

      {stage === 'uploading' && (
        <Card>
          <CardContent className="py-8">
            <div className="flex flex-col items-center text-center">
              <Loader2 className="h-10 w-10 animate-spin text-blue-600 mb-4" />
              <h3 className="text-lg font-semibold">Uploading ZIP Package...</h3>
              <div className="mt-4 w-full max-w-md">
                <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-blue-600 transition-all duration-300"
                    style={{ width: `${uploadProgress}%` }}
                  />
                </div>
                <p className="mt-2 text-sm text-gray-500">{uploadProgress}%</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {stage === 'processing' && progress && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <FileArchive className="h-8 w-8 text-blue-600" />
                <div>
                  <CardTitle className="text-lg">{progress.filename}</CardTitle>
                  <CardDescription className="text-sm">
                    {progress.status === 'extracting' && 'Extracting ZIP contents...'}
                    {progress.status === 'discovering' && 'Discovering files...'}
                    {progress.status === 'processing' && `Processing files — ${progress.current_stage}`}
                    {progress.status === 'uploaded' && 'Queued for processing...'}
                  </CardDescription>
                </div>
              </div>
              <Button variant="outline" size="sm" onClick={handleCancel}>
                <X className="h-4 w-4 mr-1" /> Cancel
              </Button>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            {connectionLost && (
              <Alert variant="default" className="border-yellow-300 bg-yellow-50">
                <AlertCircle className="h-4 w-4 text-yellow-600" />
                <AlertDescription className="text-yellow-800">
                  Connection to server lost. Your package is still processing in the background.
                  <Button variant="link" size="sm" onClick={handleRetryConnection} className="ml-2 p-0">
                    Retry connection
                  </Button>
                </AlertDescription>
              </Alert>
            )}

            <div className="w-full">
              <div className="flex justify-between text-sm mb-1">
                <span className="text-gray-600">Progress</span>
                <span className="font-medium">{processingPercentage}%</span>
              </div>
              <div className="h-3 bg-gray-200 rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-blue-500 to-blue-600 transition-all duration-500"
                  style={{ width: `${processingPercentage}%` }}
                />
              </div>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <StatCard label="Total Files" value={progress.total_files} color="blue" />
              <StatCard label="Completed" value={progress.completed_files} color="green" />
              <StatCard label="Failed" value={progress.failed_files} color="red" />
              <StatCard label="Duplicates" value={progress.duplicate_files} color="yellow" />
            </div>

            {progress.total_rows_loaded > 0 && (
              <div className="grid grid-cols-2 gap-3">
                <StatCard label="Rows Extracted" value={progress.total_rows_extracted} color="blue" />
                <StatCard label="Rows Loaded" value={progress.total_rows_loaded} color="green" />
              </div>
            )}

            {progress.status === 'processing' && progress.processing_files > 0 && (
              <div className="flex items-center gap-2 text-sm text-gray-500">
                <Loader2 className="h-4 w-4 animate-spin" />
                Processing {progress.processing_files} file(s)...
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {stage === 'done' && progress && (
        <Card>
          <CardHeader>
            <div className="flex items-center gap-3">
              {progress.status === 'completed' ? (
                <CheckCircle className="h-8 w-8 text-green-600" />
              ) : progress.status === 'completed_with_errors' ? (
                <AlertCircle className="h-8 w-8 text-yellow-600" />
              ) : (
                <XCircle className="h-8 w-8 text-red-600" />
              )}
              <div>
                <CardTitle className="text-lg">{progress.filename}</CardTitle>
                <CardDescription>
                  {progress.status === 'completed' && 'Processing completed successfully'}
                  {progress.status === 'completed_with_errors' &&
                    `Completed with ${progress.failed_files} error(s)`}
                  {progress.status === 'failed' && 'Processing failed'}
                  {progress.status === 'cancelled' && 'Processing was cancelled'}
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            {progress.status !== 'failed' && progress.status !== 'cancelled' && (
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <StatCard label="Total Files" value={progress.total_files} color="blue" />
                <StatCard label="Completed" value={progress.completed_files} color="green" />
                <StatCard label="Failed" value={progress.failed_files} color="red" />
                <StatCard label="Duplicates" value={progress.duplicate_files} color="yellow" />
              </div>
            )}

            {progress.error_message && (
              <Alert variant="destructive">
                <AlertDescription>{progress.error_message}</AlertDescription>
              </Alert>
            )}

            {progress.overall_quality_score !== null && (
              <div className="flex items-center gap-2">
                <Badge variant="secondary">
                  Quality Score: {progress.overall_quality_score}/100
                </Badge>
                <Badge variant="secondary">
                  Rows Loaded: {formatNumber(progress.total_rows_loaded)}
                </Badge>
              </div>
            )}

            <div className="flex gap-3">
              {packageId && (
                <Button onClick={() => router.push(`/datasets/etl-packages/${packageId}`)}>
                  View Details
                </Button>
              )}
              {progress.failed_files > 0 && packageId && (
                <Button variant="outline" onClick={handleRetry}>
                  <RefreshCw className="h-4 w-4 mr-1" /> Retry Failed ({progress.failed_files})
                </Button>
              )}
              <Button variant="outline" onClick={handleReset}>
                Upload Another
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {stage === 'error' && (
        <Card>
          <CardContent className="py-8">
            <div className="flex flex-col items-center text-center">
              <XCircle className="h-10 w-10 text-red-600 mb-4" />
              <h3 className="text-lg font-semibold">
                {errorType === 'backend_unavailable'
                  ? 'Server Connection Error'
                  : 'Upload Failed'}
              </h3>
              <p className="mt-1 text-sm text-gray-500 max-w-md">{error}</p>
              {errorType === 'backend_unavailable' && (
                <p className="mt-2 text-xs text-gray-400 max-w-md">
                  The backend may be restarting or under heavy load. Your file was not uploaded.
                  Please try again once the server is available.
                </p>
              )}
              <div className="flex gap-3 mt-4">
                <Button variant="outline" onClick={handleReset}>
                  Try Again
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function StatCard({
  label,
  value,
  color,
}: {
  label: string;
  value: number;
  color: 'blue' | 'green' | 'red' | 'yellow';
}) {
  const colorClasses = {
    blue: 'bg-blue-50 text-blue-700 border-blue-200',
    green: 'bg-green-50 text-green-700 border-green-200',
    red: 'bg-red-50 text-red-700 border-red-200',
    yellow: 'bg-yellow-50 text-yellow-700 border-yellow-200',
  };

  return (
    <div className={cn('rounded-lg border p-3 text-center', colorClasses[color])}>
      <div className="text-2xl font-bold">{formatNumber(value)}</div>
      <div className="text-xs mt-1 opacity-80">{label}</div>
    </div>
  );
}
