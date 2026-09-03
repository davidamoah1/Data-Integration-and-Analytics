"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import {
  Upload,
  FileText,
  Image as ImageIcon,
  Loader2,
  X,
  CheckCircle2,
  AlertCircle,
  RotateCw,
  Clock,
  FileCheck2,
  FileX2,
} from "lucide-react";
import {
  captureService,
  type CaptureDocument,
  type BatchUploadFileResult,
} from "@/services/capture/captureService";
import { etlPackageService } from "@/services/etl/etlPackageService";
import { Button } from "@/components/ui/Button";
import { Package } from "lucide-react";

const MAX_FILE_SIZE = 25 * 1024 * 1024; // 25MB
const MAX_ZIP_SIZE = 500 * 1024 * 1024; // 500MB for ZIP packages
const MAX_BATCH_SIZE = 50;
const ACCEPTED_EXTS = ["jpg", "jpeg", "png", "tiff", "tif", "bmp", "pdf", "zip"];
const POLL_INTERVAL = 3000; // 3 seconds

type FileStatus = "pending" | "uploading" | "processing" | "done" | "error";

interface UploadedFile {
  file: File;
  status: FileStatus;
  document?: CaptureDocument;
  error?: string;
  progress?: number;
  jobId?: number | null;
  isZip?: boolean;
  packageId?: number | null;
}

