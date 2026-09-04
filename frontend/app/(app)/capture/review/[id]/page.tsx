"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  ArrowLeft,
  CheckCircle2,
  XCircle,
  Save,
  RotateCcw,
  AlertTriangle,
  Loader2,
  FileText,
  Table2,
  ChevronLeft,
  ChevronRight,
  Database,
  Copy,
  Check,
} from "lucide-react";
import {
  captureService,
  type CaptureDocument,
  type CaptureField,
  type CaptureDocumentType,
} from "@/services/capture/captureService";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { toast } from "@/components/ui/Toaster";

export default function CaptureReviewDetailPage() {
  const params = useParams();
  const router = useRouter();
  const documentId = Number(params.id);

  const [doc, setDoc] = useState<CaptureDocument | null>(null);
  const [fields, setFields] = useState<CaptureField[]>([]);
  const [docTypes, setDocTypes] = useState<CaptureDocumentType[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [showTypeSelector, setShowTypeSelector] = useState(false);
  const [activeTab, setActiveTab] = useState<"fields" | "tables" | "ocr">("fields");
  const [copiedKey, setCopiedKey] = useState<string | null>(null);

  const copyToClipboard = async (text: string, key: string, label: string = "Copied to clipboard") => {
    if (!text) return;
    try {
      if (typeof navigator !== "undefined" && navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(text);
      } else {
        const textarea = document.createElement("textarea");
        textarea.value = text;
        textarea.style.position = "fixed";
        textarea.style.opacity = "0";
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand("copy");
        document.body.removeChild(textarea);
      }
      setCopiedKey(key);
      setTimeout(() => setCopiedKey(null), 2000);
      toast.success(label);
    } catch {
      toast.error("Failed to copy to clipboard");
    }
  };

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [detail, typesRes] = await Promise.all([
        captureService.getDocument(documentId),
        captureService.getDocumentTypes(),
      ]);
      setDoc(detail);
      setFields(detail.fields || []);
      setDocTypes(typesRes.document_types);
      if (detail.needs_type_confirmation) setShowTypeSelector(true);
    } catch {
      setDoc(null);
    } finally {
      setLoading(false);
    }
  }, [documentId]);

  useEffect(() => { load(); }, [load]);

  const handleFieldEdit = async (fieldId: number, value: string) => {
    try {
      const updated = await captureService.updateField(documentId, fieldId, value);
      setFields((prev) => prev.map((f) => (f.id === fieldId ? updated : f)));
    } catch (err) {
      console.error("Failed to update field:", err);
    }
  };

  const handleSetType = async (typeKey: string) => {
    setActionLoading(true);
    try {
      const updated = await captureService.setDocumentType(documentId, typeKey);
      setDoc(updated);
      setShowTypeSelector(false);
      await load();
    } catch (err) {
      console.error("Failed to set document type:", err);
    } finally {
      setActionLoading(false);
    }
  };

  const handleAction = async (action: "approve" | "reject" | "draft" | "retry") => {
    setActionLoading(true);
    try {
      if (action === "approve") await captureService.approveDocument(documentId);
      else if (action === "reject") await captureService.rejectDocument(documentId);
      else if (action === "draft") await captureService.saveDraft(documentId);
      else if (action === "retry") {
        await captureService.retryDocument(documentId);
        await load();
        return;
      }
      router.push("/capture/review");
    } catch (err) {
      console.error(`Failed to ${action}:`, err);
    } finally {
      setActionLoading(false);
    }
  };

  const handleExport = async () => {
    setActionLoading(true);
    try {
      const result = await captureService.exportToDataset(documentId);
      alert(`Exported ${result.field_count} fields to dataset: ${result.dataset_name}`);
    } catch (err: any) {
      console.error("Failed to export:", err);
      alert(err.message || "Failed to export to dataset");
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-50">
        <Loader2 size={32} className="animate-spin text-indigo-500" />
      </div>
    );
  }

  if (!doc) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center bg-slate-50">
        <p className="text-lg font-medium text-slate-500">Document not found</p>
        <Button className="mt-4" onClick={() => router.push("/capture/review")}>Back to Review Queue</Button>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Top bar */}
      <div className="sticky top-0 z-20 border-b border-slate-200 bg-white px-4 sm:px-6 py-3 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <button onClick={() => router.push("/capture/review")} className="text-slate-400 hover:text-slate-600 shrink-0">
              <ArrowLeft size={20} />
            </button>
            <div className="min-w-0">
              <h1 className="truncate text-sm font-semibold text-slate-800">{doc.filename}</h1>
              <p className="truncate text-xs text-slate-400">
                {doc.document_type_label || "Unclassified"} · {doc.page_count} page{doc.page_count > 1 ? "s" : ""}
                {doc.overall_confidence !== null && ` · ${Math.round(doc.overall_confidence * 100)}% confidence`}
              </p>
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            {doc.status === "failed" && (
              <Button variant="outline" size="sm" onClick={() => handleAction("retry")} disabled={actionLoading} className="gap-1.5">
                <RotateCcw size={14} /> Retry
              </Button>
            )}
            {doc.status === "ready_for_review" && (
              <>
                <Button variant="outline" size="sm" onClick={() => handleAction("draft")} disabled={actionLoading} className="gap-1.5 text-xs">
                  <Save size={14} /> Save Draft
                </Button>
                <Button variant="outline" size="sm" onClick={() => handleAction("reject")} disabled={actionLoading} className="gap-1.5 text-xs text-red-600 hover:bg-red-50">
                  <XCircle size={14} /> Reject
                </Button>
                <Button size="sm" onClick={() => handleAction("approve")} disabled={actionLoading} className="gap-1.5 text-xs bg-green-600 hover:bg-green-700">
                  <CheckCircle2 size={14} /> Approve
                </Button>
              </>
            )}
            {doc.status === "draft" && (
              <Button size="sm" onClick={() => handleAction("approve")} disabled={actionLoading} className="gap-1.5 text-xs bg-green-600 hover:bg-green-700">
                <CheckCircle2 size={14} /> Approve
              </Button>
            )}
            {doc.status === "approved" && (
              <Button size="sm" onClick={handleExport} disabled={actionLoading} className="gap-1.5 text-xs bg-indigo-600 hover:bg-indigo-700">
                {actionLoading ? <Loader2 size={14} className="animate-spin" /> : <Database size={14} />}
                Export to Dataset
              </Button>
            )}
          </div>
        </div>
      </div>

      {/* Type confirmation banner */}
      {showTypeSelector && (
        <div className="border-b border-amber-200 bg-amber-50 px-4 sm:px-6 py-3">
          <div className="flex items-center gap-2 text-sm text-amber-800">
            <AlertTriangle size={16} />
            <span className="font-medium">Document type needs confirmation.</span>
            <span>Select the correct type:</span>
          </div>
          <div className="mt-2 flex flex-wrap gap-2">
            {docTypes.map((t) => (
              <button
                key={t.key}
                onClick={() => handleSetType(t.key)}
                disabled={actionLoading}
                className="rounded-lg border border-amber-300 bg-white px-3 py-1.5 text-xs font-medium text-slate-700 hover:border-indigo-400 hover:bg-indigo-50 disabled:opacity-50"
              >
                {t.label}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Duplicate warning */}
      {doc.duplicate_of_id && (
        <div className="border-b border-orange-200 bg-orange-50 px-4 sm:px-6 py-2 text-sm text-orange-800">
          <AlertTriangle size={14} className="mr-1.5 inline" />
          This document may be a duplicate of document #{doc.duplicate_of_id}. Please verify before approving.
        </div>
      )}

      {/* 3-panel layout */}
      <div className="grid grid-cols-1 gap-0 lg:grid-cols-[1fr_1fr_1fr]" style={{ minHeight: "calc(100vh - 60px)" }}>
        {/* Left: Original document */}
        <div className="border-r border-slate-200 bg-slate-100 p-4">
          <h3 className="mb-3 text-xs font-semibold uppercase tracking-wide text-slate-400">Original Document</h3>
          <div className="flex items-center justify-center rounded-lg border border-slate-200 bg-white p-4" style={{ minHeight: "400px" }}>
            {doc.file_type === "pdf" ? (
              <div className="flex flex-col items-center text-slate-400">
                <FileText size={48} />
                <p className="mt-2 text-sm">PDF · {doc.page_count} page{doc.page_count > 1 ? "s" : ""}</p>
                <p className="text-xs text-slate-300">Preview not available in this view</p>
              </div>
            ) : (
              <div className="flex flex-col items-center text-slate-400">
                <FileText size={48} />
                <p className="mt-2 text-sm capitalize">{doc.file_type} image</p>
                <p className="text-xs text-slate-300">Preview not available in this view</p>
              </div>
            )}
          </div>
          {doc.raw_ocr_text && (
            <div className="mt-4">
              <div className="mb-2 flex items-center justify-between">
                <h4 className="text-xs font-semibold uppercase tracking-wide text-slate-400">Raw OCR Text</h4>
                <button
                  type="button"
                  onClick={() => copyToClipboard(doc.raw_ocr_text || "", "raw-ocr-left", "OCR text copied to clipboard")}
                  className="rounded p-1 text-slate-400 hover:bg-slate-200 hover:text-slate-700 transition-colors"
                  title="Copy raw OCR text"
                  aria-label="Copy raw OCR text"
                >
                  {copiedKey === "raw-ocr-left" ? (
                    <Check size={13} className="text-emerald-600" />
                  ) : (
                    <Copy size={13} />
                  )}
                </button>
              </div>
              <pre className="max-h-64 overflow-y-auto whitespace-pre-wrap rounded-lg border border-slate-200 bg-white p-3 text-xs text-slate-600 font-mono">
                {doc.raw_ocr_text}
              </pre>
            </div>
          )}
        </div>

        {/* Center: Extracted data summary */}
        <div className="border-r border-slate-200 bg-white p-4">
          <div className="mb-3 flex items-center gap-2">
            <h3 className="text-xs font-semibold uppercase tracking-wide text-slate-400">Extracted Data</h3>
            <div className="flex gap-1 ml-auto">
              <button
                onClick={() => setActiveTab("fields")}
                className={`rounded px-2 py-1 text-xs font-medium ${activeTab === "fields" ? "bg-indigo-100 text-indigo-700" : "text-slate-400 hover:text-slate-600"}`}
              >
                Fields
              </button>
              <button
                onClick={() => setActiveTab("tables")}
                className={`rounded px-2 py-1 text-xs font-medium ${activeTab === "tables" ? "bg-indigo-100 text-indigo-700" : "text-slate-400 hover:text-slate-600"}`}
              >
                Tables
              </button>
              <button
                onClick={() => setActiveTab("ocr")}
                className={`rounded px-2 py-1 text-xs font-medium ${activeTab === "ocr" ? "bg-indigo-100 text-indigo-700" : "text-slate-400 hover:text-slate-600"}`}
              >
                OCR
              </button>
            </div>
          </div>

          {activeTab === "fields" && (
            <div className="space-y-2">
              <div className="flex items-center justify-between pb-1">
                <span className="text-xs text-slate-400">
                  {fields.length} {fields.length === 1 ? "field" : "fields"}
                </span>
                {fields.length > 0 && (
                  <button
                    type="button"
                    onClick={() => {
                      const text = fields
                        .filter((f) => f.value)
                        .map((f) => `${f.field_label}: ${f.value}`)
                        .join("\n");
                      copyToClipboard(text, "all-fields", "All fields copied to clipboard");
                    }}
                    className="rounded p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-700 transition-colors"
                    title="Copy all fields"
                    aria-label="Copy all fields"
                  >
                    {copiedKey === "all-fields" ? (
                      <Check size={13} className="text-emerald-600" />
                    ) : (
                      <Copy size={13} />
                    )}
                  </button>
                )}
              </div>

              {fields.length === 0 ? (
                <p className="text-sm text-slate-400">No fields extracted.</p>
              ) : (
                fields.map((field) => (
                  <div key={field.id} className="group rounded-lg border border-slate-100 bg-slate-50 p-3 hover:border-slate-200 transition-colors">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-medium text-slate-500">{field.field_label}</span>
                      <div className="flex items-center gap-1.5">
                        {field.is_low_confidence && (
                          <span className="rounded-full bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-700">
                            Low confidence
                          </span>
                        )}
                        {field.was_corrected && (
                          <span className="rounded-full bg-blue-100 px-2 py-0.5 text-xs font-medium text-blue-700">
                            Corrected
                          </span>
                        )}
                        {!field.is_valid && (
                          <span className="rounded-full bg-red-100 px-2 py-0.5 text-xs font-medium text-red-700">
                            Invalid
                          </span>
                        )}
                        <span className={`text-xs font-bold ${
                          field.confidence_score >= 0.75 ? "text-green-600" :
                          field.confidence_score >= 0.5 ? "text-amber-600" : "text-red-600"
                        }`}>
                          {Math.round(field.confidence_score * 100)}%
                        </span>
                        {field.value && (
                          <button
                            type="button"
                            onClick={() => copyToClipboard(field.value || "", `field-${field.id}`, `Copied ${field.field_label}`)}
                            className="ml-1 rounded p-1 text-slate-400 hover:bg-slate-200 hover:text-slate-700 transition-colors"
                            title={`Copy ${field.field_label}`}
                            aria-label={`Copy ${field.field_label}`}
                          >
                            {copiedKey === `field-${field.id}` ? (
                              <Check size={13} className="text-emerald-600" />
                            ) : (
                              <Copy size={13} />
                            )}
                          </button>
                        )}
                      </div>
                    </div>
                    <div className="mt-1 flex items-start justify-between gap-2">
                      <p className={`text-sm ${field.value ? "text-slate-800 font-medium" : "text-slate-300 italic"}`}>
                        {field.value || "Not extracted"}
                      </p>
                    </div>
                    {field.validation_message && (
                      <p className="mt-1 text-xs text-amber-600">{field.validation_message}</p>
                    )}
                  </div>
                ))
              )}
            </div>
          )}

          {activeTab === "tables" && (
            <div className="space-y-4">
              {doc.extracted_tables && doc.extracted_tables.length > 0 ? (
                doc.extracted_tables.map((table: any, idx: number) => (
                  <div key={idx} className="rounded-lg border border-slate-200 overflow-hidden">
                    <div className="bg-slate-50 px-3 py-2 text-xs font-medium text-slate-500 flex items-center justify-between">
                      <div>
                        <Table2 size={12} className="mr-1 inline" />
                        Page {table.page} · {table.row_count} rows · {table.estimated_columns} columns
                      </div>
                      <button
                        type="button"
                        onClick={() => {
                          const headers = (table.headers || []).join("\t");
                          const rows = (table.rows || []).map((r: any[]) => r.join("\t")).join("\n");
                          const tsv = headers ? `${headers}\n${rows}` : rows;
                          copyToClipboard(tsv, `table-${idx}`, "Table data copied to clipboard (TSV)");
                        }}
                        className="rounded p-1 text-slate-400 hover:bg-slate-200 hover:text-slate-700 transition-colors"
                        title="Copy table data (TSV)"
                        aria-label="Copy table data (TSV)"
                      >
                        {copiedKey === `table-${idx}` ? (
                          <Check size={13} className="text-emerald-600" />
                        ) : (
                          <Copy size={13} />
                        )}
                      </button>
                    </div>
                    <div className="overflow-x-auto">
                      <table className="w-full text-xs">
                        {table.headers && table.headers.length > 0 && (
                          <thead>
                            <tr className="border-b border-slate-200 bg-white">
                              {table.headers.map((h: string, i: number) => (
                                <th key={i} className="px-2 py-1.5 text-left font-semibold text-slate-600">{h}</th>
                              ))}
                            </tr>
                          </thead>
                        )}
                        <tbody>
                          {table.rows.map((row: string[], ri: number) => (
                            <tr key={ri} className="border-b border-slate-100">
                              {row.map((cell, ci) => (
                                <td key={ci} className="px-2 py-1.5 text-slate-700">{cell}</td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                ))
              ) : (
                <p className="text-sm text-slate-400">No tables detected.</p>
              )}
            </div>
          )}

          {activeTab === "ocr" && (
            <div className="space-y-2">
              <div className="flex items-center justify-between pb-1">
                <span className="text-xs text-slate-400">
                  {doc.raw_ocr_text
                    ? `${doc.raw_ocr_text.split("\n").map((l: string) => l.trim()).filter(Boolean).length} items detected`
                    : "Extracted OCR text"}
                </span>
                {doc.raw_ocr_text && (
                  <button
                    type="button"
                    onClick={() => copyToClipboard(doc.raw_ocr_text || "", "ocr-all", "All OCR text copied to clipboard")}
                    className="rounded p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-700 transition-colors"
                    title="Copy all OCR text"
                    aria-label="Copy all OCR text"
                  >
                    {copiedKey === "ocr-all" ? (
                      <Check size={13} className="text-emerald-600" />
                    ) : (
                      <Copy size={13} />
                    )}
                  </button>
                )}
              </div>

              {!doc.raw_ocr_text ? (
                <p className="text-sm text-slate-400">No OCR text available.</p>
              ) : (
                <div className="max-h-[600px] overflow-y-auto space-y-1.5 pr-1">
                  {doc.raw_ocr_text
                    .split("\n")
                    .map((line: string) => line.trim())
                    .filter((line: string) => line.length > 0)
                    .map((line: string, idx: number) => (
                      <div
                        key={idx}
                        className="group flex items-center justify-between gap-3 rounded-lg border border-slate-100 bg-slate-50 px-3 py-2 hover:border-slate-200 hover:bg-slate-100/60 transition-colors"
                      >
                        <span className="font-mono text-xs text-slate-800 break-words flex-1">
                          {line}
                        </span>
                        <button
                          type="button"
                          onClick={() => copyToClipboard(line, `ocr-item-${idx}`, "Copied")}
                          className="shrink-0 rounded p-1 text-slate-400 hover:bg-white hover:text-slate-700 transition-colors"
                          title="Copy"
                          aria-label="Copy"
                        >
                          {copiedKey === `ocr-item-${idx}` ? (
                            <Check size={13} className="text-emerald-600" />
                          ) : (
                            <Copy size={13} />
                          )}
                        </button>
                      </div>
                    ))}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Right: Editable form */}
        <div className="bg-white p-4">
          <h3 className="mb-3 text-xs font-semibold uppercase tracking-wide text-slate-400">Editable Form</h3>
          <div className="space-y-3">
            {fields.length === 0 ? (
              <p className="text-sm text-slate-400">No fields to edit.</p>
            ) : (
              fields.map((field) => (
                <div key={field.id}>
                  <div className="mb-1 flex items-center justify-between">
                    <label className="block text-xs font-medium text-slate-600">
                      {field.field_label}
                      {field.is_low_confidence && <span className="ml-1.5 text-amber-500">⚠</span>}
                    </label>
                    {field.value && (
                      <button
                        type="button"
                        onClick={() => copyToClipboard(field.value || "", `edit-field-${field.id}`, `Copied ${field.field_label}`)}
                        className="rounded p-0.5 text-slate-400 hover:bg-slate-100 hover:text-slate-700 transition-colors"
                        title={`Copy ${field.field_label}`}
                      >
                        {copiedKey === `edit-field-${field.id}` ? (
                          <Check size={12} className="text-emerald-600" />
                        ) : (
                          <Copy size={12} />
                        )}
                      </button>
                    )}
                  </div>
                  <Input
                    defaultValue={field.value || ""}
                    onBlur={(e) => {
                      if (e.target.value !== field.value) {
                        handleFieldEdit(field.id, e.target.value);
                      }
                    }}
                    className={`text-sm ${field.is_low_confidence ? "border-amber-300" : ""} ${!field.is_valid ? "border-red-300" : ""}`}
                  />
                  {field.validation_message && (
                    <p className="mt-0.5 text-xs text-amber-600">{field.validation_message}</p>
                  )}
                </div>
              ))
            )}
          </div>

          {fields.length > 0 && (
            <div className="mt-6 rounded-lg bg-slate-50 p-3">
              <p className="text-xs text-slate-500">
                <strong>Tip:</strong> Edit any field above and click outside to save. Low-confidence fields are highlighted in amber. The system learns from your corrections to improve future extractions.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
