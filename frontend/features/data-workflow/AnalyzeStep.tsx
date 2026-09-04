'use client';

import { useState } from 'react';
import { BarChart3, Brain, Calculator, TrendingUp, MessageSquare, Loader2, Sparkles, AlertCircle, ArrowUpDown } from 'lucide-react';
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
  const [activeProTool, setActiveProTool] = useState<'descriptive' | 'correlation' | 'outlier' | null>(null);
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
      const typeParam = testType === 'outlier' ? 'descriptive' : testType;
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
                    handleRunProTest('descriptive');
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
                Execute exact parametric tests and distributional metrics computed on server-side engine
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <Button
                  variant={activeProTool === 'descriptive' ? 'default' : 'outline'}
                  className="justify-start h-auto py-3 px-4 text-left"
                  onClick={() => handleRunProTest('descriptive')}
                  disabled={proLoading}
                >
                  <div>
                    <div className="font-semibold text-xs">Descriptive Statistics</div>
                    <div className="text-[10px] opacity-80 mt-0.5">Mean, std, median, IQR, skewness, kurtosis</div>
                  </div>
                </Button>

                <Button
                  variant={activeProTool === 'correlation' ? 'default' : 'outline'}
                  className="justify-start h-auto py-3 px-4 text-left"
                  onClick={() => handleRunProTest('correlation')}
                  disabled={proLoading}
                >
                  <div>
                    <div className="font-semibold text-xs">Pearson Correlation Matrix</div>
                    <div className="text-[10px] opacity-80 mt-0.5">Bivariate coefficients between numeric columns</div>
                  </div>
                </Button>

                <Button
                  variant={activeProTool === 'outlier' ? 'default' : 'outline'}
                  className="justify-start h-auto py-3 px-4 text-left"
                  onClick={() => handleRunProTest('outlier')}
                  disabled={proLoading}
                >
                  <div>
                    <div className="font-semibold text-xs">Outlier & Dispersion Bounds</div>
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

          {proError && (
            <Card className="border-red-200 dark:border-red-900 bg-red-50/50 dark:bg-red-950/20">
              <CardContent className="py-4 flex items-center gap-3 text-red-600 text-sm">
                <AlertCircle className="h-5 w-5 shrink-0" />
                <span>{proError}</span>
              </CardContent>
            </Card>
          )}

          {/* DESCRIPTIVE STATS TABLE */}
          {!proLoading && (activeProTool === 'descriptive' || activeProTool === 'outlier') && proResult?.results && (
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="text-base">
                      {activeProTool === 'outlier' ? 'Dispersion & Extreme Values' : 'Comprehensive Descriptive Statistics'}
                    </CardTitle>
                    <CardDescription>{proResult.interpretation || 'Parametric summary of attributes'}</CardDescription>
                  </div>
                  <Badge variant="outline" className="text-xs">
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
                        <th className="p-3 text-right">Count</th>
                        <th className="p-3 text-right">Mean</th>
                        <th className="p-3 text-right">Median</th>
                        <th className="p-3 text-right">Std Dev</th>
                        <th className="p-3 text-right">Min</th>
                        <th className="p-3 text-right">Max</th>
                        <th className="p-3 text-right">IQR</th>
                        <th className="p-3 text-right">Skewness</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border font-mono">
                      {Object.entries(proResult.results).map(([col, stats]) => (
                        <tr key={col} className="hover:bg-muted/30 transition-colors">
                          <td className="p-3 font-sans font-semibold text-foreground">{col}</td>
                          <td className="p-3 text-right">{stats.count}</td>
                          <td className="p-3 text-right">{stats.mean != null ? stats.mean.toFixed(2) : '—'}</td>
                          <td className="p-3 text-right">{stats.median != null ? stats.median.toFixed(2) : '—'}</td>
                          <td className="p-3 text-right">{stats.std != null ? stats.std.toFixed(2) : '—'}</td>
                          <td className="p-3 text-right">{stats.min != null ? stats.min.toFixed(2) : '—'}</td>
                          <td className="p-3 text-right">{stats.max != null ? stats.max.toFixed(2) : '—'}</td>
                          <td className="p-3 text-right">{stats.iqr != null ? stats.iqr.toFixed(2) : '—'}</td>
                          <td className="p-3 text-right">{stats.skewness != null ? stats.skewness.toFixed(2) : '—'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          )}

          {/* CORRELATION MATRIX */}
          {!proLoading && activeProTool === 'correlation' && proResult?.matrix && (
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="text-base">Pearson Correlation Matrix (r)</CardTitle>
                    <CardDescription>{proResult.interpretation || 'Bivariate relationships between numeric features'}</CardDescription>
                  </div>
                  <div className="flex items-center gap-3 text-xs">
                    <span className="flex items-center gap-1">
                      <span className="w-3 h-3 rounded bg-emerald-500/20 border border-emerald-500"></span> Positive (+1)
                    </span>
                    <span className="flex items-center gap-1">
                      <span className="w-3 h-3 rounded bg-rose-500/20 border border-rose-500"></span> Negative (-1)
                    </span>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="rounded-lg border overflow-x-auto">
                  <table className="w-full text-left text-xs border-collapse font-mono">
                    <thead className="bg-muted/50 border-b">
                      <tr>
                        <th className="p-2.5 font-sans font-semibold text-foreground">Variable</th>
                        {Object.keys(proResult.matrix).map((col) => (
                          <th key={col} className="p-2.5 text-center font-sans font-medium whitespace-nowrap">
                            {col}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border">
                      {Object.entries(proResult.matrix).map(([rowCol, rowVals]) => (
                        <tr key={rowCol}>
                          <td className="p-2.5 font-sans font-semibold text-foreground whitespace-nowrap bg-muted/20">
                            {rowCol}
                          </td>
                          {Object.entries(rowVals).map(([colKey, val]) => {
                            const num = typeof val === 'number' ? val : 0;
                            const isPositive = num > 0.3;
                            const isNegative = num < -0.3;
                            return (
                              <td
                                key={colKey}
                                className={`p-2.5 text-center font-semibold text-xs ${
                                  rowCol === colKey
                                    ? 'bg-muted/60 text-muted-foreground'
                                    : isPositive
                                      ? 'bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 font-bold'
                                      : isNegative
                                        ? 'bg-rose-500/10 text-rose-700 dark:text-rose-400 font-bold'
                                        : 'text-muted-foreground'
                                }`}
                              >
                                {num.toFixed(2)}
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

