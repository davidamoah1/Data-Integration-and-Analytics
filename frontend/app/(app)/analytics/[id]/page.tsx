'use client';

import { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { ArrowLeft, BarChart3, Database, LayoutDashboard, Lightbulb } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Skeleton, SkeletonCard } from '@/components/ui/Skeleton';
import { ErrorState } from '@/components/ui/ErrorState';
import { EmptyState } from '@/components/ui/EmptyState';
import { dashboardService } from '@/services/dashboard/dashboardService';

interface DashboardDetail {
  id: number;
  name: string;
  description?: string;
  theme?: string;
  layout?: unknown[];
  is_public: boolean;
  version: number;
  widgets: Array<{
    id: number;
    widget_type: string;
    title: string;
    configuration: Record<string, unknown>;
    position: { x: number; y: number; w: number; h: number };
    group_name?: string;
  }>;
}

export default function DashboardDetailPage() {
  const router = useRouter();
  const params = useParams();
  const dashboardId = Number(params.id);

  const [dashboard, setDashboard] = useState<DashboardDetail | null>(null);
  const [kpis, setKpis] = useState<Array<{
    id: number;
    name: string;
    category?: string;
    unit?: string;
    is_active: boolean;
  }>>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!dashboardId) return;
    async function load() {
      try {
        setLoading(true);
        const [dash, kpiList] = await Promise.all([
          dashboardService.getDashboard(dashboardId),
          dashboardService.listKPIs(),
        ]);
        setDashboard(dash as unknown as DashboardDetail);
        setKpis(kpiList || []);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load dashboard');
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [dashboardId]);

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="sm" onClick={() => router.push('/analytics')}>
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back
          </Button>
        </div>
        <Skeleton className="h-8 w-48" />
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => <SkeletonCard key={i} />)}
        </div>
      </div>
    );
  }

  if (error) return <ErrorState message={error} onRetry={() => router.refresh()} />;

  if (!dashboard) {
    return (
      <div className="space-y-6">
        <Button variant="ghost" size="sm" onClick={() => router.push('/analytics')}>
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to Analytics
        </Button>
        <EmptyState
          icon={<LayoutDashboard className="h-10 w-10" />}
          title="Dashboard not found"
          description="This dashboard may have been deleted."
        />
      </div>
    );
  }

  const widgets = dashboard.widgets || [];
  const kpiWidgets = widgets.filter((w) => w.widget_type === 'kpi_card' || w.widget_type === 'kpi');
  const chartWidgets = widgets.filter((w) => w.widget_type === 'chart' || w.widget_type === 'graph');
  const otherWidgets = widgets.filter((w) => !['kpi_card', 'kpi', 'chart', 'graph'].includes(w.widget_type));

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="sm" onClick={() => router.push('/analytics')}>
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back
          </Button>
          <div>
            <h1 className="text-2xl font-bold">{dashboard.name}</h1>
            {dashboard.description && (
              <p className="text-sm text-muted-foreground">{dashboard.description}</p>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2">
          {dashboard.theme && (
            <Badge variant="secondary" className="capitalize">{dashboard.theme}</Badge>
          )}
          <Badge variant="outline">v{dashboard.version}</Badge>
          {dashboard.is_public && <Badge variant="success">Public</Badge>}
        </div>
      </div>

      {/* KPI Widgets */}
      {kpiWidgets.length > 0 && (
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <BarChart3 className="h-4 w-4" />
            <h2 className="text-sm font-semibold">KPI Cards</h2>
          </div>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            {kpiWidgets.map((w) => (
              <Card key={w.id}>
                <CardContent className="p-6">
                  <p className="text-sm text-muted-foreground">{w.title}</p>
                  <p className="mt-2 text-2xl font-bold">
                    {String(w.configuration?.value ?? w.configuration?.metric ?? '—')}
                  </p>
                  {Boolean(w.configuration?.entity) && (
                    <Badge variant="secondary" className="mt-1 text-xs">
                      {String(w.configuration?.entity)}
                    </Badge>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* Chart Widgets */}
      {chartWidgets.length > 0 && (
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <LayoutDashboard className="h-4 w-4" />
            <h2 className="text-sm font-semibold">Charts & Visualizations</h2>
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            {chartWidgets.map((w) => (
              <Card key={w.id}>
                <CardHeader>
                  <CardTitle className="text-base">{w.title}</CardTitle>
                  {w.group_name && (
                    <CardDescription>{w.group_name}</CardDescription>
                  )}
                </CardHeader>
                <CardContent>
                  <div className="flex h-48 items-center justify-center rounded-lg border-2 border-dashed border-muted-foreground/20">
                    <div className="text-center">
                      <BarChart3 className="mx-auto mb-2 h-8 w-8 text-muted-foreground/40" />
                      <p className="text-xs text-muted-foreground">
                        {w.configuration?.metric
                          ? `Metric: ${String(w.configuration.metric)}`
                          : 'Chart visualization'}
                      </p>
                      {w.configuration?.available === false && (
                        <Badge variant="warning" className="mt-2 text-xs">
                          Requires data
                        </Badge>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* Other Widgets */}
      {otherWidgets.length > 0 && (
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <Database className="h-4 w-4" />
            <h2 className="text-sm font-semibold">Widgets</h2>
          </div>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {otherWidgets.map((w) => (
              <Card key={w.id}>
                <CardHeader>
                  <CardTitle className="text-sm">{w.title}</CardTitle>
                </CardHeader>
                <CardContent>
                  <Badge variant="outline" className="text-xs">{w.widget_type}</Badge>
                  {w.group_name && (
                    <p className="mt-1 text-xs text-muted-foreground">{w.group_name}</p>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* All KPIs from the system */}
      {kpis.length > 0 && (
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <Lightbulb className="h-4 w-4" />
            <h2 className="text-sm font-semibold">Tracked KPIs</h2>
          </div>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            {kpis.map((kpi) => (
              <Card key={kpi.id}>
                <CardContent className="p-4">
                  <p className="text-sm font-medium">{kpi.name}</p>
                  <div className="mt-1 flex items-center gap-2">
                    {kpi.category && (
                      <Badge variant="secondary" className="text-xs">{kpi.category}</Badge>
                    )}
                    {kpi.unit && (
                      <span className="text-xs text-muted-foreground">{kpi.unit}</span>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* No widgets */}
      {widgets.length === 0 && kpis.length === 0 && (
        <EmptyState
          icon={<LayoutDashboard className="h-10 w-10" />}
          title="No widgets yet"
          description="This dashboard has no widgets configured yet."
        />
      )}
    </div>
  );
}
