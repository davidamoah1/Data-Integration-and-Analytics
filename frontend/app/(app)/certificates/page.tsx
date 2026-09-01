"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  Award,
  Upload,
  Search,
  Download,
  FileText,
  CheckCircle2,
  Clock,
  AlertCircle,
  XCircle,
  ShieldCheck,
  Loader2,
  FileCheck,
  BarChart3,
  ArrowRight,
  Filter,
  X,
  Presentation,
  RefreshCw,
  ScanLine,
  Eye,
} from "lucide-react";
import { certificateService, type CertificateDashboard, type Certificate } from "@/services/certificates/certificateService";
import { Button } from "@/components/ui/Button";
import { CertificateDetail } from "@/components/certificates/CertificateDetail";
import { toast } from "@/components/ui/Toaster";

const STATUS_LABELS: Record<string, string> = {
  uploaded: "Uploaded",
  preprocessing: "Preprocessing",
  extracting: "Extracting",
  classifying: "Classifying",
  validating: "Validating",
  ready_for_review: "Ready for Review",
  approved: "Approved",
  rejected: "Rejected",
  draft: "Draft",
  failed: "Failed",
};

const STATUS_COLORS: Record<string, string> = {
  uploaded: "bg-slate-100 text-slate-600",
  preprocessing: "bg-blue-100 text-blue-700",
  extracting: "bg-blue-100 text-blue-700",
  classifying: "bg-blue-100 text-blue-700",
  validating: "bg-blue-100 text-blue-700",
  ready_for_review: "bg-amber-100 text-amber-700",
  approved: "bg-green-100 text-green-700",
  rejected: "bg-red-100 text-red-700",
  draft: "bg-purple-100 text-purple-700",
  failed: "bg-red-100 text-red-700",
};

const VERIFICATION_LABELS: Record<string, string> = {
  not_verified: "Not Verified",
  extraction_complete: "Extraction Complete",
  verification_pending: "Verification Pending",
  verified: "Verified",
  verification_failed: "Verification Failed",
  unable_to_verify: "Unable to Verify",
  suspicious: "Suspicious",
};

const VERIFICATION_COLORS: Record<string, string> = {
  not_verified: "bg-slate-100 text-slate-600",
  extraction_complete: "bg-blue-100 text-blue-700",
  verification_pending: "bg-amber-100 text-amber-700",
  verified: "bg-green-100 text-green-700",
  verification_failed: "bg-red-100 text-red-700",
  unable_to_verify: "bg-slate-100 text-slate-600",
  suspicious: "bg-orange-100 text-orange-700",
};

const PROCESSING_STATUSES = ["uploaded", "preprocessing", "extracting", "classifying", "validating"];
const MAX_FILE_SIZE = 20 * 1024 * 1024;
const POLL_INTERVAL = 3000;
const MAX_POLL_ATTEMPTS = 40; // 40 * 3s = 120s max
const MAX_CONSECUTIVE_FAILURES = 5; // Stop after 5 consecutive network errors

interface UploadResultItem {
  id?: number;
  filename: string;
  file_type?: string;
  file_size?: number;
  status: string;
  error_message?: string | null;
  document_type?: string | null;
  document_type_label?: string | null;
  overall_confidence?: number | null;
  is_duplicate?: boolean;
  verification_status?: string;
  verification_reason?: string | null;
}

