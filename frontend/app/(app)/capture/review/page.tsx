"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { FileSearch, Clock, CheckCircle2, AlertCircle, Loader2, RefreshCw } from "lucide-react";
import { captureService, type CaptureDocument } from "@/services/capture/captureService";
import { Button } from "@/components/ui/Button";

const STATUS_BADGE: Record<string, { label: string; color: string }> = {
  ready_for_review: { label: "Ready for Review", color: "bg-amber-100 text-amber-700" },
  approved: { label: "Approved", color: "bg-green-100 text-green-700" },
  rejected: { label: "Rejected", color: "bg-red-100 text-red-700" },
  draft: { label: "Draft", color: "bg-purple-100 text-purple-700" },
  failed: { label: "Failed", color: "bg-red-100 text-red-700" },
  uploaded: { label: "Processing", color: "bg-blue-100 text-blue-700" },
  preprocessing: { label: "Processing", color: "bg-blue-100 text-blue-700" },
  classifying: { label: "Processing", color: "bg-blue-100 text-blue-700" },
  extracting: { label: "Processing", color: "bg-blue-100 text-blue-700" },
  validating: { label: "Processing", color: "bg-blue-100 text-blue-700" },
};

export default function CaptureReviewQueuePage() {
  const router = useRouter();
  const [documents, setDocuments] = useState<CaptureDocument[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>("ready_for_review");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await captureService.listDocuments({ status: filter, limit: 100 });
      setDocuments(res.documents);
    } catch {
      setDocuments([]);
    } finally {
      setLoading(false);
    }
  }, [filter]);

  useEffect(() => { load(); }, [load]);

  return (
    <div className="min-h-screen w-full max-w-full overflow-x-hidden bg-slate-50 py-6 sm:py-8">
      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        <div className="mb-6 flex items-center justify-between gap-3">
          <div>
            <h1 className="text-xl sm:text-2xl font-bold text-slate-900">Review Queue</h1>
            <p className="text-xs sm:text-sm text-slate-500">Review and approve extracted document data</p>
          </div>
          <Button variant="outline" size="sm" onClick={load} className="gap-1.5 shrink-0">
            <RefreshCw size={13} /> Refresh
          </Button>
        </div>

        {/* Filter tabs */}
        <div className="mb-6 grid grid-cols-3 gap-1 rounded-xl bg-slate-200/75 p-1 border border-slate-200/80 sm:flex sm:w-fit sm:gap-2 sm:bg-transparent sm:border-0 sm:p-0">
          {[
            { key: "ready_for_review", label: "Pending Review", shortLabel: "Pending", icon: Clock },
            { key: "approved", label: "Approved", shortLabel: "Approved", icon: CheckCircle2 },
            { key: "failed", label: "Failed", shortLabel: "Failed", icon: AlertCircle },
          ].map((tab) => (
            <button
              key={tab.key}
              onClick={() => setFilter(tab.key)}
              className={`inline-flex items-center justify-center gap-1.5 rounded-lg py-2 px-1 sm:px-4 text-xs sm:text-sm font-medium transition-all ${
                filter === tab.key
                  ? "bg-indigo-600 text-white shadow-sm font-semibold"
                  : "text-slate-600 hover:text-slate-900 hover:bg-white/60 sm:bg-white sm:border sm:border-slate-200/80 sm:hover:bg-slate-100"
              }`}
            >
              <tab.icon size={14} className="shrink-0" />
              <span className="hidden sm:inline">{tab.label}</span>
              <span className="sm:hidden">{tab.shortLabel}</span>
            </button>
          ))}
        </div>

        {/* Document list */}
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 size={32} className="animate-spin text-indigo-500" />
          </div>
        ) : documents.length === 0 ? (
          <div className="flex flex-col items-center justify-center rounded-2xl border-2 border-dashed border-slate-200 bg-white py-20 text-center">
            <FileSearch size={48} className="mb-4 text-slate-300" />
            <p className="text-lg font-medium text-slate-500">No documents in this queue</p>
            <p className="mt-1 text-sm text-slate-400">Upload documents to see them here for review</p>
            <Button className="mt-4" onClick={() => router.push("/capture/upload")}>
              Upload Documents
            </Button>
          </div>
        ) : (
          <div className="space-y-3">
            {documents.map((doc) => {
              const badge = STATUS_BADGE[doc.status] || { label: doc.status, color: "bg-slate-100 text-slate-600" };
              return (
                <div
                  key={doc.id}
                  onClick={() => router.push(`/capture/review/${doc.id}`)}
                  className="group relative flex flex-col sm:flex-row sm:items-center gap-3 sm:gap-4 rounded-xl border border-slate-200 bg-white p-4 shadow-sm transition-all hover:border-indigo-200 hover:shadow-md cursor-pointer"
                >
                  <div className="flex items-start gap-3 min-w-0 flex-1">
                    <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-lg bg-slate-100 border border-slate-200/60 font-semibold">
                      {doc.file_type === "pdf" ? (
                        <span className="text-xs font-bold text-rose-600">PDF</span>
                      ) : (
                        <span className="text-xs font-bold text-sky-600 uppercase">{doc.file_type}</span>
                      )}
                    </div>

                    <div className="min-w-0 flex-1">
                      <div className="flex items-start justify-between gap-2">
                        <p className="truncate text-sm font-semibold text-slate-800 group-hover:text-indigo-600 transition-colors">
                          {doc.filename}
                        </p>
                        {/* Mobile status badge */}
                        <span className={`inline-flex sm:hidden shrink-0 rounded-full px-2.5 py-0.5 text-[11px] font-medium ${badge.color}`}>
                          {badge.label}
                        </span>
                      </div>

                      <div className="mt-1.5 flex flex-wrap items-center gap-x-2 gap-y-1.5 text-xs text-slate-500">
                        <span>{doc.page_count} page{doc.page_count > 1 ? "s" : ""}</span>
                        {doc.document_type_label && (
                          <>
                            <span className="text-slate-300">•</span>
                            <span className="rounded bg-indigo-50 px-1.5 py-0.5 text-[11px] font-medium text-indigo-700">
                              {doc.document_type_label}
                            </span>
                          </>
                        )}
                        {doc.overall_confidence !== null && (
                          <>
                            <span className="text-slate-300">•</span>
                            <span className={`font-medium ${doc.overall_confidence < 0.75 ? "text-amber-600" : "text-emerald-600"}`}>
                              {Math.round(doc.overall_confidence * 100)}% confidence
                            </span>
                          </>
                        )}
                        {doc.needs_type_confirmation && (
                          <>
                            <span className="text-slate-300">•</span>
                            <span className="rounded bg-amber-50 px-1.5 py-0.5 text-[11px] font-medium text-amber-700 border border-amber-200/60">
                              Type needs confirmation
                            </span>
                          </>
                        )}
                        {doc.duplicate_of_id && (
                          <>
                            <span className="text-slate-300">•</span>
                            <span className="rounded bg-rose-50 px-1.5 py-0.5 text-[11px] font-medium text-rose-700 border border-rose-200/60">
                              Possible duplicate
                            </span>
                          </>
                        )}
                      </div>

                      {doc.status === "failed" && doc.error_message && (
                        <p className="mt-1.5 text-xs text-rose-600 break-words line-clamp-2">{doc.error_message}</p>
                      )}
                    </div>
                  </div>

                  {/* Desktop status badge */}
                  <div className="hidden sm:flex sm:shrink-0 items-center">
                    <span className={`rounded-full px-3 py-1 text-xs font-medium ${badge.color}`}>
                      {badge.label}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
