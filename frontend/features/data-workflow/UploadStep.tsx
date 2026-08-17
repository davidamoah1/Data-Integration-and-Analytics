'use client';

import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, File as FileIcon, X, CheckCircle2, AlertCircle } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { cn, formatFileSize } from '@/lib/utils';

const ACCEPTED_TYPES = {
  'text/csv': ['.csv'],
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
  'application/vnd.ms-excel': ['.xls'],
  'application/json': ['.json'],
  'text/xml': ['.xml'],
  'text/tab-separated-values': ['.tsv'],
  'text/plain': ['.txt'],
  'application/vnd.oasis.opendocument.spreadsheet': ['.ods'],
  'application/pdf': ['.pdf'],
  'image/jpeg': ['.jpg', '.jpeg'],
  'image/png': ['.png'],
  'image/tiff': ['.tif', '.tiff'],
  'image/bmp': ['.bmp'],
};

const MAX_SIZE = 100 * 1024 * 1024; // 100MB

interface Props {
  onFileSelected: (file: File) => void;
  onStartProcessing: () => void;
  file: File | null;
  isProcessing: boolean;
}

export function UploadStep({ onFileSelected, onStartProcessing, file, isProcessing }: Props) {
  const [validationError, setValidationError] = useState<string | null>(null);

  const onDrop = useCallback(
    (acceptedFiles: File[], rejectedFiles: unknown[]) => {
      setValidationError(null);
      if (rejectedFiles && (rejectedFiles as Array<unknown>).length > 0) {
        setValidationError('File type not supported or exceeds maximum size (100MB).');
        return;
      }
      if (acceptedFiles.length > 0) {
        onFileSelected(acceptedFiles[0]);
      }
    },
    [onFileSelected],
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: ACCEPTED_TYPES,
    maxFiles: 1,
    maxSize: MAX_SIZE,
  });

  const handleRemoveFile = () => {
    onFileSelected(null as unknown as File);
    setValidationError(null);
  };

  return (
    <Card className="border-2">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Upload className="h-5 w-5 text-primary" />
          Upload Your Data
        </CardTitle>
        <CardDescription>
          Drag and drop a file or click to browse. Supports CSV, Excel (XLSX/XLS), JSON, XML, TSV, ODS, PDF, JPG, PNG, TIFF, BMP formats.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {!file ? (
          <div
            {...getRootProps()}
            className={cn(
              'flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed p-16 transition-all',
              isDragActive
                ? 'border-primary bg-primary/5 scale-[1.01]'
                : 'border-muted-foreground/25 hover:border-primary/50 hover:bg-muted/30',
            )}
          >
            <input {...getInputProps()} />
            <div className="flex flex-col items-center gap-3">
              <div className="rounded-full bg-primary/10 p-4">
                <Upload className="h-8 w-8 text-primary" />
              </div>
              <div className="text-center">
                <p className="text-base font-medium">
                  {isDragActive ? 'Drop your file here' : 'Drag & drop your file here'}
                </p>
                <p className="mt-1 text-sm text-muted-foreground">
                  or click to browse your computer
                </p>
              </div>
              <div className="flex flex-wrap justify-center gap-1.5 mt-2">
                {['CSV', 'XLSX', 'XLS', 'JSON', 'XML', 'TSV', 'ODS', 'PDF', 'JPG', 'PNG', 'TIFF'].map((ext) => (
                  <Badge key={ext} variant="outline" className="text-xs">
                    {ext}
                  </Badge>
                ))}
              </div>
              <p className="text-xs text-muted-foreground mt-1">Maximum file size: 100MB</p>
            </div>
          </div>
        ) : (
          <div className="flex items-center justify-between rounded-lg border bg-muted/30 p-4">
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-primary/10 p-2">
                <FileIcon className="h-5 w-5 text-primary" />
              </div>
              <div>
                <p className="font-medium text-sm">{file.name}</p>
                <p className="text-xs text-muted-foreground">{formatFileSize(file.size)}</p>
              </div>
              <CheckCircle2 className="h-4 w-4 text-green-600" />
            </div>
            {!isProcessing && (
              <Button variant="ghost" size="sm" onClick={handleRemoveFile}>
                <X className="h-4 w-4" />
              </Button>
            )}
          </div>
        )}

        {validationError && (
          <div className="flex items-center gap-2 text-sm text-red-600 bg-red-50 dark:bg-red-950/30 rounded-lg p-3">
            <AlertCircle className="h-4 w-4 flex-shrink-0" />
            <span>{validationError}</span>
          </div>
        )}

        {file && !isProcessing && (
          <Button onClick={onStartProcessing} className="w-full" size="lg">
            <Upload className="mr-2 h-4 w-4" />
            Process Dataset
          </Button>
        )}
      </CardContent>
    </Card>
  );
}
