'use client';

import { useState } from 'react';
import { BarChart3, Brain, Calculator, TrendingUp, MessageSquare } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Input } from '@/components/ui/Input';
import type { InsightsResult, Insight } from '@/types/workflow';

type AnalysisMode = 'easy' | 'pro';

interface Props {
  insights: InsightsResult | null;
  industry: string;
  onAskQuestion: (question: string) => Promise<void>;
  onContinue: () => void;
}

export function AnalyzeStep({ insights, industry, onAskQuestion, onContinue }: Props) {
  const [mode, setMode] = useState<AnalysisMode>('easy');
  const [question, setQuestion] = useState('');
  const [asking, setAsking] = useState(false);

  const handleAsk = async () => {
    if (!question.trim()) return;
    setAsking(true);
    try {
      await onAskQuestion(question);
      setQuestion('');
    } finally {
      setAsking(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Mode Toggle */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <BarChart3 className="h-5 w-5 text-primary" />
              <div>
                <p className="font-medium">Analysis Mode</p>
                <p className="text-sm text-muted-foreground">
                  {mode === 'easy'
                    ? 'Ask questions in plain language'
                    : 'Full statistical controls'}
                </p>
              </div>
            </div>
            <div className="flex rounded-lg border p-0.5">
              <button
                onClick={() => setMode('easy')}
                className={`px-4 py-1.5 text-sm font-medium rounded-md transition-colors ${
                  mode === 'easy'
                    ? 'bg-primary text-primary-foreground'
                    : 'text-muted-foreground hover:text-foreground'
                }`}
              >
                <MessageSquare className="inline-block mr-1 h-3 w-3" />
                Easy
              </button>
              <button
                onClick={() => setMode('pro')}
                className={`px-4 py-1.5 text-sm font-medium rounded-md transition-colors ${
                  mode === 'pro'
                    ? 'bg-primary text-primary-foreground'
                    : 'text-muted-foreground hover:text-foreground'
                }`}
              >
                <Calculator className="inline-block mr-1 h-3 w-3" />
                Pro
              </button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Easy Mode - Ask Questions */}
      {mode === 'easy' && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Brain className="h-4 w-4 text-primary" />
              Ask Your Data
            </CardTitle>
            <CardDescription>
              Ask questions in plain language. The system will translate them into appropriate analysis.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex gap-2">
              <Input
                placeholder="e.g., What are my biggest trends? Which products are declining?"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleAsk()}
                className="flex-1"
              />
              <Button onClick={handleAsk} disabled={asking || !question.trim()}>
                Ask
              </Button>
            </div>
            <div className="flex flex-wrap gap-2">
              {getSuggestedQuestions(industry).map((q, i) => (
                <button
                  key={i}
                  onClick={() => setQuestion(q)}
                  className="text-xs border rounded-full px-3 py-1 hover:bg-muted transition-colors text-muted-foreground hover:text-foreground"
                >
                  {q}
                </button>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Pro Mode - Statistical Controls */}
      {mode === 'pro' && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Calculator className="h-4 w-4 text-primary" />
              Statistical Analysis
            </CardTitle>
            <CardDescription>
              Full statistical tools for researchers and analysts
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
              {[
                'Descriptive Statistics',
                'Frequency Analysis',
                'Cross-Tabulation',
                'Correlation Matrix',
                'Distribution Analysis',
                'Outlier Detection',
                'Time-Series Analysis',
                'Trend Analysis',
                'Comparative Analysis',
              ].map((analysis) => (
                <Button key={analysis} variant="outline" size="sm" className="justify-start">
                  {analysis}
                </Button>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Auto-Generated Insights */}
      {insights && insights.insights.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-primary" />
              Key Insights ({insights.total_insights})
            </CardTitle>
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

      <Button onClick={onContinue} size="lg" className="w-full">
        Continue to Visualize
      </Button>
    </div>
  );
}

function InsightCard({ insight }: { insight: Insight }) {
  const typeColors: Record<string, string> = {
    trend: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
    anomaly: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
    correlation: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200',
    dominance: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
    distribution: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
  };

  return (
    <div className="rounded-lg border p-4">
      <div className="flex items-start gap-3">
        <Badge className={typeColors[insight.type] || 'bg-gray-100 text-gray-800'}>
          {insight.type}
        </Badge>
        <div className="flex-1">
          <p className="text-sm font-medium">{insight.title}</p>
          <p className="text-sm text-muted-foreground mt-0.5">{insight.description}</p>
          {insight.recommendation && (
            <p className="text-sm text-primary mt-1">
              Recommendation: {insight.recommendation}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

function getSuggestedQuestions(industry: string): string[] {
  const general = [
    'What are the main trends?',
    'Show me the key patterns',
    'What needs attention?',
  ];

  const sectorQuestions: Record<string, string[]> = {
    healthcare: [
      'What are the patient volume trends?',
      'Which diagnoses are most common?',
      'Show age distribution',
    ],
    education: [
      'What are the pass rates?',
      'Which subjects need attention?',
      'Show attendance trends',
    ],
    business: [
      'Which products are performing best?',
      'What are the revenue trends?',
      'Show regional performance',
    ],
    retail: [
      'Which products are top sellers?',
      'What are the sales trends?',
      'Show customer patterns',
    ],
    government: [
      'Show budget utilization',
      'What are the regional comparisons?',
      'Which projects are on track?',
    ],
  };

  return sectorQuestions[industry] || general;
}
