'use client';

import { useState, useRef, useEffect, useCallback } from 'react';
import {
  Send, Bot, User as UserIcon, Sparkles, Loader2,
  TrendingUp, AlertTriangle, FileText, Lightbulb,
  BarChart3, FileBarChart, Brain, ChevronRight,
  ArrowUp, ArrowDown, Minus, Download, RefreshCw,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { cn } from '@/lib/utils';
import { aiService } from '@/services/ai/aiService';
import type {
  ChatMessage, ExecutiveSummary, RootCauseAnalysis, ForecastResult,
  AnomalyResult, RecommendationResult, NLAnalyticsResult, ReportResult,
} from '@/types';

type TabId = 'chat' | 'summary' | 'rootcause' | 'forecast' | 'anomaly' | 'recommendations' | 'analytics' | 'report';

interface Tab {
  id: TabId;
  label: string;
  icon: typeof Bot;
}

const TABS: Tab[] = [
  { id: 'chat', label: 'Chat', icon: Bot },
  { id: 'summary', label: 'Exec Summary', icon: FileBarChart },
  { id: 'rootcause', label: 'Root Cause', icon: Brain },
  { id: 'forecast', label: 'Forecast', icon: TrendingUp },
  { id: 'anomaly', label: 'Anomalies', icon: AlertTriangle },
  { id: 'recommendations', label: 'Recommend', icon: Lightbulb },
  { id: 'analytics', label: 'NL Analytics', icon: BarChart3 },
  { id: 'report', label: 'Report', icon: FileText },
];

const SUGGESTED_QUESTIONS = [
  'Give me a summary of this data',
  'What are the top 5 items?',
  'Are there any anomalies?',
  "What's the trend over time?",
];

export default function AICopilotPage() {
  const [activeTab, setActiveTab] = useState<TabId>('chat');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [conversationId, setConversationId] = useState<number | null>(null);
  const [datasetId] = useState<string | undefined>(undefined);
  const [industry, setIndustry] = useState<string>('unknown');
  const scrollRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSend = useCallback(async (text?: string) => {
    const message = text || input.trim();
    if (!message || loading) return;

    const userMsg: ChatMessage = {
      id: crypto.randomUUID(),
      role: 'user',
      content: message,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const res = await aiService.chat({
        message,
        conversation_id: conversationId || undefined,
      });
      setConversationId(res.conversation_id);
      const aiMsg: ChatMessage = {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: res.response,
        citations: res.citations,
        confidence: res.confidence_score,
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, aiMsg]);
    } catch (err) {
      const errMsg: ChatMessage = {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: `Sorry, I encountered an error: ${err instanceof Error ? err.message : 'Unknown error'}`,
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errMsg]);
    } finally {
      setLoading(false);
    }
  }, [input, loading, conversationId]);

  return (
    <div className="flex h-[calc(100vh-8rem)] flex-col space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Enterprise AI Copilot</h1>
        <div className="flex items-center gap-2">
          <select
            value={industry}
            onChange={(e) => setIndustry(e.target.value)}
            className="h-8 rounded-md border border-input bg-background px-2 text-xs"
          >
            <option value="unknown">Auto-detect</option>
            <option value="retail">Retail</option>
            <option value="healthcare">Healthcare</option>
            <option value="education">Education</option>
            <option value="government">Government</option>
            <option value="finance">Finance</option>
            <option value="manufacturing">Manufacturing</option>
            <option value="logistics">Logistics</option>
          </select>
          {messages.length > 0 && activeTab === 'chat' && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => { setMessages([]); setConversationId(null); }}
            >
              Clear Chat
            </Button>
          )}
        </div>
      </div>

      {/* Tab Bar */}
      <div className="flex flex-wrap gap-1 border-b pb-1">
        {TABS.map((tab) => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={cn(
                'flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium transition-colors',
                activeTab === tab.id
                  ? 'bg-primary text-primary-foreground'
                  : 'text-muted-foreground hover:bg-accent hover:text-foreground',
              )}
            >
              <Icon className="h-4 w-4" />
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Tab Content */}
      <div className="flex-1 overflow-hidden">
        {activeTab === 'chat' && (
          <ChatTab
            messages={messages}
            input={input}
            setInput={setInput}
            loading={loading}
            onSend={handleSend}
            scrollRef={scrollRef}
          />
        )}
        {activeTab === 'summary' && (
          <ExecutiveSummaryTab datasetId={datasetId} industry={industry} />
        )}
        {activeTab === 'rootcause' && (
          <RootCauseTab datasetId={datasetId} industry={industry} />
        )}
        {activeTab === 'forecast' && (
          <ForecastTab datasetId={datasetId} industry={industry} />
        )}
        {activeTab === 'anomaly' && (
          <AnomalyTab datasetId={datasetId} industry={industry} />
        )}
        {activeTab === 'recommendations' && (
          <RecommendationsTab datasetId={datasetId} industry={industry} />
        )}
        {activeTab === 'analytics' && (
          <NLAnalyticsTab datasetId={datasetId} industry={industry} />
        )}
        {activeTab === 'report' && (
          <ReportTab datasetId={datasetId} industry={industry} />
        )}
      </div>
    </div>
  );
}

