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
    <div className="min-h-screen bg-slate-50 py-8">
      <div className="mx-auto max-w-6xl px-6">
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Review Queue</h1>
            <p className="text-sm text-slate-500">Review and approve extracted document data</p>
          </div>
          <Button variant="outline" size="sm" onClick={load} className="gap-2">
            <RefreshCw size={14} /> Refresh
          </Button>
        </div>

        {/* Filter tabs */}
        <div className="mb-6 flex gap-2">
          {[
            { key: "ready_for_review", label: "Pending Review", icon: Clock },
            { key: "approved", label: "Approved", icon: CheckCircle2 },
            { key: "failed", label: "Failed", icon: AlertCircle },
          ].map((tab) => (
            <button
              key={tab.key}
              onClick={() => setFilter(tab.key)}
              className={`inline-flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition-colors ${
                filter === tab.key ? "bg-indigo-600 text-white" : "bg-white text-slate-600 hover:bg-slate-100"
              }`}
            >
              <tab.icon size={16} />
              {tab.label}
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
                  className="group flex cursor-pointer items-center gap-4 rounded-xl border border-slate-200 bg-white p-4 shadow-sm transition-all hover:-translate-y-0.5 hover:shadow-md"
                >
                  <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-lg bg-slate-100">
                    {doc.file_type === "pdf" ? (
                      <span className="text-xs font-bold text-red-500">PDF</span>
                    ) : (
                      <span className="text-xs font-bold text-blue-500 uppercase">{doc.file_type}</span>
                    )}
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-medium text-slate-800">{doc.filename}</p>
                    <div className="mt-1 flex items-center gap-3 text-xs text-slate-400">
                      <span>{doc.page_count} page{doc.page_count > 1 ? "s" : ""}</span>
                      {doc.document_type_label && (
                        <span className="font-medium text-indigo-600">{doc.document_type_label}</span>
                      )}
                      {doc.overall_confidence !== null && (
                        <span className={doc.overall_confidence < 0.75 ? "text-amber-600" : "text-green-600"}>
                          {Math.round(doc.overall_confidence * 100)}% confidence
                        </span>
                      )}
                      {doc.needs_type_confirmation && (
                        <span className="text-amber-600 font-medium">Type needs confirmation</span>
                      )}
                      {doc.duplicate_of_id && (
                        <span className="text-orange-600 font-medium">Possible duplicate</span>
                      )}
                    </div>
                    {doc.status === "failed" && doc.error_message && (
                      <p className="mt-1 truncate text-xs text-red-500">{doc.error_message}</p>
                    )}
                  </div>
                  <span className={`shrink-0 rounded-full px-3 py-1 text-xs font-medium ${badge.color}`}>
                    {badge.label}
                  </span>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
