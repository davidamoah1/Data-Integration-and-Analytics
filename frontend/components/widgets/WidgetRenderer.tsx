'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Skeleton } from '@/components/ui/Skeleton';
import { ErrorState } from '@/components/ui/ErrorState';
import { useEffect, useState } from 'react';
import {
  Activity, TrendingUp, TrendingDown, Minus, AlertCircle,
  FileText, MapPin, BarChart3, Table2, type LucideIcon,
  Users, ClipboardList, CheckCircle2, BedDouble, RotateCcw,
  GraduationCap, BookOpen, Building2, CalendarCheck, Award,
  DollarSign, ShoppingCart, Package, AlertTriangle, Truck,
  FlaskConical, Database, Newspaper, LayoutDashboard,
} from 'lucide-react';
import { dashboardCompositionService } from '@/services/dashboard/dashboardCompositionService';
import type { ComposedWidget, WidgetData } from '@/types';

const ICON_MAP: Record<string, LucideIcon> = {
  Activity, TrendingUp, Users, ClipboardList, CheckCircle2, AlertCircle,
  BedDouble, RotateCcw, GraduationCap, BookOpen, Building2, CalendarCheck,
  Award, DollarSign, ShoppingCart, Package, AlertTriangle, Truck,
  FlaskConical, FileText, Database, Newspaper, LayoutDashboard,
};

// ── KPI Card Widget ───────────────────────────────────

function KpiCardWidget({ data }: { data: WidgetData }) {
  const Icon = ICON_MAP[data.icon || 'Activity'] || Activity;
  const trend = data.trend;
  const TrendIcon = trend?.direction === 'up' ? TrendingUp : trend?.direction === 'down' ? TrendingDown : Minus;
  const trendColor = trend?.direction === 'up' ? 'text-green-500' : trend?.direction === 'down' ? 'text-red-500' : 'text-muted-foreground';

  return (
    <Card>
      <CardContent className="flex items-center justify-between p-6">
        <div>
          <p className="text-sm text-muted-foreground">{data.title}</p>
          <p className="text-2xl font-bold">
            {data.value?.toLocaleString() || 0}
            {data.unit && <span className="ml-1 text-sm text-muted-foreground">{data.unit}</span>}
          </p>
          {trend && (
            <div className={`mt-1 flex items-center gap-1 text-xs ${trendColor}`}>
              <TrendIcon className="h-3 w-3" />
              {Math.abs(trend.change_pct)}% vs last period
            </div>
          )}
        </div>
        <Icon className="h-8 w-8 text-muted-foreground" />
      </CardContent>
    </Card>
  );
}

// ── Chart Widget ─────────────────────────────────────

