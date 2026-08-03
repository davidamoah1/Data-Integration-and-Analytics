'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Database, Plus, Search } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Badge } from '@/components/ui/Badge';
import { Table, TableRow, TableCell } from '@/components/ui/Table';
import { SkeletonTable } from '@/components/ui/Skeleton';
import { ErrorState } from '@/components/ui/ErrorState';
import { EmptyState } from '@/components/ui/EmptyState';
import { SmartEmptyState } from '@/components/onboarding/SmartEmptyState';
import { DatasetUpload } from '@/features/datasets/DatasetUpload';
import { datasetService } from '@/services/datasets/datasetService';
import type { Dataset } from '@/types';
import { formatNumber, formatDate } from '@/lib/utils';
import { useAuthStore } from '@/stores/authStore';

export default function DatasetsPage() {
  const router = useRouter();
  const { hasPermission } = useAuthStore();
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [showUpload, setShowUpload] = useState(false);

  const canUpload = hasPermission('datasets.view');

  useEffect(() => {
    loadDatasets();
  }, []);

  async function loadDatasets() {
    try {
      setLoading(true);
      const res = await datasetService.list();
      setDatasets(res?.datasets || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load datasets');
    } finally {
      setLoading(false);
    }
  }

  const filtered = datasets.filter((d) =>
    (d.name || '').toLowerCase().includes(search.toLowerCase()) ||
    (d.industry || '').toLowerCase().includes(search.toLowerCase()),
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Datasets</h1>
        {canUpload && (
          <Button onClick={() => setShowUpload(!showUpload)}>
            <Plus className="mr-2 h-4 w-4" />
            Upload Dataset
          </Button>
        )}
      </div>

      {showUpload && <DatasetUpload />}

      {/* Search */}
      <div className="relative max-w-sm">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          placeholder="Search datasets..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="pl-10"
        />
      </div>

      {/* Table */}
      <Card>
        <CardHeader>
          <CardTitle>All Datasets ({filtered.length})</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <SkeletonTable rows={5} />
          ) : error ? (
            <ErrorState message={error} onRetry={loadDatasets} />
          ) : filtered.length === 0 ? (
            search ? (
              <EmptyState
                icon={<Database className="h-10 w-10" />}
                title="No datasets found"
                description="Try a different search term."
              />
            ) : (
              <SmartEmptyState context="datasets" />
            )
          ) : (
            <Table headers={['Name', 'Industry', 'Rows', 'Status', 'Quality', 'Created']}>
              {filtered.map((ds) => (
                <TableRow
                  key={ds.id}
                  className="cursor-pointer"
                  onClick={() => router.push(`/datasets/${ds.id}`)}
                >
                  <TableCell className="font-medium">{ds.name}</TableCell>
                  <TableCell>
                    <Badge variant="outline">{ds.industry}</Badge>
                  </TableCell>
                  <TableCell>{formatNumber(ds.row_count)}</TableCell>
                  <TableCell>
                    <Badge variant={ds.status === 'ready' ? 'success' : ds.status === 'failed' ? 'destructive' : 'warning'}>
                      {ds.status}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    {ds.quality_score != null ? `${ds.quality_score.toFixed(0)}%` : '—'}
                  </TableCell>
                  <TableCell className="text-muted-foreground">{formatDate(ds.created_at)}</TableCell>
                </TableRow>
              ))}
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
