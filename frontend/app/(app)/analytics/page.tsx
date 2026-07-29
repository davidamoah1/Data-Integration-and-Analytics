'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { BarChart3, TrendingUp, TrendingDown, Minus, ChevronRight } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { SkeletonCard } from '@/components/ui/Skeleton';
import { EmptyState } from '@/components/ui/EmptyState';
import { ErrorState } from '@/components/ui/ErrorState';
import { dashboardService } from '@/services/dashboard/dashboardService';
import type { Dashboard, KPI } from '@/types';
import { cn, formatNumber } from '@/lib/utils';

export default function AnalyticsPage() {
  const router = useRouter();
  const [dashboards, setDashboards] = useState<Dashboard[]>([]);
  const [kpis, setKpis] = useState<KPI[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        setLoading(true);
        const [dashes, k] = await Promise.all([
          dashboardService.listDashboards(),
          dashboardService.listKPIs(),
        ]);
        setDashboards(dashes || []);
        setKpis(k || []);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load analytics');
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold">Analytics</h1>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => <SkeletonCard key={i} />)}
        </div>
      </div>
    );
  }

  if (error) return <ErrorState message={error} />;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Analytics</h1>

      {/* KPI Cards */}
      {kpis.length > 0 && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {kpis.slice(0, 8).map((kpi) => {
            const TrendIcon = kpi.trend === 'up' ? TrendingUp : kpi.trend === 'down' ? TrendingDown : Minus;
            const trendColor = kpi.trend === 'up' ? 'text-green-500' : kpi.trend === 'down' ? 'text-red-500' : 'text-muted-foreground';
            return (
              <Card key={kpi.id}>
                <CardContent className="p-6">
                  <p className="text-sm text-muted-foreground">{kpi.name}</p>
                  <div className="mt-2 flex items-baseline gap-2">
                    <span className="text-2xl font-bold">{formatNumber(kpi.value)}</span>
                    {kpi.unit && <span className="text-sm text-muted-foreground">{kpi.unit}</span>}
                    {kpi.trend_value != null && (
                      <span className={cn('flex items-center text-xs', trendColor)}>
                        <TrendIcon className="h-3 w-3" />
                        {Math.abs(kpi.trend_value)}%
                      </span>
                    )}
                  </div>
                  {kpi.target && (
                    <p className="mt-1 text-xs text-muted-foreground">
                      Target: {formatNumber(kpi.target)}
                    </p>
                  )}
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      {/* Dashboards */}
      <Card>
        <CardHeader>
          <CardTitle>Dashboards</CardTitle>
          <CardDescription>Visual analytics and interactive dashboards</CardDescription>
        </CardHeader>
        <CardContent>
          {dashboards.length === 0 ? (
            <EmptyState
              icon={<BarChart3 className="h-10 w-10" />}
              title="No dashboards yet"
              description="Create a dashboard to start visualizing your data."
            />
          ) : (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {dashboards.map((dash) => (
                <Card
                  key={dash.id}
                  className="hover:shadow-md transition-shadow cursor-pointer"
                  onClick={() => router.push(`/analytics/${dash.id}`)}
                >
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-medium">{dash.name}</p>
                        <p className="text-xs text-muted-foreground mt-1">
                          {(dash as unknown as Record<string, unknown>).widget_count as number ?? dash.widgets?.length ?? 0} widgets · v{dash.version}
                        </p>
                        {dash.description && (
                          <p className="text-xs text-muted-foreground mt-1 line-clamp-2">{dash.description}</p>
                        )}
                      </div>
                      <ChevronRight className="h-5 w-5 text-muted-foreground" />
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
