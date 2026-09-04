'use client';

import { useState } from 'react';
import { FileText, Download, Settings, Check, Loader2, Shield, BarChart3, CheckCircle2 } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Input } from '@/components/ui/Input';
import { cleanMojibake } from '@/lib/utils';
import type { ReportConfig } from '@/types/workflow';

interface Props {
  datasetName: string;
  industry: string;
  onGenerateReport: (config: ReportConfig) => Promise<void>;
  onContinue: () => void;
  reportId: number | null;
  isGenerating: boolean;
  hasDownloadedReport?: boolean;
}

export function ReportStep({
  datasetName,
  industry,
  onGenerateReport,
  onContinue,
  reportId,
  isGenerating,
  hasDownloadedReport = false,
}: Props) {
  const [config, setConfig] = useState<ReportConfig>({
    title: `${cleanMojibake(datasetName)} — Decision Audit Report`,
    organization: '',
    author: '',
    include_executive_summary: true,
    include_data_quality: true,
    include_methodology: true,
    include_visualizations: true,
    include_recommendations: true,
    include_limitations: true,
  });

  const sections = [
    { key: 'include_executive_summary', label: 'Executive Summary', desc: 'Dataset scope, context, and key takeaways' },
    { key: 'include_data_quality', label: 'Data Quality & Cleaning Audit', desc: 'Quality scorecard, cleaning log, and completeness' },
    { key: 'include_methodology', label: 'Key Performance Indicators', desc: 'Pre-computed KPI metric cards & ranges' },
    { key: 'include_visualizations', label: 'Visualization Portfolio', desc: 'Overview of recommended chart specifications' },
    { key: 'include_recommendations', label: 'Automated Statistical Insights', desc: 'Parametric anomalies and pattern detections' },
    { key: 'include_limitations', label: 'Strategic Recommendations', desc: 'Actionable business steps derived from data' },
  ] as const;

  const isReady = reportId !== null || hasDownloadedReport;

  return (
    <div className="space-y-6">
      {/* Report Configuration */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2 text-base">
                <FileText className="h-5 w-5 text-primary" />
                Executive Decision Report Setup
              </CardTitle>
              <CardDescription>
                Generates a formal, publication-grade PDF report with headers, metadata, cleaning audits, and insights
              </CardDescription>
            </div>
            <Badge variant="outline" className="text-xs">
              PDF Format (A4)
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1 block">
                Report Title
              </label>
              <Input
                value={config.title}
                onChange={(e) => setConfig({ ...config, title: e.target.value })}
                className="h-9 text-xs font-medium"
              />
            </div>
            <div>
              <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1 block">
                Client / Organization
              </label>
              <Input
                placeholder="e.g., Enterprise Analytics Team"
                value={config.organization}
                onChange={(e) => setConfig({ ...config, organization: e.target.value })}
                className="h-9 text-xs"
              />
            </div>
            <div>
              <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1 block">
                Author / Lead Analyst
              </label>
              <Input
                placeholder="e.g., Lead Data Engineer"
                value={config.author}
                onChange={(e) => setConfig({ ...config, author: e.target.value })}
                className="h-9 text-xs"
              />
            </div>
            <div>
              <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1 block">
                Detected Sector
              </label>
              <Input value={industry || 'General Business'} disabled className="h-9 text-xs capitalize bg-muted/30 font-medium" />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Report Sections Customizer */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-semibold flex items-center gap-2">
            <Settings className="h-4 w-4 text-primary" />
            Report Modules & Inclusions
          </CardTitle>
          <CardDescription className="text-xs">
            Toggle modules to include in the generated PDF report
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {sections.map((section) => {
              const isEnabled = !!config[section.key];
              return (
                <button
                  key={section.key}
                  type="button"
                  onClick={() => setConfig({ ...config, [section.key]: !isEnabled })}
                  className={`flex items-start gap-3 rounded-lg border p-3 text-left transition-all ${
                    isEnabled
                      ? 'border-primary/50 bg-primary/5 shadow-xs'
                      : 'border-border hover:border-muted-foreground/40 opacity-70'
                  }`}
                >
                  <div
                    className={`mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center rounded border ${
                      isEnabled ? 'border-primary bg-primary text-white' : 'border-muted-foreground/30'
                    }`}
                  >
                    {isEnabled && <Check className="h-3 w-3" />}
                  </div>
                  <div>
                    <p className="text-xs font-semibold text-foreground">{section.label}</p>
                    <p className="text-[11px] text-muted-foreground mt-0.5">{section.desc}</p>
                  </div>
                </button>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Generation & Download Bar */}
      <Card className="border-primary/30 bg-primary/5">
        <CardContent className="pt-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <FileText className="h-5 w-5 text-primary" />
                <span className="font-semibold text-sm">Publication-Grade Executive PDF</span>
                {isReady && (
                  <Badge className="bg-emerald-600 text-white text-[10px] flex items-center gap-1">
                    <CheckCircle2 className="h-3 w-3" /> Ready
                  </Badge>
                )}
              </div>
              <p className="text-xs text-muted-foreground">
                Formal document complete with cover banner, data hygiene scorecards, and audit trails.
              </p>
            </div>

            <div className="flex items-center gap-3">
              <Button
                onClick={() => onGenerateReport(config)}
                disabled={isGenerating}
                size="default"
                className="gap-2 shadow-sm font-semibold"
              >
                {isGenerating ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Generating PDF...
                  </>
                ) : isReady ? (
                  <>
                    <Download className="h-4 w-4" />
                    Download PDF Again
                  </>
                ) : (
                  <>
                    <Download className="h-4 w-4" />
                    Download PDF Report
                  </>
                )}
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      <Button onClick={onContinue} size="lg" className="w-full">
        Proceed to Executive Presentation &rarr;
      </Button>
    </div>
  );
}

