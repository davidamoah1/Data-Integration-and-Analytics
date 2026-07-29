"use client";

import { useEffect, useState } from "react";
import { BarChart3, TrendingUp, FileText, CheckCircle2, Clock, AlertCircle, Loader2 } from "lucide-react";
import { captureService, type CaptureAnalyticsSummary } from "@/services/capture/captureService";

export default function CaptureAnalyticsPage() {
  const [summary, setSummary] = useState<CaptureAnalyticsSummary | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    captureService.getAnalyticsSummary()
      .then(setSummary)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-50">
        <Loader2 size={32} className="animate-spin text-indigo-500" />
      </div>
    );
  }

  if (!summary) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center bg-slate-50">
        <p className="text-lg font-medium text-slate-500">Unable to load analytics</p>
      </div>
    );
  }

  const stats = [
    { label: "Total Documents", value: summary.total_documents, icon: FileText, color: "text-blue-600 bg-blue-50" },
    { label: "Approved", value: summary.approved_documents, icon: CheckCircle2, color: "text-green-600 bg-green-50" },
    { label: "Pending Review", value: summary.pending_review, icon: Clock, color: "text-amber-600 bg-amber-50" },
    { label: "Failed", value: summary.failed_documents, icon: AlertCircle, color: "text-red-600 bg-red-50" },
  ];

  const maxTypeCount = Math.max(...Object.values(summary.by_document_type || { 1: 1 }), 1);

  return (
    <div className="min-h-screen bg-slate-50 py-8">
      <div className="mx-auto max-w-5xl px-6">
        <div className="mb-6">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-blue-600 text-white shadow-lg">
              <BarChart3 size={24} />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-slate-900">Capture Analytics</h1>
              <p className="text-sm text-slate-500">Processing performance and data quality metrics</p>
            </div>
          </div>
        </div>

        {/* Stat cards */}
        <div className="mb-8 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {stats.map((s) => (
            <div key={s.label} className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
              <div className={`mb-3 inline-flex h-9 w-9 items-center justify-center rounded-lg ${s.color}`}>
                <s.icon size={18} />
              </div>
              <p className="text-2xl font-bold text-slate-900">{s.value}</p>
              <p className="text-xs font-medium text-slate-500">{s.label}</p>
            </div>
          ))}
        </div>

        {/* Confidence */}
        <div className="mb-8 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex items-center gap-2">
            <TrendingUp size={18} className="text-indigo-600" />
            <h3 className="text-sm font-semibold text-slate-700">Average Extraction Confidence</h3>
          </div>
          <div className="mt-4 flex items-center gap-4">
            <div className="text-3xl font-bold text-slate-900">
              {Math.round(summary.average_confidence * 100)}%
            </div>
            <div className="h-3 flex-1 overflow-hidden rounded-full bg-slate-100">
              <div
                className={`h-full rounded-full ${
                  summary.average_confidence >= 0.75 ? "bg-green-500" :
                  summary.average_confidence >= 0.5 ? "bg-amber-500" : "bg-red-500"
                }`}
                style={{ width: `${Math.round(summary.average_confidence * 100)}%` }}
              />
            </div>
          </div>
        </div>

        {/* Document type breakdown */}
        {Object.keys(summary.by_document_type).length > 0 && (
          <div className="mb-8 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
            <h3 className="mb-4 text-sm font-semibold text-slate-700">Documents by Type</h3>
            <div className="space-y-3">
              {Object.entries(summary.by_document_type)
                .sort((a, b) => b[1] - a[1])
                .map(([type, count]) => (
                  <div key={type} className="flex items-center gap-3">
                    <span className="w-40 shrink-0 truncate text-sm font-medium text-slate-600">{type}</span>
                    <div className="h-6 flex-1 overflow-hidden rounded-full bg-slate-100">
                      <div
                        className="h-full rounded-full bg-gradient-to-r from-indigo-500 to-blue-400"
                        style={{ width: `${(count / maxTypeCount) * 100}%` }}
                      />
                    </div>
                    <span className="w-8 shrink-0 text-right text-sm font-bold text-slate-700">{count}</span>
                  </div>
                ))}
            </div>
          </div>
        )}

        {/* Industry breakdown */}
        {Object.keys(summary.by_industry).length > 0 && (
          <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
            <h3 className="mb-4 text-sm font-semibold text-slate-700">Documents by Industry</h3>
            <div className="flex flex-wrap gap-3">
              {Object.entries(summary.by_industry).map(([industry, count]) => (
                <div key={industry} className="flex items-center gap-2 rounded-lg border border-slate-200 bg-slate-50 px-4 py-2">
                  <span className="text-sm font-medium capitalize text-slate-700">{industry}</span>
                  <span className="rounded-full bg-indigo-100 px-2 py-0.5 text-xs font-bold text-indigo-700">{count}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
