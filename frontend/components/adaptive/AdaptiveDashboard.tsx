'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/stores/authStore';
import { getDashboardConfigsForRoles, type DashboardWidget } from '@/lib/dashboards';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { SkeletonCard } from '@/components/ui/Skeleton';
import { ErrorState } from '@/components/ui/ErrorState';
import { QuickActions } from './QuickActions';
import { AdaptiveEmptyState } from './AdaptiveEmptyState';
import { dashboardService } from '@/services/dashboard/dashboardService';
import { datasetService } from '@/services/datasets/datasetService';
import type { Dashboard, Dataset } from '@/types';
import { formatNumber, timeAgo } from '@/lib/utils';
import { Badge } from '@/components/ui/Badge';
import { Database, ArrowRight, BarChart3, FileText, Activity, Users } from 'lucide-react';
import Link from 'next/link';

interface WidgetData {
  dashboards: Dashboard[];
  datasets: Dataset[];
}

export function AdaptiveDashboard() {
  const router = useRouter();
  const { user, hasPermission } = useAuthStore();
  const [data, setData] = useState<WidgetData>({ dashboards: [], datasets: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const [dashRes, dsRes] = await Promise.all([
          dashboardService.listDashboards(),
          datasetService.list({ limit: 5 }),
        ]);
        setData({
          dashboards: dashRes || [],
          datasets: dsRes?.datasets || [],
        });
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load dashboard data');
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  if (!user) return null;

  const config = getDashboardConfigsForRoles(user.roles);
  const firstName = user.full_name?.split(' ')[0] || 'there';

  if (loading) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold">{config.greeting}</h1>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => <SkeletonCard key={i} />)}
        </div>
      </div>
    );
  }

  if (error) {
    return <ErrorState message={error} onRetry={() => router.refresh()} />;
  }

  const hasData = data.dashboards.length > 0 || data.datasets.length > 0;

  return (
    <div className="space-y-8">
      {/* Greeting */}
      <div>
        <h1 className="text-2xl font-bold">{config.greeting}</h1>
        <p className="mt-1 text-muted-foreground">
          Welcome back, {firstName}. {config.purpose}.
        </p>
      </div>

      {/* Quick Actions */}
      <div>
        <h2 className="mb-4 text-lg font-semibold">Quick Actions</h2>
        <QuickActions />
      </div>

      {/* Dashboard sections */}
      {config.sections.map((section) => (
        <div key={section.id}>
          <h2 className="mb-4 text-lg font-semibold">{section.title}</h2>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            {section.widgets.map((widget) => (
              <WidgetRenderer
                key={widget.id}
                widget={widget}
                data={data}
                hasPermission={hasPermission}
              />
            ))}
          </div>
        </div>
      ))}

      {/* Empty state if no data */}
      {!hasData && (
        <Card>
          <CardContent className="p-6">
            <AdaptiveEmptyState
              icon={<Database className="h-10 w-10" />}
              title="No data yet"
              description="Get started by uploading your first dataset or connecting a database."
              context="datasets"
            />
          </CardContent>
        </Card>
      )}

      {/* Recent datasets (for roles that can view datasets) */}
      {hasPermission('datasets.view') && data.datasets.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Recent Datasets</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {data.datasets.map((ds) => (
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
          </CardContent>
        </Card>
      )}

      {/* Dashboards (for roles that can view dashboards) */}
      {hasPermission('analytics.view') && data.dashboards.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Your Dashboards</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {data.dashboards.map((dash) => (
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
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function WidgetRenderer({
  widget,
  data,
  hasPermission,
}: {
  widget: DashboardWidget;
  data: WidgetData;
  hasPermission: (perm: string) => boolean;
}) {
  const Icon = widget.icon;

  if (widget.permission && !hasPermission(widget.permission)) {
    return null;
  }

  if (widget.type === 'kpi') {
    let value: number | string = '—';
    if (widget.dataSource === 'dashboards.count' || widget.dataSource === 'dashboards.favorites') {
      value = data.dashboards.length;
    } else if (widget.dataSource === 'datasets.count' || widget.dataSource === 'datasets.recent') {
      value = data.datasets.length;
    } else if (widget.dataSource === 'datasets.processing') {
      value = data.datasets.filter((d) => d.status === 'processing').length;
    } else if (widget.dataSource === 'reports.recent' || widget.dataSource === 'reports.count') {
      value = 0;
    }

    return (
      <Card>
        <CardContent className="flex items-center justify-between p-6">
          <div>
            <p className="text-sm text-muted-foreground">{widget.title}</p>
            <p className="text-2xl font-bold">{formatNumber(value as number)}</p>
          </div>
          <Icon className="h-8 w-8 text-muted-foreground" />
        </CardContent>
      </Card>
    );
  }

  if (widget.type === 'list') {
    let items: { id: number | string; name: string; sub: string }[] = [];

    if (widget.dataSource === 'datasets.recent' || widget.dataSource === 'org.datasets' || widget.dataSource === 'dept.datasets') {
      items = data.datasets.slice(0, widget.limit || 5).map((d) => ({
        id: d.id,
        name: d.name,
        sub: `${formatNumber(d.row_count)} rows · ${timeAgo(d.created_at)}`,
      }));
    } else if (widget.dataSource === 'dashboards.favorites' || widget.dataSource === 'dashboards.count') {
      items = data.dashboards.slice(0, widget.limit || 5).map((d) => ({
        id: d.id,
        name: d.name,
        sub: `${d.widgets?.length || 0} widgets`,
      }));
    }

    return (
      <Card className="col-span-2">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Icon className="h-4 w-4 text-muted-foreground" />
            {widget.title}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {items.length === 0 ? (
            <p className="py-4 text-center text-sm text-muted-foreground">No items yet.</p>
          ) : (
            <div className="space-y-2">
              {items.map((item) => (
                <div key={item.id} className="flex items-center justify-between rounded-lg border p-2">
                  <div>
                    <p className="text-sm font-medium">{item.name}</p>
                    <p className="text-xs text-muted-foreground">{item.sub}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    );
  }

  if (widget.type === 'status') {
    return (
      <Card>
        <CardContent className="flex items-center justify-between p-6">
          <div>
            <p className="text-sm text-muted-foreground">{widget.title}</p>
            <p className="text-lg font-semibold text-green-500">Operational</p>
          </div>
          <Icon className="h-8 w-8 text-green-500" />
        </CardContent>
      </Card>
    );
  }

  if (widget.type === 'alert') {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center gap-2">
            <Icon className="h-5 w-5 text-muted-foreground" />
            <p className="text-sm font-medium">{widget.title}</p>
          </div>
          <p className="mt-2 text-sm text-muted-foreground">No alerts.</p>
        </CardContent>
      </Card>
    );
  }

  if (widget.type === 'chart') {
    return (
      <Card className="col-span-2">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Icon className="h-4 w-4 text-muted-foreground" />
            {widget.title}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex h-32 items-center justify-center text-muted-foreground">
            <BarChart3 className="h-12 w-12 opacity-20" />
          </div>
        </CardContent>
      </Card>
    );
  }

  return null;
}
