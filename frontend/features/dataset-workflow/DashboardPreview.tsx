"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Alert } from "@/components/ui/Alert";
import { Skeleton } from "@/components/ui/Skeleton";
import { LayoutDashboard, Check, Settings, X, Lightbulb, Download, Info, TrendingUp, TrendingDown, Activity, AlertTriangle } from "lucide-react";
import { workflowService } from "@/services/workflow/workflowService";
import type { AutoDashboardSpec, ChartExplanation, ChartSpec, KPISpec, InsightSpec, DashboardRecommendation } from "@/types/workflow";

interface Props {
  workflowId: string;
}

const CHART_ICONS: Record<string, string> = {
  line_chart: "📈",
  bar_chart: "📊",
  horizontal_bar: "📊",
  pie_chart: "🥧",
  donut_chart: "🥧",
  scatter_plot: "🔵",
  histogram: "📉",
  heatmap: "🔥",
  geo_map: "🗺️",
};

const SEVERITY_ICONS: Record<string, typeof AlertTriangle> = {
  critical: AlertTriangle,
  warning: AlertTriangle,
  positive: TrendingUp,
  info: Info,
};

const SEVERITY_COLORS: Record<string, string> = {
  critical: "text-red-600 bg-red-50 border-red-200",
  warning: "text-yellow-600 bg-yellow-50 border-yellow-200",
  positive: "text-green-600 bg-green-50 border-green-200",
  info: "text-blue-600 bg-blue-50 border-blue-200",
};

