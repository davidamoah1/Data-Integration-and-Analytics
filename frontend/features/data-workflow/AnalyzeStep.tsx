'use client';

import { useState } from 'react';
import {
  BarChart3,
  Brain,
  Calculator,
  TrendingUp,
  MessageSquare,
  Loader2,
  Sparkles,
  AlertCircle,
  ArrowUpDown,
  ShieldAlert,
  Info,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Input } from '@/components/ui/Input';
import { workflowService } from '@/services/workflow/workflowService';
import type { InsightsResult, Insight, ProAnalysisResult, DescriptiveStats } from '@/types/workflow';

type AnalysisMode = 'easy' | 'pro';

interface Props {
  workflowId?: string;
  insights: InsightsResult | null;
  industry: string;
  onAskQuestion: (question: string) => Promise<void>;
  onContinue: () => void;
}

interface QAItem {
  question: string;
  answer: string;
  timestamp: string;
}

export function AnalyzeStep({ workflowId, insights, industry, onAskQuestion, onContinue }: Props) {
  const [mode, setMode] = useState<AnalysisMode>('easy');
  const [question, setQuestion] = useState('');
  const [asking, setAsking] = useState(false);
  const [qaHistory, setQaHistory] = useState<QAItem[]>([]);

  // Pro mode state
  const [activeProTool, setActiveProTool] = useState<'descriptive' | 'correlation' | 'outlier'>('descriptive');
  const [proLoading, setProLoading] = useState(false);
  const [proResult, setProResult] = useState<ProAnalysisResult | null>(null);
  const [proError, setProError] = useState<string | null>(null);

  const handleAsk = async () => {
    if (!question.trim()) return;
    const currentQ = question.trim();
    setAsking(true);
    try {
      if (workflowId) {
        const res = await workflowService.runAnalysis(workflowId, {
          mode: 'easy',
          question: currentQ,
        });
        const answer = res?.data?.answer || res?.answer || `Analysis completed for: ${currentQ}`;
        setQaHistory((prev) => [
          { question: currentQ, answer, timestamp: new Date().toLocaleTimeString() },
          ...prev,
        ]);
      } else {
        await onAskQuestion(currentQ);
      }
      setQuestion('');
    } catch (e: any) {
      setQaHistory((prev) => [
        { question: currentQ, answer: e?.message || 'Failed to complete question analysis.', timestamp: new Date().toLocaleTimeString() },
        ...prev,
      ]);
    } finally {
      setAsking(false);
    }
  };

  const handleRunProTest = async (testType: 'descriptive' | 'correlation' | 'outlier') => {
    if (!workflowId) return;
    setActiveProTool(testType);
    setProLoading(true);
    setProError(null);
    try {
      const typeParam = testType === 'outlier' ? 'outlier' : testType;
      const res = await workflowService.runProAnalysis(workflowId, typeParam);
      setProResult(res);
    } catch (err: any) {
      setProError(err?.message || `Failed to run ${testType} analysis`);
    } finally {
      setProLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Mode Toggle */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="rounded-full bg-primary/10 p-2.5">
                <BarChart3 className="h-5 w-5 text-primary" />
              </div>
              <div>
                <p className="font-semibold text-base">Analytics Engine</p>
                <p className="text-xs text-muted-foreground">
                  {mode === 'easy'
                    ? 'Plain language natural intelligence with contextual question answering'
                    : 'Parametric and non-parametric statistical computing suite'}
                </p>
              </div>
            </div>
            <div className="flex rounded-lg border p-0.5 bg-muted/20">
              <button
                onClick={() => setMode('easy')}
                className={`px-4 py-1.5 text-xs font-semibold rounded-md transition-all ${
                  mode === 'easy'
                    ? 'bg-primary text-primary-foreground shadow-sm'
                    : 'text-muted-foreground hover:text-foreground'
                }`}
              >
                <MessageSquare className="inline-block mr-1.5 h-3.5 w-3.5" />
                Easy (Natural Q&A)
              </button>
              <button
                onClick={() => {
                  setMode('pro');
                  if (!proResult && !proLoading) {
                    handleRunProTest(activeProTool || 'descriptive');
                  }
                }}
                className={`px-4 py-1.5 text-xs font-semibold rounded-md transition-all ${
                  mode === 'pro'
                    ? 'bg-primary text-primary-foreground shadow-sm'
                    : 'text-muted-foreground hover:text-foreground'
                }`}
              >
                <Calculator className="inline-block mr-1.5 h-3.5 w-3.5" />
                Pro (Statistical Suite)
              </button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* EASY MODE: Natural Language Q&A */}
      {mode === 'easy' && (
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <Brain className="h-4 w-4 text-primary" />
                Ask Your Data in Natural Language
              </CardTitle>
              <CardDescription>
                Ask questions about averages, totals, outliers, or trends. The engine queries your live dataset.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex gap-2">
                <Input
                  placeholder="e.g., How many total records? What is the average value? Which product is top?"
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleAsk()}
                  className="flex-1"
                />
                <Button onClick={handleAsk} disabled={asking || !question.trim()}>
                  {asking ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Analyzing...
                    </>
                  ) : (
                    <>
                      <Sparkles className="mr-2 h-4 w-4" />
                      Ask Data
                    </>
                  )}
                </Button>
              </div>

              {/* Quick Prompts */}
              <div className="flex flex-wrap gap-2 pt-1">
                <span className="text-xs text-muted-foreground self-center font-medium mr-1">Suggested:</span>
                {getSuggestedQuestions(industry).map((q, i) => (
                  <button
                    key={i}
                    onClick={() => {
                      setQuestion(q);
                    }}
                    className="text-xs border rounded-full px-3 py-1 hover:bg-muted/80 hover:border-primary/40 transition-colors text-muted-foreground hover:text-foreground"
                  >
                    {q}
                  </button>
                ))}
              </div>

              {/* Interactive Conversation History */}
              {qaHistory.length > 0 && (
                <div className="space-y-3 pt-4 border-t">
                  <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    Recent Inquiries
                  </p>
                  {qaHistory.map((item, idx) => (
                    <div key={idx} className="rounded-lg border p-4 bg-muted/20 space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold text-primary flex items-center gap-1.5">
                          <MessageSquare className="h-3 w-3" /> Q: {item.question}
                        </span>
                        <span className="text-[10px] text-muted-foreground">{item.timestamp}</span>
                      </div>
                      <div className="text-xs text-foreground bg-card p-3 rounded border font-medium">
                        {item.answer}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Auto-Generated Insights */}
          {insights && insights.insights && insights.insights.length > 0 && (
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base flex items-center gap-2">
                    <TrendingUp className="h-4 w-4 text-primary" />
                    Automated Intelligence Findings ({insights.total_insights})
                  </CardTitle>
                  <Badge variant="outline" className="text-xs">
                    {industry ? `${industry.toUpperCase()} Sector` : 'General Analysis'}
                  </Badge>
                </div>
                {insights.executive_summary && (
                  <CardDescription>{insights.executive_summary}</CardDescription>
                )}
              </CardHeader>
              <CardContent className="space-y-3">
                {insights.insights.map((insight, i) => (
                  <InsightCard key={i} insight={insight} />
                ))}
              </CardContent>
            </Card>
          )}
        </div>
      )}

      {/* PRO MODE: Statistical Computing Suite */}
      {mode === 'pro' && (
        <div className="space-y-6">
          {/* Statistical Tool Selector */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <Calculator className="h-4 w-4 text-primary" />
                Select Statistical Method
              </CardTitle>
              <CardDescription>
                Execute exact parametric tests, bivariate dependency matrices, and dispersion boundaries on server-side engine
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <Button
                  variant={activeProTool === 'descriptive' ? 'default' : 'outline'}
                  className={`justify-start h-auto py-3 px-4 text-left transition-all ${
                    activeProTool === 'descriptive' ? 'ring-2 ring-primary/20 shadow-sm' : ''
                  }`}
                  onClick={() => handleRunProTest('descriptive')}
                  disabled={proLoading}
                >
                  <div>
                    <div className="font-semibold text-xs flex items-center gap-1.5">
                      <Calculator className="h-3.5 w-3.5" />
                      Descriptive Statistics
                    </div>
                    <div className="text-[10px] opacity-80 mt-0.5">Mean, std, median, IQR, skewness, kurtosis</div>
                  </div>
                </Button>

                <Button
                  variant={activeProTool === 'correlation' ? 'default' : 'outline'}
                  className={`justify-start h-auto py-3 px-4 text-left transition-all ${
                    activeProTool === 'correlation' ? 'ring-2 ring-primary/20 shadow-sm' : ''
                  }`}
                  onClick={() => handleRunProTest('correlation')}
                  disabled={proLoading}
                >
                  <div>
                    <div className="font-semibold text-xs flex items-center gap-1.5">
                      <ArrowUpDown className="h-3.5 w-3.5" />
                      Pearson Correlation Matrix
                    </div>
                    <div className="text-[10px] opacity-80 mt-0.5">Bivariate coefficients between numeric columns</div>
                  </div>
                </Button>

                <Button
                  variant={activeProTool === 'outlier' ? 'default' : 'outline'}
                  className={`justify-start h-auto py-3 px-4 text-left transition-all ${
                    activeProTool === 'outlier' ? 'ring-2 ring-primary/20 shadow-sm' : ''
                  }`}
                  onClick={() => handleRunProTest('outlier')}
                  disabled={proLoading}
                >
                  <div>
                    <div className="font-semibold text-xs flex items-center gap-1.5">
                      <AlertCircle className="h-3.5 w-3.5" />
                      Outlier & Dispersion Bounds
                    </div>
                    <div className="text-[10px] opacity-80 mt-0.5">IQR thresholds, min/max ranges & variances</div>
                  </div>
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Computation Status */}
          {proLoading && (
            <Card>
              <CardContent className="py-12 text-center text-muted-foreground flex flex-col items-center gap-2">
                <Loader2 className="h-6 w-6 animate-spin text-primary" />
                <span className="text-sm font-medium">Computing statistical properties on dataset...</span>
              </CardContent>
            </Card>
          )}

          {/* Error Banner with Retry */}
          {proError && (
            <Card className="border-red-200 dark:border-red-900 bg-red-50/50 dark:bg-red-950/20">
              <CardContent className="py-4 flex items-center justify-between gap-3 text-red-600 dark:text-red-400 text-sm">
                <div className="flex items-center gap-2">
                  <AlertCircle className="h-5 w-5 shrink-0" />
                  <span>{proError}</span>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleRunProTest(activeProTool)}
                  className="border-red-200 hover:bg-red-100 dark:border-red-800 text-xs shrink-0"
                >
                  Retry Analysis
                </Button>
              </CardContent>
            </Card>
          )}

          {/* 1. DESCRIPTIVE STATS TABLE */}
          {!proLoading && activeProTool === 'descriptive' && proResult?.results && (
            <div className="space-y-4">
              {/* Metric Overview Cards */}
              {(() => {
                const statsList = Object.entries(proResult.results);
                const numericVars = statsList.filter(([_, s]) => s.mean != null || s.min != null);
                const catVars = statsList.filter(([_, s]) => s.mean == null && s.min == null);

                return (
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                    <Card className="p-4 bg-muted/20 border-muted">
                      <p className="text-[11px] font-medium text-muted-foreground uppercase tracking-wider">Total Evaluated Columns</p>
                      <p className="text-xl font-bold mt-1">{statsList.length}</p>
                      <p className="text-[10px] text-muted-foreground mt-0.5">Attributes analyzed across dataset</p>
                    </Card>
                    <Card className="p-4 bg-muted/20 border-muted">
                      <p className="text-[11px] font-medium text-muted-foreground uppercase tracking-wider">Numeric Continuous</p>
                      <p className="text-xl font-bold mt-1 text-primary">{numericVars.length}</p>
                      <p className="text-[10px] text-muted-foreground mt-0.5">Parametric moments and quantiles computed</p>
                    </Card>
                    <Card className="p-4 bg-muted/20 border-muted">
                      <p className="text-[11px] font-medium text-muted-foreground uppercase tracking-wider">Categorical / Text</p>
                      <p className="text-xl font-bold mt-1 text-foreground">{catVars.length}</p>
                      <p className="text-[10px] text-muted-foreground mt-0.5">Distinct categories & modal distributions</p>
                    </Card>
                  </div>
                );
              })()}

              <Card>
                <CardHeader>
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                    <div>
                      <CardTitle className="text-base flex items-center gap-2">
                        <Calculator className="h-4 w-4 text-primary" />
                        Comprehensive Descriptive Statistics
                      </CardTitle>
                      <CardDescription>{proResult.interpretation || 'Summary of central tendency, dispersion, and distribution symmetry'}</CardDescription>
                    </div>
                    <Badge variant="outline" className="text-xs self-start sm:self-auto">
                      {Object.keys(proResult.results).length} columns evaluated
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="rounded-lg border overflow-x-auto">
                    <table className="w-full text-left text-xs border-collapse">
                      <thead className="bg-muted/50 border-b font-medium text-muted-foreground">
                        <tr>
                          <th className="p-3">Variable</th>
                          <th className="p-3 text-right">Count (N)</th>
                          <th className="p-3 text-right">Mean</th>
                          <th className="p-3 text-right">Median</th>
                          <th className="p-3 text-right">Std Dev</th>
                          <th className="p-3 text-right">Min</th>
                          <th className="p-3 text-right">Max</th>
                          <th className="p-3 text-right">IQR</th>
                          <th className="p-3 text-center">Skewness & Distribution</th>
                          <th className="p-3 text-right">Kurtosis</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-border font-mono">
                        {Object.entries(proResult.results).map(([col, stats]) => {
                          const isNumeric = stats.mean != null || stats.min != null;
                          const skew = stats.skewness;
                          const isRightSkew = skew != null && skew > 0.5;
                          const isLeftSkew = skew != null && skew < -0.5;

                          return (
                            <tr key={col} className="hover:bg-muted/30 transition-colors">
                              <td className="p-3 font-sans font-semibold text-foreground">
                                <div className="flex items-center gap-1.5">
                                  <span className="truncate max-w-[160px]" title={col}>{col}</span>
                                  {!isNumeric && (
                                    <span className="text-[10px] font-normal text-muted-foreground bg-muted px-1.5 py-0.5 rounded">Cat</span>
                                  )}
                                </div>
                              </td>
                              <td className="p-3 text-right">{stats.count?.toLocaleString()}</td>
                              <td className="p-3 text-right">{isNumeric && stats.mean != null ? stats.mean.toFixed(2) : '—'}</td>
                              <td className="p-3 text-right">{isNumeric && stats.median != null ? stats.median.toFixed(2) : '—'}</td>
                              <td className="p-3 text-right">{isNumeric && stats.std != null ? stats.std.toFixed(2) : '—'}</td>
                              <td className="p-3 text-right">{isNumeric && stats.min != null ? stats.min.toFixed(2) : '—'}</td>
                              <td className="p-3 text-right">{isNumeric && stats.max != null ? stats.max.toFixed(2) : '—'}</td>
                              <td className="p-3 text-right">{isNumeric && stats.iqr != null ? stats.iqr.toFixed(2) : '—'}</td>
                              <td className="p-3 text-center font-sans">
                                {!isNumeric || skew == null ? (
                                  <span className="text-muted-foreground text-[11px]">—</span>
                                ) : isRightSkew ? (
                                  <Badge variant="outline" className="bg-amber-500/10 text-amber-700 dark:text-amber-400 border-amber-300 dark:border-amber-800 text-[10px]">
                                    Right-skewed (+{skew.toFixed(2)})
                                  </Badge>
                                ) : isLeftSkew ? (
                                  <Badge variant="outline" className="bg-indigo-500/10 text-indigo-700 dark:text-indigo-400 border-indigo-300 dark:border-indigo-800 text-[10px]">
                                    Left-skewed ({skew.toFixed(2)})
                                  </Badge>
                                ) : (
                                  <Badge variant="outline" className="bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border-emerald-300 dark:border-emerald-800 text-[10px]">
                                    Symmetric ({skew.toFixed(2)})
                                  </Badge>
                                )}
                              </td>
                              <td className="p-3 text-right">
                                {isNumeric && stats.kurtosis != null ? stats.kurtosis.toFixed(2) : '—'}
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {/* 2. PEARSON CORRELATION MATRIX */}
          {!proLoading && activeProTool === 'correlation' && (proResult?.matrix || proResult?.correlation_matrix) && (
            <div className="space-y-4">
              <Card>
                <CardHeader>
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                    <div>
                      <CardTitle className="text-base flex items-center gap-2">
                        <ArrowUpDown className="h-4 w-4 text-primary" />
                        Pearson Correlation Matrix (r)
                      </CardTitle>
                      <CardDescription>
                        {proResult.interpretation || 'Bivariate relationships between numeric features (-1.00 to +1.00)'}
                      </CardDescription>
                    </div>
                    <div className="flex items-center gap-3 text-xs">
                      <span className="flex items-center gap-1.5">
                        <span className="w-3 h-3 rounded bg-emerald-500/30 border border-emerald-500"></span>
                        <span className="text-muted-foreground">Positive (+1.0)</span>
                      </span>
                      <span className="flex items-center gap-1.5">
                        <span className="w-3 h-3 rounded bg-muted/60 border border-border"></span>
                        <span className="text-muted-foreground">Neutral (0.0)</span>
                      </span>
                      <span className="flex items-center gap-1.5">
                        <span className="w-3 h-3 rounded bg-rose-500/30 border border-rose-500"></span>
                        <span className="text-muted-foreground">Negative (-1.0)</span>
                      </span>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  {(() => {
                    const matrix = (proResult.matrix || proResult.correlation_matrix) as Record<string, Record<string, number>>;
                    const cols = Object.keys(matrix);
                    if (cols.length === 0) {
                      return (
                        <div className="py-8 text-center text-sm text-muted-foreground">
                          At least 2 numeric columns with variance are required to compute a bivariate correlation matrix.
                        </div>
                      );
                    }
                    return (
                      <div className="rounded-lg border overflow-x-auto">
                        <table className="w-full text-left text-xs border-collapse font-mono">
                          <thead className="bg-muted/50 border-b">
                            <tr>
                              <th className="p-2.5 font-sans font-semibold text-foreground whitespace-nowrap">Variable</th>
                              {cols.map((col) => (
                                <th key={col} className="p-2.5 text-center font-sans font-medium whitespace-nowrap" title={col}>
                                  <span className="truncate max-w-[120px] inline-block">{col}</span>
                                </th>
                              ))}
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-border">
                            {cols.map((rowCol) => (
                              <tr key={rowCol}>
                                <td className="p-2.5 font-sans font-semibold text-foreground whitespace-nowrap bg-muted/20" title={rowCol}>
                                  <span className="truncate max-w-[140px] inline-block">{rowCol}</span>
                                </td>
                                {cols.map((colKey) => {
                                  const rawVal = matrix[rowCol]?.[colKey];
                                  const num = typeof rawVal === 'number' ? rawVal : null;
                                  const isDiag = rowCol === colKey;
                                  const isStrongPos = num != null && num >= 0.7 && !isDiag;
                                  const isModPos = num != null && num >= 0.3 && num < 0.7 && !isDiag;
                                  const isStrongNeg = num != null && num <= -0.7 && !isDiag;
                                  const isModNeg = num != null && num <= -0.3 && num > -0.7 && !isDiag;

                                  return (
                                    <td
                                      key={colKey}
                                      className={`p-2.5 text-center text-xs transition-colors ${
                                        isDiag
                                          ? 'bg-muted/60 text-muted-foreground font-medium'
                                          : isStrongPos
                                            ? 'bg-emerald-500/20 text-emerald-800 dark:text-emerald-300 font-bold'
                                            : isModPos
                                              ? 'bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 font-medium'
                                              : isStrongNeg
                                                ? 'bg-rose-500/20 text-rose-800 dark:text-rose-300 font-bold'
                                                : isModNeg
                                                  ? 'bg-rose-500/10 text-rose-700 dark:text-rose-400 font-medium'
                                                  : 'text-muted-foreground'
                                      }`}
                                    >
                                      {num != null ? num.toFixed(2) : '—'}
                                    </td>
                                  );
                                })}
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    );
                  })()}
                </CardContent>
              </Card>

              {/* Strongest Bivariate Correlations */}
              {proResult.strongest_correlations && proResult.strongest_correlations.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle className="text-sm font-semibold flex items-center gap-2">
                      <Sparkles className="h-4 w-4 text-primary" />
                      Strongest Observed Bivariate Relationships
                    </CardTitle>
                    <CardDescription>
                      Ranked pairs ordered by coefficient absolute magnitude (|r|)
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                      {proResult.strongest_correlations.map((pair, idx) => {
                        const isPos = pair.direction === 'positive';
                        const isStrong = pair.strength === 'strong';
                        return (
                          <div
                            key={idx}
                            className={`p-3 rounded-lg border flex flex-col justify-between gap-2 ${
                              isStrong
                                ? isPos
                                  ? 'border-emerald-300 bg-emerald-50/30 dark:border-emerald-900 dark:bg-emerald-950/20'
                                  : 'border-rose-300 bg-rose-50/30 dark:border-rose-900 dark:bg-rose-950/20'
                                : 'bg-card border-border'
                            }`}
                          >
                            <div className="flex items-center justify-between gap-2">
                              <span className="text-xs font-semibold truncate" title={`${pair.var1} ↔ ${pair.var2}`}>
                                {pair.var1} <span className="text-muted-foreground">↔</span> {pair.var2}
                              </span>
                              <Badge
                                className={`text-[10px] font-mono shrink-0 ${
                                  isPos
                                    ? 'bg-emerald-500/15 text-emerald-700 dark:text-emerald-400 border-emerald-300'
                                    : 'bg-rose-500/15 text-rose-700 dark:text-rose-400 border-rose-300'
                                }`}
                              >
                                r = {pair.correlation > 0 ? `+${pair.correlation.toFixed(2)}` : pair.correlation.toFixed(2)}
                              </Badge>
                            </div>
                            <div className="flex items-center justify-between text-[11px] text-muted-foreground">
                              <span className="capitalize">{pair.strength} {pair.direction}</span>
                              <span className="text-[10px]">
                                {isStrong ? 'High collinearity risk' : 'Moderate association'}
                              </span>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Statistical Assumptions Note */}
              <div className="p-3.5 rounded-lg border bg-muted/15 text-xs text-muted-foreground flex items-start gap-2.5">
                <Info className="h-4 w-4 text-primary shrink-0 mt-0.5" />
                <div>
                  <span className="font-semibold text-foreground">Statistical Assumptions & Limitations: </span>
                  Pearson's r measures linear dependence between continuous variables. It is sensitive to extreme outliers and does not establish causation. Non-linear relationships (e.g. polynomial, logarithmic) may exhibit low Pearson r despite strong functional connection.
                </div>
              </div>
            </div>
          )}

          {/* 3. OUTLIER & DISPERSION BOUNDS */}
          {!proLoading && activeProTool === 'outlier' && proResult?.results && (
            <div className="space-y-4">
              {/* KPI Summary Cards */}
              {(() => {
                const statsList = Object.entries(proResult.results);
                const numericStats = statsList.filter(([_, s]) => s.mean != null || s.min != null);
                const outlierVars = numericStats.filter(([_, s]) => (s.outlier_count || 0) > 0);
                const totalOutliers = numericStats.reduce((sum, [_, s]) => sum + (s.outlier_count || 0), 0);

                return (
                  <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
                    <Card className="p-4 bg-muted/20 border-muted">
                      <p className="text-[11px] font-medium text-muted-foreground uppercase tracking-wider">Analyzed Variables</p>
                      <p className="text-xl font-bold mt-1">{numericStats.length}</p>
                      <p className="text-[10px] text-muted-foreground mt-0.5">Continuous numeric features</p>
                    </Card>
                    <Card className="p-4 bg-muted/20 border-muted">
                      <p className="text-[11px] font-medium text-muted-foreground uppercase tracking-wider">Features With Outliers</p>
                      <p className="text-xl font-bold mt-1 text-amber-600 dark:text-amber-400">
                        {outlierVars.length} <span className="text-xs font-normal text-muted-foreground">/ {numericStats.length}</span>
                      </p>
                      <p className="text-[10px] text-muted-foreground mt-0.5">Exceeding Tukey's fences</p>
                    </Card>
                    <Card className="p-4 bg-muted/20 border-muted">
                      <p className="text-[11px] font-medium text-muted-foreground uppercase tracking-wider">Total Outlier Points</p>
                      <p className={`text-xl font-bold mt-1 ${totalOutliers > 0 ? 'text-rose-600 dark:text-rose-400' : 'text-emerald-600 dark:text-emerald-400'}`}>
                        {totalOutliers}
                      </p>
                      <p className="text-[10px] text-muted-foreground mt-0.5">Flagged data points</p>
                    </Card>
                    <Card className="p-4 bg-muted/20 border-muted">
                      <p className="text-[11px] font-medium text-muted-foreground uppercase tracking-wider">Fence Formulation</p>
                      <p className="text-sm font-semibold mt-1.5 text-foreground font-mono">Q1/Q3 ± 1.5 × IQR</p>
                      <p className="text-[10px] text-muted-foreground mt-0.5">Standard non-parametric bounds</p>
                    </Card>
                  </div>
                );
              })()}

              <Card>
                <CardHeader>
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                    <div>
                      <CardTitle className="text-base flex items-center gap-2">
                        <ShieldAlert className="h-4 w-4 text-primary" />
                        Outlier & Dispersion Boundaries
                      </CardTitle>
                      <CardDescription>
                        {proResult.interpretation || "Evaluates dispersion metrics, interquartile fences, and extreme anomalous points."}
                      </CardDescription>
                    </div>
                    <Badge variant="outline" className="text-xs self-start sm:self-auto">
                      {Object.keys(proResult.results).length} features evaluated
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="rounded-lg border overflow-x-auto">
                    <table className="w-full text-left text-xs border-collapse">
                      <thead className="bg-muted/50 border-b font-medium text-muted-foreground">
                        <tr>
                          <th className="p-3">Variable</th>
                          <th className="p-3 text-right">Count (N)</th>
                          <th className="p-3 text-right">Std Dev / Variance</th>
                          <th className="p-3 text-right">Range [Min, Max]</th>
                          <th className="p-3 text-right">IQR (Q1 – Q3)</th>
                          <th className="p-3 text-right text-rose-600 dark:text-rose-400">Lower Fence</th>
                          <th className="p-3 text-right text-rose-600 dark:text-rose-400">Upper Fence</th>
                          <th className="p-3 text-center">Outliers Flagged</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-border font-mono">
                        {Object.entries(proResult.results).map(([col, stats]) => {
                          const isNumeric = stats.mean != null || stats.min != null;
                          const hasOutliers = (stats.outlier_count || 0) > 0;
                          return (
                            <tr key={col} className={`hover:bg-muted/30 transition-colors ${hasOutliers ? 'bg-rose-50/20 dark:bg-rose-950/10' : ''}`}>
                              <td className="p-3 font-sans font-semibold text-foreground">
                                <div className="flex items-center gap-1.5">
                                  <span className="truncate max-w-[160px]" title={col}>{col}</span>
                                  {!isNumeric && (
                                    <span className="text-[10px] font-normal text-muted-foreground bg-muted px-1.5 py-0.5 rounded">Cat</span>
                                  )}
                                </div>
                              </td>
                              <td className="p-3 text-right">{stats.count?.toLocaleString()}</td>
                              <td className="p-3 text-right">
                                {isNumeric && stats.std != null ? (
                                  <span>
                                    {stats.std.toFixed(2)}{' '}
                                    <span className="text-[10px] text-muted-foreground">
                                      (v: {stats.variance != null ? stats.variance.toFixed(1) : '—'})
                                    </span>
                                  </span>
                                ) : (
                                  '—'
                                )}
                              </td>
                              <td className="p-3 text-right">
                                {isNumeric && stats.min != null && stats.max != null
                                  ? `[${stats.min.toFixed(1)}, ${stats.max.toFixed(1)}]`
                                  : '—'}
                              </td>
                              <td className="p-3 text-right">
                                {isNumeric && stats.iqr != null ? (
                                  <span>
                                    {stats.iqr.toFixed(2)}{' '}
                                    <span className="text-[10px] text-muted-foreground">
                                      ({stats.q1?.toFixed(1)}–{stats.q3?.toFixed(1)})
                                    </span>
                                  </span>
                                ) : (
                                  '—'
                                )}
                              </td>
                              <td className="p-3 text-right font-semibold text-amber-700 dark:text-amber-400">
                                {isNumeric && stats.lower_bound != null ? stats.lower_bound.toFixed(2) : '—'}
                              </td>
                              <td className="p-3 text-right font-semibold text-amber-700 dark:text-amber-400">
                                {isNumeric && stats.upper_bound != null ? stats.upper_bound.toFixed(2) : '—'}
                              </td>
                              <td className="p-3 text-center">
                                {!isNumeric ? (
                                  <span className="text-muted-foreground font-sans text-[11px]">—</span>
                                ) : hasOutliers ? (
                                  <Badge className="bg-rose-500/15 text-rose-700 dark:text-rose-400 border border-rose-300 dark:border-rose-800 text-[11px] font-sans font-semibold">
                                    {stats.outlier_count} ({stats.outlier_pct}%)
                                  </Badge>
                                ) : (
                                  <Badge variant="outline" className="bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border-emerald-200 dark:border-emerald-800 text-[11px] font-sans font-medium">
                                    0 (0.0%)
                                  </Badge>
                                )}
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}
        </div>
      )}

      <Button onClick={onContinue} size="lg" className="w-full">
        Continue to Visualize Data &rarr;
      </Button>
    </div>
  );
}

function InsightCard({ insight }: { insight: Insight }) {
  const typeColors: Record<string, string> = {
    trend: 'bg-blue-100 text-blue-800 dark:bg-blue-900/60 dark:text-blue-300 border-blue-200',
    anomaly: 'bg-rose-100 text-rose-800 dark:bg-rose-900/60 dark:text-rose-300 border-rose-200',
    correlation: 'bg-purple-100 text-purple-800 dark:bg-purple-900/60 dark:text-purple-300 border-purple-200',
    dominance: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/60 dark:text-emerald-300 border-emerald-200',
    distribution: 'bg-amber-100 text-amber-800 dark:bg-amber-900/60 dark:text-amber-300 border-amber-200',
  };

  return (
    <div className="rounded-lg border p-4 bg-card hover:border-primary/40 transition-colors">
      <div className="flex items-start gap-3">
        <Badge className={`${typeColors[insight.type] || 'bg-muted text-foreground'} uppercase text-[10px]`}>
          {insight.type}
        </Badge>
        <div className="flex-1">
          <p className="text-sm font-semibold">{insight.title}</p>
          <p className="text-xs text-muted-foreground mt-1 leading-relaxed">{insight.description}</p>
          {insight.recommendation && (
            <p className="text-xs text-primary font-medium mt-1.5 flex items-center gap-1.5">
              <span className="font-bold">&rarr;</span> {insight.recommendation}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

function getSuggestedQuestions(industry: string): string[] {
  const general = [
    'How many total records are there?',
    'What are the key averages across numeric fields?',
    'What are the highest values observed?',
    'Are there any missing values left?',
  ];

  const sectorQuestions: Record<string, string[]> = {
    healthcare: [
      'What are the patient volume trends?',
      'Which diagnoses or metrics are highest?',
      'How many total records are there?',
    ],
    finance: [
      'What are the average revenue numbers?',
      'What are the highest transaction amounts?',
      'Show key numeric averages',
    ],
    retail: [
      'What are the top sales averages?',
      'What is the highest unit price?',
      'How many total records are in the catalog?',
    ],
  };

  return sectorQuestions[industry.toLowerCase()] || general;
}

