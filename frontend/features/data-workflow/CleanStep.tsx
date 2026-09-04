'use client';

import { useState } from 'react';
import { Sparkles, Check, Undo2, AlertCircle, CheckCircle2, Eye, Table2, RefreshCw } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import type { QualityFinding, CleanPreviewData, CleaningTransformation } from '@/types/workflow';

interface TransformationRecord {
  id: string;
  timestamp: string;
  action: string;
  description: string;
  affected_rows: number;
  undone: boolean;
}

interface Props {
  findings: QualityFinding[];
  transformations: TransformationRecord[];
  onApplyFix: (finding: QualityFinding) => void;
  onUndoTransformation: (id: string) => void;
  onApplyAllSuggested: () => void;
  onContinue: () => void;
  isApplying: boolean;
  cleanPreview?: CleanPreviewData | null;
  onRefreshPreview?: () => Promise<void>;
}

export function CleanStep({
  findings,
  transformations,
  onApplyFix,
  onUndoTransformation,
  onApplyAllSuggested,
  onContinue,
  isApplying,
  cleanPreview,
  onRefreshPreview,
}: Props) {
  const [showHistory, setShowHistory] = useState(false);
  const [showPreview, setShowPreview] = useState(true);

  const fixableFindings = findings.filter((f) => f.suggested_fix);
  const criticalFindings = findings.filter((f) => f.severity === 'critical' || f.severity === 'error');
  const warningFindings = findings.filter((f) => f.severity === 'warning');

  const qualityScore = cleanPreview?.quality_score ?? 90;
  const activeTransformations = transformations.filter((t) => !t.undone);

  return (
    <div className="space-y-6">
      {/* Live Quality & Clean Hygiene Summary */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <p className="text-xs uppercase tracking-wider text-muted-foreground font-semibold">Post-Clean Score</p>
            <div className="flex items-baseline gap-2 mt-1">
              <p className="text-2xl font-bold text-emerald-600">{qualityScore.toFixed(0)}</p>
              <span className="text-sm text-muted-foreground">/100</span>
              <Badge className="bg-emerald-600 text-white text-[10px]">
                {qualityScore >= 90 ? 'Grade A' : qualityScore >= 75 ? 'Grade B' : 'Grade C'}
              </Badge>
            </div>
            <p className="text-xs text-muted-foreground mt-1">Recalculated in real-time</p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <p className="text-xs uppercase tracking-wider text-muted-foreground font-semibold">Active Transformations</p>
            <p className="text-2xl font-bold mt-1 text-primary">{activeTransformations.length}</p>
            <p className="text-xs text-muted-foreground mt-1">
              {transformations.filter((t) => t.undone).length} reverted
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <p className="text-xs uppercase tracking-wider text-muted-foreground font-semibold">Missing Values Left</p>
            <p className="text-2xl font-bold mt-1 text-amber-600">
              {cleanPreview?.total_missing != null ? cleanPreview.total_missing : '0'}
            </p>
            <p className="text-xs text-muted-foreground mt-1">Across all attributes</p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <p className="text-xs uppercase tracking-wider text-muted-foreground font-semibold">Duplicate Rows</p>
            <p className="text-2xl font-bold mt-1 text-indigo-600">
              {cleanPreview?.duplicate_rows != null ? cleanPreview.duplicate_rows : '0'}
            </p>
            <p className="text-xs text-muted-foreground mt-1">Exact duplicates</p>
          </CardContent>
        </Card>
      </div>

      {/* Action Header */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex items-center gap-4">
              <div className="rounded-full bg-primary/10 p-3">
                <Sparkles className="h-5 w-5 text-primary" />
              </div>
              <div>
                <p className="font-semibold text-base">Intelligent Cleaning & Hygiene</p>
                <p className="text-sm text-muted-foreground">
                  {fixableFindings.length} issues identified with automated remedies
                </p>
              </div>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <Button variant="outline" size="sm" onClick={() => setShowPreview(!showPreview)}>
                <Table2 className="mr-1 h-3.5 w-3.5" />
                {showPreview ? 'Hide Data Preview' : 'Show Data Preview'}
              </Button>
              <Button variant="outline" size="sm" onClick={() => setShowHistory(!showHistory)}>
                <Eye className="mr-1 h-3.5 w-3.5" />
                History ({transformations.length})
              </Button>
              {onRefreshPreview && (
                <Button variant="outline" size="sm" onClick={onRefreshPreview} disabled={isApplying}>
                  <RefreshCw className="h-3.5 w-3.5" />
                </Button>
              )}
              {fixableFindings.length > 0 && (
                <Button onClick={onApplyAllSuggested} disabled={isApplying} size="sm">
                  <Sparkles className="mr-1.5 h-3.5 w-3.5" />
                  Apply All Fixes ({fixableFindings.length})
                </Button>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* LIVE CLEANED DATA PREVIEW */}
      {showPreview && cleanPreview && cleanPreview.rows.length > 0 && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-base flex items-center gap-2">
                  <Table2 className="h-4 w-4 text-primary" />
                  Cleaned Dataset Live Preview (First {cleanPreview.rows.length} records)
                </CardTitle>
                <CardDescription>
                  Reflects all applied imputations, outlier caps, and deduplications
                </CardDescription>
              </div>
              <Badge variant="outline" className="text-xs">
                {cleanPreview.row_count} rows &bull; {cleanPreview.column_count} columns
              </Badge>
            </div>
          </CardHeader>
          <CardContent>
            <div className="rounded-lg border overflow-x-auto max-h-80">
              <table className="w-full text-left text-xs border-collapse">
                <thead className="bg-muted/60 border-b font-semibold text-foreground sticky top-0 z-10 backdrop-blur-sm">
                  <tr>
                    <th className="p-2.5 text-muted-foreground w-12 text-center">#</th>
                    {cleanPreview.columns.map((col) => (
                      <th key={col} className="p-2.5 whitespace-nowrap">
                        {col}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-border font-mono">
                  {cleanPreview.rows.map((row, idx) => (
                    <tr key={idx} className="hover:bg-muted/30 transition-colors">
                      <td className="p-2 text-center text-muted-foreground text-[11px]">{idx + 1}</td>
                      {cleanPreview.columns.map((col) => {
                        const val = row[col];
                        return (
                          <td key={col} className="p-2 whitespace-nowrap text-[11px]">
                            {val === null || val === undefined ? (
                              <span className="text-rose-400 italic">null</span>
                            ) : typeof val === 'number' ? (
                              val.toLocaleString(undefined, { maximumFractionDigits: 2 })
                            ) : (
                              String(val)
                            )}
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Transformation History & Undo */}
      {showHistory && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Audit Trail & Transformation Snapshots</CardTitle>
            <CardDescription>Every clean step is safely versioned and reversible</CardDescription>
          </CardHeader>
          <CardContent>
            {transformations.length > 0 ? (
              <div className="space-y-2">
                {transformations.map((t) => (
                  <div
                    key={t.id}
                    className={`flex items-center justify-between rounded-lg border p-3 ${
                      t.undone ? 'opacity-50 bg-muted/20' : 'bg-card'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      {t.undone ? (
                        <Undo2 className="h-4 w-4 text-muted-foreground" />
                      ) : (
                        <CheckCircle2 className="h-4 w-4 text-emerald-600" />
                      )}
                      <div>
                        <p className={`text-sm font-medium ${t.undone ? 'line-through text-muted-foreground' : ''}`}>
                          {t.description}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          {t.affected_rows} rows affected &bull; {new Date(t.timestamp).toLocaleTimeString()}
                        </p>
                      </div>
                    </div>
                    {!t.undone && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => onUndoTransformation(t.id)}
                        disabled={isApplying}
                      >
                        <Undo2 className="h-3.5 w-3.5 mr-1" />
                        Undo
                      </Button>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground text-center py-4">
                No transformations applied yet. Apply fixes below to build the audit log.
              </p>
            )}
          </CardContent>
        </Card>
      )}

      {/* Critical Issues */}
      {criticalFindings.length > 0 && (
        <Card className="border-red-200 dark:border-red-900">
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2 text-rose-700 dark:text-rose-400">
              <AlertCircle className="h-4 w-4" />
              Critical Issues ({criticalFindings.length})
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {criticalFindings.map((finding, i) => (
              <FindingCard key={i} finding={finding} onApplyFix={onApplyFix} isApplying={isApplying} />
            ))}
          </CardContent>
        </Card>
      )}

      {/* Warnings */}
      {warningFindings.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              Warnings ({warningFindings.length})
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {warningFindings.slice(0, 10).map((finding, i) => (
              <FindingCard key={i} finding={finding} onApplyFix={onApplyFix} isApplying={isApplying} />
            ))}
            {warningFindings.length > 10 && (
              <p className="text-xs text-muted-foreground text-center pt-2">
                +{warningFindings.length - 10} more warnings detected
              </p>
            )}
          </CardContent>
        </Card>
      )}

      {/* No Issues */}
      {findings.length === 0 && (
        <Card>
          <CardContent className="py-12 text-center">
            <CheckCircle2 className="h-10 w-10 text-green-600 mx-auto mb-3" />
            <p className="font-medium">No issues detected</p>
            <p className="text-sm text-muted-foreground mt-1">
              Your data looks clean. You can proceed to analysis.
            </p>
          </CardContent>
        </Card>
      )}

      <Button onClick={onContinue} size="lg" className="w-full">
        Continue to Advanced Analysis &rarr;
      </Button>
    </div>
  );
}

function FindingCard({
  finding,
  onApplyFix,
  isApplying,
}: {
  finding: QualityFinding;
  onApplyFix: (f: QualityFinding) => void;
  isApplying: boolean;
}) {
  return (
    <div className="rounded-lg border p-4 bg-card hover:border-primary/40 transition-colors">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <Badge
              variant={finding.severity === 'critical' ? 'destructive' : 'secondary'}
              className="text-xs capitalize"
            >
              {finding.severity}
            </Badge>
            {finding.column && (
              <Badge variant="outline" className="text-xs font-mono">
                {finding.column}
              </Badge>
            )}
            <span className="text-xs text-muted-foreground">
              {finding.affected_rows} rows affected ({finding.affected_pct.toFixed(1)}%)
            </span>
          </div>
          <p className="text-sm font-medium">{finding.message}</p>
          {finding.suggested_fix && (
            <p className="text-xs text-emerald-600 dark:text-emerald-400 font-medium mt-1">
              Suggested Fix: {finding.suggested_fix}
            </p>
          )}
          {finding.sample_values && finding.sample_values.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-2">
              {finding.sample_values.slice(0, 5).map((v, j) => (
                <Badge key={j} variant="outline" className="text-[10px] font-mono">
                  {String(v)}
                </Badge>
              ))}
            </div>
          )}
        </div>
        {finding.suggested_fix && (
          <Button
            variant="outline"
            size="sm"
            onClick={() => onApplyFix(finding)}
            disabled={isApplying}
            className="ml-3 flex-shrink-0"
          >
            <Check className="h-3.5 w-3.5 mr-1 text-emerald-600" />
            Apply Fix
          </Button>
        )}
      </div>
    </div>
  );
}
