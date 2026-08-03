'use client';

import { useEffect, useState, useCallback } from 'react';
import {
  Plus, Trash2, Download, FileText, Presentation as PresentationIcon,
  BarChart3, Table as TableIcon, Lightbulb, CheckSquare, Loader2,
  ArrowRight, Sparkles, LayoutDashboard, GripVertical,
} from 'lucide-react';
import {
  reportEngineService,
  type ReportComposition,
  type ReportSection,
  type TemplateInfo,
} from '@/services/reports/reportEngineService';
import { Button } from '@/components/ui/Button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import { Badge } from '@/components/ui/Badge';
import { cn } from '@/lib/utils';
import { PresentationViewer } from './PresentationViewer';
import { useAuthStore } from '@/stores/authStore';
import { toast } from '@/components/ui/Toaster';

const SECTION_ICONS: Record<string, typeof FileText> = {
  cover: FileText,
  executive_summary: Sparkles,
  key_metrics: LayoutDashboard,
  chart: BarChart3,
  table: TableIcon,
  insights: Lightbulb,
  recommendations: CheckSquare,
  methodology: FileText,
  appendix: FileText,
  custom: FileText,
};

const SEVERITY_COLORS: Record<string, string> = {
  critical: 'border-red-500 bg-red-50 dark:bg-red-950/30',
  warning: 'border-amber-500 bg-amber-50 dark:bg-amber-950/30',
  positive: 'border-green-500 bg-green-50 dark:bg-green-950/30',
  info: 'border-blue-500 bg-blue-50 dark:bg-blue-950/30',
};

const PRIORITY_COLORS: Record<string, string> = {
  high: 'bg-red-100 text-red-700 dark:bg-red-950 dark:text-red-400',
  medium: 'bg-amber-100 text-amber-700 dark:bg-amber-950 dark:text-amber-400',
  low: 'bg-blue-100 text-blue-700 dark:bg-blue-950 dark:text-blue-400',
};

interface ReportBuilderProps {
  reportId?: string;
  onSaved?: (reportId: string) => void;
}

