'use client';

import { Presentation, Download, CheckCircle2, RotateCcw } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';

interface Props {
  onGeneratePresentation: () => Promise<void>;
  onDownloadPresentation: () => void;
  onStartOver: () => void;
  isGenerating: boolean;
  presentationReady: boolean;
  datasetName: string;
}

export function PresentStep({
  onGeneratePresentation,
  onDownloadPresentation,
  onStartOver,
  isGenerating,
  presentationReady,
  datasetName,
}: Props) {
  return (
    <div className="space-y-6">
      {/* One-Click Presentation */}
      <Card className="border-2 border-primary/20">
        <CardHeader className="text-center pb-4">
          <div className="mx-auto rounded-full bg-primary/10 p-4 w-fit mb-3">
            <Presentation className="h-8 w-8 text-primary" />
          </div>
          <CardTitle className="text-xl">Create Professional Presentation</CardTitle>
          <CardDescription>
            Generate a presentation-ready PPTX from your analysis with one click.
            Includes executive summary, key findings, visualizations, and recommendations.
          </CardDescription>
        </CardHeader>
        <CardContent className="text-center space-y-4">
          {!presentationReady ? (
            <Button
              size="lg"
              onClick={onGeneratePresentation}
              disabled={isGenerating}
              className="px-8"
            >
              <Presentation className="mr-2 h-5 w-5" />
              {isGenerating ? 'Generating Presentation...' : 'Create Presentation'}
            </Button>
          ) : (
            <div className="space-y-4">
              <div className="flex items-center justify-center gap-2 text-green-600">
                <CheckCircle2 className="h-5 w-5" />
                <span className="font-medium">Presentation Ready!</span>
              </div>
              <Button size="lg" onClick={onDownloadPresentation} className="px-8">
                <Download className="mr-2 h-5 w-5" />
                Download PPTX
              </Button>
            </div>
          )}

          {/* Slide Preview */}
          <div className="mt-6 text-left">
            <p className="text-sm font-medium text-muted-foreground mb-3 text-center">
              Your presentation will include:
            </p>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-2 max-w-md mx-auto">
              {[
                'Title Slide',
                'Executive Summary',
                'Dataset Overview',
                'Data Quality',
                'Key Metrics',
                'Main Trends',
                'Key Findings',
                'Recommendations',
                'Conclusion',
              ].map((slide, i) => (
                <div
                  key={i}
                  className="flex items-center gap-2 rounded border p-2 text-xs"
                >
                  <span className="text-muted-foreground font-mono">{i + 1}</span>
                  <span>{slide}</span>
                </div>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Workflow Complete */}
      {presentationReady && (
        <Card className="bg-green-50 dark:bg-green-950/20 border-green-200 dark:border-green-900">
          <CardContent className="pt-6 text-center">
            <CheckCircle2 className="h-10 w-10 text-green-600 mx-auto mb-3" />
            <p className="text-lg font-semibold">Data-to-Decision Complete</p>
            <p className="text-sm text-muted-foreground mt-1 max-w-md mx-auto">
              Your data has been uploaded, understood, cleaned, analyzed, visualized,
              and packaged into a professional report and presentation.
            </p>
            <div className="flex flex-wrap justify-center gap-2 mt-4">
              <Badge>Upload</Badge>
              <Badge>Understand</Badge>
              <Badge>Clean</Badge>
              <Badge>Analyze</Badge>
              <Badge>Visualize</Badge>
              <Badge>Report</Badge>
              <Badge variant="default" className="bg-green-600">Present</Badge>
            </div>
            <Button variant="outline" className="mt-6" onClick={onStartOver}>
              <RotateCcw className="mr-2 h-4 w-4" />
              Start New Analysis
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