export function DashboardPreview({ workflowId }: Props) {
  const [autoDashboard, setAutoDashboard] = useState<AutoDashboardSpec | null>(null);
  const [legacyData, setLegacyData] = useState<DashboardRecommendation | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [explainedChart, setExplainedChart] = useState<ChartExplanation | null>(null);
  const [explaining, setExplaining] = useState(false);
  const [downloading, setDownloading] = useState(false);

  useEffect(() => {
    loadDashboard();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [workflowId]);

  async function loadDashboard() {
    try {
      setLoading(true);
      const dashboard = await workflowService.getAutoDashboard(workflowId);
      setAutoDashboard(dashboard);
    } catch {
      // Fall back to legacy dashboard
      try {
        const legacy = await workflowService.getDashboard(workflowId);
        setLegacyData(legacy);
      } catch {
        setError("Dashboard not available");
      }
    } finally {
      setLoading(false);
    }
  }

  async function handleExplainChart(chart: ChartSpec) {
    try {
      setExplaining(true);
      const explanation = await workflowService.explainChart(workflowId, chart.id);
      setExplainedChart(explanation);
    } catch {
      setExplainedChart({
        chart_id: chart.id,
        chart_type: chart.chart_type,
        title: chart.title,
        reason: chart.reason,
        importance_score: chart.importance_score,
        confidence: chart.confidence,
        source_analysis: chart.source_analysis,
      });
    } finally {
      setExplaining(false);
    }
  }

  async function handleDownloadPresentation() {
    try {
      setDownloading(true);
      const blob = await workflowService.generatePresentation(workflowId, "executive");
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${autoDashboard?.dataset_name || "dataset"}_presentation.pptx`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch {
      setError("Failed to generate presentation");
    } finally {
      setDownloading(false);
    }
  }

  if (loading) return <Skeleton className="h-96" />;
  if (error) return <p className="text-muted-foreground">{error}</p>;

  // ── Auto dashboard view ──
  if (autoDashboard) {
    const primaryCharts = autoDashboard.charts.filter(c => c.section === "primary_charts");
    const supportingCharts = autoDashboard.charts.filter(c => c.section === "supporting_charts");

    return (
      <div className="space-y-6">
        {/* Header */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg flex items-center gap-2">
                <LayoutDashboard className="h-5 w-5" />
                {autoDashboard.title}
              </CardTitle>
              <div className="flex items-center gap-2">
                <Badge variant="default" className="bg-green-600">Auto-Generated</Badge>
                <Badge variant="outline" className="capitalize">{autoDashboard.industry}</Badge>
                <Button size="sm" variant="outline" onClick={handleDownloadPresentation} disabled={downloading} className="gap-2">
                  <Download className="h-4 w-4" />
                  {downloading ? "Generating..." : "Download PPTX"}
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">{autoDashboard.subtitle}</p>
            <p className="text-xs text-muted-foreground mt-1">
              {autoDashboard.charts.length} charts · {autoDashboard.kpis.length} KPIs · {autoDashboard.insights.length} insights · {autoDashboard.filters.length} filters
            </p>
          </CardContent>
        </Card>

        {/* KPI Row */}
        {autoDashboard.kpis.length > 0 && (
          <div>
            <h3 className="text-sm font-semibold text-muted-foreground mb-3">Key Performance Indicators</h3>
            <div className="grid gap-4 grid-cols-2 md:grid-cols-3 lg:grid-cols-6">
              {autoDashboard.kpis.map((kpi) => (
                <KPICard key={kpi.id} kpi={kpi} />
              ))}
            </div>
          </div>
        )}

        {/* Primary Charts */}
        {primaryCharts.length > 0 && (
          <div>
            <h3 className="text-sm font-semibold text-muted-foreground mb-3">Primary Visualizations</h3>
            <div className="grid gap-4 grid-cols-1 lg:grid-cols-2">
              {primaryCharts.map((chart) => (
                <ChartCard key={chart.id} chart={chart} onExplain={() => handleExplainChart(chart)} explaining={explaining} />
              ))}
            </div>
          </div>
        )}

        {/* Supporting Charts */}
        {supportingCharts.length > 0 && (
          <div>
            <h3 className="text-sm font-semibold text-muted-foreground mb-3">Supporting Analysis</h3>
            <div className="grid gap-4 grid-cols-1 lg:grid-cols-2">
              {supportingCharts.map((chart) => (
                <ChartCard key={chart.id} chart={chart} onExplain={() => handleExplainChart(chart)} explaining={explaining} />
              ))}
            </div>
          </div>
        )}

        {/* AI Insights */}
        {autoDashboard.insights.length > 0 && (
          <div>
            <h3 className="text-sm font-semibold text-muted-foreground mb-3 flex items-center gap-2">
              <Lightbulb className="h-4 w-4 text-yellow-600" />
              AI Insights
            </h3>
            <div className="space-y-2">
              {autoDashboard.insights.map((insight) => (
                <InsightCard key={insight.id} insight={insight} />
              ))}
            </div>
          </div>
        )}

        {/* Recommendations */}
        {autoDashboard.recommendations.length > 0 && (
          <div>
            <h3 className="text-sm font-semibold text-muted-foreground mb-3">Recommendations</h3>
            <div className="space-y-1">
              {autoDashboard.recommendations.map((rec, i) => (
                <div key={i} className="flex items-start gap-2 text-sm border rounded-lg p-3">
                  <span className="text-blue-600 font-bold">•</span>
                  <span>{rec}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Chart Explanation Modal */}
        {explainedChart && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={() => setExplainedChart(null)}>
            <Card className="max-w-lg w-full mx-4" onClick={(e) => e.stopPropagation()}>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <Info className="h-4 w-4 text-blue-600" />
                  Why this chart?
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div>
                  <p className="font-medium">{explainedChart.title}</p>
                  <Badge variant="outline" className="text-xs capitalize mt-1">
                    {explainedChart.chart_type.replace(/_/g, " ")}
                  </Badge>
                </div>
                <p className="text-sm text-muted-foreground">{explainedChart.reason}</p>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div className="border rounded p-2">
                    <p className="text-xs text-muted-foreground">Importance Score</p>
                    <p className="font-bold">{explainedChart.importance_score?.toFixed(1)}/100</p>
                  </div>
                  <div className="border rounded p-2">
                    <p className="text-xs text-muted-foreground">Confidence</p>
                    <p className="font-bold">{(explainedChart.confidence * 100).toFixed(0)}%</p>
                  </div>
                </div>
                <Button size="sm" variant="outline" onClick={() => setExplainedChart(null)} className="w-full">
                  Close
                </Button>
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    );
  }

  // ── Legacy fallback view ──
  if (legacyData) {
    return (
      <div className="space-y-4">
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <LayoutDashboard className="h-5 w-5" />
              Dashboard Recommendation
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-4 mb-4">
              <div>
                <p className="text-2xl font-bold capitalize">{legacyData.industry}</p>
                <p className="text-sm text-muted-foreground">
                  {legacyData.industry_confidence.toFixed(0)}% confidence
                </p>
              </div>
              {legacyData.recommended ? (
                <Badge variant="default" className="bg-green-600">Recommended</Badge>
              ) : (
                <Badge variant="secondary">Not Recommended</Badge>
              )}
            </div>

            <div className="bg-muted/50 rounded-lg p-4 mb-4">
              <p className="text-sm flex items-start gap-2">
                <Lightbulb className="h-4 w-4 text-yellow-600 mt-0.5 flex-shrink-0" />
                <span>{legacyData.reasoning}</span>
              </p>
            </div>

            {legacyData.needs_confirmation && (
              <Alert variant="destructive" className="mb-4">
                <span>{legacyData.confirmation_reason}</span>
              </Alert>
            )}

            <div className="grid grid-cols-2 gap-4 mt-4">
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Available Measures</CardTitle>
                </CardHeader>
                <CardContent>
                  {legacyData.available_measures.length > 0 ? (
                    <div className="space-y-1">
                      {legacyData.available_measures.map((m) => (
                        <div key={m.column} className="flex items-center justify-between text-sm">
                          <span>{m.display}</span>
                          <Badge variant="outline" className="text-xs">{m.column}</Badge>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-sm text-muted-foreground">No measures detected</p>
                  )}
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Available Dimensions</CardTitle>
                </CardHeader>
                <CardContent>
                  {legacyData.available_dimensions.length > 0 ? (
                    <div className="space-y-1">
                      {legacyData.available_dimensions.map((d) => (
                        <div key={d.column} className="flex items-center justify-between text-sm">
                          <span>{d.display}</span>
                          <Badge variant="outline" className="text-xs">{d.column}</Badge>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-sm text-muted-foreground">No dimensions detected</p>
                  )}
                </CardContent>
              </Card>
            </div>

            <Card className="mt-4">
              <CardHeader>
                <CardTitle className="text-lg">Recommended Charts ({legacyData.recommended_charts.length})</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid gap-3 md:grid-cols-2">
                  {legacyData.recommended_charts.map((chart, i) => (
                    <div key={i} className="border rounded-lg p-4">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="text-lg">{CHART_ICONS[chart.type] || "📊"}</span>
                        <span className="font-medium text-sm">{chart.title}</span>
                        <Badge variant="outline" className="text-xs capitalize ml-auto">
                          {chart.type.replace(/_/g, " ")}
                        </Badge>
                      </div>
                      <p className="text-xs text-muted-foreground">{chart.reasoning}</p>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </CardContent>
        </Card>
      </div>
    );
  }

  return <p className="text-muted-foreground">Dashboard recommendations not available</p>;
}

// ── Sub-components ──

function KPICard({ kpi }: { kpi: KPISpec }) {
  const isUp = kpi.comparison_direction === "up";
  const isDown = kpi.comparison_direction === "down";
  return (
    <div className="border rounded-lg p-4 space-y-1">
      <div className="flex items-center justify-between">
        <span className="text-lg">{kpi.icon}</span>
        {isUp && <TrendingUp className="h-4 w-4 text-green-600" />}
        {isDown && <TrendingDown className="h-4 w-4 text-red-600" />}
      </div>
      <p className="text-xs text-muted-foreground">{kpi.label}</p>
      <p className="text-xl font-bold">
        {typeof kpi.value === "number" ? kpi.value.toLocaleString() : kpi.value}
        {kpi.unit && <span className="text-sm font-normal text-muted-foreground ml-1">{kpi.unit}</span>}
      </p>
      {kpi.comparison_label && (
        <p className="text-xs text-muted-foreground">{kpi.comparison_label}</p>
      )}
    </div>
  );
}

function ChartCard({
  chart,
  onExplain,
  explaining,
}: {
  chart: ChartSpec;
  onExplain: () => void;
  explaining: boolean;
}) {
  return (
    <div className="border rounded-lg p-4 space-y-2">
      <div className="flex items-center gap-2">
        <span className="text-lg">{CHART_ICONS[chart.chart_type] || "📊"}</span>
        <span className="font-medium text-sm flex-1">{chart.title}</span>
        <Badge variant="outline" className="text-xs capitalize">
          {chart.chart_type.replace(/_/g, " ")}
        </Badge>
      </div>
      <p className="text-xs text-muted-foreground">{chart.description}</p>

      {/* Chart data preview */}
      {chart.data.length > 0 && (
        <div className="bg-muted/30 rounded p-2 max-h-32 overflow-y-auto">
          <div className="text-xs space-y-1">
            {chart.data.slice(0, 5).map((row, i) => (
              <div key={i} className="flex justify-between">
                <span className="truncate">{String(row.x ?? row.label ?? "")}</span>
                <span className="font-mono">{String(row.y ?? row.value ?? "")}</span>
              </div>
            ))}
            {chart.data.length > 5 && (
              <p className="text-muted-foreground">... +{chart.data.length - 5} more</p>
            )}
          </div>
        </div>
      )}

      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Badge variant="secondary" className="text-xs">
            Score: {chart.importance_score.toFixed(0)}
          </Badge>
          <Badge variant="outline" className="text-xs capitalize">
            {chart.source_analysis.replace(/_/g, " ")}
          </Badge>
        </div>
        <Button size="sm" variant="ghost" onClick={onExplain} disabled={explaining} className="text-xs gap-1">
          <Info className="h-3 w-3" />
          Why?
        </Button>
      </div>
    </div>
  );
}

function InsightCard({ insight }: { insight: InsightSpec }) {
  const Icon = SEVERITY_ICONS[insight.severity] || Info;
  const colorClass = SEVERITY_COLORS[insight.severity] || SEVERITY_COLORS.info;
  return (
    <div className={`border rounded-lg p-3 ${colorClass}`}>
      <div className="flex items-start gap-2">
        <Icon className="h-4 w-4 mt-0.5 flex-shrink-0" />
        <div className="flex-1">
          <p className="font-medium text-sm">{insight.title}</p>
          <p className="text-xs mt-1 opacity-90">{insight.description}</p>
          {insight.recommendation && (
            <p className="text-xs mt-1 italic opacity-75">→ {insight.recommendation}</p>
          )}
        </div>
        <Badge variant="outline" className="text-xs capitalize flex-shrink-0">
          {insight.insight_type.replace(/_/g, " ")}
        </Badge>
      </div>
    </div>
  );
}