export function ReportBuilder({ reportId: initialReportId, onSaved }: ReportBuilderProps) {
  const { user } = useAuthStore();
  const [report, setReport] = useState<ReportComposition | null>(null);
  const [templates, setTemplates] = useState<TemplateInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [view, setView] = useState<'compose' | 'preview' | 'presentation'>('compose');
  const [reportId, setReportId] = useState(initialReportId || '');

  const loadTemplates = useCallback(async () => {
    try {
      const data = await reportEngineService.listTemplates();
      setTemplates(data.templates);
    } catch {
      // ignore
    }
  }, []);

  const loadReport = useCallback(async (id: string) => {
    try {
      const data = await reportEngineService.getReport(id);
      setReport(data);
    } catch {
      // ignore
    }
  }, []);

  useEffect(() => {
    loadTemplates();
    if (reportId) {
      loadReport(reportId);
    }
    setLoading(false);
  }, [reportId, loadTemplates, loadReport]);

  const handleCreate = async (template: string) => {
    setCreating(true);
    try {
      const data = await reportEngineService.createReport({
        title: 'Untitled Report',
        template,
        organization_name: (user as any)?.organization_name || '',
        author_name: (user as any)?.full_name || (user as any)?.email || '',
        industry: (user as any)?.industry || '',
      });
      setReport(data);
      setReportId(data.report_id);
      onSaved?.(data.report_id);
      toast.success('Report created');
    } catch (err) {
      toast.error('Failed to create report');
    } finally {
      setCreating(false);
    }
  };

  const handleDeleteSection = async (sectionOrder: number) => {
    if (!reportId) return;
    try {
      const updated = await reportEngineService.removeSection(reportId, sectionOrder);
      setReport(updated);
    } catch {
      toast.error('Failed to remove section');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-16">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  // No report yet — show template picker
  if (!report && !reportId) {
    return (
      <div className="space-y-6">
        <div>
          <h2 className="text-2xl font-bold">Create a Report</h2>
          <p className="mt-1 text-muted-foreground">Choose a template to get started</p>
        </div>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {templates.map((tpl) => (
            <Card
              key={tpl.key}
              className="cursor-pointer transition-all hover:shadow-lg hover:border-primary"
              onClick={() => handleCreate(tpl.key)}
            >
              <CardContent className="p-6">
                <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10 text-primary">
                  <FileText size={24} />
                </div>
                <h3 className="font-semibold">{tpl.name}</h3>
                <p className="mt-1 text-sm text-muted-foreground">{tpl.description}</p>
                {creating ? (
                  <div className="mt-4 flex items-center gap-2 text-sm text-muted-foreground">
                    <Loader2 size={14} className="animate-spin" /> Creating...
                  </div>
                ) : (
                  <Button size="sm" className="mt-4 gap-1">
                    Use Template <ArrowRight size={14} />
                  </Button>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  // Loading existing report
  if (!report) {
    return (
      <div className="flex items-center justify-center py-16">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">{report.title}</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            {report.subtitle} · {report.template} template · {report.sections.length} sections
          </p>
        </div>
        <div className="flex items-center gap-2">
          {/* View toggle */}
          <div className="flex rounded-lg border p-1">
            <button
              onClick={() => setView('compose')}
              className={cn(
                'rounded px-3 py-1 text-xs font-medium transition-colors',
                view === 'compose' ? 'bg-primary text-primary-foreground' : 'text-muted-foreground hover:text-foreground'
              )}
            >
              Compose
            </button>
            <button
              onClick={() => setView('preview')}
              className={cn(
                'rounded px-3 py-1 text-xs font-medium transition-colors',
                view === 'preview' ? 'bg-primary text-primary-foreground' : 'text-muted-foreground hover:text-foreground'
              )}
            >
              Preview
            </button>
            <button
              onClick={() => setView('presentation')}
              className={cn(
                'rounded px-3 py-1 text-xs font-medium transition-colors',
                view === 'presentation' ? 'bg-primary text-primary-foreground' : 'text-muted-foreground hover:text-foreground'
              )}
            >
              Presentation
            </button>
          </div>
          {/* Export buttons */}
          <a href={reportEngineService.exportReportUrl(reportId, 'pdf')} download>
            <Button variant="outline" size="sm" className="gap-1">
              <Download size={14} /> PDF
            </Button>
          </a>
          <a href={reportEngineService.exportReportUrl(reportId, 'pptx')} download>
            <Button variant="outline" size="sm" className="gap-1">
              <Download size={14} /> PPTX
            </Button>
          </a>
        </div>
      </div>

      {/* Compose view */}
      {view === 'compose' && (
        <div className="space-y-4">
          {report.sections.map((section) => {
            const Icon = SECTION_ICONS[section.section_type] || FileText;
            return (
              <Card key={section.order}>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <GripVertical className="h-4 w-4 text-muted-foreground" />
                      <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10 text-primary">
                        <Icon size={16} />
                      </div>
                      <div>
                        <CardTitle className="text-base">{section.title}</CardTitle>
                        <Badge variant="outline" className="mt-1 text-xs">{section.section_type.replace('_', ' ')}</Badge>
                      </div>
                    </div>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => handleDeleteSection(section.order)}
                      className="text-red-500 hover:text-red-700"
                    >
                      <Trash2 size={14} />
                    </Button>
                  </div>
                </CardHeader>
                <CardContent>
                  {/* KPIs */}
                  {section.kpis && section.kpis.length > 0 && (
                    <div className="mb-4">
                      <p className="mb-2 text-xs font-semibold uppercase text-muted-foreground">KPIs</p>
                      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
                        {section.kpis.map((kpi, i) => (
                          <div key={i} className="rounded-lg border p-3 text-center">
                            <p className="text-xs text-muted-foreground">{kpi.label}</p>
                            <p className="mt-1 text-xl font-bold text-primary">{kpi.value}{kpi.unit}</p>
                            {kpi.trend_value && (
                              <p className={cn(
                                'text-xs',
                                kpi.trend === 'up' ? 'text-green-600' : kpi.trend === 'down' ? 'text-red-600' : 'text-muted-foreground'
                              )}>
                                {kpi.trend_value}
                              </p>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Charts */}
                  {section.charts && section.charts.length > 0 && (
                    <div className="mb-4">
                      <p className="mb-2 text-xs font-semibold uppercase text-muted-foreground">Charts</p>
                      {section.charts.map((chart, i) => (
                        <div key={i} className="mb-2 rounded-lg border-2 border-dashed p-4">
                          <p className="text-sm font-medium">{chart.title}</p>
                          <p className="text-xs text-muted-foreground">{chart.chart_type} · X: {chart.x_axis} · Y: {chart.y_axis}</p>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Tables */}
                  {section.tables && section.tables.length > 0 && (
                    <div className="mb-4">
                      <p className="mb-2 text-xs font-semibold uppercase text-muted-foreground">Tables</p>
                      {section.tables.map((table, i) => (
                        <div key={i} className="mb-2 overflow-auto rounded-lg border">
                          <p className="border-b p-2 text-sm font-medium">{table.title}</p>
                          <table className="w-full text-xs">
                            <thead>
                              <tr className="border-b bg-muted/50">
                                {table.columns.map((col, j) => (
                                  <th key={j} className="px-2 py-1 text-left font-semibold">{col}</th>
                                ))}
                              </tr>
                            </thead>
                            <tbody>
                              {table.rows.slice(0, 5).map((row, j) => (
                                <tr key={j} className="border-b">
                                  {Array.isArray(row) && row.map((cell, k) => (
                                    <td key={k} className="px-2 py-1">{String(cell)}</td>
                                  ))}
                                </tr>
                              ))}
                            </tbody>
                          </table>
                          {table.rows.length > 5 && (
                            <p className="p-1 text-center text-xs text-muted-foreground">+{table.rows.length - 5} more rows</p>
                          )}
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Insights */}
                  {section.insights && section.insights.length > 0 && (
                    <div className="mb-4">
                      <p className="mb-2 text-xs font-semibold uppercase text-muted-foreground">Insights</p>
                      <div className="space-y-2">
                        {section.insights.map((insight, i) => (
                          <div key={i} className={cn('rounded-lg border-l-4 p-3', SEVERITY_COLORS[insight.severity || 'info'])}>
                            <p className="text-sm font-semibold">{insight.title}</p>
                            <p className="mt-1 text-xs text-muted-foreground">{insight.description}</p>
                            {insight.impact && <p className="mt-1 text-xs italic">Impact: {insight.impact}</p>}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Recommendations */}
                  {section.recommendations && section.recommendations.length > 0 && (
                    <div className="mb-4">
                      <p className="mb-2 text-xs font-semibold uppercase text-muted-foreground">Recommendations</p>
                      <div className="space-y-2">
                        {section.recommendations.map((rec, i) => (
                          <div key={i} className="rounded-lg border p-3">
                            <div className="flex items-center gap-2">
                              <span className={cn('rounded px-2 py-0.5 text-xs font-bold', PRIORITY_COLORS[rec.priority || 'medium'])}>
                                {rec.priority?.toUpperCase()}
                              </span>
                              <p className="text-sm font-semibold">{rec.title}</p>
                            </div>
                            <p className="mt-1 text-xs text-muted-foreground">{rec.description}</p>
                            {rec.action && <p className="mt-1 text-xs">Action: {rec.action}</p>}
                            {rec.timeline && <p className="text-xs italic">Timeline: {rec.timeline}</p>}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Content */}
                  {section.content && (
                    <p className="text-sm text-muted-foreground">{section.content}</p>
                  )}
                </CardContent>
              </Card>
            );
          })}

          {/* Add section button */}
          <Button variant="outline" className="w-full gap-2 border-dashed">
            <Plus size={16} /> Add Section
          </Button>
        </div>
      )}

      {/* Preview view */}
      {view === 'preview' && (
        <Card>
          <CardContent className="p-8">
            {/* Cover */}
            <div className="mb-8 text-center">
              <h1 className="text-3xl font-bold text-slate-900 dark:text-slate-100">{report.title}</h1>
              <p className="mt-2 text-lg text-muted-foreground">{report.subtitle}</p>
              <div className="mt-4 text-sm text-muted-foreground">
                <p>Organization: {report.organization_name || 'N/A'}</p>
                <p>Author: {report.author_name || 'N/A'}</p>
                <p>Date: {new Date().toLocaleDateString()}</p>
              </div>
            </div>

            {/* Executive Summary */}
            {report.executive_summary && (
              <div className="mb-8">
                <h2 className="mb-3 border-b-2 border-primary pb-2 text-xl font-bold">Executive Summary</h2>
                <p className="text-sm text-muted-foreground">{report.executive_summary}</p>
              </div>
            )}

            {/* Sections */}
            {report.sections.filter(s => s.section_type !== 'cover').map((section) => {
              const Icon = SECTION_ICONS[section.section_type] || FileText;
              return (
                <div key={section.order} className="mb-8">
                  <h2 className="mb-3 flex items-center gap-2 border-b-2 border-primary pb-2 text-xl font-bold">
                    <Icon size={18} /> {section.title}
                  </h2>
                  {section.content && <p className="mb-3 text-sm text-muted-foreground">{section.content}</p>}

                  {/* KPIs */}
                  {section.kpis && section.kpis.length > 0 && (
                    <div className="mb-4 grid grid-cols-2 gap-3 md:grid-cols-4">
                      {section.kpis.map((kpi, i) => (
                        <div key={i} className="rounded-lg border p-4 text-center">
                          <p className="text-xs uppercase text-muted-foreground">{kpi.label}</p>
                          <p className="mt-1 text-2xl font-bold text-primary">{kpi.value}{kpi.unit}</p>
                          {kpi.trend_value && (
                            <p className={cn('text-xs', kpi.trend === 'up' ? 'text-green-600' : 'text-red-600')}>
                              {kpi.trend_value}
                            </p>
                          )}
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Insights */}
                  {section.insights && section.insights.length > 0 && (
                    <div className="mb-4 space-y-2">
                      {section.insights.map((insight, i) => (
                        <div key={i} className={cn('rounded-lg border-l-4 p-3', SEVERITY_COLORS[insight.severity || 'info'])}>
                          <p className="text-sm font-semibold">{insight.title}</p>
                          <p className="mt-1 text-xs text-muted-foreground">{insight.description}</p>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Recommendations */}
                  {section.recommendations && section.recommendations.length > 0 && (
                    <div className="space-y-2">
                      {section.recommendations.map((rec, i) => (
                        <div key={i} className="rounded-lg border p-3">
                          <div className="flex items-center gap-2">
                            <span className={cn('rounded px-2 py-0.5 text-xs font-bold', PRIORITY_COLORS[rec.priority || 'medium'])}>
                              {rec.priority?.toUpperCase()}
                            </span>
                            <p className="text-sm font-semibold">{rec.title}</p>
                          </div>
                          <p className="mt-1 text-xs text-muted-foreground">{rec.description}</p>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              );
            })}
          </CardContent>
        </Card>
      )}

      {/* Presentation view */}
      {view === 'presentation' && (
        <PresentationViewer reportId={reportId} />
      )}
    </div>
  );
}
