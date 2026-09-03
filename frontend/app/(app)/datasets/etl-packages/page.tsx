'use client';

import { useEffect, useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { Package, Search, Plus, Download } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Input } from '@/components/ui/Input';
import { Table, TableRow, TableCell } from '@/components/ui/Table';
import { SkeletonTable } from '@/components/ui/Skeleton';
import { ErrorState } from '@/components/ui/ErrorState';
import { EmptyState } from '@/components/ui/EmptyState';
import { ETLPackageUpload } from '@/features/etl/ETLPackageUpload';
import { etlPackageService, type ETLPackage } from '@/services/etl/etlPackageService';
import { formatNumber, formatDate } from '@/lib/utils';

export default function ETLPackagesPage() {
  const router = useRouter();
  const [packages, setPackages] = useState<ETLPackage[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [showUpload, setShowUpload] = useState(false);

  const loadPackages = useCallback(async () => {
    try {
      setLoading(true);
      const res = await etlPackageService.list(100, 0, {
        status: statusFilter || undefined,
        search: search || undefined,
      });
      setPackages(res?.packages || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load packages');
    } finally {
      setLoading(false);
    }
  }, [statusFilter, search]);

  useEffect(() => {
    loadPackages();
  }, [loadPackages]);

  const handleDownload = async (e: React.MouseEvent, packageId: number, filename: string) => {
    e.stopPropagation();
    try {
      const blob = await etlPackageService.download(packageId);
      const url = window.URL.createObjectURL(blob);
      const a = window.document.createElement('a');
      a.href = url;
      a.download = filename;
      window.document.body.appendChild(a);
      a.click();
      window.document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch {
      // ignore download errors
    }
  };

  const filtered = packages;

  if (loading) {
    return (
      <div className="container mx-auto py-6">
        <SkeletonTable rows={5} />
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto py-6">
        <ErrorState message={error} onRetry={loadPackages} />
      </div>
    );
  }

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">ETL Packages</h1>
          <p className="text-sm text-gray-500 mt-1">
            Upload and process ZIP packages containing thousands of files
          </p>
        </div>
        <Button onClick={() => setShowUpload(!showUpload)}>
          <Plus className="h-4 w-4 mr-1" /> Upload Package
        </Button>
      </div>

      {showUpload && (
        <div className="py-4">
          <ETLPackageUpload />
        </div>
      )}

      {packages.length === 0 && !showUpload ? (
        <EmptyState
          icon={<Package className="h-12 w-12 text-gray-400" />}
          title="No ETL packages yet"
          description="Upload a ZIP package to get started with bulk data processing."
          action={
            <Button onClick={() => setShowUpload(true)}>
              <Plus className="h-4 w-4 mr-1" /> Upload Package
            </Button>
          }
        />
      ) : (
        <>
          <div className="flex items-center gap-2">
            <div className="relative flex-1 max-w-sm">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
              <Input
                placeholder="Search packages..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-9"
              />
            </div>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="border rounded-md px-3 py-2 text-sm"
            >
              <option value="">All Statuses</option>
              <option value="uploaded">Uploaded</option>
              <option value="extracting">Extracting</option>
              <option value="discovering">Discovering</option>
              <option value="processing">Processing</option>
              <option value="completed">Completed</option>
              <option value="completed_with_errors">Completed with Errors</option>
              <option value="failed">Failed</option>
              <option value="cancelled">Cancelled</option>
            </select>
          </div>

          <Card>
            <CardContent className="py-4">
              {filtered.length === 0 ? (
                <p className="text-center text-gray-500 py-8">No packages match your search.</p>
              ) : (
                <div className="overflow-x-auto">
                  <Table headers={['Filename', 'Status', 'Files', 'Completed', 'Failed', 'Quality', 'Created', '']}>
                      {filtered.map((p) => (
                        <TableRow
                          key={p.id}
                          className="cursor-pointer hover:bg-gray-50"
                          onClick={() => router.push(`/datasets/etl-packages/${p.id}`)}
                        >
                          <TableCell className="font-medium">
                            <div className="flex items-center gap-2">
                              <Package className="h-4 w-4 text-gray-400" />
                              {p.filename}
                            </div>
                          </TableCell>
                          <TableCell>
                            <PackageStatusBadge status={p.status} />
                          </TableCell>
                          <TableCell className="text-right">
                            {formatNumber(p.total_files)}
                          </TableCell>
                          <TableCell className="text-right text-green-600">
                            {formatNumber(p.completed_files)}
                          </TableCell>
                          <TableCell className="text-right text-red-600">
                            {formatNumber(p.failed_files)}
                          </TableCell>
                          <TableCell className="text-right">
                            {p.overall_quality_score !== null
                              ? `${p.overall_quality_score}`
                              : '-'}
                          </TableCell>
                          <TableCell className="text-sm text-gray-500">
                            {formatDate(p.created_at)}
                          </TableCell>
                          <TableCell>
                            <button
                              onClick={(e) => handleDownload(e, p.id, p.filename)}
                              className="text-gray-400 hover:text-gray-600"
                              title="Download original ZIP"
                            >
                              <Download className="h-4 w-4" />
                            </button>
                          </TableCell>
                        </TableRow>
                      ))}
                  </Table>
                </div>
              )}
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}

function PackageStatusBadge({ status }: { status: string }) {
  const variants: Record<string, 'default' | 'secondary' | 'destructive' | 'outline'> = {
    completed: 'default',
    completed_with_errors: 'secondary',
    failed: 'destructive',
    cancelled: 'outline',
    uploaded: 'outline',
    extracting: 'secondary',
    discovering: 'secondary',
    processing: 'secondary',
  };
  return (
    <Badge variant={variants[status] || 'outline'}>
      {status.replace(/_/g, ' ')}
    </Badge>
  );
}
