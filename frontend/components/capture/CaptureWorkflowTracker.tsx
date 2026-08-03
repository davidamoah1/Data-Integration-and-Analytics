'use client';

import { useEffect, useState } from 'react';
import {
  Upload, ScanLine, FileSearch, CheckSquare, Eye, CheckCircle2,
  Database, ArrowRight, Loader2,
} from 'lucide-react';
import { captureService, type CaptureAnalyticsSummary } from '@/services/capture/captureService';
import { Card, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { cn } from '@/lib/utils';
import { toast } from '@/components/ui/Toaster';
import { useRouter } from 'next/navigation';

const PIPELINE_STEPS = [
  { key: 'upload', label: 'Upload', icon: Upload, description: 'Document or image uploaded', href: '/capture/upload' },
  { key: 'ocr', label: 'OCR Extraction', icon: ScanLine, description: 'Text extracted from document' },
  { key: 'field_detection', label: 'Field Detection', icon: FileSearch, description: 'Fields identified and extracted' },
  { key: 'validation', label: 'Validation', icon: CheckSquare, description: 'Data validated against rules' },
  { key: 'review', label: 'Human Review', icon: Eye, description: 'Reviewer checks and corrects', href: '/capture/review' },
  { key: 'approval', label: 'Approval', icon: CheckCircle2, description: 'Document approved for entry' },
  { key: 'database_entry', label: 'Database Entry', icon: Database, description: 'Data exported to dataset' },
];

export function CaptureWorkflowTracker() {
  const router = useRouter();
  const [summary, setSummary] = useState<CaptureAnalyticsSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(false);

  const loadSummary = async () => {
    try {
      const s = await captureService.getAnalyticsSummary();
      setSummary(s);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSummary();
  }, []);

  const handleBulkExport = async () => {
    setExporting(true);
    try {
      const result = await captureService.bulkExportApproved();
      toast.success(`Exported ${result.row_count} documents to ${result.dataset_name}`);
    } catch (err) {
      toast.error('Failed to export approved documents');
    } finally {
      setExporting(false);
    }
  };

  // Determine which steps are "active" based on data
  const getStepStatus = (stepKey: string): 'active' | 'done' | 'pending' => {
    if (!summary) return 'pending';
    const total = summary.total_documents;
    if (total === 0) return 'pending';

    switch (stepKey) {
      case 'upload':
        return total > 0 ? 'done' : 'pending';
      case 'ocr':
        return total > 0 ? 'done' : 'pending';
      case 'field_detection':
        return total > 0 ? 'done' : 'pending';
      case 'validation':
        return total > 0 ? 'done' : 'pending';
      case 'review':
        return summary.pending_review > 0 ? 'active' : 'done';
      case 'approval':
        return summary.approved_documents > 0 ? 'done' : 'pending';
      case 'database_entry':
        return summary.approved_documents > 0 ? 'active' : 'pending';
      default:
        return 'pending';
    }
  };

  return (
    <Card>
      <CardContent className="p-6">
        <div className="mb-4 flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold">Smart Data Capture Pipeline</h3>
            <p className="text-sm text-muted-foreground">
              Upload → OCR → Field Detection → Validation → Review → Approval → Database Entry
            </p>
          </div>
          {summary && summary.approved_documents > 0 && (
            <Button onClick={handleBulkExport} disabled={exporting} size="sm" className="gap-2">
              {exporting ? <Loader2 size={14} className="animate-spin" /> : <Database size={14} />}
              Export Approved to Dataset
            </Button>
          )}
        </div>

        {/* Pipeline visualization */}
        <div className="flex items-center justify-between overflow-x-auto pb-2">
          {PIPELINE_STEPS.map((step, i) => {
            const status = getStepStatus(step.key);
            const Icon = step.icon;

            return (
              <div key={step.key} className="flex flex-1 items-center min-w-[120px]">
                <button
                  onClick={() => step.href && router.push(step.href)}
                  className="group flex flex-col items-center gap-1.5"
                  disabled={!step.href}
                >
                  <div
                    className={cn(
                      'flex h-10 w-10 items-center justify-center rounded-full border-2 transition-all',
                      status === 'done' && 'border-green-500 bg-green-500 text-white',
                      status === 'active' && 'border-primary bg-primary text-primary-foreground scale-110 shadow-md',
                      status === 'pending' && 'border-slate-200 bg-white text-slate-300 dark:border-slate-700 dark:bg-slate-800',
                      step.href && 'cursor-pointer hover:scale-105'
                    )}
                  >
                    <Icon size={18} />
                  </div>
                  <span
                    className={cn(
                      'text-[10px] font-medium text-center',
                      status === 'done' && 'text-green-600',
                      status === 'active' && 'text-primary',
                      status === 'pending' && 'text-muted-foreground'
                    )}
                  >
                    {step.label}
                  </span>
                </button>
                {i < PIPELINE_STEPS.length - 1 && (
                  <div className={cn(
                    'mx-1 h-0.5 flex-1 transition-colors',
                    status === 'done' ? 'bg-green-500' : 'bg-slate-200 dark:bg-slate-700'
                  )} />
                )}
              </div>
            );
          })}
        </div>

        {/* Stats row */}
        {!loading && summary && (
          <div className="mt-4 grid grid-cols-2 gap-3 md:grid-cols-4">
            <div className="rounded-lg border p-3 text-center">
              <p className="text-2xl font-bold text-blue-600">{summary.total_documents}</p>
              <p className="text-xs text-muted-foreground">Total Documents</p>
            </div>
            <div className="rounded-lg border p-3 text-center">
              <p className="text-2xl font-bold text-amber-600">{summary.pending_review}</p>
              <p className="text-xs text-muted-foreground">Pending Review</p>
            </div>
            <div className="rounded-lg border p-3 text-center">
              <p className="text-2xl font-bold text-green-600">{summary.approved_documents}</p>
              <p className="text-xs text-muted-foreground">Approved</p>
            </div>
            <div className="rounded-lg border p-3 text-center">
              <p className="text-2xl font-bold text-purple-600">
                {Math.round(summary.average_confidence * 100)}%
              </p>
              <p className="text-xs text-muted-foreground">Avg Confidence</p>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
