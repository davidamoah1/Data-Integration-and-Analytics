'use client';

import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, File as FileIcon, CheckCircle, XCircle, Loader2 } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Alert, AlertDescription } from '@/components/ui/Alert';
import { toast } from '@/components/ui/Toaster';
import { datasetService } from '@/services/datasets/datasetService';
import { cn } from '@/lib/utils';

type UploadStage = 'idle' | 'uploading' | 'validating' | 'analyzing' | 'done' | 'error';

export function DatasetUpload() {
  const [file, setFile] = useState<File | null>(null);
  const [stage, setStage] = useState<UploadStage>('idle');
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<Record<string, unknown> | null>(null);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      setFile(acceptedFiles[0]);
      setStage('idle');
      setError(null);
      setResult(null);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/csv': ['.csv'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/vnd.ms-excel': ['.xls'],
    },
    maxFiles: 1,
  });

  const handleUpload = async () => {
    if (!file) return;
    setStage('uploading');
    setError(null);
    try {
      // Step 1: Upload
      await datasetService.uploadFile(file);
      setStage('validating');

      // Step 2: Validate
      await datasetService.validateFile(file);
      setStage('analyzing');

      // Step 3: Semantic analysis
      const analysisResult = await datasetService.semanticAnalyze(file);
      setResult(analysisResult as Record<string, unknown>);
      setStage('done');
      toast.success('Dataset uploaded and analyzed successfully!');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed');
      setStage('error');
      toast.error('Upload failed. Please try again.');
    }
  };

  const handleReset = () => {
    setFile(null);
    setStage('idle');
    setError(null);
    setResult(null);
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Upload Dataset</CardTitle>
        <CardDescription>Upload a CSV or Excel file to analyze</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {!file && (
          <div
            {...getRootProps()}
            className={cn(
              'flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed p-12 transition-colors',
              isDragActive ? 'border-primary bg-primary/5' : 'border-muted-foreground/30 hover:border-primary/50',
            )}
          >
            <input {...getInputProps()} />
            <Upload className="mb-3 h-8 w-8 text-muted-foreground" />
            <p className="text-sm font-medium">
              {isDragActive ? 'Drop the file here' : 'Drag & drop or click to browse'}
            </p>
            <p className="mt-1 text-xs text-muted-foreground">Supports CSV, XLSX, XLS (max 50MB)</p>
          </div>
        )}

        {file && (
          <div className="space-y-4">
            {/* File info */}
            <div className="flex items-center justify-between rounded-lg border p-4">
              <div className="flex items-center gap-3">
                <FileIcon className="h-8 w-8 text-primary" />
                <div>
                  <p className="font-medium">{file.name}</p>
                  <p className="text-xs text-muted-foreground">
                    {(file.size / 1024).toFixed(1)} KB · {file.type || 'Unknown type'}
                  </p>
                </div>
              </div>
              {stage === 'done' && <CheckCircle className="h-6 w-6 text-green-500" />}
              {stage === 'error' && <XCircle className="h-6 w-6 text-destructive" />}
            </div>

            {/* Progress stages */}
            {stage !== 'idle' && stage !== 'error' && (
              <div className="space-y-2">
                {(['uploading', 'validating', 'analyzing', 'done'] as UploadStage[]).map((s) => {
                  const isCurrent = stage === s;
                  const isPast = ['uploading', 'validating', 'analyzing', 'done'].indexOf(stage) >
                    ['uploading', 'validating', 'analyzing', 'done'].indexOf(s);
                  return (
                    <div key={s} className="flex items-center gap-2">
                      {isCurrent ? (
                        <Loader2 className="h-4 w-4 animate-spin text-primary" />
                      ) : isPast ? (
                        <CheckCircle className="h-4 w-4 text-green-500" />
                      ) : (
                        <div className="h-4 w-4 rounded-full border" />
                      )}
                      <span className={cn('text-sm', isCurrent && 'font-medium', !isCurrent && !isPast && 'text-muted-foreground')}>
                        {s === 'uploading' && 'Uploading file...'}
                        {s === 'validating' && 'Validating data quality...'}
                        {s === 'analyzing' && 'Running semantic analysis...'}
                        {s === 'done' && 'Complete!'}
                      </span>
                    </div>
                  );
                })}
              </div>
            )}

            {error && (
              <Alert variant="destructive">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            {result && (
              <Alert variant="info">
                <AlertDescription>
                  <strong>Industry detected:</strong>{' '}
                  {String((result as { industry?: string }).industry || 'Unknown')}{' '}
                  ({Number((result as { industry_confidence?: number }).industry_confidence || 0).toFixed(0)}% confidence)
                </AlertDescription>
              </Alert>
            )}

            <div className="flex gap-2">
              {stage === 'idle' || stage === 'error' ? (
                <Button onClick={handleUpload} disabled={stage === 'uploading'}>
                  <Upload className="mr-2 h-4 w-4" />
                  Upload & Analyze
                </Button>
              ) : null}
              <Button variant="outline" onClick={handleReset}>
                {stage === 'done' ? 'Upload Another' : 'Cancel'}
              </Button>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
