'use client';

import { FileText, Download, Settings, Check } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Input } from '@/components/ui/Input';
import { useState } from 'react';

interface ReportConfig {
  title: string;
  organization: string;
  author: string;
  includeExecutiveSummary: boolean;
  includeDataQuality: boolean;
  includeMethodology: boolean;
  includeVisualizations: boolean;
  includeRecommendations: boolean;
  includeLimitations: boolean;
}

interface Props {
  datasetName: string;
  industry: string;
  onGenerateReport: (config: ReportConfig) => Promise<void>;
  onContinue: () => void;
  reportId: number | null;
  isGenerating: boolean;
}

export function ReportStep({
  datasetName,
  industry,
  onGenerateReport,
  onContinue,
  reportId,
  isGenerating,
}: Props) {
  const [config, setConfig] = useState<ReportConfig>({
    title: `${datasetName} - Analysis Report`,
    organization: '',
    author: '',
    includeExecutiveSummary: true,
    includeDataQuality: true,
    includeMethodology: true,
    includeVisualizations: true,
    includeRecommendations: true,
    includeLimitations: true,
  });

  const sections = [
    { key: 'includeExecutiveSummary', label: 'Executive Summary', desc: 'High-level findings overview' },
    { key: 'includeDataQuality', label: 'Data Quality', desc: 'Quality assessment and cleaning actions' },
    { key: 'includeMethodology', label: 'Methodology', desc: 'Analysis approach and methods used' },
    { key: 'includeVisualizations', label: 'Visualizations', desc: 'Charts and dashboard views' },
    { key: 'includeRecommendations', label: 'Recommendations', desc: 'Actionable recommendations' },
    { key: 'includeLimitations', label: 'Limitations', desc: 'Data limitations and caveats' },
  ] as const;

  return (
    <div className="space-y-6">
      {/* Report Configuration */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5 text-primary" />
            Report Configuration
          </CardTitle>
          <CardDescription>
            Configure your professional report. All sections use real analysis data.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium mb-1 block">Report Title</label>
              <Input
                value={config.title}
                onChange={(e) => setConfig({ ...config, title: e.target.value })}
              />
            </div>
            <div>
              <label className="text-sm font-medium mb-1 block">Organization</label>
              <Input
                placeholder="Your organization name"
                value={config.organization}
                onChange={(e) => setConfig({ ...config, organization: e.target.value })}
              />
            </div>
            <div>
              <label className="text-sm font-medium mb-1 block">Author</label>
              <Input
                placeholder="Report author"
                value={config.author}
                onChange={(e) => setConfig({ ...config, author: e.target.value })}
              />
            </div>
            <div>
              <label className="text-sm font-medium mb-1 block">Sector</label>
              <Input value={industry} disabled className="capitalize" />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Report Sections */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <Settings className="h-4 w-4" />
            Report Sections
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {sections.map((section) => {
              const isEnabled = config[section.key];
              return (
                <button
                  key={section.key}
                  onClick={() => setConfig({ ...config, [section.key]: !isEnabled })}
                  className={`flex items-start gap-3 rounded-lg border p-3 text-left transition-colors ${
                    isEnabled ? 'border-primary/50 bg-primary/5' : 'border-border hover:border-muted-foreground/50'
                  }`}
                >
                  <div
                    className={`mt-0.5 flex h-5 w-5 items-center justify-center rounded border ${
                      isEnabled ? 'border-primary bg-primary text-white' : 'border-muted-foreground/30'
                    }`}
                  >
                    {isEnabled && <Check className="h-3 w-3" />}
                  </div>
                  <div>
                    <p className="text-sm font-medium">{section.label}</p>
                    <p className="text-xs text-muted-foreground">{section.desc}</p>
                  </div>
                </button>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Generate Button */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium">Report Structure</p>
              <p className="text-sm text-muted-foreground">
                Cover Page - {sections.filter((s) => config[s.key]).map((s) => s.label).join(' - ')} - Appendix
              </p>
            </div>
            <div className="flex gap-2">
              {reportId ? (
                <Badge variant="default" className="bg-green-600">Report Generated</Badge>
              ) : (
                <Button onClick={() => onGenerateReport(config)} disabled={isGenerating}>
                  <FileText className="mr-2 h-4 w-4" />
                  {isGenerating ? 'Generating...' : 'Generate Report'}
                </Button>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      <Button onClick={onContinue} size="lg" className="w-full" disabled={!reportId}>
        Continue to Presentation
      </Button>
    </div>
  );
}