function formatFileSize(bytes?: number): string {
  if (!bytes) return "—";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function getFileExtension(filename: string): string {
  const match = filename.match(/\.(\w+)$/);
  return match ? match[1].toUpperCase() : "—";
}

function validateFile(file: File): string | null {
  const ext = file.name.match(/\.(\w+)$/)?.[1]?.toLowerCase();
  if (!ext || !["pdf", "jpg", "jpeg", "png"].includes(ext)) {
    return `Unsupported file type: .${ext || "unknown"}. Only PDF, JPG, JPEG, PNG are accepted.`;
  }
  if (file.size > MAX_FILE_SIZE) {
    return `File is too large (${formatFileSize(file.size)}). Maximum size is ${formatFileSize(MAX_FILE_SIZE)}.`;
  }
  if (file.size === 0) {
    return "File is empty or corrupted.";
  }
  return null;
}

function getErrorMessage(err: unknown): string {
  const e = err as { status?: number; message?: string; data?: any };
  if (e?.status) {
    // For 500 errors, prefer the actual server message if available
    if (e.status === 500) {
      const detail = e?.data?.detail || e?.data?.message;
      return detail || "Server error — please try again later.";
    }
    switch (e.status) {
      case 400: return "Bad request — the server could not process the file.";
      case 401: return "Authentication required — please log in again.";
      case 403: return "You do not have permission to perform this action.";
      case 404: return "Certificate not found — it may have been deleted.";
      case 413: return "File is too large — please upload a smaller file.";
      case 422: return "Validation error — the file format is not supported.";
      case 429: return "Too many requests — please wait and try again.";
      case 502:
      case 503:
      case 504: return "Backend service unavailable — please try again later.";
    }
  }
  if (e?.message?.includes("Network") || e?.message?.includes("fetch")) {
    return "Network error — unable to connect to the server.";
  }
  return e?.message || "An unexpected error occurred.";
}

export default function CertificateIntelligencePage() {
  const [dashboard, setDashboard] = useState<CertificateDashboard | null>(null);
  const [certificates, setCertificates] = useState<Certificate[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [filterType, setFilterType] = useState("");
  const [filterStatus, setFilterStatus] = useState("");
  const [filterVerification, setFilterVerification] = useState("");
  const [uploadResults, setUploadResults] = useState<UploadResultItem[] | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [currentBatchId, setCurrentBatchId] = useState<number | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [selectedCertId, setSelectedCertId] = useState<number | null>(null);
  const [pollingIds, setPollingIds] = useState<Set<number>>(new Set());
  const pollAttemptsRef = useRef<Map<number, number>>(new Map());
  const pollFailuresRef = useRef<Map<number, number>>(new Map());
  const uploadResultsRef = useRef<UploadResultItem[] | null>(null);

  const loadData = useCallback(async () => {
    try {
      const [dash, search] = await Promise.all([
        certificateService.getDashboard(),
        certificateService.search({ limit: 100 }),
      ]);
      setDashboard(dash);
      setCertificates(search.certificates);
    } catch (err) {
      setCertificates([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    // Reset current batch state on page load/refresh
    setUploadResults(null);
    setUploadError(null);
    setCurrentBatchId(null);
    loadData();
  }, [loadData]);

  // Poll for processing status updates with timeout and error handling
  useEffect(() => {
    if (pollingIds.size === 0) return;

    const interval = setInterval(async () => {
      const ids = Array.from(pollingIds);
      const stillProcessing = new Set<number>();

      for (const id of ids) {
        // Check max attempts (timeout)
        const attempts = (pollAttemptsRef.current.get(id) || 0) + 1;
        pollAttemptsRef.current.set(id, attempts);

        if (attempts >= MAX_POLL_ATTEMPTS) {
          // Timeout — mark as timed out
          setUploadResults((prev) =>
            prev?.map((r) =>
              r.id === id
                ? { ...r, status: "failed", error_message: "Certificate processing is taking longer than expected. The server may be overloaded or the OCR engine may be unavailable." }
                : r
            ) || prev
          );
          toast.error(`Certificate processing timed out after ${Math.round(MAX_POLL_ATTEMPTS * POLL_INTERVAL / 1000)}s`);
          pollAttemptsRef.current.delete(id);
          pollFailuresRef.current.delete(id);
          continue;
        }

        try {
          const cert = await certificateService.getStatus(id);
          if (cert) {
            // Reset failure counter on successful response
            pollFailuresRef.current.set(id, 0);

            setUploadResults((prev) =>
              prev?.map((r) =>
                r.id === id
                  ? { ...r, status: cert.status, document_type: cert.document_type, document_type_label: cert.document_type_label, overall_confidence: cert.overall_confidence, error_message: cert.error_message }
                  : r
              ) || prev
            );
            if (PROCESSING_STATUSES.includes(cert.status)) {
              stillProcessing.add(id);
            } else {
              await loadData();
              if (cert.status === "ready_for_review") {
                const filename = uploadResultsRef.current?.find((r) => r.id === id)?.filename || "Certificate";
                toast.success(`Certificate "${filename}" extracted successfully`);
              } else if (cert.status === "failed") {
                const filename = uploadResultsRef.current?.find((r) => r.id === id)?.filename || "Certificate";
                toast.error(`Certificate "${filename}" processing failed: ${cert.error_message || "Unknown error"}`);
              }
              pollAttemptsRef.current.delete(id);
              pollFailuresRef.current.delete(id);
            }
          }
        } catch (err) {
          // Track consecutive failures (backend unreachable)
          const failures = (pollFailuresRef.current.get(id) || 0) + 1;
          pollFailuresRef.current.set(id, failures);

          if (failures >= MAX_CONSECUTIVE_FAILURES) {
            // Backend appears to be down — stop polling and show error
            setUploadResults((prev) =>
              prev?.map((r) =>
                r.id === id
                  ? { ...r, status: "failed", error_message: "Unable to reach the server. The backend may be down or restarting. Please try again later." }
                  : r
              ) || prev
            );
            toast.error("Server unreachable — certificate processing status check failed");
            pollAttemptsRef.current.delete(id);
            pollFailuresRef.current.delete(id);
          } else {
            stillProcessing.add(id);
          }
        }
      }

      setPollingIds(stillProcessing);
    }, POLL_INTERVAL);

    return () => clearInterval(interval);
  }, [pollingIds, loadData]);

  useEffect(() => {
    uploadResultsRef.current = uploadResults;
  }, [uploadResults]);

  const loadDetail = useCallback((id: number) => {
    setSelectedCertId(id);
  }, []);

  const handleSearch = useCallback(async () => {
    setLoading(true);
    try {
      const result = await certificateService.search({
        q: searchQuery || undefined,
        certificate_type: filterType || undefined,
        review_status: filterStatus || undefined,
        verification_status: filterVerification || undefined,
        limit: 100,
      });
      setCertificates(result.certificates);
    } catch (err) {
      setCertificates([]);
      toast.error(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, [searchQuery, filterType, filterStatus, filterVerification]);

  const handleClearFilters = useCallback(() => {
    setSearchQuery("");
    setFilterType("");
    setFilterStatus("");
    setFilterVerification("");
    setLoading(true);
    certificateService.search({ limit: 100 }).then((result) => {
      setCertificates(result.certificates);
    }).catch(() => {
      setCertificates([]);
    }).finally(() => {
      setLoading(false);
    });
  }, []);

  const handleNewBatch = useCallback(() => {
    setUploadResults(null);
    setUploadError(null);
    setCurrentBatchId(null);
    setPollingIds(new Set());
    pollAttemptsRef.current.clear();
    pollFailuresRef.current.clear();
  }, []);

  const handleUpload = useCallback(async (files: File[]) => {
    if (files.length === 0) return;

    const validationErrors: { filename: string; error: string }[] = [];
    const validFiles: File[] = [];

    for (const file of files) {
      const error = validateFile(file);
      if (error) {
        validationErrors.push({ filename: file.name, error });
      } else {
        validFiles.push(file);
      }
    }

    if (validationErrors.length > 0) {
      setUploadError(`${validationErrors.length} file(s) rejected: ${validationErrors[0].error}`);
      if (validFiles.length === 0) return;
    } else {
      setUploadError(null);
    }

    setUploading(true);
    setUploadResults(null);
    setUploadError(null);
    setCurrentBatchId(null);
    try {
      const result = await certificateService.upload(
        validFiles,
        `Certificate Batch ${new Date().toLocaleDateString()}`
      );

      setCurrentBatchId(result.batch_id);

      const results: UploadResultItem[] = result.certificates.map((c: any) => ({
        id: c.id,
        filename: c.filename || "Unknown",
        file_type: getFileExtension(c.filename || ""),
        file_size: validFiles.find((f) => f.name === c.filename)?.size,
        status: c.status || "uploaded",
        error_message: c.error_message,
        document_type: c.document_type,
        document_type_label: c.document_type_label,
        overall_confidence: c.overall_confidence,
        is_duplicate: c.is_duplicate || false,
        verification_status: c.verification_status,
        verification_reason: c.verification_reason,
      }));

      setUploadResults(results);

      const idsToPoll = new Set(
        results
          .filter((r) => r.id && PROCESSING_STATUSES.includes(r.status))
          .map((r) => r.id!)
      );
      if (idsToPoll.size > 0) {
        // Reset polling counters
        idsToPoll.forEach((id) => {
          pollAttemptsRef.current.set(id, 0);
          pollFailuresRef.current.set(id, 0);
        });
        setPollingIds(idsToPoll);
      }

      // Refresh dashboard + certificate list to include newly uploaded certs
      await loadData();
    } catch (err) {
      setUploadError(getErrorMessage(err));
      setUploadResults([
        { filename: "Upload failed", status: "failed", error_message: getErrorMessage(err) },
      ]);
    } finally {
      setUploading(false);
    }
  }, [loadData]);

  const handleFileSelect = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const files = Array.from(e.target.files || []);
      if (files.length > 0) handleUpload(files);
      e.target.value = "";
    },
    [handleUpload]
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragOver(false);
      const files = Array.from(e.dataTransfer.files).filter((f) =>
        /\.(pdf|jpg|jpeg|png)$/i.test(f.name)
      );
      if (files.length === 0) {
        setUploadError("No valid files. Only PDF, JPG, JPEG, PNG are accepted.");
        return;
      }
      handleUpload(files);
    },
    [handleUpload]
  );

  const handleRetryUpload = () => {
    setUploadError(null);
    setUploadResults(null);
    setCurrentBatchId(null);
    fileInputRef.current?.click();
  };

  const stats = dashboard
    ? [
        { label: "Total Certificates", value: dashboard.total, icon: FileText, color: "text-blue-600 bg-blue-50" },
        { label: "Pending Review", value: dashboard.review_required, icon: Clock, color: "text-amber-600 bg-amber-50" },
        { label: "Approved", value: dashboard.approved, icon: CheckCircle2, color: "text-green-600 bg-green-50" },
        { label: "Failed", value: dashboard.failed, icon: AlertCircle, color: "text-red-600 bg-red-50" },
        { label: "Verified", value: dashboard.verified, icon: ShieldCheck, color: "text-emerald-600 bg-emerald-50" },
        { label: "Duplicates", value: dashboard.duplicates, icon: FileCheck, color: "text-purple-600 bg-purple-50" },
      ]
    : [];

  return (
    <div className="min-h-screen bg-slate-50 py-8">
      <div className="mx-auto max-w-7xl px-4 sm:px-6">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-indigo-600 text-white shadow-lg shadow-indigo-600/20">
              <Award size={24} />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-slate-900">Certificate Intelligence</h1>
              <p className="text-sm text-slate-500">
                Upload certificates and automatically extract, validate, and analyze certificate data
              </p>
            </div>
          </div>
        </div>

        {/* Stats */}
        <div className="mb-8 grid grid-cols-2 gap-3 sm:gap-4 sm:grid-cols-3 lg:grid-cols-6">
          {stats.map((stat) => (
            <div key={stat.label} className="rounded-xl border border-slate-200 bg-white p-3 sm:p-4 shadow-sm">
              <div className={`mb-2 inline-flex h-8 w-8 items-center justify-center rounded-lg ${stat.color}`}>
                <stat.icon size={16} />
              </div>
              <div className="text-xl sm:text-2xl font-bold text-slate-900">{stat.value}</div>
              <div className="text-xs text-slate-500">{stat.label}</div>
            </div>
          ))}
        </div>

        {/* Upload Area */}
        <div className="mb-8">
          <div
            onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`cursor-pointer rounded-xl border-2 border-dashed p-6 sm:p-8 text-center transition-colors ${
              dragOver ? "border-indigo-500 bg-indigo-50" : "border-slate-300 bg-white hover:border-indigo-400"
            }`}
            role="button"
            tabIndex={0}
            aria-label="Upload certificates"
            onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") fileInputRef.current?.click(); }}
          >
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept=".pdf,.jpg,.jpeg,.png"
              onChange={handleFileSelect}
              className="hidden"
            />
            {uploading ? (
              <div className="flex flex-col items-center gap-3">
                <Loader2 className="h-8 w-8 animate-spin text-indigo-600" />
                <p className="text-sm font-medium text-slate-700">Processing certificates...</p>
                <p className="text-xs text-slate-500">This may take a moment while we extract and classify your documents</p>
              </div>
            ) : (
              <div className="flex flex-col items-center gap-3">
                <div className="flex h-12 w-12 items-center justify-center rounded-full bg-indigo-100">
                  <Upload className="h-6 w-6 text-indigo-600" />
                </div>
                <div>
                  <p className="text-sm font-medium text-slate-700">
                    Drag and drop certificates here, or click to browse
                  </p>
                  <p className="text-xs text-slate-500 mt-1">
                    Supports PDF, JPG, JPEG, PNG — up to 50 files per batch (max {formatFileSize(MAX_FILE_SIZE)} per file)
                  </p>
                </div>
              </div>
            )}
          </div>

          {/* Upload Error */}
          {uploadError && (
            <div className="mt-4 rounded-xl border border-red-200 bg-red-50 p-4">
              <div className="flex items-start gap-2">
                <AlertCircle className="h-5 w-5 text-red-600 flex-shrink-0 mt-0.5" />
                <div className="flex-1">
                  <p className="text-sm font-medium text-red-900">Upload Error</p>
                  <p className="text-sm text-red-700 mt-0.5">{uploadError}</p>
                </div>
                <button onClick={() => setUploadError(null)} className="text-red-400 hover:text-red-600" aria-label="Dismiss error">
                  <X size={16} />
                </button>
              </div>
              <div className="mt-3">
                <Button onClick={handleRetryUpload} variant="outline" size="sm">
                  <Upload size={14} className="mr-2" /> Upload Another Certificate
                </Button>
              </div>
            </div>
          )}

          {/* New Batch Button */}
          {uploadResults && !uploading && (
            <div className="mt-3 flex items-center justify-between">
              <div className="text-xs text-slate-500">
                {currentBatchId && `Batch #${currentBatchId} — `}
                {uploadResults.length} certificate{uploadResults.length !== 1 ? "s" : ""} in current batch
              </div>
              <Button onClick={handleNewBatch} variant="outline" size="sm">
                <Upload size={14} className="mr-1.5" /> New Batch
              </Button>
            </div>
          )}

          {/* Upload Results */}
          {uploadResults && (
            <div className="mt-4 rounded-xl border border-slate-200 bg-white p-4">
              <div className="mb-3 flex items-center justify-between">
                <h3 className="text-sm font-semibold text-slate-900">Upload Results</h3>
                <button
                  onClick={() => { setUploadResults(null); setUploadError(null); }}
                  className="text-slate-400 hover:text-slate-600"
                  aria-label="Dismiss upload results"
                >
                  <X size={16} />
                </button>
              </div>
              <div className="space-y-2 max-h-80 overflow-y-auto">
                {uploadResults.map((r, i) => {
                  const isProcessing = PROCESSING_STATUSES.includes(r.status);
                  const isReady = r.status === "ready_for_review";
                  const isFailed = r.status === "failed";

                  return (
                    <div key={i} className="rounded-lg bg-slate-50 p-3">
                      <div className="flex items-center justify-between gap-2">
                        <div className="flex items-center gap-2 min-w-0 flex-1">
                          {isProcessing ? (
                            <Loader2 className="h-4 w-4 text-blue-600 animate-spin flex-shrink-0" />
                          ) : isFailed ? (
                            <XCircle className="h-4 w-4 text-red-500 flex-shrink-0" />
                          ) : isReady ? (
                            <CheckCircle2 className="h-4 w-4 text-green-500 flex-shrink-0" />
                          ) : (
                            <FileText className="h-4 w-4 text-slate-400 flex-shrink-0" />
                          )}
                          <span className="text-sm text-slate-700 truncate">{r.filename}</span>
                        </div>
                        <span className={`text-xs font-medium px-2 py-0.5 rounded-full flex-shrink-0 ${
                          STATUS_COLORS[r.status] || "bg-slate-100 text-slate-600"
                        }`}>
                          {STATUS_LABELS[r.status] || r.status}
                        </span>
                      </div>

                      <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-slate-500">
                        <span>Type: {r.file_type || getFileExtension(r.filename)}</span>
                        <span>Size: {formatFileSize(r.file_size)}</span>
                        {r.is_duplicate && <span className="text-purple-600 font-medium">Duplicate</span>}
                        {r.document_type_label && <span>Classified as: {r.document_type_label}</span>}
                        {r.overall_confidence != null && <span>Confidence: {(r.overall_confidence * 100).toFixed(0)}%</span>}
                      </div>

                      {r.error_message && (
                        <div className="mt-2 text-xs text-red-600 bg-red-50 rounded p-2">{r.error_message}</div>
                      )}

                      {r.verification_status && r.verification_reason && (
                        <div className="mt-1 text-xs text-slate-500 bg-slate-50 rounded p-1.5">
                          <span className="font-medium">{VERIFICATION_LABELS[r.verification_status] || r.verification_status}:</span> {r.verification_reason}
                        </div>
                      )}

                      <div className="mt-3 flex flex-col sm:flex-row gap-2">
                        {isProcessing && (
                          <div className="flex flex-col gap-1.5 text-xs text-blue-600 w-full">
                            <div className="flex items-center gap-1.5">
                              <Loader2 size={12} className="animate-spin" />
                              <span>Processing certificate... Please wait.</span>
                            </div>
                            <div className="flex items-center gap-2 pl-5 text-slate-500">
                              <span className={r.status === "uploaded" || r.status === "preprocessing" ? "text-blue-600 font-medium" : "text-green-600"}>
                                {r.status === "uploaded" || r.status === "preprocessing" ? "⏳" : "✓"} Uploading
                              </span>
                              <span className="text-slate-300">→</span>
                              <span className={r.status === "extracting" ? "text-blue-600 font-medium" : PROCESSING_STATUSES.indexOf(r.status) > PROCESSING_STATUSES.indexOf("extracting") ? "text-green-600" : "text-slate-400"}>
                                {r.status === "extracting" ? "⏳" : PROCESSING_STATUSES.indexOf(r.status) > PROCESSING_STATUSES.indexOf("extracting") ? "✓" : "○"} Extracting
                              </span>
                              <span className="text-slate-300">→</span>
                              <span className={r.status === "classifying" ? "text-blue-600 font-medium" : PROCESSING_STATUSES.indexOf(r.status) > PROCESSING_STATUSES.indexOf("classifying") ? "text-green-600" : "text-slate-400"}>
                                {r.status === "classifying" ? "⏳" : PROCESSING_STATUSES.indexOf(r.status) > PROCESSING_STATUSES.indexOf("classifying") ? "✓" : "○"} Classifying
                              </span>
                              <span className="text-slate-300">→</span>
                              <span className={r.status === "validating" ? "text-blue-600 font-medium" : "text-slate-400"}>
                                {r.status === "validating" ? "⏳" : "○"} Validating
                              </span>
                            </div>
                          </div>
                        )}
                        {isReady && r.id && (
                          <>
                            <Button onClick={() => loadDetail(r.id!)} size="sm" className="w-full sm:w-auto">
                              <ScanLine size={14} className="mr-1.5" /> View Extracted Information
                            </Button>
                            <Button
                              onClick={() => { setUploadResults(null); loadDetail(r.id!); }}
                              variant="outline"
                              size="sm"
                              className="w-full sm:w-auto"
                            >
                              <Eye size={14} className="mr-1.5" /> Review & Analyze
                            </Button>
                          </>
                        )}
                        {isFailed && (
                          <Button onClick={handleRetryUpload} variant="outline" size="sm" className="w-full sm:w-auto">
                            <RefreshCw size={14} className="mr-1.5" /> Try Again
                          </Button>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>

              {uploadResults.some((r) => r.status === "ready_for_review" || r.status === "approved") && (
                <div className="mt-4 border-t border-slate-100 pt-3 flex gap-2">
                  <Button
                    onClick={() => { handleNewBatch(); fileInputRef.current?.click(); }}
                    variant="outline"
                    size="sm"
                  >
                    <Upload size={14} className="mr-2" /> Upload Another Batch
                  </Button>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Charts / Distribution */}
        {dashboard && dashboard.total > 0 && (
          <div className="mb-8 grid grid-cols-1 gap-4 lg:grid-cols-2">
            {Object.keys(dashboard.by_type).length > 0 && (
              <div className="rounded-xl border border-slate-200 bg-white p-5">
                <h3 className="mb-4 text-sm font-semibold text-slate-900">Certificates by Type</h3>
                <div className="space-y-2">
                  {Object.entries(dashboard.by_type).map(([type, count]) => (
                    <div key={type} className="flex items-center gap-3">
                      <span className="text-xs text-slate-600 w-32 sm:w-40 truncate" title={type.replace(/_/g, " ")}>
                        {type.replace(/_/g, " ")}
                      </span>
                      <div className="flex-1 h-6 bg-slate-100 rounded overflow-hidden">
                        <div className="h-full bg-indigo-500 rounded transition-all duration-500" style={{ width: `${(count / dashboard.total) * 100}%` }} />
                      </div>
                      <span className="text-xs font-medium text-slate-700 w-8 text-right">{count}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
            {Object.keys(dashboard.by_verification).length > 0 && (
              <div className="rounded-xl border border-slate-200 bg-white p-5">
                <h3 className="mb-4 text-sm font-semibold text-slate-900">Verification Status</h3>
                <div className="space-y-2">
                  {Object.entries(dashboard.by_verification).map(([status, count]) => (
                    <div key={status} className="flex items-center gap-3">
                      <span className="text-xs text-slate-600 w-32 sm:w-40 truncate">
                        {VERIFICATION_LABELS[status] || status}
                      </span>
                      <div className="flex-1 h-6 bg-slate-100 rounded overflow-hidden">
                        <div className="h-full bg-emerald-500 rounded transition-all duration-500" style={{ width: `${(count / dashboard.total) * 100}%` }} />
                      </div>
                      <span className="text-xs font-medium text-slate-700 w-8 text-right">{count}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Search & Filters */}
        <div className="mb-4 flex flex-wrap items-center gap-3">
          <div className="relative flex-1 min-w-[200px]">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
            <input
              type="text"
              placeholder="Search by name, certificate number, institution..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSearch()}
              className="w-full pl-10 pr-4 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
              aria-label="Search certificates"
            />
          </div>
          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            className="px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
            aria-label="Filter by type"
          >
            <option value="">All Types</option>
            <option value="academic_certificate">Academic Certificate</option>
            <option value="degree_certificate">Degree Certificate</option>
            <option value="diploma">Diploma</option>
            <option value="professional_certificate">Professional Certificate</option>
            <option value="training_certificate">Training Certificate</option>
            <option value="certificate_of_completion">Certificate of Completion</option>
            <option value="certificate_of_attendance">Certificate of Attendance</option>
            <option value="membership_certificate">Membership Certificate</option>
            <option value="license_certification">License/Certification</option>
          </select>
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
            aria-label="Filter by status"
          >
            <option value="">All Statuses</option>
            <option value="ready_for_review">Ready for Review</option>
            <option value="approved">Approved</option>
            <option value="rejected">Rejected</option>
            <option value="failed">Failed</option>
          </select>
          <select
            value={filterVerification}
            onChange={(e) => setFilterVerification(e.target.value)}
            className="px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
            aria-label="Filter by verification"
          >
            <option value="">All Verifications</option>
            <option value="not_verified">Not Verified</option>
            <option value="extraction_complete">Extraction Complete</option>
            <option value="verification_pending">Verification Pending</option>
            <option value="verified">Verified</option>
            <option value="verification_failed">Verification Failed</option>
            <option value="unable_to_verify">Unable to Verify</option>
            <option value="suspicious">Suspicious</option>
          </select>
          <Button onClick={handleSearch} variant="secondary" size="sm">
            <Filter size={14} className="mr-1" /> Filter
          </Button>
          {(searchQuery || filterType || filterStatus || filterVerification) && (
            <Button onClick={handleClearFilters} variant="ghost" size="sm">
              <X size={14} className="mr-1" /> Clear
            </Button>
          )}
          <div className="flex gap-2">
            <Button onClick={() => certificateService.exportCsv()} variant="secondary" size="sm" disabled={!dashboard || dashboard.total === 0}>
              <Download size={14} className="mr-1" /> CSV
            </Button>
            <Button onClick={() => certificateService.exportXlsx()} variant="secondary" size="sm" disabled={!dashboard || dashboard.total === 0}>
              <Download size={14} className="mr-1" /> XLSX
            </Button>
            <Button onClick={() => certificateService.downloadPresentation()} variant="secondary" size="sm" disabled={!dashboard || dashboard.total === 0}>
              <Presentation size={14} className="mr-1" /> PPTX
            </Button>
          </div>
        </div>

        {/* Certificate List */}
        <div className="rounded-xl border border-slate-200 bg-white overflow-hidden">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-6 w-6 animate-spin text-slate-400" />
            </div>
          ) : certificates.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-16 text-center">
              <Award className="h-12 w-12 text-slate-300 mb-3" />
              <p className="text-sm font-medium text-slate-700">
                {searchQuery || filterType || filterStatus || filterVerification
                  ? "No certificates found matching the selected filters."
                  : "No certificates yet"}
              </p>
              <p className="text-xs text-slate-500 mt-1">
                {searchQuery || filterType || filterStatus || filterVerification
                  ? "Try adjusting your search or filters."
                  : "Upload your first certificate to begin extracting and analyzing certificate data."}
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-slate-50 border-b border-slate-200">
                  <tr>
                    <th className="px-4 py-3 text-left font-medium text-slate-600">Filename</th>
                    <th className="px-4 py-3 text-left font-medium text-slate-600 hidden md:table-cell">Student Name</th>
                    <th className="px-4 py-3 text-left font-medium text-slate-600 hidden lg:table-cell">Course</th>
                    <th className="px-4 py-3 text-left font-medium text-slate-600 hidden sm:table-cell">Type</th>
                    <th className="px-4 py-3 text-left font-medium text-slate-600">Status</th>
                    <th className="px-4 py-3 text-left font-medium text-slate-600 hidden md:table-cell">Verification</th>
                    <th className="px-4 py-3 text-left font-medium text-slate-600 hidden lg:table-cell">Confidence</th>
                    <th className="px-4 py-3 text-left font-medium text-slate-600 hidden lg:table-cell">Created</th>
                    <th className="px-4 py-3 text-left font-medium text-slate-600">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {certificates.map((cert) => (
                    <tr key={cert.id} className="hover:bg-slate-50 cursor-pointer" onClick={() => loadDetail(cert.id)}>
                      <td className="px-4 py-3 text-slate-900 truncate max-w-[180px] sm:max-w-xs">{cert.filename}</td>
                      <td className="px-4 py-3 text-slate-700 hidden md:table-cell truncate max-w-[150px]">
                        {cert.student_name || "—"}
                      </td>
                      <td className="px-4 py-3 text-slate-600 hidden lg:table-cell truncate max-w-[150px]">
                        {cert.course || "—"}
                      </td>
                      <td className="px-4 py-3 text-slate-600 hidden sm:table-cell">
                        {cert.document_type_label || cert.document_type || "—"}
                      </td>
                      <td className="px-4 py-3">
                        <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                          STATUS_COLORS[cert.status] || "bg-slate-100 text-slate-600"
                        }`}>
                          {PROCESSING_STATUSES.includes(cert.status) && <Loader2 size={10} className="mr-1 animate-spin" />}
                          {STATUS_LABELS[cert.status] || cert.status}
                        </span>
                      </td>
                      <td className="px-4 py-3 hidden md:table-cell">
                        <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                          VERIFICATION_COLORS[cert.verification_status] || "bg-slate-100 text-slate-600"
                        }`}>
                          {VERIFICATION_LABELS[cert.verification_status] || cert.verification_status}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-slate-600 hidden lg:table-cell">
                        {cert.overall_confidence != null ? `${(cert.overall_confidence * 100).toFixed(1)}%` : "—"}
                      </td>
                      <td className="px-4 py-3 text-slate-500 text-xs hidden lg:table-cell">
                        {cert.created_at ? new Date(cert.created_at).toLocaleDateString() : "—"}
                      </td>
                      <td className="px-4 py-3">
                        <button
                          onClick={(e) => { e.stopPropagation(); loadDetail(cert.id); }}
                          className="text-xs text-indigo-600 font-medium hover:underline"
                        >
                          View Details
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Analytics Bridge */}
        {dashboard && dashboard.approved > 0 && (
          <div className="mt-8 rounded-xl border border-indigo-200 bg-indigo-50 p-5">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-indigo-600 text-white">
                  <BarChart3 size={20} />
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-slate-900">Analyze Certificate Data</h3>
                  <p className="text-xs text-slate-600">
                    Export {dashboard.approved} approved certificates to a dataset for analysis, dashboards, and reports
                  </p>
                </div>
              </div>
              <Button
                onClick={async () => {
                  try {
                    const result = await certificateService.toDataset("Certificate Analytics Dataset");
                    toast.success(result.message);
                  } catch (err: any) {
                    toast.error(err.message || "Failed to export to dataset");
                  }
                }}
                size="sm"
                className="w-full sm:w-auto flex-shrink-0"
              >
                Export to Dataset <ArrowRight size={14} className="ml-1" />
              </Button>
            </div>
          </div>
        )}
      </div>

      {/* Certificate Detail Modal */}
      {selectedCertId && (
        <CertificateDetail
          certificateId={selectedCertId}
          onClose={() => setSelectedCertId(null)}
          dashboardData={dashboard ? {
            by_type: dashboard.by_type,
            by_verification: dashboard.by_verification,
            by_institution: dashboard.by_institution,
            by_year: dashboard.by_year,
            total: dashboard.total,
          } : undefined}
        />
      )}
    </div>
  );
}
