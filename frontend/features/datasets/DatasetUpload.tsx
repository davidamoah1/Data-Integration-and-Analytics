'use client';

import { useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { useDropzone } from 'react-dropzone';
import {
  Upload,
  File as FileIcon,
  CheckCircle,
  XCircle,
  Loader2,
  Database,
  BarChart3,
  Table as TableIcon,
  Shield,
  Lightbulb,
  AlertCircle,
  Save,
  LayoutDashboard,
  FileText,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Alert, AlertDescription } from '@/components/ui/Alert';
import { toast } from '@/components/ui/Toaster';
import { datasetService } from '@/services/datasets/datasetService';
import { cn, formatNumber } from '@/lib/utils';

type UploadStage = 'idle' | 'uploading' | 'validating' | 'analyzing' | 'done' | 'error';

interface AnalysisResult {
  mapping?: {
    industry?: string;
    industry_confidence?: number;
    business_entities?: string[];
    semantic?: {
      mappings?: Array<{
        column: string;
        entity: string;
        display: string;
        industry: string;
        confidence: number;
        method: string;
        role: string;
      }>;
    };
    profile?: {
      overall_quality_score?: number;
      row_count?: number;
      column_count?: number;
      null_percentage?: number;
      duplicate_percentage?: number;
    };
    recommendations?: string[];
    alerts?: Array<{ title: string; description: string; severity?: string }>;
  };
  kpis?: {
    industry?: string;
    kpis?: Array<{
      key: string;
      label: string;
      value: number;
      formatted: string;
      entity: string;
      category: string;
      icon?: string;
    }>;
  };
  dashboard?: {
    title?: string;
    subtitle?: string;
    industry?: string;
    kpi_cards?: Array<{ label: string; value: string; icon?: string; entity?: string; category?: string }>;
    widgets?: Array<{ key: string; type: string; title: string; entity?: string; metric?: string; available?: boolean }>;
    recommendations?: string[];
    ai_insights?: string[];
  } | null;
  governance?: {
    glossary?: Array<{ term: string; definition: string; entity?: string; industry?: string }>;
    data_dictionary?: Array<{
      column: string;
      business_name: string;
      entity: string;
      data_type: string;
      nullable: boolean;
      description: string;
      classification?: string;
      sensitivity?: string;
      pii?: boolean;
    }>;
    classifications?: Record<string, { classification?: string; sensitivity?: string; pii?: boolean }>;
  };
  needs_confirmation?: boolean;
  confirmation_reason?: string;
}

const INDUSTRIES = [
  { key: 'healthcare', label: 'Healthcare' },
  { key: 'education', label: 'Education' },
  { key: 'retail', label: 'Retail' },
  { key: 'banking', label: 'Banking' },
  { key: 'insurance', label: 'Insurance' },
  { key: 'government', label: 'Government' },
  { key: 'church', label: 'Church / Religious' },
  { key: 'ngo', label: 'NGO' },
  { key: 'manufacturing', label: 'Manufacturing' },
  { key: 'agriculture', label: 'Agriculture' },
  { key: 'hospitality', label: 'Hospitality' },
  { key: 'telecommunications', label: 'Telecommunications' },
];

export function DatasetUpload() {
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const [stage, setStage] = useState<UploadStage>('idle');
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [selectedIndustry, setSelectedIndustry] = useState<string>('');
  const [confirming, setConfirming] = useState(false);
  const [persisting, setPersisting] = useState(false);
  const [persistedId, setPersistedId] = useState<number | null>(null);
  const [persistedReportId, setPersistedReportId] = useState<number | null>(null);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      setFile(acceptedFiles[0]);
      setStage('idle');
      setError(null);
      setResult(null);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/csv': ['.csv'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/vnd.ms-excel': ['.xls'],
    },
    maxFiles: 1,
  });

  const handleUpload = async () => {
    if (!file) return;
    setStage('uploading');
    setError(null);
    try {
      // Step 1: Upload
      await datasetService.uploadFile(file);
      setStage('validating');

      // Step 2: Validate
      await datasetService.validateFile(file);
      setStage('analyzing');

      // Step 3: Semantic analysis
      const analysisResult = await datasetService.semanticAnalyze(file) as AnalysisResult;
      setResult(analysisResult);
      setStage('done');
      toast.success('Dataset uploaded and analyzed successfully!');
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Upload failed';
      setError(msg);
      setStage('error');
      toast.error(msg);
    }
  };

  const handleConfirmIndustry = async () => {
    if (!file || !selectedIndustry) return;
    setConfirming(true);
    try {
      const overrides: Record<string, string> = {};
      // Build overrides from existing mappings to preserve them
      const mappings = result?.mapping?.semantic?.mappings;
      if (mappings) {
        for (const m of mappings) {
          if (m.entity && m.entity !== 'date' && m.entity !== 'revenue') {
            overrides[m.column] = m.entity;
          }
        }
      }
      // Re-analyze with admin confirmation and forced industry
      const analysisResult = await datasetService.semanticAnalyzeWithOverrides(
        file,
        overrides,
        true,
        selectedIndustry,
      ) as AnalysisResult;
      setResult(analysisResult);
      toast.success('Industry confirmed! Dashboard generated.');
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to confirm industry');
    } finally {
      setConfirming(false);
    }
  };

  const handlePersist = async () => {
    if (!result || !file) return;
    setPersisting(true);
    try {
      const persistResult = await datasetService.persistAnalysis({
        table_name: file.name,
        industry: result.mapping?.industry,
        dashboard_config: result.dashboard ?? undefined,
        kpis: result.kpis?.kpis ?? undefined,
        recommendations: result.mapping?.recommendations,
        alerts: result.mapping?.alerts,
      });
      setPersistedId(persistResult.dashboard_id);
      setPersistedReportId(persistResult.report_id);
      toast.success('Results saved! Dashboard and report created.');    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to save results');
    } finally {
      setPersisting(false);
    }
  };

  const handleReset = () => {
    setFile(null);
    setStage('idle');
    setError(null);
    setResult(null);
    setSelectedIndustry('');
    setPersistedId(null);
    setPersistedReportId(null);
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Upload Dataset</CardTitle>
        <CardDescription>Upload a CSV or Excel file to analyze</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {!file && (
          <div
            {...getRootProps()}
            className={cn(
              'flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed p-12 transition-colors',
              isDragActive ? 'border-primary bg-primary/5' : 'border-muted-foreground/30 hover:border-primary/50',
            )}
          >
            <input {...getInputProps()} />
            <Upload className="mb-3 h-8 w-8 text-muted-foreground" />
            <p className="text-sm font-medium">
              {isDragActive ? 'Drop the file here' : 'Drag & drop or click to browse'}
            </p>
            <p className="mt-1 text-xs text-muted-foreground">Supports CSV, XLSX, XLS (max 50MB)</p>
          </div>
        )}

        {file && (
          <div className="space-y-4">
            {/* File info */}
            <div className="flex items-center justify-between rounded-lg border p-4">
              <div className="flex items-center gap-3">
                <FileIcon className="h-8 w-8 text-primary" />
                <div>
                  <p className="font-medium">{file.name}</p>
                  <p className="text-xs text-muted-foreground">
                    {(file.size / 1024).toFixed(1)} KB · {file.type || 'Unknown type'}
                  </p>
                </div>
              </div>
              {stage === 'done' && <CheckCircle className="h-6 w-6 text-green-500" />}
              {stage === 'error' && <XCircle className="h-6 w-6 text-destructive" />}
            </div>

            {/* Progress stages */}
            {stage !== 'idle' && stage !== 'error' && (
              <div className="space-y-2">
                {(['uploading', 'validating', 'analyzing', 'done'] as UploadStage[]).map((s) => {
                  const isCurrent = stage === s;
                  const isPast = ['uploading', 'validating', 'analyzing', 'done'].indexOf(stage) >
                    ['uploading', 'validating', 'analyzing', 'done'].indexOf(s);
                  return (
                    <div key={s} className="flex items-center gap-2">
                      {isCurrent ? (
                        <Loader2 className="h-4 w-4 animate-spin text-primary" />
                      ) : isPast ? (
                        <CheckCircle className="h-4 w-4 text-green-500" />
                      ) : (
                        <div className="h-4 w-4 rounded-full border" />
                      )}
                      <span className={cn('text-sm', isCurrent && 'font-medium', !isCurrent && !isPast && 'text-muted-foreground')}>
                        {s === 'uploading' && 'Uploading file...'}
                        {s === 'validating' && 'Validating data quality...'}
                        {s === 'analyzing' && 'Running semantic analysis...'}
                        {s === 'done' && 'Complete!'}
                      </span>
                    </div>
                  );
                })}
              </div>
            )}

            {error && (
              <Alert variant="destructive">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            {/* ─── Analysis Results ─── */}
            {stage === 'done' && result && (
              <div className="space-y-4">
                {/* Industry Detection */}
                <div className="flex items-center gap-3 rounded-lg border p-4">
                  <Database className="h-5 w-5 text-primary" />
                  <div className="flex-1">
                    <p className="text-sm font-medium">
                      Industry Detected:{' '}
                      <span className="font-bold">{result.mapping?.industry || 'Unknown'}</span>{' '}
                      <Badge variant={(result.mapping?.industry_confidence || 0) > 70 ? 'success' : (result.mapping?.industry_confidence || 0) > 0 ? 'warning' : 'secondary'}>
                        {(result.mapping?.industry_confidence || 0).toFixed(0)}% confidence
                      </Badge>
                    </p>
                    {result.mapping?.business_entities && result.mapping.business_entities.length > 0 && (
                      <p className="mt-1 text-xs text-muted-foreground">
                        Entities: {result.mapping.business_entities.join(', ')}
                      </p>
                    )}
                  </div>
                </div>

                {/* Needs Confirmation - Industry Selection */}
                {result.needs_confirmation && !result.dashboard && (
                  <Alert>
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription>
                      <p className="font-medium mb-2">{result.confirmation_reason || 'Industry confidence is low. Select the correct industry to generate a dashboard.'}</p>
                      <div className="mt-2 space-y-2">
                        <select
                          value={selectedIndustry}
                          onChange={(e) => setSelectedIndustry(e.target.value)}
                          className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                        >
                          <option value="">Select an industry...</option>
                          {INDUSTRIES.map((ind) => (
                            <option key={ind.key} value={ind.key}>{ind.label}</option>
                          ))}
                        </select>
                        <Button
                          size="sm"
                          onClick={handleConfirmIndustry}
                          disabled={!selectedIndustry || confirming}
                        >
                          {confirming ? (
                            <>
                              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                              Confirming...
                            </>
                          ) : (
                            'Confirm Industry & Generate Dashboard'
                          )}
                        </Button>
                      </div>
                    </AlertDescription>
                  </Alert>
                )}

                {/* Data Profile */}
                {result.mapping?.profile && (
                  <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                    <div className="rounded-lg border p-3">
                      <p className="text-xs text-muted-foreground">Rows</p>
                      <p className="text-lg font-bold">{formatNumber(result.mapping.profile.row_count)}</p>
                    </div>
                    <div className="rounded-lg border p-3">
                      <p className="text-xs text-muted-foreground">Columns</p>
                      <p className="text-lg font-bold">{formatNumber(result.mapping.profile.column_count)}</p>
                    </div>
                    <div className="rounded-lg border p-3">
                      <p className="text-xs text-muted-foreground">Quality Score</p>
                      <p className="text-lg font-bold">
                        {result.mapping.profile.overall_quality_score != null
                          ? `${result.mapping.profile.overall_quality_score.toFixed(1)}%`
                          : '—'}
                      </p>
                    </div>
                    <div className="rounded-lg border p-3">
                      <p className="text-xs text-muted-foreground">Null %</p>
                      <p className="text-lg font-bold">
                        {result.mapping.profile.null_percentage != null
                          ? `${result.mapping.profile.null_percentage.toFixed(1)}%`
                          : '—'}
                      </p>
                    </div>
                  </div>
                )}

                {/* KPIs */}
                {result.kpis?.kpis && result.kpis.kpis.length > 0 && (
                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      <BarChart3 className="h-4 w-4" />
                      <h3 className="text-sm font-semibold">Generated KPIs</h3>
                    </div>
                    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                      {result.kpis.kpis.map((kpi) => (
                        <div key={kpi.key} className="rounded-lg border p-3">
                          <p className="text-xs text-muted-foreground">{kpi.label}</p>
                          <p className="text-xl font-bold">{kpi.formatted}</p>
                          <Badge variant="secondary" className="mt-1 text-xs">{kpi.category}</Badge>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Dashboard */}
                {result.dashboard && (
                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      <Database className="h-4 w-4" />
                      <h3 className="text-sm font-semibold">Dashboard Configuration</h3>
                    </div>
                    <div className="rounded-lg border p-4 space-y-3">
                      <div>
                        <p className="font-medium">{result.dashboard.title}</p>
                        <p className="text-xs text-muted-foreground">{result.dashboard.subtitle}</p>
                      </div>
                      {result.dashboard.kpi_cards && result.dashboard.kpi_cards.length > 0 && (
                        <div className="grid gap-2 sm:grid-cols-3 lg:grid-cols-4">
                          {result.dashboard.kpi_cards.map((card, i) => (
                            <div key={i} className="rounded border p-2 text-center">
                              <p className="text-xs text-muted-foreground">{card.label}</p>
                              <p className="text-base font-bold">{card.value}</p>
                            </div>
                          ))}
                        </div>
                      )}
                      {result.dashboard.widgets && result.dashboard.widgets.length > 0 && (
                        <div>
                          <p className="text-xs font-medium text-muted-foreground mb-1">Widgets:</p>
                          <div className="flex flex-wrap gap-1">
                            {result.dashboard.widgets.map((w) => (
                              <Badge
                                key={w.key}
                                variant={w.available ? 'success' : 'secondary'}
                                className="text-xs"
                              >
                                {w.title}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      )}
                      {result.dashboard.ai_insights && result.dashboard.ai_insights.length > 0 && (
                        <div>
                          <p className="text-xs font-medium text-muted-foreground mb-1">Smart Insights:</p>
                          <ul className="text-xs text-muted-foreground list-disc pl-4 space-y-0.5">
                            {result.dashboard.ai_insights.map((insight, i) => (
                              <li key={i}>{insight}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Column Mappings */}
                {result.mapping?.semantic?.mappings && result.mapping.semantic.mappings.length > 0 && (
                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      <TableIcon className="h-4 w-4" />
                      <h3 className="text-sm font-semibold">Column Mappings</h3>
                    </div>
                    <div className="overflow-x-auto">
                      <table className="w-full text-xs">
                        <thead className="border-b bg-muted/50">
                          <tr>
                            <th className="p-2 text-left font-medium">Column</th>
                            <th className="p-2 text-left font-medium">Business Entity</th>
                            <th className="p-2 text-left font-medium">Industry</th>
                            <th className="p-2 text-left font-medium">Confidence</th>
                            <th className="p-2 text-left font-medium">Method</th>
                            <th className="p-2 text-left font-medium">Role</th>
                          </tr>
                        </thead>
                        <tbody>
                          {result.mapping.semantic.mappings.map((m, i) => (
                            <tr key={i} className="border-b">
                              <td className="p-2 font-medium">{m.column}</td>
                              <td className="p-2">{m.display}</td>
                              <td className="p-2">
                                <Badge variant="outline" className="text-xs">{m.industry}</Badge>
                              </td>
                              <td className="p-2">{(m.confidence * 100).toFixed(0)}%</td>
                              <td className="p-2 text-muted-foreground">{m.method}</td>
                              <td className="p-2 text-muted-foreground">{m.role}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {/* Data Dictionary */}
                {result.governance?.data_dictionary && result.governance.data_dictionary.length > 0 && (
                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      <Shield className="h-4 w-4" />
                      <h3 className="text-sm font-semibold">Data Dictionary & Governance</h3>
                    </div>
                    <div className="overflow-x-auto">
                      <table className="w-full text-xs">
                        <thead className="border-b bg-muted/50">
                          <tr>
                            <th className="p-2 text-left font-medium">Column</th>
                            <th className="p-2 text-left font-medium">Business Name</th>
                            <th className="p-2 text-left font-medium">Type</th>
                            <th className="p-2 text-left font-medium">Sensitivity</th>
                            <th className="p-2 text-left font-medium">PII</th>
                          </tr>
                        </thead>
                        <tbody>
                          {result.governance.data_dictionary.map((d, i) => (
                            <tr key={i} className="border-b">
                              <td className="p-2 font-medium">{d.column}</td>
                              <td className="p-2">{d.business_name}</td>
                              <td className="p-2 text-muted-foreground">{d.data_type}</td>
                              <td className="p-2">
                                <Badge variant={d.sensitivity === 'high' ? 'destructive' : d.sensitivity === 'medium' ? 'warning' : 'secondary'} className="text-xs">
                                  {d.sensitivity || '—'}
                                </Badge>
                              </td>
                              <td className="p-2">{d.pii ? '⚠️ Yes' : 'No'}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {/* Alerts */}
                {result.mapping?.alerts && result.mapping.alerts.length > 0 && (
                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      <AlertCircle className="h-4 w-4" />
                      <h3 className="text-sm font-semibold">Alerts</h3>
                    </div>
                    {result.mapping.alerts.map((alert, i) => (
                      <div key={i} className="rounded-lg border p-3">
                        <p className="text-sm font-medium">{alert.title}</p>
                        {alert.description && (
                          <p className="text-xs text-muted-foreground mt-0.5">{alert.description}</p>
                        )}
                      </div>
                    ))}
                  </div>
                )}

                {/* Recommendations */}
                {result.mapping?.recommendations && result.mapping.recommendations.length > 0 && (
                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      <Lightbulb className="h-4 w-4" />
                      <h3 className="text-sm font-semibold">Recommendations</h3>
                    </div>
                    <ul className="text-sm text-muted-foreground list-disc pl-4 space-y-1">
                      {result.mapping.recommendations.map((rec, i) => (
                        <li key={i}>{rec}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}

            <div className="flex flex-wrap gap-2">
              {stage === 'idle' || stage === 'error' ? (
                <Button onClick={handleUpload}>
                  <Upload className="mr-2 h-4 w-4" />
                  Upload & Analyze
                </Button>
              ) : null}
              {stage === 'done' && result && (
                <Button
                  onClick={handlePersist}
                  disabled={persisting || persistedId !== null}
                >
                  {persisting ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Saving...
                    </>
                  ) : persistedId !== null ? (
                    <>
                      <CheckCircle className="mr-2 h-4 w-4" />
                      Saved to Dashboard
                    </>
                  ) : (
                    <>
                      <Save className="mr-2 h-4 w-4" />
                      Save to Dashboard
                    </>
                  )}
                </Button>
              )}
              {persistedId !== null && (
                <Button
                  variant="outline"
                  onClick={() => router.push(`/analytics/${persistedId}`)}
                >
                  <LayoutDashboard className="mr-2 h-4 w-4" />
                  View Dashboard
                </Button>
              )}
              {persistedReportId !== null && (
                <Button
                  variant="outline"
                  onClick={() => router.push('/reports')}
                >
                  <FileText className="mr-2 h-4 w-4" />
                  View Report
                </Button>
              )}
              <Button variant="outline" onClick={handleReset}>
                {stage === 'done' ? 'Upload Another' : 'Cancel'}
              </Button>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