function ChartWidget({ data }: { data: WidgetData }) {
  const chartData = data.data;
  return (
    <Card className="col-span-2">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <BarChart3 className="h-4 w-4 text-muted-foreground" />
          {data.title}
        </CardTitle>
      </CardHeader>
      <CardContent>
        {chartData && chartData.labels && chartData.labels.length > 0 ? (
          <div className="flex h-48 items-center justify-center rounded-lg bg-muted/30">
            <BarChart3 className="h-16 w-16 text-muted-foreground/30" />
            <span className="ml-2 text-sm text-muted-foreground">
              {data.chart_subtype || 'bar'} chart — {chartData.labels.length} data points
            </span>
          </div>
        ) : (
          <div className="flex h-48 items-center justify-center text-muted-foreground">
            <BarChart3 className="h-12 w-12 opacity-20" />
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// ── Table Widget ──────────────────────────────────────

function TableWidget({ data }: { data: WidgetData }) {
  const columns = data.columns || [];
  const rows = data.rows || [];

  return (
    <Card className="col-span-2">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <Table2 className="h-4 w-4 text-muted-foreground" />
          {data.title}
        </CardTitle>
      </CardHeader>
      <CardContent>
        {rows.length === 0 ? (
          <p className="py-4 text-center text-sm text-muted-foreground">No data available.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  {columns.map((col) => (
                    <th key={col} className="px-3 py-2 text-left font-medium text-muted-foreground">
                      {col.replace(/_/g, ' ')}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {rows.map((row, i) => (
                  <tr key={i} className="border-b last:border-0">
                    {columns.map((col) => (
                      <td key={col} className="px-3 py-2">
                        {String(row[col] ?? '—')}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// ── Map Widget ────────────────────────────────────────

function MapWidget({ data }: { data: WidgetData }) {
  const regions = data.regions || [];
  return (
    <Card className="col-span-2">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <MapPin className="h-4 w-4 text-muted-foreground" />
          {data.title}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex h-48 items-center justify-center rounded-lg bg-muted/30">
          <MapPin className="h-16 w-16 text-muted-foreground/30" />
          <span className="ml-2 text-sm text-muted-foreground">
            {regions.length} regions mapped
          </span>
        </div>
      </CardContent>
    </Card>
  );
}

// ── Trend Widget ──────────────────────────────────────

function TrendWidget({ data }: { data: WidgetData }) {
  const direction = data.direction || 'neutral';
  const TrendIcon = direction === 'up' ? TrendingUp : direction === 'down' ? TrendingDown : Minus;
  const trendColor = direction === 'up' ? 'text-green-500' : direction === 'down' ? 'text-red-500' : 'text-muted-foreground';

  return (
    <Card className="col-span-2">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <TrendingUp className="h-4 w-4 text-muted-foreground" />
          {data.title}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-muted-foreground">Current</p>
            <p className="text-2xl font-bold">{data.current?.toLocaleString() || 0}</p>
          </div>
          <div className="text-right">
            <p className="text-sm text-muted-foreground">Previous</p>
            <p className="text-lg font-medium text-muted-foreground">{data.previous?.toLocaleString() || 0}</p>
          </div>
        </div>
        <div className={`mt-2 flex items-center gap-1 text-sm ${trendColor}`}>
          <TrendIcon className="h-4 w-4" />
          {Math.abs(data.change_pct || 0)}% change
        </div>
        {data.series && data.series.length > 0 && (
          <div className="mt-4 flex h-24 items-center justify-center rounded-lg bg-muted/30">
            <TrendingUp className="h-12 w-12 text-muted-foreground/20" />
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// ── Alert Widget ──────────────────────────────────────

function AlertWidget({ data }: { data: WidgetData }) {
  const alerts = data.alerts || [];
  const severity = data.severity || 'warning';
  const variant = severity === 'critical' ? 'destructive' : 'warning';

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <AlertCircle className="h-4 w-4 text-muted-foreground" />
          {data.title}
        </CardTitle>
      </CardHeader>
      <CardContent>
        {alerts.length === 0 ? (
          <p className="py-4 text-center text-sm text-muted-foreground">No active alerts.</p>
        ) : (
          <div className="space-y-2">
            {alerts.map((alert: any, i: number) => (
              <div key={i} className="flex items-center gap-2 rounded-lg border p-2">
                <Badge variant={variant}>{alert.severity || severity}</Badge>
                <span className="text-sm">{alert.message || alert.title}</span>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// ── Report Widget ─────────────────────────────────────

function ReportWidget({ data }: { data: WidgetData }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <FileText className="h-4 w-4 text-muted-foreground" />
          {data.title}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-muted-foreground">{data.report_type || 'Report'}</p>
            <Badge variant={data.status === 'generated' ? 'success' : 'default'}>
              {data.status || 'not_generated'}
            </Badge>
          </div>
          {data.url && (
            <a
              href={data.url}
              className="text-sm text-primary hover:underline"
              target="_blank"
              rel="noopener noreferrer"
            >
              View Report →
            </a>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

// ── Widget Renderer (dispatcher) ─────────────────────

export function WidgetRenderer({ widget, dashboardId }: { widget: ComposedWidget; dashboardId: string }) {
  const [data, setData] = useState<WidgetData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const result = await dashboardCompositionService.getWidgetData(dashboardId, widget.key);
        setData(result);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load widget data');
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [dashboardId, widget.key]);

  if (loading) {
    return <Skeleton className="h-32 w-full" />;
  }

  if (error) {
    return <ErrorState message={error} />;
  }

  if (!data) {
    return null;
  }

  switch (widget.widget_type) {
    case 'kpi_card':
    case 'kpi':
      return <KpiCardWidget data={data} />;
    case 'chart':
      return <ChartWidget data={data} />;
    case 'table':
      return <TableWidget data={data} />;
    case 'map':
      return <MapWidget data={data} />;
    case 'trend':
      return <TrendWidget data={data} />;
    case 'alert':
      return <AlertWidget data={data} />;
    case 'report':
      return <ReportWidget data={data} />;
    default:
      return (
        <Card>
          <CardContent className="p-6 text-center text-sm text-muted-foreground">
            Unknown widget type: {widget.widget_type}
          </CardContent>
        </Card>
      );
  }
}
