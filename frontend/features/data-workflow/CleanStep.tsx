'use client';

import { useState } from 'react';
import { Sparkles, Check, Undo2, AlertCircle, CheckCircle2, Eye } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import type { QualityFinding } from '@/types/workflow';

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
}

export function CleanStep({
  findings,
  transformations,
  onApplyFix,
  onUndoTransformation,
  onApplyAllSuggested,
  onContinue,
  isApplying,
}: Props) {
  const [showHistory, setShowHistory] = useState(false);

  const fixableFindings = findings.filter((f) => f.suggested_fix);
  const criticalFindings = findings.filter((f) => f.severity === 'critical' || f.severity === 'error');
  const warningFindings = findings.filter((f) => f.severity === 'warning');

  return (
    <div className="space-y-6">
      {/* Summary Bar */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="rounded-full bg-primary/10 p-3">
                <Sparkles className="h-5 w-5 text-primary" />
              </div>
              <div>
                <p className="font-medium">Smart Cleaning</p>
                <p className="text-sm text-muted-foreground">
                  {fixableFindings.length} issues can be automatically fixed
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Button variant="outline" size="sm" onClick={() => setShowHistory(!showHistory)}>
                <Eye className="mr-1 h-3 w-3" />
                {showHistory ? 'Hide' : 'Show'} History ({transformations.length})
              </Button>
              {fixableFindings.length > 0 && (
                <Button onClick={onApplyAllSuggested} disabled={isApplying} size="sm">
                  <Sparkles className="mr-1 h-3 w-3" />
                  Apply All Suggested Fixes
                </Button>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Transformation History */}
      {showHistory && transformations.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Transformation History</CardTitle>
            <CardDescription>Every change is tracked and can be undone</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {transformations.map((t) => (
                <div
                  key={t.id}
                  className={`flex items-center justify-between rounded-lg border p-3 ${t.undone ? 'opacity-50' : ''}`}
                >
                  <div className="flex items-center gap-3">
                    {t.undone ? (
                      <Undo2 className="h-4 w-4 text-muted-foreground" />
                    ) : (
                      <CheckCircle2 className="h-4 w-4 text-green-600" />
                    )}
                    <div>
                      <p className="text-sm font-medium">{t.description}</p>
                      <p className="text-xs text-muted-foreground">
                        {t.affected_rows} rows affected - {new Date(t.timestamp).toLocaleTimeString()}
                      </p>
                    </div>
                  </div>
                  {!t.undone && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => onUndoTransformation(t.id)}
                    >
                      <Undo2 className="h-3 w-3 mr-1" />
                      Undo
                    </Button>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Critical Issues */}
      {criticalFindings.length > 0 && (
        <Card className="border-red-200 dark:border-red-900">
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2 text-red-700 dark:text-red-400">
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
              <p className="text-sm text-muted-foreground">
                + {warningFindings.length - 10} more warnings
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
        Continue to Analyze
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
    <div className="rounded-lg border p-4">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <Badge
              variant={finding.severity === 'critical' ? 'destructive' : 'secondary'}
              className="text-xs"
            >
              {finding.severity}
            </Badge>
            {finding.column && (
              <Badge variant="outline" className="text-xs">
                {finding.column}
              </Badge>
            )}
            <span className="text-xs text-muted-foreground">
              {finding.affected_rows} rows ({finding.affected_pct.toFixed(1)}%)
            </span>
          </div>
          <p className="text-sm">{finding.message}</p>
          {finding.suggested_fix && (
            <p className="text-sm text-green-700 dark:text-green-400 mt-1">
              Suggested: {finding.suggested_fix}
            </p>
          )}
          {finding.sample_values.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-2">
              {finding.sample_values.slice(0, 5).map((v, j) => (
                <Badge key={j} variant="outline" className="text-xs font-mono">
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
            <Check className="h-3 w-3 mr-1" />
            Fix
          </Button>
        )}
      </div>
    </div>
  );
}
