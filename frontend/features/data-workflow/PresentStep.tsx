'use client';

import { useState } from 'react';
import { Presentation, Download, CheckCircle2, RotateCcw, Loader2, Sparkles, Layout } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Input } from '@/components/ui/Input';

interface Props {
  onGeneratePresentation: (template: string, title: string) => Promise<void>;
  onDownloadPresentation: () => void;
  onStartOver: () => void;
  isGenerating: boolean;
  presentationReady: boolean;
  datasetName: string;
}

const TEMPLATES = [
  {
    id: 'executive',
    name: 'Executive Briefing',
    desc: 'High-level C-suite summary, strategic KPIs, and major findings',
  },
  {
    id: 'analytical',
    name: 'Analytical Deep-Dive',
    desc: 'Focus on chart distributions, correlation heatmaps, and outlier tests',
  },
  {
    id: 'research',
    name: 'Technical / Research',
    desc: 'Structured methodology, data quality audit tables, and statistical inference',
  },
  {
    id: 'pitch',
    name: 'Investor / Pitch',
    desc: 'Fast-paced narrative with punchy headline metrics and strategic growth steps',
  },
];

export function PresentStep({
  onGeneratePresentation,
  onDownloadPresentation,
  onStartOver,
  isGenerating,
  presentationReady,
  datasetName,
}: Props) {
  const [selectedTemplate, setSelectedTemplate] = useState('executive');
  const [title, setTitle] = useState(`${datasetName} — Strategic Analysis`);

  const handleGenerate = () => {
    onGeneratePresentation(selectedTemplate, title);
  };

  return (
    <div className="space-y-6">
      {/* Configuration Card */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-base flex items-center gap-2">
                <Presentation className="h-5 w-5 text-primary" />
                PowerPoint Presentation Designer (.pptx)
              </CardTitle>
              <CardDescription>
                Generates a native 16:9 widescreen presentation with embedded native charts and speaker notes
              </CardDescription>
            </div>
            <Badge variant="outline" className="text-xs">
              Native PPTX
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1 block">
              Presentation Title
            </label>
            <Input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="h-9 text-xs font-medium"
            />
          </div>

          <div>
            <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-2 block">
              Presentation Theme & Narrative Style
            </label>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {TEMPLATES.map((t) => {
                const isSelected = selectedTemplate === t.id;
                return (
                  <button
                    key={t.id}
                    type="button"
                    onClick={() => setSelectedTemplate(t.id)}
                    className={`p-3 rounded-lg border text-left transition-all ${
                      isSelected
                        ? 'border-primary bg-primary/5 ring-1 ring-primary/30 shadow-xs'
                        : 'border-border hover:border-muted-foreground/40'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-foreground">{t.name}</span>
                      {isSelected && <Badge className="text-[10px] bg-primary text-primary-foreground">Selected</Badge>}
                    </div>
                    <p className="text-[11px] text-muted-foreground mt-1 leading-snug">{t.desc}</p>
                  </button>
                );
              })}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Generation Bar */}
      <Card className="border-2 border-primary/20 bg-card">
        <CardContent className="pt-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <Layout className="h-5 w-5 text-primary" />
                <span className="font-semibold text-sm">Slide Deck Architecture</span>
                {presentationReady && (
                  <Badge className="bg-emerald-600 text-white text-[10px] flex items-center gap-1">
                    <CheckCircle2 className="h-3 w-3" /> Ready
                  </Badge>
                )}
              </div>
              <p className="text-xs text-muted-foreground">
                Synthesizes Executive Summary, Metrics, Visualizations, and Recommendations into editable slides.
              </p>
            </div>

            <div className="flex items-center gap-3">
              {!presentationReady ? (
                <Button
                  size="default"
                  onClick={handleGenerate}
                  disabled={isGenerating}
                  className="px-6 font-semibold"
                >
                  {isGenerating ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Rendering Slides...
                    </>
                  ) : (
                    <>
                      <Presentation className="mr-2 h-4 w-4" />
                      Create & Download PPTX
                    </>
                  )}
                </Button>
              ) : (
                <div className="flex items-center gap-2">
                  <Button size="default" onClick={onDownloadPresentation} className="px-6 font-semibold">
                    <Download className="mr-2 h-4 w-4" />
                    Download PPTX Again
                  </Button>
                </div>
              )}
            </div>
          </div>

          {/* Slide Outline Preview */}
          <div className="mt-6 pt-4 border-t">
            <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-3">
              Generated Slide Outline (Widescreen 16:9)
            </p>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-2">
              {[
                { num: 1, name: 'Title Slide', type: 'Header' },
                { num: 2, name: 'Executive Summary', type: 'Text + Cards' },
                { num: 3, name: 'Dataset Profile', type: 'Stats' },
                { num: 4, name: 'Data Hygiene Audit', type: 'Table' },
                { num: 5, name: 'Primary Metric Charts', type: 'Native Chart' },
                { num: 6, name: 'Key Distribution Trends', type: 'Native Chart' },
                { num: 7, name: 'Comparative Breakdown', type: 'Native Chart' },
                { num: 8, name: 'Statistical Anomalies', type: 'Insights' },
                { num: 9, name: 'Strategic Next Steps', type: 'Bullets' },
                { num: 10, name: 'Conclusion & Sign-off', type: 'Closing' },
              ].map((slide) => (
                <div
                  key={slide.num}
                  className="rounded-md border p-2.5 bg-muted/20 hover:bg-muted/40 transition-colors"
                >
                  <div className="flex items-center justify-between text-[10px] text-muted-foreground font-mono">
                    <span>Slide {slide.num}</span>
                    <span className="text-primary font-sans">{slide.type}</span>
                  </div>
                  <p className="font-medium text-xs text-foreground mt-1 truncate">{slide.name}</p>
                </div>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Workflow Complete Banner */}
      {presentationReady && (
        <Card className="bg-emerald-50 dark:bg-emerald-950/20 border-emerald-200 dark:border-emerald-900">
          <CardContent className="pt-6 text-center">
            <CheckCircle2 className="h-10 w-10 text-emerald-600 mx-auto mb-3" />
            <p className="text-lg font-bold text-foreground">Data-to-Decision Pipeline Completed</p>
            <p className="text-xs text-muted-foreground mt-1 max-w-md mx-auto leading-relaxed">
              Your raw data has traveled through understanding, cleaning, advanced analysis, visual dashboarding,
              formal reporting, and slide generation.
            </p>
            <div className="flex flex-wrap justify-center gap-1.5 mt-4">
              <Badge variant="outline" className="text-xs">1. Upload</Badge>
              <Badge variant="outline" className="text-xs">2. Understand</Badge>
              <Badge variant="outline" className="text-xs">3. Clean</Badge>
              <Badge variant="outline" className="text-xs">4. Analyze</Badge>
              <Badge variant="outline" className="text-xs">5. Visualize</Badge>
              <Badge variant="outline" className="text-xs">6. Report</Badge>
              <Badge className="bg-emerald-600 text-white text-xs">7. Present</Badge>
            </div>
            <Button variant="outline" size="sm" className="mt-6" onClick={onStartOver}>
              <RotateCcw className="mr-2 h-3.5 w-3.5" />
              Analyze Another Dataset
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

