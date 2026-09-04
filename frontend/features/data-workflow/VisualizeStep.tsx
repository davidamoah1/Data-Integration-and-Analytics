'use client';

import { useState, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import {
  LayoutDashboard,
  Save,
  CheckCircle2,
  TrendingUp,
  Info,
  Database,
  Search,
  Filter,
  BarChart3,
  Hash,
  Type,
  Calendar,
  AlertCircle,
  Sparkles,
  PieChart,
  Layers,
  ArrowUpDown,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Input } from '@/components/ui/Input';
import { SlideChart } from '@/components/reports/SlideChart';
import { cleanMojibake } from '@/lib/utils';
import type {
  DashboardRecommendation,
  AutoDashboardSpec,
  ChartSpec,
  DatasetProfile,
} from '@/types/workflow';

interface Props {
  dashboard: DashboardRecommendation | null;
  autoDashboard?: AutoDashboardSpec | null;
  profile?: DatasetProfile | null;
  onSaveDashboard: () => void;
  onContinue: () => void;
  isSaving: boolean;
  savedDashboardId: number | null;
}

export function VisualizeStep({
  dashboard,
  autoDashboard,
  profile,
  onSaveDashboard,
  onContinue,
  isSaving,
  savedDashboardId,
}: Props) {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<'dashboard' | 'schema'>('dashboard');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<'all' | 'measure' | 'dimension' | 'temporal'>('all');

  // Compute all available fields from profile, autoDashboard, or dashboard
  const allFields = useMemo(() => {
    if (profile?.columns && profile.columns.length > 0) {
      return profile.columns.map((col) => {
        const dtypeLower = (col.dtype || '').toLowerCase();
        const isTime =
          dtypeLower.includes('date') ||
          dtypeLower.includes('time') ||
          dashboard?.time_fields?.some((t) => t.column === col.name);
        const isGeo = dashboard?.geo_fields?.some((g) => g.column === col.name);
        const isMeasure =
          !isTime &&
          !isGeo &&
          (['int', 'float', 'number', 'double', 'decimal'].some((t) => dtypeLower.includes(t)) ||
            dashboard?.available_measures?.some((m) => m.column === col.name));

        const category: 'measure' | 'dimension' | 'temporal' | 'geo' = isTime
          ? 'temporal'
          : isGeo
          ? 'geo'
          : isMeasure
          ? 'measure'
          : 'dimension';

        // Find which auto dashboard charts or KPIs use this field
        const usedInCharts = (autoDashboard?.charts || [])
          .filter(
            (c) =>
              (c.source_columns && c.source_columns.includes(col.name)) ||
              c.x_axis === col.name ||
              c.y_axis === col.name
          )
          .map((c) => cleanMojibake(c.title));

        const usedInKPIs = (autoDashboard?.kpis || [])
          .filter((k) => k.source_columns && k.source_columns.includes(col.name))
          .map((k) => cleanMojibake(k.label));

        const compPct =
          col.completeness != null
            ? col.completeness <= 1
              ? col.completeness * 100
              : col.completeness
            : col.null_percentage != null
            ? 100 - col.null_percentage
            : 100;

        return {
          name: col.name,
          dtype: col.dtype.toUpperCase(),
          category,
          completeness: Math.round(compPct * 10) / 10,
          nullCount: col.null_count ?? 0,
          uniqueCount: col.unique_count ?? 0,
          cardinality: col.cardinality || (col.unique_count ? `${col.unique_count} unique` : 'Standard'),
          minValue: col.min_value,
          maxValue: col.max_value,
          meanValue: col.mean_value,
          topValues: col.top_values,
          usedInCharts,
          usedInKPIs,
        };
      });
    }

    // Fallback: build from dashboard recommendations and autoDashboard charts
    const fieldMap = new Map<
      string,
      {
        name: string;
        dtype: string;
        category: 'measure' | 'dimension' | 'temporal' | 'geo';
        completeness: number;
        nullCount: number;
        uniqueCount: number;
        cardinality: string;
        minValue?: number | null;
        maxValue?: number | null;
        meanValue?: number | null;
        topValues?: Record<string, number>;
        usedInCharts: string[];
        usedInKPIs: string[];
      }
    >();

    dashboard?.available_measures?.forEach((m) => {
      fieldMap.set(m.column, {
        name: m.column,
        dtype: 'NUMERIC',
        category: 'measure',
        completeness: 100,
        nullCount: 0,
        uniqueCount: 0,
        cardinality: 'Continuous Metric',
        usedInCharts: [],
        usedInKPIs: [],
      });
    });

    dashboard?.available_dimensions?.forEach((d) => {
      if (!fieldMap.has(d.column)) {
        fieldMap.set(d.column, {
          name: d.column,
          dtype: 'STRING',
          category: 'dimension',
          completeness: 100,
          nullCount: 0,
          uniqueCount: 0,
          cardinality: 'Categorical',
          usedInCharts: [],
          usedInKPIs: [],
        });
      }
    });

    dashboard?.time_fields?.forEach((t) => {
      fieldMap.set(t.column, {
        name: t.column,
        dtype: 'DATETIME',
        category: 'temporal',
        completeness: 100,
        nullCount: 0,
        uniqueCount: 0,
        cardinality: 'Temporal',
        usedInCharts: [],
        usedInKPIs: [],
      });
    });

    autoDashboard?.charts?.forEach((c) => {
      c.source_columns?.forEach((col) => {
        const isY = c.y_axis === col;
        if (!fieldMap.has(col)) {
          fieldMap.set(col, {
            name: col,
            dtype: isY ? 'NUMERIC' : 'STRING',
            category: isY ? 'measure' : 'dimension',
            completeness: 100,
            nullCount: 0,
            uniqueCount: 0,
            cardinality: isY ? 'Continuous' : 'Categorical',
            usedInCharts: [cleanMojibake(c.title)],
            usedInKPIs: [],
          });
        } else {
          const item = fieldMap.get(col)!;
          if (!item.usedInCharts.includes(cleanMojibake(c.title))) {
            item.usedInCharts.push(cleanMojibake(c.title));
          }
        }
      });
    });

    return Array.from(fieldMap.values());
  }, [profile, dashboard, autoDashboard]);

  // Filtered fields based on category and search query
  const filteredFields = useMemo(() => {
    return allFields.filter((f) => {
      const matchesCategory =
        selectedCategory === 'all' || f.category === selectedCategory;
      const matchesSearch =
        !searchQuery.trim() ||
        f.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        f.dtype.toLowerCase().includes(searchQuery.toLowerCase());
      return matchesCategory && matchesSearch;
    });
  }, [allFields, selectedCategory, searchQuery]);

  const measureCount = useMemo(
    () => allFields.filter((f) => f.category === 'measure').length,
    [allFields]
  );
  const dimensionCount = useMemo(
    () => allFields.filter((f) => f.category === 'dimension').length,
    [allFields]
  );
  const temporalCount = useMemo(
    () => allFields.filter((f) => f.category === 'temporal').length,
    [allFields]
  );

  if (!dashboard && !autoDashboard && (!profile || !profile.columns)) {
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
                  {cleanMojibake(autoDashboard?.title) || 'Automated Intelligence Dashboard'}
                </p>
                <p className="text-xs text-muted-foreground">
                  Sector: <span className="capitalize font-medium text-foreground">{industryName}</span> &bull;{' '}
                  {charts.length > 0 ? `${charts.length} interactive charts generated` : 'AI recommendations ready'} &bull;{' '}
                  {allFields.length} data fields available
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant={activeTab === 'dashboard' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setActiveTab('dashboard')}
              >
                <BarChart3 className="mr-1.5 h-3.5 w-3.5" />
                Visualizations
              </Button>
              <Button
                variant={activeTab === 'schema' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setActiveTab('schema')}
              >
                <Database className="mr-1.5 h-3.5 w-3.5" />
                Data Fields ({allFields.length})
              </Button>
              {!savedDashboardId ? (
                <Button onClick={onSaveDashboard} disabled={isSaving} size="sm" variant="secondary" className="shadow-sm">
                  <Save className="mr-1.5 h-3.5 w-3.5" />
                  {isSaving ? 'Saving...' : 'Save Dashboard'}
                </Button>
              ) : (
                <div className="flex items-center gap-2">
                  <Badge variant="default" className="bg-emerald-600 text-white flex items-center gap-1 py-1 px-2.5 shadow-sm">
                    <CheckCircle2 className="h-3.5 w-3.5" /> Saved
                  </Badge>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => router.push(`/analytics/${savedDashboardId}`)}
                    className="border-emerald-600/40 text-emerald-700 hover:bg-emerald-50 dark:text-emerald-400 dark:hover:bg-emerald-950/50"
                  >
                    Open Studio &rarr;
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => router.push('/dashboard')}
                    className="text-slate-600 hover:text-slate-900 dark:text-slate-400"
                  >
                    View Org Dashboard
                  </Button>
                </div>
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
                        <CardTitle className="text-sm font-semibold">{cleanMojibake(chart.title)}</CardTitle>
                        {chart.description && (
                          <CardDescription className="text-xs mt-0.5">{cleanMojibake(chart.description)}</CardDescription>
                        )}
                      </div>
                      <Badge variant="outline" className="text-[10px] uppercase font-mono shrink-0">
                        {chart.chart_type}
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent className="pt-2">
                    {chart.data && chart.data.length > 0 ? (
                      <div className="w-full overflow-hidden">
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
                        <span>{cleanMojibake(chart.reason)}</span>
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : dashboard?.recommended_charts && dashboard.recommended_charts.length > 0 ? (
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

      {/* TAB 2: DATA FIELDS & SCHEMA EXPLORER */}
      {activeTab === 'schema' && (
        <div className="space-y-6">
          {/* Schema Overview Strip */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <Card>
              <CardContent className="pt-4 pb-4">
                <p className="text-xs text-muted-foreground font-medium">Total Fields</p>
                <p className="text-2xl font-bold mt-0.5 text-foreground">{allFields.length}</p>
                <p className="text-[11px] text-muted-foreground mt-0.5">
                  Across {profile?.row_count ? `${profile.row_count.toLocaleString()} rows` : 'active dataset'}
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-4 pb-4">
                <p className="text-xs text-muted-foreground font-medium">Numeric Measures</p>
                <p className="text-2xl font-bold mt-0.5 text-blue-600 dark:text-blue-400">{measureCount}</p>
                <p className="text-[11px] text-muted-foreground mt-0.5">Continuous aggregations</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-4 pb-4">
                <p className="text-xs text-muted-foreground font-medium">Dimensions</p>
                <p className="text-2xl font-bold mt-0.5 text-purple-600 dark:text-purple-400">{dimensionCount}</p>
                <p className="text-[11px] text-muted-foreground mt-0.5">Categorical attributes</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-4 pb-4">
                <p className="text-xs text-muted-foreground font-medium">Overall Completeness</p>
                <p className="text-2xl font-bold mt-0.5 text-emerald-600 dark:text-emerald-400">
                  {profile?.overall_completeness != null
                    ? `${Math.round(profile.overall_completeness <= 1 ? profile.overall_completeness * 100 : profile.overall_completeness)}%`
                    : '100%'}
                </p>
                <p className="text-[11px] text-muted-foreground mt-0.5">Dataset integrity score</p>
              </CardContent>
            </Card>
          </div>

          {/* Filter & Search Toolbar */}
          <Card>
            <CardContent className="py-4">
              <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
                <div className="relative w-full sm:w-80">
                  <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                  <Input
                    placeholder="Search field name or type..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-9 h-9 text-xs"
                  />
                </div>
                <div className="flex items-center gap-1.5 w-full sm:w-auto overflow-x-auto pb-1 sm:pb-0">
                  <Button
                    variant={selectedCategory === 'all' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setSelectedCategory('all')}
                    className="h-8 text-xs shrink-0"
                  >
                    All Fields ({allFields.length})
                  </Button>
                  <Button
                    variant={selectedCategory === 'measure' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setSelectedCategory('measure')}
                    className="h-8 text-xs shrink-0"
                  >
                    <Hash className="mr-1 h-3 w-3 text-blue-500" />
                    Measures ({measureCount})
                  </Button>
                  <Button
                    variant={selectedCategory === 'dimension' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setSelectedCategory('dimension')}
                    className="h-8 text-xs shrink-0"
                  >
                    <Type className="mr-1 h-3 w-3 text-purple-500" />
                    Dimensions ({dimensionCount})
                  </Button>
                  {temporalCount > 0 && (
                    <Button
                      variant={selectedCategory === 'temporal' ? 'default' : 'outline'}
                      size="sm"
                      onClick={() => setSelectedCategory('temporal')}
                      className="h-8 text-xs shrink-0"
                    >
                      <Calendar className="mr-1 h-3 w-3 text-amber-500" />
                      Temporal ({temporalCount})
                    </Button>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Fields List */}
          {filteredFields.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {filteredFields.map((field) => (
                <Card key={field.name} className="hover:border-primary/40 transition-colors">
                  <CardHeader className="pb-3 pt-4">
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex items-center gap-2 min-w-0">
                        <div className={`p-1.5 rounded-md shrink-0 ${
                          field.category === 'measure'
                            ? 'bg-blue-100 dark:bg-blue-950 text-blue-600 dark:text-blue-400'
                            : field.category === 'temporal'
                            ? 'bg-amber-100 dark:bg-amber-950 text-amber-600 dark:text-amber-400'
                            : 'bg-purple-100 dark:bg-purple-950 text-purple-600 dark:text-purple-400'
                        }`}>
                          {field.category === 'measure' ? (
                            <Hash className="h-4 w-4" />
                          ) : field.category === 'temporal' ? (
                            <Calendar className="h-4 w-4" />
                          ) : (
                            <Type className="h-4 w-4" />
                          )}
                        </div>
                        <div className="min-w-0">
                          <CardTitle className="text-sm font-semibold truncate" title={field.name}>
                            {field.name}
                          </CardTitle>
                          <p className="text-[11px] text-muted-foreground font-mono">
                            {field.dtype} &bull; {field.cardinality}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-1.5 shrink-0">
                        <Badge
                          variant={field.category === 'measure' ? 'default' : 'secondary'}
                          className={`text-[10px] capitalize ${
                            field.category === 'measure'
                              ? 'bg-blue-600 text-white hover:bg-blue-700'
                              : field.category === 'temporal'
                              ? 'bg-amber-600 text-white hover:bg-amber-700'
                              : 'bg-purple-100 text-purple-700 dark:bg-purple-900/50 dark:text-purple-300'
                          }`}
                        >
                          {field.category}
                        </Badge>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-3 pb-4">
                    {/* Completeness bar */}
                    <div>
                      <div className="flex items-center justify-between text-[11px] mb-1">
                        <span className="text-muted-foreground font-medium">Completeness</span>
                        <span className="font-semibold">{field.completeness}% ({field.nullCount} missing)</span>
                      </div>
                      <div className="w-full bg-slate-100 dark:bg-slate-800 rounded-full h-1.5 overflow-hidden">
                        <div
                          className={`h-full rounded-full ${
                            field.completeness >= 95
                              ? 'bg-emerald-500'
                              : field.completeness >= 80
                              ? 'bg-amber-500'
                              : 'bg-rose-500'
                          }`}
                          style={{ width: `${Math.min(100, Math.max(0, field.completeness))}%` }}
                        />
                      </div>
                    </div>

                    {/* Numeric Statistics if available */}
                    {field.category === 'measure' && (field.minValue != null || field.maxValue != null) && (
                      <div className="grid grid-cols-3 gap-2 bg-muted/30 p-2 rounded text-[11px]">
                        <div>
                          <p className="text-muted-foreground text-[10px]">Min</p>
                          <p className="font-semibold text-foreground">
                            {typeof field.minValue === 'number'
                              ? field.minValue.toLocaleString(undefined, { maximumFractionDigits: 1 })
                              : field.minValue ?? '—'}
                          </p>
                        </div>
                        <div>
                          <p className="text-muted-foreground text-[10px]">Max</p>
                          <p className="font-semibold text-foreground">
                            {typeof field.maxValue === 'number'
                              ? field.maxValue.toLocaleString(undefined, { maximumFractionDigits: 1 })
                              : field.maxValue ?? '—'}
                          </p>
                        </div>
                        <div>
                          <p className="text-muted-foreground text-[10px]">Mean (Avg)</p>
                          <p className="font-semibold text-foreground">
                            {typeof field.meanValue === 'number'
                              ? field.meanValue.toLocaleString(undefined, { maximumFractionDigits: 1 })
                              : field.meanValue ?? '—'}
                          </p>
                        </div>
                      </div>
                    )}

                    {/* Frequent Top Values if categorical */}
                    {field.topValues && Object.keys(field.topValues).length > 0 && (
                      <div className="bg-muted/30 p-2 rounded text-[11px]">
                        <p className="text-muted-foreground text-[10px] mb-1">Top Sample Segments</p>
                        <div className="flex flex-wrap gap-1">
                          {Object.entries(field.topValues)
                            .slice(0, 4)
                            .map(([val, cnt], i) => (
                              <span
                                key={i}
                                className="inline-flex items-center px-1.5 py-0.5 rounded bg-background border border-border/60 text-[10px]"
                              >
                                <span className="font-medium truncate max-w-[90px]">{cleanMojibake(val)}</span>
                                <span className="ml-1 text-muted-foreground">({cnt})</span>
                              </span>
                            ))}
                        </div>
                      </div>
                    )}

                    {/* Dashboard Visualizations using this field */}
                    {(field.usedInCharts.length > 0 || field.usedInKPIs.length > 0) && (
                      <div className="pt-1">
                        <p className="text-[10px] text-muted-foreground font-medium mb-1.5 flex items-center gap-1">
                          <Sparkles className="h-3 w-3 text-primary" /> Active in Visualizations:
                        </p>
                        <div className="flex flex-wrap gap-1">
                          {field.usedInCharts.map((title, i) => (
                            <Badge
                              key={i}
                              variant="outline"
                              className="text-[10px] py-0 px-1.5 font-normal bg-primary/5 text-primary border-primary/20"
                            >
                              <BarChart3 className="mr-1 h-2.5 w-2.5" />
                              {title}
                            </Badge>
                          ))}
                          {field.usedInKPIs.map((label, i) => (
                            <Badge
                              key={i}
                              variant="outline"
                              className="text-[10px] py-0 px-1.5 font-normal bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300 border-emerald-200 dark:border-emerald-800"
                            >
                              <TrendingUp className="mr-1 h-2.5 w-2.5" />
                              KPI: {label}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : (
            <Card>
              <CardContent className="py-12 text-center text-muted-foreground text-sm">
                No data fields found matching "{searchQuery}".
              </CardContent>
            </Card>
          )}
        </div>
      )}

      <Button onClick={onContinue} size="lg" className="w-full">
        Continue to Formal Report &rarr;
      </Button>
    </div>
  );
}
