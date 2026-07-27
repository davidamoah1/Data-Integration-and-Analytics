'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/stores/authStore';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { SkeletonCard } from '@/components/ui/Skeleton';
import { ErrorState } from '@/components/ui/ErrorState';
import { EmptyState } from '@/components/ui/EmptyState';
import { dashboardService } from '@/services/dashboard/dashboardService';
import { datasetService } from '@/services/datasets/datasetService';
import type { Dashboard, Dataset } from '@/types';
import { BarChart3, Database, TrendingUp, Activity, ArrowRight } from 'lucide-react';
import Link from 'next/link';
import { formatNumber, timeAgo } from '@/lib/utils';
import { Badge } from '@/components/ui/Badge';

export default function DashboardPage() {
  const router = useRouter();
  const { isAuthenticated } = useAuthStore();
  const [dashboards, setDashboards] = useState<Dashboard[]>([]);
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isAuthenticated) return;
    async function loadData() {
      try {
        setLoading(true);
        const [dashRes, dsRes] = await Promise.all([
          dashboardService.listDashboards(),
          datasetService.list({ limit: 5 }),
        ]);
        setDashboards(dashRes || []);
        setDatasets(dsRes?.datasets || []);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load dashboard data');
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [isAuthenticated]);

  if (loading) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => <SkeletonCard key={i} />)}
        </div>
      </div>
    );
  }

  if (error) {
    return <ErrorState message={error} onRetry={() => router.refresh()} />;
  }

  const stats = [
    { label: 'Dashboards', value: dashboards.length, icon: BarChart3, color: 'text-blue-500' },
    { label: 'Datasets', value: datasets.length, icon: Database, color: 'text-green-500' },
    { label: 'Active', value: datasets.filter((d) => d.status === 'ready').length, icon: Activity, color: 'text-purple-500' },
    { label: 'Processing', value: datasets.filter((d) => d.status === 'processing').length, icon: TrendingUp, color: 'text-orange-500' },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <Link href="/datasets" className="text-sm text-primary hover:underline">
          Upload Dataset →
        </Link>
      </div>

      {/* KPI Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => {
          const Icon = stat.icon;
          return (
            <Card key={stat.label}>
              <CardContent className="flex items-center justify-between p-6">
                <div>
                  <p className="text-sm text-muted-foreground">{stat.label}</p>
                  <p className="text-2xl font-bold">{formatNumber(stat.value)}</p>
                </div>
                <Icon className={`h-8 w-8 ${stat.color}`} />
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Recent Datasets */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Datasets</CardTitle>
        </CardHeader>
        <CardContent>
          {datasets.length === 0 ? (
            <EmptyState
              icon={<Database className="h-10 w-10" />}
              title="No datasets yet"
              description="Upload your first dataset to start analyzing data."
              action={
                <Link href="/datasets" className="text-sm text-primary hover:underline">
                  Upload Dataset →
                </Link>
              }
            />
          ) : (
            <div className="space-y-2">
              {datasets.map((ds) => (
                <Link
                  key={ds.id}
                  href={`/datasets/${ds.id}`}
                  className="flex items-center justify-between rounded-lg border p-3 hover:bg-accent"
                >
                  <div className="flex items-center gap-3">
                    <Database className="h-5 w-5 text-muted-foreground" />
                    <div>
                      <p className="font-medium">{ds.name}</p>
                      <p className="text-xs text-muted-foreground">
                        {ds.industry} · {formatNumber(ds.row_count)} rows · {timeAgo(ds.created_at)}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant={ds.status === 'ready' ? 'success' : ds.status === 'failed' ? 'destructive' : 'warning'}>
                      {ds.status}
                    </Badge>
                    <ArrowRight className="h-4 w-4 text-muted-foreground" />
                  </div>
                </Link>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Dashboards */}
      <Card>
        <CardHeader>
          <CardTitle>Your Dashboards</CardTitle>
        </CardHeader>
        <CardContent>
          {dashboards.length === 0 ? (
            <EmptyState
              icon={<BarChart3 className="h-10 w-10" />}
              title="No dashboards yet"
              description="Create a dashboard to visualize your data."
            />
          ) : (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {dashboards.map((dash) => (
                <Link
                  key={dash.id}
                  href={`/analytics/${dash.id}`}
                  className="rounded-lg border p-4 hover:bg-accent"
                >
                  <p className="font-medium">{dash.name}</p>
                  <p className="text-xs text-muted-foreground">
                    {dash.widgets?.length || 0} widgets · v{dash.version}
                  </p>
                </Link>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
