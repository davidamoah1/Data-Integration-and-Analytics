'use client';

import { useState } from 'react';
import { LayoutDashboard, Save, CheckCircle2, TrendingUp, Info } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { SlideChart } from '@/components/reports/SlideChart';
import type { DashboardRecommendation, AutoDashboardSpec, ChartSpec } from '@/types/workflow';

interface Props {
  dashboard: DashboardRecommendation | null;
  autoDashboard?: AutoDashboardSpec | null;
  onSaveDashboard: () => void;
  onContinue: () => void;
  isSaving: boolean;
  savedDashboardId: number | null;
}

export function VisualizeStep({
  dashboard,
  autoDashboard,
  onSaveDashboard,
  onContinue,
  isSaving,
  savedDashboardId,
}: Props) {
  const [activeTab, setActiveTab] = useState<'dashboard' | 'schema'>('dashboard');

  if (!dashboard && !autoDashboard) {
    return (
      <Card>
        <CardContent className="py-12 text-center text-muted-foreground">
          Generating visualization recommendations...
        </CardContent>
      </Card>
    );
  }

  const kpis = autoDashboard?.kpis || [];
  const charts = autoDashboard?.charts || [];
  const industryName = autoDashboard?.industry || dashboard?.industry || 'General';

  return (
    <div className="space-y-6">
      {/* Dashboard Recommendation Header */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="rounded-full bg-primary/10 p-3">
                <LayoutDashboard className="h-5 w-5 text-primary" />
              </div>
              <div>
                <p className="font-semibold text-base">
                  {autoDashboard?.title || 'Automated Intelligence Dashboard'}
                </p>
                <p className="text-xs text-muted-foreground">
                  Sector: <span className="capitalize font-medium text-foreground">{industryName}</span> &bull;{' '}
                  {charts.length > 0 ? `${charts.length} interactive charts generated` : 'AI recommendations ready'}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant={activeTab === 'dashboard' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setActiveTab('dashboard')}
              >
                Visualizations
              </Button>
              <Button
                variant={activeTab === 'schema' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setActiveTab('schema')}
              >
                Data Fields
              </Button>
              {!savedDashboardId ? (
                <Button onClick={onSaveDashboard} disabled={isSaving} size="sm" variant="secondary">
                  <Save className="mr-1.5 h-3.5 w-3.5" />
                  {isSaving ? 'Saving...' : 'Save Dashboard'}
                </Button>
              ) : (
                <Badge variant="default" className="bg-emerald-600 text-white flex items-center gap-1">
                  <CheckCircle2 className="h-3 w-3" /> Saved
                </Badge>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* TAB 1: VISUALIZATIONS & CHARTS */}
      {activeTab === 'dashboard' && (
        <div className="space-y-6">
          {/* KPI Cards Strip */}
          {kpis.length > 0 && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {kpis.slice(0, 4).map((kpi) => (
                <Card key={kpi.id} className="relative overflow-hidden">
                  <CardContent className="pt-5">
                    <p className="text-xs text-muted-foreground font-medium truncate">{kpi.label}</p>
                    <p className="text-2xl font-bold mt-1 tracking-tight text-foreground">
                      {typeof kpi.value === 'number'
                        ? kpi.value.toLocaleString(undefined, { maximumFractionDigits: 1 })
                        : kpi.value}
                      {kpi.unit ? <span className="text-xs font-normal text-muted-foreground ml-1">{kpi.unit}</span> : null}
                    </p>
                    {kpi.comparison_label && (
                      <p className="text-[11px] text-emerald-600 dark:text-emerald-400 mt-1 font-medium">
                        {kpi.comparison_label}
                      </p>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          )}

          {/* RENDERED CHARTS GRID */}
          {charts.length > 0 ? (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {charts.map((chart: ChartSpec) => (
                <Card key={chart.id} className="flex flex-col justify-between">
                  <CardHeader className="pb-2">
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <CardTitle className="text-sm font-semibold">{chart.title}</CardTitle>
                        {chart.description && (
                          <CardDescription className="text-xs mt-0.5">{chart.description}</CardDescription>
                        )}
                      </div>
                      <Badge variant="outline" className="text-[10px] uppercase font-mono shrink-0">
                        {chart.chart_type}
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent className="pt-2">
                    {chart.data && chart.data.length > 0 ? (
                      <div className="rounded-lg border bg-muted/10 p-2">
                        <SlideChart
                          chartType={chart.chart_type}
                          data={chart.data as any}
                          xAxis={chart.x_axis || 'x'}
                          yAxis={chart.y_axis || 'y'}
                          height={240}
                        />
                      </div>
                    ) : (
                      <div className="h-60 flex items-center justify-center border-2 border-dashed rounded-lg text-xs text-muted-foreground">
                        Chart data being synthesized
                      </div>
                    )}
                    {chart.reason && (
                      <div className="mt-3 flex items-start gap-1.5 text-[11px] text-muted-foreground bg-muted/30 p-2 rounded">
                        <Info className="h-3.5 w-3.5 text-primary shrink-0 mt-0.5" />
                        <span>{chart.reason}</span>
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : dashboard?.recommended_charts && dashboard.recommended_charts.length > 0 ? (
            /* Fallback to recommended charts list */
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {dashboard.recommended_charts.map((chart, i) => (
                <Card key={i} className="hover:border-primary/50 transition-colors">
                  <CardHeader>
                    <div className="flex items-center gap-2 mb-1">
                      <Badge variant="outline" className="text-xs capitalize">
                        {chart.type}
                      </Badge>
                    </div>
                    <CardTitle className="text-sm font-medium">{chart.title}</CardTitle>
                    {chart.reasoning && (
                      <CardDescription className="text-xs">{chart.reasoning}</CardDescription>
                    )}
                  </CardHeader>
                </Card>
              ))}
            </div>
          ) : (
            <Card>
              <CardContent className="py-12 text-center text-muted-foreground text-sm">
                No visualizations available. Proceed to generate your presentation or report.
              </CardContent>
            </Card>
          )}
        </div>
      )}

      {/* TAB 2: DATA FIELDS & MEASURES */}
      {activeTab === 'schema' && dashboard && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {dashboard.available_measures && dashboard.available_measures.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Measures (Numerical Metrics)</CardTitle>
                  <CardDescription>Variables suitable for continuous aggregation</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="flex flex-wrap gap-2">
                    {dashboard.available_measures.map((m, i) => (
                      <Badge key={i} variant="outline" className="font-mono text-xs">
                        {m.display || m.column}
                      </Badge>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {dashboard.available_dimensions && dashboard.available_dimensions.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Dimensions (Categorical Fields)</CardTitle>
                  <CardDescription>Attributes suitable for slicing, grouping, and filtering</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="flex flex-wrap gap-2">
                    {dashboard.available_dimensions.map((d, i) => (
                      <Badge key={i} variant="secondary" className="text-xs">
                        {d.display || d.column}
                      </Badge>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}
          </div>

          {((dashboard.time_fields && dashboard.time_fields.length > 0) ||
            (dashboard.geo_fields && dashboard.geo_fields.length > 0)) && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {dashboard.time_fields && dashboard.time_fields.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle className="text-sm">Temporal / Date Dimensions</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="flex flex-wrap gap-2">
                      {dashboard.time_fields.map((t, i) => (
                        <Badge key={i} variant="outline" className="text-xs font-mono">{t.display || t.column}</Badge>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}
              {dashboard.geo_fields && dashboard.geo_fields.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle className="text-sm">Geographic / Regional Dimensions</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="flex flex-wrap gap-2">
                      {dashboard.geo_fields.map((g, i) => (
                        <Badge key={i} variant="outline" className="text-xs font-mono">{g.display || g.column}</Badge>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          )}
        </div>
      )}

      <Button onClick={onContinue} size="lg" className="w-full">
        Continue to Formal Report &rarr;
      </Button>
    </div>
  );
}

