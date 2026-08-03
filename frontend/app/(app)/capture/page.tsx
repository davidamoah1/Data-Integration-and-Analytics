"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import {
  Upload,
  FileSearch,
  CheckCircle2,
  Clock,
  AlertCircle,
  ScanLine,
  FileText,
  BarChart3,
  Settings,
  ArrowRight,
  ListChecks,
} from "lucide-react";
import { captureService, type CaptureAnalyticsSummary, type CaptureEngineStatus } from "@/services/capture/captureService";
import { CaptureWorkflowTracker } from "@/components/capture/CaptureWorkflowTracker";
import { Button } from "@/components/ui/Button";

const STATUS_COLORS: Record<string, string> = {
  uploaded: "bg-slate-100 text-slate-600",
  processing: "bg-blue-100 text-blue-700",
  ready_for_review: "bg-amber-100 text-amber-700",
  approved: "bg-green-100 text-green-700",
  rejected: "bg-red-100 text-red-700",
  draft: "bg-purple-100 text-purple-700",
  failed: "bg-red-100 text-red-700",
};

export default function CaptureHubPage() {
  const [summary, setSummary] = useState<CaptureAnalyticsSummary | null>(null);
  const [status, setStatus] = useState<CaptureEngineStatus | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([captureService.getAnalyticsSummary(), captureService.getStatus()])
      .then(([s, st]) => {
        setSummary(s);
        setStatus(st);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const stats = summary
    ? [
        { label: "Total Documents", value: summary.total_documents, icon: FileText, color: "text-blue-600 bg-blue-50" },
        { label: "Pending Review", value: summary.pending_review, icon: Clock, color: "text-amber-600 bg-amber-50" },
        { label: "Approved", value: summary.approved_documents, icon: CheckCircle2, color: "text-green-600 bg-green-50" },
        { label: "Failed", value: summary.failed_documents, icon: AlertCircle, color: "text-red-600 bg-red-50" },
      ]
    : [];

  return (
    <div className="min-h-screen bg-slate-50 py-8">
      <div className="mx-auto max-w-7xl px-6">
        <div className="mb-8">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-indigo-600 text-white shadow-lg shadow-indigo-600/20">
              <ScanLine size={24} />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-slate-900">Smart Data Capture</h1>
              <p className="text-sm text-slate-500">Transform paper documents into structured digital data</p>
            </div>
          </div>
          {status && (
            <div className="mt-4 flex items-center gap-4 text-sm">
              <span className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 font-medium ${
                status.ocr_available ? "bg-green-50 text-green-700" : "bg-red-50 text-red-700"
              }`}>
                <span className={`h-1.5 w-1.5 rounded-full ${status.ocr_available ? "bg-green-500" : "bg-red-500"}`} />
                OCR Engine {status.ocr_available ? "Ready" : "Unavailable"}
              </span>
            </div>
          )}
        </div>

        {/* Stats */}
        <div className="mb-8 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {loading
            ? Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="h-28 animate-pulse rounded-xl border border-slate-200 bg-white" />
              ))
            : stats.map((s) => (
                <div key={s.label} className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
                  <div className={`mb-3 inline-flex h-9 w-9 items-center justify-center rounded-lg ${s.color}`}>
                    <s.icon size={18} />
                  </div>
                  <p className="text-2xl font-bold text-slate-900">{s.value}</p>
                  <p className="text-xs font-medium text-slate-500">{s.label}</p>
                </div>
              ))}
        </div>

        {/* Pipeline tracker */}
        <div className="mb-8">
          <CaptureWorkflowTracker />
        </div>

        {/* Action cards */}
        <div className="grid grid-cols-1 gap-6 md:grid-cols-3 lg:grid-cols-4">
          <Link href="/capture/upload" className="group">
            <div className="flex h-full flex-col rounded-xl border border-slate-200 bg-white p-6 shadow-sm transition-all hover:-translate-y-0.5 hover:shadow-md">
              <div className="mb-4 inline-flex h-12 w-12 items-center justify-center rounded-xl bg-indigo-50 text-indigo-600">
                <Upload size={24} />
              </div>
              <h3 className="text-lg font-semibold text-slate-900">Upload Document</h3>
              <p className="mt-1 flex-1 text-sm text-slate-500">
                Upload a photo, scan, or PDF. The system will automatically extract and validate the data for your review.
              </p>
              <span className="mt-4 inline-flex items-center gap-1 text-sm font-medium text-indigo-600 group-hover:gap-2 transition-all">
                Start <ArrowRight size={16} />
              </span>
            </div>
          </Link>

          <Link href="/capture/review" className="group">
            <div className="flex h-full flex-col rounded-xl border border-slate-200 bg-white p-6 shadow-sm transition-all hover:-translate-y-0.5 hover:shadow-md">
              <div className="mb-4 inline-flex h-12 w-12 items-center justify-center rounded-xl bg-amber-50 text-amber-600">
                <FileSearch size={24} />
              </div>
              <h3 className="text-lg font-semibold text-slate-900">Review Queue</h3>
              <p className="mt-1 flex-1 text-sm text-slate-500">
                Review extracted data side-by-side with the original document. Edit, approve, or reject with confidence scores.
              </p>
              <span className="mt-4 inline-flex items-center gap-1 text-sm font-medium text-amber-600 group-hover:gap-2 transition-all">
                Open <ArrowRight size={16} />
              </span>
            </div>
          </Link>

          <Link href="/capture/analytics" className="group">
            <div className="flex h-full flex-col rounded-xl border border-slate-200 bg-white p-6 shadow-sm transition-all hover:-translate-y-0.5 hover:shadow-md">
              <div className="mb-4 inline-flex h-12 w-12 items-center justify-center rounded-xl bg-blue-50 text-blue-600">
                <BarChart3 size={24} />
              </div>
              <h3 className="text-lg font-semibold text-slate-900">Analytics</h3>
              <p className="mt-1 flex-1 text-sm text-slate-500">
                View capture statistics, document type breakdowns, confidence trends, and processing performance.
              </p>
              <span className="mt-4 inline-flex items-center gap-1 text-sm font-medium text-blue-600 group-hover:gap-2 transition-all">
                View <ArrowRight size={16} />
              </span>
            </div>
          </Link>

          <Link href="/jobs" className="group">
            <div className="flex h-full flex-col rounded-xl border border-slate-200 bg-white p-6 shadow-sm transition-all hover:-translate-y-0.5 hover:shadow-md">
              <div className="mb-4 inline-flex h-12 w-12 items-center justify-center rounded-xl bg-purple-50 text-purple-600">
                <ListChecks size={24} />
              </div>
              <h3 className="text-lg font-semibold text-slate-900">Background Jobs</h3>
              <p className="mt-1 flex-1 text-sm text-slate-500">
                Monitor long-running tasks: ETL pipelines, OCR batch processing, report generation, and large data imports.
              </p>
              <span className="mt-4 inline-flex items-center gap-1 text-sm font-medium text-purple-600 group-hover:gap-2 transition-all">
                View <ArrowRight size={16} />
              </span>
            </div>
          </Link>
        </div>

        {/* Document type breakdown */}
        {summary && Object.keys(summary.by_document_type).length > 0 && (
          <div className="mt-8 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
            <h3 className="mb-4 text-sm font-semibold text-slate-700">Documents by Type</h3>
            <div className="flex flex-wrap gap-2">
              {Object.entries(summary.by_document_type).map(([type, count]) => (
                <span key={type} className="inline-flex items-center gap-2 rounded-lg border border-slate-200 bg-slate-50 px-3 py-1.5 text-sm">
                  <span className="font-medium text-slate-700">{type}</span>
                  <span className="rounded-full bg-indigo-100 px-2 py-0.5 text-xs font-bold text-indigo-700">{count}</span>
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