// ── Chat Tab ───────────────────────────────────────────

function ChatTab({
  messages, input, setInput, loading, onSend, scrollRef,
}: {
  messages: ChatMessage[];
  input: string;
  setInput: (v: string) => void;
  loading: boolean;
  onSend: (text?: string) => void;
  scrollRef: React.MutableRefObject<HTMLDivElement | null>;
}) {
  return (
    <Card className="flex h-full flex-col overflow-hidden">
      <div ref={scrollRef} className="flex-1 overflow-y-auto scrollbar-thin p-6 space-y-4">
        {messages.length === 0 ? (
          <div className="flex h-full flex-col items-center justify-center text-center">
            <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-primary/10">
              <Bot className="h-8 w-8 text-primary" />
            </div>
            <h2 className="text-lg font-semibold">AI Data Analyst</h2>
            <p className="mt-1 text-sm text-muted-foreground max-w-md">
              Ask questions about your data in natural language. I can analyze trends,
              find anomalies, and generate insights.
            </p>
            <div className="mt-6 grid gap-2 sm:grid-cols-2">
              {SUGGESTED_QUESTIONS.map((q) => (
                <button
                  key={q}
                  onClick={() => onSend(q)}
                  className="flex items-center gap-2 rounded-lg border p-3 text-left text-sm hover:bg-accent"
                >
                  <Sparkles className="h-4 w-4 text-primary" />
                  {q}
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((msg) => (
            <div
              key={msg.id}
              className={cn('flex gap-3', msg.role === 'user' ? 'justify-end' : 'justify-start')}
            >
              {msg.role === 'assistant' && (
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary/10">
                  <Bot className="h-5 w-5 text-primary" />
                </div>
              )}
              <div
                className={cn(
                  'max-w-[70%] rounded-lg p-3',
                  msg.role === 'user' ? 'bg-primary text-primary-foreground' : 'bg-muted',
                )}
              >
                <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                {msg.citations && msg.citations.length > 0 && (
                  <div className="mt-2 border-t border-border/50 pt-2">
                    <p className="text-xs font-medium text-muted-foreground">Sources:</p>
                    <ul className="mt-1 space-y-1">
                      {msg.citations.map((cite, i) => (
                        <li key={i} className="text-xs text-muted-foreground">- {cite}</li>
                      ))}
                    </ul>
                  </div>
                )}
                {msg.confidence != null && (
                  <p className="mt-1 text-xs text-muted-foreground">
                    Confidence: {Math.round(msg.confidence * 100)}%
                  </p>
                )}
              </div>
              {msg.role === 'user' && (
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-secondary">
                  <UserIcon className="h-5 w-5" />
                </div>
              )}
            </div>
          ))
        )}
        {loading && (
          <div className="flex gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/10">
              <Bot className="h-5 w-5 text-primary" />
            </div>
            <div className="flex items-center gap-2 rounded-lg bg-muted p-3">
              <Loader2 className="h-4 w-4 animate-spin" />
              <span className="text-sm text-muted-foreground">Thinking...</span>
            </div>
          </div>
        )}
      </div>

      <div className="border-t p-4">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && onSend()}
            placeholder="Ask the AI Copilot..."
            className="flex h-10 flex-1 rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            disabled={loading}
          />
          <Button onClick={() => onSend()} disabled={loading || !input.trim()}>
            <Send className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </Card>
  );
}

// ── Executive Summary Tab ──────────────────────────────

function ExecutiveSummaryTab({ datasetId, industry }: { datasetId?: string; industry: string }) {
  const [data, setData] = useState<ExecutiveSummary | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const generate = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await aiService.generateExecutiveSummary({ dataset_id: datasetId, industry });
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate summary');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className="h-full overflow-y-auto scrollbar-thin">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Executive Summary</CardTitle>
          <Button size="sm" onClick={generate} disabled={loading}>
            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
            Generate
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {error && <p className="text-sm text-destructive">{error}</p>}
        {!data && !loading && !error && (
          <p className="text-sm text-muted-foreground">Click Generate to create an executive summary.</p>
        )}
        {data && (
          <>
            <div>
              <h3 className="font-semibold">{data.title}</h3>
              <p className="mt-1 text-sm text-muted-foreground">{data.executive_summary}</p>
            </div>

            {data.kpi_highlights?.length > 0 && (
              <div>
                <h4 className="mb-2 text-sm font-semibold">KPI Highlights</h4>
                <div className="grid gap-2 sm:grid-cols-2">
                  {data.kpi_highlights.map((kpi, i) => (
                    <div key={i} className="rounded-lg border p-3">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium">{kpi.metric}</span>
                        {kpi.direction === 'up' && <ArrowUp className="h-4 w-4 text-green-500" />}
                        {kpi.direction === 'down' && <ArrowDown className="h-4 w-4 text-red-500" />}
                        {kpi.direction === 'stable' && <Minus className="h-4 w-4 text-muted-foreground" />}
                      </div>
                      <p className="mt-1 text-lg font-bold">{kpi.value}</p>
                      <p className="text-xs text-muted-foreground">{kpi.change}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {data.main_drivers?.length > 0 && (
              <div>
                <h4 className="mb-2 text-sm font-semibold">Main Drivers</h4>
                <ul className="space-y-1">
                  {data.main_drivers.map((d, i) => (
                    <li key={i} className="text-sm text-muted-foreground">- {d}</li>
                  ))}
                </ul>
              </div>
            )}

            {data.risks?.length > 0 && (
              <div>
                <h4 className="mb-2 text-sm font-semibold">Risks</h4>
                <div className="space-y-2">
                  {data.risks.map((r, i) => (
                    <div key={i} className="rounded-lg border p-3">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium">{r.risk}</span>
                        <Badge variant={r.severity === 'high' ? 'destructive' : 'secondary'}>
                          {r.severity}
                        </Badge>
                      </div>
                      {r.evidence && <p className="mt-1 text-xs text-muted-foreground">{r.evidence}</p>}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {data.recommended_actions?.length > 0 && (
              <div>
                <h4 className="mb-2 text-sm font-semibold">Recommended Actions</h4>
                <div className="space-y-2">
                  {data.recommended_actions.map((a, i) => (
                    <div key={i} className="rounded-lg border p-3">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium">{a.action}</span>
                        <div className="flex gap-1">
                          <Badge variant={a.priority === 'high' ? 'destructive' : 'secondary'}>
                            {a.priority}
                          </Badge>
                        </div>
                      </div>
                      <p className="mt-1 text-xs text-muted-foreground">
                        Impact: {a.expected_impact} | Feasibility: {a.feasibility}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {data.confidence && (
              <div className="rounded-lg bg-muted p-3">
                <p className="text-xs text-muted-foreground">
                  Confidence: {Math.round((data.confidence.score || 0) * 100)}% - {data.confidence.methodology}
                </p>
              </div>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
}

// ── Root Cause Tab ─────────────────────────────────────

function RootCauseTab({ datasetId, industry }: { datasetId?: string; industry: string }) {
  const [question, setQuestion] = useState('');
  const [data, setData] = useState<RootCauseAnalysis | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const analyze = async () => {
    if (!question.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const result = await aiService.analyzeRootCause({ question, dataset_id: datasetId, industry });
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to analyze');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className="h-full overflow-y-auto scrollbar-thin">
      <CardHeader>
        <CardTitle>Root Cause Analysis</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex gap-2">
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && analyze()}
            placeholder="e.g., Why did revenue decrease last month?"
            className="flex h-10 flex-1 rounded-md border border-input bg-background px-3 py-2 text-sm"
            disabled={loading}
          />
          <Button onClick={analyze} disabled={loading || !question.trim()}>
            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Brain className="h-4 w-4" />}
            Analyze
          </Button>
        </div>

        {error && <p className="text-sm text-destructive">{error}</p>}

        {data && (
          <>
            <div className="rounded-lg border p-3">
              <p className="text-sm font-medium">{data.observation}</p>
              <p className="mt-1 text-lg font-bold">{data.magnitude}</p>
            </div>

            {data.root_causes?.length > 0 && (
              <div>
                <h4 className="mb-2 text-sm font-semibold">Root Causes</h4>
                <div className="space-y-2">
                  {data.root_causes.map((rc, i) => (
                    <div key={i} className="rounded-lg border p-3">
                      <p className="text-sm font-medium">{rc.cause}</p>
                      <p className="mt-1 text-xs text-muted-foreground">Evidence: {rc.evidence}</p>
                      <p className="text-xs text-muted-foreground">Contribution: {rc.contribution}</p>
                      <Badge variant="secondary" className="mt-1">
                        Confidence: {Math.round((rc.confidence || 0) * 100)}%
                      </Badge>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {data.ruled_out?.length > 0 && (
              <div>
                <h4 className="mb-2 text-sm font-semibold">Ruled Out</h4>
                <ul className="space-y-1">
                  {data.ruled_out.map((r, i) => (
                    <li key={i} className="text-sm text-muted-foreground">- {r}</li>
                  ))}
                </ul>
              </div>
            )}

            <div className="rounded-lg bg-muted p-3">
              <p className="text-sm font-medium">Conclusion</p>
              <p className="mt-1 text-sm text-muted-foreground">{data.conclusion}</p>
              <p className="mt-2 text-xs text-muted-foreground">
                Overall Confidence: {Math.round((data.overall_confidence || 0) * 100)}%
              </p>
            </div>

            {data.recommended_actions?.length > 0 && (
              <div>
                <h4 className="mb-2 text-sm font-semibold">Recommended Actions</h4>
                <ul className="space-y-1">
                  {data.recommended_actions.map((a, i) => (
                    <li key={i} className="text-sm text-muted-foreground">- {a}</li>
                  ))}
                </ul>
              </div>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
}

// ── Forecast Tab ───────────────────────────────────────

function ForecastTab({ datasetId, industry }: { datasetId?: string; industry: string }) {
  const [metric, setMetric] = useState('revenue');
  const [horizon, setHorizon] = useState('medium');
  const [data, setData] = useState<ForecastResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const generate = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await aiService.generateForecast({ metric, dataset_id: datasetId, industry, horizon });
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate forecast');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className="h-full overflow-y-auto scrollbar-thin">
      <CardHeader>
        <CardTitle>Forecasting</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex gap-2">
          <input
            type="text"
            value={metric}
            onChange={(e) => setMetric(e.target.value)}
            placeholder="Metric (e.g., revenue)"
            className="flex h-10 flex-1 rounded-md border border-input bg-background px-3 py-2 text-sm"
            disabled={loading}
          />
          <select
            value={horizon}
            onChange={(e) => setHorizon(e.target.value)}
            className="h-10 rounded-md border border-input bg-background px-2 text-sm"
          >
            <option value="short">Short (7d)</option>
            <option value="medium">Medium (30d)</option>
            <option value="long">Long (90d)</option>
          </select>
          <Button onClick={generate} disabled={loading || !metric.trim()}>
            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <TrendingUp className="h-4 w-4" />}
            Forecast
          </Button>
        </div>

        {error && <p className="text-sm text-destructive">{error}</p>}

        {data && (
          <>
            <div className="rounded-lg border p-3">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">{data.metric}</span>
                <Badge variant="secondary">{data.method}</Badge>
              </div>
              <p className="mt-1 text-xs text-muted-foreground">
                Horizon: {data.horizon} periods | Accuracy: {Math.round((data.accuracy_score || 0) * 100)}%
              </p>
            </div>

            {data.predictions?.length > 0 && (
              <div>
                <h4 className="mb-2 text-sm font-semibold">Predictions</h4>
                <div className="max-h-48 overflow-y-auto rounded-lg border">
                  <table className="w-full text-sm">
                    <thead className="bg-muted sticky top-0">
                      <tr>
                        <th className="p-2 text-left">Date</th>
                        <th className="p-2 text-right">Value</th>
                        <th className="p-2 text-right">Lower CI</th>
                        <th className="p-2 text-right">Upper CI</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.predictions.map((p, i) => (
                        <tr key={i} className="border-t">
                          <td className="p-2">{p.date}</td>
                          <td className="p-2 text-right font-medium">{p.value.toFixed(2)}</td>
                          <td className="p-2 text-right text-muted-foreground">{p.lower_ci.toFixed(2)}</td>
                          <td className="p-2 text-right text-muted-foreground">{p.upper_ci.toFixed(2)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {data.assumptions?.length > 0 && (
              <div>
                <h4 className="mb-2 text-sm font-semibold">Assumptions</h4>
                <ul className="space-y-1">
                  {data.assumptions.map((a, i) => (
                    <li key={i} className="text-sm text-muted-foreground">- {a}</li>
                  ))}
                </ul>
              </div>
            )}

            {data.model_limitations?.length > 0 && (
              <div>
                <h4 className="mb-2 text-sm font-semibold">Limitations</h4>
                <ul className="space-y-1">
                  {data.model_limitations.map((l, i) => (
                    <li key={i} className="text-sm text-muted-foreground">- {l}</li>
                  ))}
                </ul>
              </div>
            )}

            {data.interpretation && (
              <div className="rounded-lg bg-muted p-3">
                <p className="text-sm">{data.interpretation}</p>
              </div>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
}

// ── Anomaly Tab ────────────────────────────────────────

function AnomalyTab({ datasetId, industry }: { datasetId?: string; industry: string }) {
  const [metric, setMetric] = useState('revenue');
  const [data, setData] = useState<AnomalyResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const detect = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await aiService.detectAnomalies({ metric, dataset_id: datasetId, industry });
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to detect anomalies');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className="h-full overflow-y-auto scrollbar-thin">
      <CardHeader>
        <CardTitle>Anomaly Detection</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex gap-2">
          <input
            type="text"
            value={metric}
            onChange={(e) => setMetric(e.target.value)}
            placeholder="Metric (e.g., revenue)"
            className="flex h-10 flex-1 rounded-md border border-input bg-background px-3 py-2 text-sm"
            disabled={loading}
          />
          <Button onClick={detect} disabled={loading || !metric.trim()}>
            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <AlertTriangle className="h-4 w-4" />}
            Detect
          </Button>
        </div>

        {error && <p className="text-sm text-destructive">{error}</p>}

        {data && (
          <>
            <div className="rounded-lg border p-3">
              <p className="text-sm font-medium">{data.summary}</p>
              <p className="mt-1 text-xs text-muted-foreground">
                Sensitivity: {data.sensitivity} | Metric: {data.metric}
              </p>
            </div>

            {data.alerts?.length > 0 ? (
              <div className="space-y-2">
                <h4 className="text-sm font-semibold">Alerts ({data.total_anomalies})</h4>
                {data.alerts.map((alert, i) => (
                  <div key={i} className="rounded-lg border p-3">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium">{alert.title}</span>
                      <Badge
                        variant={
                          alert.severity === 'critical' ? 'destructive'
                          : alert.severity === 'warning' ? 'secondary'
                          : 'secondary'
                        }
                      >
                        {alert.severity}
                      </Badge>
                    </div>
                    <p className="mt-1 text-xs text-muted-foreground">{alert.description}</p>
                    {alert.deviation_percentage != null && (
                      <p className="mt-1 text-xs text-muted-foreground">
                        Deviation: {alert.deviation_percentage.toFixed(1)}%
                      </p>
                    )}
                    <p className="mt-2 text-xs text-muted-foreground italic">{alert.explanation}</p>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">No anomalies detected.</p>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
}

// ── Recommendations Tab ────────────────────────────────

function RecommendationsTab({ datasetId, industry }: { datasetId?: string; industry: string }) {
  const [data, setData] = useState<RecommendationResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const generate = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await aiService.getRecommendations({ dataset_id: datasetId, industry });
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to get recommendations');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className="h-full overflow-y-auto scrollbar-thin">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Recommendations</CardTitle>
          <Button size="sm" onClick={generate} disabled={loading}>
            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Lightbulb className="h-4 w-4" />}
            Generate
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {error && <p className="text-sm text-destructive">{error}</p>}
        {!data && !loading && !error && (
          <p className="text-sm text-muted-foreground">Click Generate to get AI-powered recommendations.</p>
        )}
        {data && (
          <>
            {data.triggers_detected?.length > 0 && (
              <div>
                <h4 className="mb-2 text-sm font-semibold">Detected Triggers</h4>
                <div className="flex flex-wrap gap-2">
                  {data.triggers_detected.map((t, i) => (
                    <Badge key={i} variant="secondary">
                      {t.trigger}: {t.evidence}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {data.recommendations?.length > 0 && (
              <div className="space-y-2">
                <h4 className="text-sm font-semibold">Recommended Actions</h4>
                {data.recommendations.map((rec, i) => (
                  <div key={i} className="rounded-lg border p-3">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium">{rec.action}</span>
                      <div className="flex gap-1">
                        <Badge variant={rec.priority === 'high' ? 'destructive' : 'secondary'}>
                          {rec.priority}
                        </Badge>
                        <Badge variant="secondary">{rec.feasibility}</Badge>
                      </div>
                    </div>
                    <p className="mt-1 text-xs text-muted-foreground">
                      Expected Impact: {rec.expected_impact}
                    </p>
                  </div>
                ))}
              </div>
            )}

            <div className="rounded-lg bg-muted p-3">
              <p className="text-xs text-muted-foreground">
                Confidence: {Math.round((data.confidence || 0) * 100)}%
              </p>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}

// ── NL Analytics Tab ───────────────────────────────────

function NLAnalyticsTab({ datasetId, industry }: { datasetId?: string; industry: string }) {
  const [question, setQuestion] = useState('');
  const [data, setData] = useState<NLAnalyticsResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const analyze = async () => {
    if (!question.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const result = await aiService.analyzeNaturalLanguage({ question, dataset_id: datasetId, industry });
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to analyze');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className="h-full overflow-y-auto scrollbar-thin">
      <CardHeader>
        <CardTitle>Natural Language Analytics</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex gap-2">
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && analyze()}
            placeholder="e.g., Compare top performing regions"
            className="flex h-10 flex-1 rounded-md border border-input bg-background px-3 py-2 text-sm"
            disabled={loading}
          />
          <Button onClick={analyze} disabled={loading || !question.trim()}>
            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <BarChart3 className="h-4 w-4" />}
            Analyze
          </Button>
        </div>

        {error && <p className="text-sm text-destructive">{error}</p>}

        {data && (
          <>
            <div className="rounded-lg border p-3">
              <Badge variant="secondary">{data.intent}</Badge>
              <p className="mt-2 text-sm text-muted-foreground">{data.query_interpretation}</p>
            </div>

            {data.analysis?.results && (
              <div className="rounded-lg bg-muted p-3">
                <p className="text-sm font-medium">Results</p>
                <p className="mt-1 text-sm whitespace-pre-wrap">{data.analysis.results}</p>
              </div>
            )}

            {data.explanation && (
              <div className="rounded-lg border p-3">
                <p className="text-sm font-medium">Explanation</p>
                <p className="mt-1 text-sm text-muted-foreground">{data.explanation}</p>
              </div>
            )}

            {data.visualizations?.length > 0 && (
              <div>
                <h4 className="mb-2 text-sm font-semibold">Recommended Visualizations</h4>
                <div className="space-y-1">
                  {data.visualizations.map((v, i) => (
                    <div key={i} className="flex items-center gap-2 text-sm">
                      <ChevronRight className="h-4 w-4 text-primary" />
                      <span className="font-medium">{v.type}</span>
                      <span className="text-muted-foreground">- {v.rationale}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <p className="text-xs text-muted-foreground">
              Confidence: {Math.round((data.confidence || 0) * 100)}%
            </p>
          </>
        )}
      </CardContent>
    </Card>
  );
}

// ── Report Tab ─────────────────────────────────────────

function ReportTab({ datasetId, industry }: { datasetId?: string; industry: string }) {
  const [reportType, setReportType] = useState('executive');
  const [format, setFormat] = useState('markdown');
  const [data, setData] = useState<ReportResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const generate = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await aiService.generateReport({
        report_type: reportType,
        dataset_id: datasetId,
        industry,
        format,
      });
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate report');
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = () => {
    if (!data?.content) return;
    const blob = new Blob([data.content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${data.title || 'report'}.${format === 'markdown' ? 'md' : format}`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <Card className="h-full overflow-y-auto scrollbar-thin">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Report Generation</CardTitle>
          <div className="flex gap-2">
            <select
              value={reportType}
              onChange={(e) => setReportType(e.target.value)}
              className="h-8 rounded-md border border-input bg-background px-2 text-xs"
            >
              <option value="executive">Executive</option>
              <option value="monthly">Monthly</option>
              <option value="annual">Annual</option>
              <option value="quality">Quality</option>
              <option value="performance">Performance</option>
            </select>
            <select
              value={format}
              onChange={(e) => setFormat(e.target.value)}
              className="h-8 rounded-md border border-input bg-background px-2 text-xs"
            >
              <option value="markdown">Markdown</option>
              <option value="html">HTML</option>
              <option value="pdf">PDF</option>
              <option value="docx">DOCX</option>
            </select>
            <Button size="sm" onClick={generate} disabled={loading}>
              {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <FileText className="h-4 w-4" />}
              Generate
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {error && <p className="text-sm text-destructive">{error}</p>}
        {!data && !loading && !error && (
          <p className="text-sm text-muted-foreground">Select a report type and format, then click Generate.</p>
        )}
        {data && (
          <>
            <div className="flex items-center justify-between">
              <h3 className="font-semibold">{data.title}</h3>
              <Button size="sm" variant="outline" onClick={handleDownload}>
                <Download className="h-4 w-4" />
                Download
              </Button>
            </div>

            {data.summary && (
              <div className="rounded-lg bg-muted p-3">
                <p className="text-sm font-medium">Summary</p>
                <p className="mt-1 text-sm text-muted-foreground">{data.summary}</p>
              </div>
            )}

            {data.sections?.length > 0 && (
              <div className="flex flex-wrap gap-1">
                {data.sections.map((s, i) => (
                  <Badge key={i} variant="secondary">{s}</Badge>
                ))}
              </div>
            )}

            <div className="rounded-lg border p-4">
              <pre className="text-xs whitespace-pre-wrap max-h-96 overflow-y-auto">{data.content}</pre>
            </div>

            {data.methodology && (
              <div className="rounded-lg border p-3">
                <p className="text-sm font-medium">Methodology</p>
                <p className="mt-1 text-xs text-muted-foreground whitespace-pre-wrap">{data.methodology}</p>
              </div>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
}