export default function CaptureUploadPage() {
  const router = useRouter();
  const inputRef = useRef<HTMLInputElement>(null);
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [batchProgress, setBatchProgress] = useState(0);

  const handleFiles = useCallback((fileList: FileList) => {
    const newFiles: UploadedFile[] = [];
    for (const f of Array.from(fileList)) {
      const ext = f.name.split(".").pop()?.toLowerCase();
      const isZip = ext === "zip";
      if (!ACCEPTED_EXTS.includes(ext || "")) {
        newFiles.push({ file: f, status: "error", error: `Unsupported file type: .${ext}. Supported: JPG, JPEG, PNG, TIFF, BMP, PDF, ZIP` });
        continue;
      }
      const maxSize = isZip ? MAX_ZIP_SIZE : MAX_FILE_SIZE;
      const maxLabel = isZip ? "500 MB" : "25 MB";
      if (f.size > maxSize) {
        newFiles.push({ file: f, status: "error", error: `File too large (${(f.size / 1024 / 1024).toFixed(1)} MB). Maximum: ${maxLabel}` });
        continue;
      }
      newFiles.push({ file: f, status: "pending", isZip });
    }
    setFiles((prev) => {
      const pendingCount = prev.filter((p) => p.status === "pending").length;
      const totalCount = prev.length + newFiles.length;
      if (totalCount > MAX_BATCH_SIZE) {
        const overflow = totalCount - MAX_BATCH_SIZE;
        const limited = newFiles.slice(0, newFiles.length - overflow);
        if (overflow > 0) {
          limited.push({
            file: newFiles[newFiles.length - overflow].file,
            status: "error" as FileStatus,
            error: `Maximum ${MAX_BATCH_SIZE} files per batch. This file exceeds the limit.`,
          });
        }
        return [...prev, ...limited];
      }
      return [...prev, ...newFiles];
    });
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    handleFiles(e.dataTransfer.files);
  }, [handleFiles]);

  const uploadAll = useCallback(async () => {
    const pendingFiles = files.filter((f) => f.status === "pending");
    if (pendingFiles.length === 0 || isSubmitting) return;

    setIsSubmitting(true);
    setBatchProgress(0);

    const zipFiles = pendingFiles.filter((f) => f.isZip);
    const docFiles = pendingFiles.filter((f) => !f.isZip);

    // Upload ZIP files via ETL package service
    if (zipFiles.length > 0) {
      setFiles((prev) =>
        prev.map((f) =>
          f.isZip && f.status === "pending"
            ? { ...f, status: "uploading", progress: 0, error: undefined }
            : f,
        ),
      );

      for (const zf of zipFiles) {
        try {
          const result = await etlPackageService.upload(zf.file, (percent) => {
            setFiles((prev) =>
              prev.map((f) =>
                f.file === zf.file && f.status === "uploading"
                  ? { ...f, progress: percent }
                  : f,
              ),
            );
          });
          setFiles((prev) =>
            prev.map((f) =>
              f.file === zf.file
                ? {
                    ...f,
                    status: "processing" as FileStatus,
                    progress: 100,
                    packageId: result.package_id,
                    jobId: result.job_id,
                  }
                : f,
            ),
          );
        } catch (err: unknown) {
          const msg = err instanceof Error ? err.message : "ZIP upload failed";
          setFiles((prev) =>
            prev.map((f) =>
              f.file === zf.file
                ? { ...f, status: "error" as FileStatus, error: msg }
                : f,
            ),
          );
        }
      }
    }

    // Upload document files via capture service
    if (docFiles.length > 0) {
      setFiles((prev) =>
        prev.map((f) =>
          !f.isZip && f.status === "pending"
            ? { ...f, status: "uploading", progress: 0, error: undefined }
            : f,
        ),
      );

      try {
        const result = await captureService.batchUploadWithProgress(
          docFiles.map((f) => f.file),
          (percent) => setBatchProgress(percent),
        );

        const fileResults = result.files;
        const resultByName = new Map<string, BatchUploadFileResult>();
        for (const r of fileResults) {
          resultByName.set(r.filename, r);
        }

        setFiles((prev) =>
          prev.map((f) => {
            if (f.isZip || f.status !== "uploading") return f;
            const r = resultByName.get(f.file.name);
            if (!r) {
              return { ...f, status: "error" as FileStatus, error: "No response received for this file." };
            }
            if (r.status === "failed") {
              return { ...f, status: "error" as FileStatus, error: r.error || "Upload failed" };
            }
            const doc: Partial<CaptureDocument> = {
              id: r.id ?? 0,
              batch_id: r.batch_id ?? null,
              filename: r.filename,
              file_type: r.file_type || "",
              status: "uploaded",
              document_type: r.document_type ?? null,
              document_type_label: r.document_type_label ?? null,
              classification_confidence: r.classification_confidence ?? null,
              overall_confidence: r.overall_confidence ?? null,
              duplicate_of_id: r.duplicate_of_id ?? null,
            };
            return {
              ...f,
              status: "processing" as FileStatus,
              document: doc as CaptureDocument,
              progress: 100,
              jobId: r.job_id ?? null,
            };
          }),
        );
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : "Upload failed";
        setFiles((prev) =>
          prev.map((f) =>
            !f.isZip && f.status === "uploading" ? { ...f, status: "error" as FileStatus, error: msg } : f,
          ),
        );
      }
    }

    setIsSubmitting(false);
    setBatchProgress(0);
  }, [files, isSubmitting]);

  const retryFailed = useCallback(async () => {
    const failedFiles = files.filter((f) => f.status === "error");
    if (failedFiles.length === 0 || isSubmitting) return;

    setIsSubmitting(true);
    setBatchProgress(0);

    const failedZipFiles = failedFiles.filter((f) => f.isZip);
    const failedDocFiles = failedFiles.filter((f) => !f.isZip);

    // Retry ZIP files via ETL package service
    if (failedZipFiles.length > 0) {
      setFiles((prev) =>
        prev.map((f) =>
          f.isZip && f.status === "error" ? { ...f, status: "uploading" as FileStatus, progress: 0, error: undefined } : f,
        ),
      );

      for (const zf of failedZipFiles) {
        try {
          const result = await etlPackageService.upload(zf.file, (percent) => {
            setFiles((prev) =>
              prev.map((f) =>
                f.file === zf.file && f.status === "uploading"
                  ? { ...f, progress: percent }
                  : f,
              ),
            );
          });
          setFiles((prev) =>
            prev.map((f) =>
              f.file === zf.file
                ? {
                    ...f,
                    status: "processing" as FileStatus,
                    progress: 100,
                    packageId: result.package_id,
                    jobId: result.job_id,
                  }
                : f,
            ),
          );
        } catch (err: unknown) {
          const msg = err instanceof Error ? err.message : "ZIP upload failed";
          setFiles((prev) =>
            prev.map((f) =>
              f.file === zf.file
                ? { ...f, status: "error" as FileStatus, error: msg }
                : f,
            ),
          );
        }
      }
    }

    // Retry document files via capture service
    if (failedDocFiles.length > 0) {
      setFiles((prev) =>
        prev.map((f) =>
          !f.isZip && f.status === "error" ? { ...f, status: "uploading" as FileStatus, progress: 0, error: undefined } : f,
        ),
      );

      try {
        const result = await captureService.batchUploadWithProgress(
          failedDocFiles.map((f) => f.file),
          (percent) => setBatchProgress(percent),
        );

        const fileResults = result.files;
        const resultByName = new Map<string, BatchUploadFileResult>();
        for (const r of fileResults) {
          resultByName.set(r.filename, r);
        }

        setFiles((prev) =>
          prev.map((f) => {
            if (f.isZip || f.status !== "uploading") return f;
            const r = resultByName.get(f.file.name);
            if (!r) {
              return { ...f, status: "error" as FileStatus, error: "No response received for this file." };
            }
            if (r.status === "failed") {
              return { ...f, status: "error" as FileStatus, error: r.error || "Upload failed" };
            }
            const doc: Partial<CaptureDocument> = {
              id: r.id ?? 0,
              batch_id: r.batch_id ?? null,
              filename: r.filename,
              file_type: r.file_type || "",
              status: "uploaded",
              document_type: r.document_type ?? null,
              document_type_label: r.document_type_label ?? null,
              classification_confidence: r.classification_confidence ?? null,
              overall_confidence: r.overall_confidence ?? null,
              duplicate_of_id: r.duplicate_of_id ?? null,
            };
            return {
              ...f,
              status: "processing" as FileStatus,
              document: doc as CaptureDocument,
              progress: 100,
              jobId: r.job_id ?? null,
            };
          }),
      );
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : "Retry failed";
        setFiles((prev) =>
          prev.map((f) =>
            !f.isZip && f.status === "uploading" ? { ...f, status: "error" as FileStatus, error: msg } : f,
          ),
        );
      }
    }

    setIsSubmitting(false);
    setBatchProgress(0);
  }, [files, isSubmitting]);

  const removeFile = (index: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const clearAll = () => {
    setFiles([]);
  };

  const pendingCount = files.filter((f) => f.status === "pending").length;
  const doneCount = files.filter((f) => f.status === "done").length;
  const errorCount = files.filter((f) => f.status === "error").length;
  const uploadingCount = files.filter((f) => f.status === "uploading").length;
  const processingCount = files.filter((f) => f.status === "processing").length;

  // Track polling state in refs to avoid recreating interval on every render
  const pollAttemptsRef = useRef<Record<number, number>>({});
  const pollDelayRef = useRef(POLL_INTERVAL);

  // Poll for status updates on processing documents and ZIP packages
  useEffect(() => {
    const hasProcessingDocs = files.some((f) => f.status === "processing" && f.document);
    const hasProcessingZips = files.some((f) => f.status === "processing" && f.isZip && f.packageId);
    if (!hasProcessingDocs && !hasProcessingZips) return;

    let cancelled = false;
    let timeoutId: ReturnType<typeof setTimeout>;

    const poll = async () => {
      if (cancelled) return;

      // Poll ZIP packages
      const processingZips = files
        .filter((f) => f.status === "processing" && f.isZip && f.packageId)
        .map((f) => f.packageId!);

      for (const pkgId of processingZips) {
        try {
          const p = await etlPackageService.getProgress(pkgId);
          if (cancelled) break;

          const isDone = ["completed", "completed_with_errors", "failed", "cancelled"].includes(p.status);
          if (isDone) {
            setFiles((prev) =>
              prev.map((pf) =>
                pf.packageId === pkgId
                  ? {
                      ...pf,
                      status: p.status === "failed" ? ("error" as FileStatus) : ("done" as FileStatus),
                      error: p.status === "failed" ? p.error_message || "Package processing failed" : undefined,
                    }
                  : pf,
              ),
            );
          }
        } catch {
          // Network error — keep polling
        }
      }

      // Poll capture documents
      const processingDocs = files
        .filter((f) => f.status === "processing" && f.document)
        .map((f) => f.document!.id);

      if (processingDocs.length === 0 && processingZips.length === 0) return;

      for (const docId of processingDocs) {
        const attempts = (pollAttemptsRef.current[docId] || 0) + 1;
        pollAttemptsRef.current[docId] = attempts;

        // Max 100 polling attempts (~10 minutes at 6s avg)
        if (attempts > 100) {
          setFiles((prev) =>
            prev.map((pf) =>
              pf.document?.id === docId
                ? {
                    ...pf,
                    status: "error" as FileStatus,
                    error: "Processing timed out. Please retry.",
                  }
                : pf,
            ),
          );
          continue;
        }

        try {
          const updated = await captureService.getDocument(docId);
          if (cancelled) break;

          const isDone =
            updated.status === "ready_for_review" ||
            updated.status === "approved" ||
            updated.status === "rejected" ||
            updated.status === "draft";
          const isFailed = updated.status === "failed";

          if (isDone || isFailed) {
            // Reset attempt counter for this doc
            delete pollAttemptsRef.current[docId];
          }

          setFiles((prev) =>
            prev.map((pf) =>
              pf.document?.id === docId
                ? {
                    ...pf,
                    status: isFailed
                      ? ("error" as FileStatus)
                      : isDone
                        ? ("done" as FileStatus)
                        : "processing",
                    document: updated,
                    error: isFailed
                      ? updated.error_message || "Processing failed"
                      : undefined,
                  }
                : pf,
            ),
          );
        } catch {
          // Network error — keep polling with backoff
        }
      }

      // Exponential backoff: 3s → 6s → 12s → 15s (capped)
      pollDelayRef.current = Math.min(pollDelayRef.current * 2, 15000);

      // Schedule next poll only if there are still processing items
      const stillProcessing = files.some(
        (f) =>
          (f.status === "processing" && f.document) ||
          (f.status === "processing" && f.isZip && f.packageId),
      );
      if (stillProcessing && !cancelled) {
        timeoutId = setTimeout(poll, pollDelayRef.current);
      }
    };

    // Reset backoff on new polling cycle
    pollDelayRef.current = POLL_INTERVAL;
    timeoutId = setTimeout(poll, POLL_INTERVAL);

    return () => {
      cancelled = true;
      clearTimeout(timeoutId);
    };
  }, [files]);

  const uploadProgressText = isSubmitting && batchProgress > 0
    ? `Uploading ${pendingCount + uploadingCount} files... ${batchProgress}%`
    : isSubmitting
      ? `Uploading ${uploadingCount} files...`
      : null;

  return (
    <div className="min-h-screen bg-slate-50 py-8">
      <div className="mx-auto max-w-4xl px-6">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-slate-900">Upload Documents</h1>
          <p className="text-sm text-slate-500">Upload photos, scans, or PDFs for automatic data extraction</p>
        </div>

        {/* Top action bar: Select Files + Upload All */}
        <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-3">
            <Button
              variant="outline"
              onClick={() => inputRef.current?.click()}
              className="gap-2"
              disabled={isSubmitting}
            >
              <Upload size={16} /> Select Files
            </Button>
            <span className="text-sm text-slate-500">
              {files.length > 0
                ? `Selected: ${files.length} file${files.length !== 1 ? "s" : ""}`
                : "No files selected"}
            </span>
          </div>
          <div className="flex items-center gap-3">
            {errorCount > 0 && !isSubmitting && (
              <Button
                variant="outline"
                onClick={retryFailed}
                className="gap-2"
                disabled={isSubmitting}
              >
                <RotateCw size={16} /> Retry Failed ({errorCount})
              </Button>
            )}
            {pendingCount > 0 && (
              <Button
                onClick={uploadAll}
                className="gap-2"
                disabled={isSubmitting}
              >
                {isSubmitting ? (
                  <>
                    <Loader2 size={16} className="animate-spin" />
                    {uploadProgressText || "Uploading..."}
                  </>
                ) : (
                  <>
                    <Upload size={16} /> Upload All ({pendingCount})
                  </>
                )}
              </Button>
            )}
          </div>
        </div>

        {/* Batch progress bar */}
        {isSubmitting && (
          <div className="mb-4">
            <div className="h-2 w-full overflow-hidden rounded-full bg-slate-200">
              <div
                className="h-full rounded-full bg-indigo-500 transition-all duration-200"
                style={{ width: `${batchProgress}%` }}
              />
            </div>
            <p className="mt-1 text-xs text-indigo-500">{uploadProgressText}</p>
          </div>
        )}

        {/* Hidden file input (always available) */}
        <input
          ref={inputRef}
          type="file"
          multiple
          accept=".jpg,.jpeg,.png,.tiff,.tif,.bmp,.pdf,.zip"
          className="hidden"
          onChange={(e) => {
            if (e.target.files) handleFiles(e.target.files);
            e.target.value = "";
          }}
        />

        {/* Drop zone (only show when no files yet) */}
        {files.length === 0 && (
          <div
            onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
            onDragLeave={() => setIsDragging(false)}
            onDrop={handleDrop}
            onClick={() => inputRef.current?.click()}
            className={`cursor-pointer rounded-2xl border-2 border-dashed p-12 text-center transition-colors ${
              isDragging ? "border-indigo-500 bg-indigo-50" : "border-slate-300 bg-white hover:border-indigo-400 hover:bg-slate-50"
            }`}
          >
            <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-indigo-100">
              <Upload size={28} className="text-indigo-600" />
            </div>
            <p className="text-lg font-medium text-slate-700">Drop files here or click to browse</p>
            <p className="mt-1 text-sm text-slate-400">Supports JPG, JPEG, PNG, TIFF, BMP, PDF, ZIP — up to 25MB each (500MB for ZIP) — max {MAX_BATCH_SIZE} files per batch</p>
          </div>
        )}

        {/* File list table */}
        {files.length > 0 && (
          <div className="mt-4">
            {/* Summary bar */}
            <div className="mb-3 flex items-center justify-between">
              <div className="flex flex-wrap items-center gap-3 text-sm">
                {doneCount > 0 && (
                  <span className="inline-flex items-center gap-1 font-medium text-green-600">
                    <FileCheck2 size={16} /> {doneCount} uploaded
                  </span>
                )}
                {processingCount > 0 && (
                  <span className="inline-flex items-center gap-1 font-medium text-indigo-600">
                    <Clock size={16} className="animate-pulse" /> {processingCount} processing
                  </span>
                )}
                {pendingCount > 0 && (
                  <span className="inline-flex items-center gap-1 font-medium text-slate-500">
                    {pendingCount} ready
                  </span>
                )}
                {errorCount > 0 && (
                  <span className="inline-flex items-center gap-1 font-medium text-red-600">
                    <FileX2 size={16} /> {errorCount} failed
                  </span>
                )}
              </div>
              <div className="flex items-center gap-2">
                {doneCount > 0 && !isSubmitting && (
                  <Button variant="outline" size="sm" onClick={() => router.push("/capture/review")}>
                    Go to Review Queue
                  </Button>
                )}
                {!isSubmitting && (
                  <button
                    onClick={clearAll}
                    className="text-sm text-slate-400 hover:text-slate-600"
                  >
                    Clear all
                  </button>
                )}
              </div>
            </div>

            {/* File rows */}
            <div className="space-y-2">
              {files.map((f, i) => (
                <div key={i} className={`flex items-center gap-4 rounded-xl border p-4 shadow-sm transition-colors ${
                  f.status === "error" ? "border-red-200 bg-red-50/30" : f.status === "done" ? "border-green-200 bg-green-50/30" : "border-slate-200 bg-white"
                }`}>
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-slate-100">
                    {f.isZip ? <Package size={20} className="text-amber-600" /> : f.file.name.endsWith(".pdf") ? <FileText size={20} className="text-red-500" /> : <ImageIcon size={20} className="text-blue-500" />}
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-medium text-slate-800">{f.file.name}</p>
                    <p className="text-xs text-slate-400">{(f.file.size / 1024).toFixed(0)} KB</p>
                    {f.status === "uploading" && (
                      <div className="mt-1.5">
                        <div className="h-1.5 w-full overflow-hidden rounded-full bg-slate-200">
                          <div
                            className="h-full rounded-full bg-indigo-500 transition-all duration-200"
                            style={{ width: `${f.progress ?? 0}%` }}
                          />
                        </div>
                        <p className="mt-0.5 text-xs text-indigo-500">Uploading... {f.progress ?? 0}%</p>
                      </div>
                    )}
                    {f.status === "processing" && f.isZip && (
                      <p className="mt-0.5 text-xs font-medium text-indigo-600">
                        Package processing... <button onClick={() => router.push(`/datasets/etl-packages/${f.packageId}`)} className="underline hover:text-indigo-700">View progress</button>
                      </p>
                    )}
                    {f.status === "processing" && !f.isZip && f.document && (
                      <p className="mt-0.5 text-xs font-medium text-indigo-600">
                        Processing... {f.document.status || "queued"}
                      </p>
                    )}
                    {f.status === "done" && f.isZip && (
                      <p className="mt-0.5 text-xs font-medium text-green-600">
                        Package uploaded — <button onClick={() => router.push(`/datasets/etl-packages/${f.packageId}`)} className="underline hover:text-green-700">View details</button>
                      </p>
                    )}
                    {f.status === "done" && !f.isZip && f.document && (
                      <p className="mt-0.5 text-xs font-medium text-green-600">
                        {f.document.document_type_label || "Unknown type"} — {f.document.status === "ready_for_review" ? "Ready for review" : f.document.status}
                      </p>
                    )}
                    {f.status === "error" && (
                      <p className="mt-0.5 text-xs font-medium text-red-600">{f.error}</p>
                    )}
                  </div>
                  <div className="shrink-0 flex items-center gap-2">
                    {f.status === "uploading" && <Loader2 size={20} className="animate-spin text-indigo-500" />}
                    {f.status === "processing" && <Clock size={20} className="text-indigo-400 animate-pulse" />}
                    {f.status === "done" && <CheckCircle2 size={20} className="text-green-500" />}
                    {f.status === "error" && <AlertCircle size={20} className="text-red-500" />}
                  </div>
                  {!isSubmitting && (
                    <button onClick={() => removeFile(i)} className="shrink-0 text-slate-300 hover:text-slate-500">
                      <X size={18} />
                    </button>
                  )}
                </div>
              ))}
            </div>

            {/* Add more files link */}
            {!isSubmitting && (
              <div className="mt-4">
                <button
                  onClick={() => inputRef.current?.click()}
                  className="text-sm font-medium text-indigo-600 hover:text-indigo-700"
                >
                  + Add more files
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
