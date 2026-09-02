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
import { Button } from "@/components/ui/Button";

const MAX_FILE_SIZE = 25 * 1024 * 1024; // 25MB
const MAX_BATCH_SIZE = 50;
const ACCEPTED_EXTS = ["jpg", "jpeg", "png", "tiff", "tif", "bmp", "pdf"];
const POLL_INTERVAL = 3000; // 3 seconds

type FileStatus = "pending" | "uploading" | "processing" | "done" | "error";

interface UploadedFile {
  file: File;
  status: FileStatus;
  document?: CaptureDocument;
  error?: string;
  progress?: number;
  jobId?: number | null;
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
      if (!ACCEPTED_EXTS.includes(ext || "")) {
        newFiles.push({ file: f, status: "error", error: `Unsupported file type: .${ext}. Supported: JPG, JPEG, PNG, TIFF, BMP, PDF` });
        continue;
      }
      if (f.size > MAX_FILE_SIZE) {
        newFiles.push({ file: f, status: "error", error: `File too large (${(f.size / 1024 / 1024).toFixed(1)} MB). Maximum: 25 MB` });
        continue;
      }
      newFiles.push({ file: f, status: "pending" });
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

    setFiles((prev) =>
      prev.map((f) =>
        f.status === "pending" ? { ...f, status: "uploading", progress: 0, error: undefined } : f,
      ),
    );

    try {
      const result = await captureService.batchUploadWithProgress(
        pendingFiles.map((f) => f.file),
        (percent) => setBatchProgress(percent),
      );

      const fileResults = result.files;
      const resultByName = new Map<string, BatchUploadFileResult>();
      for (const r of fileResults) {
        resultByName.set(r.filename, r);
      }

      setFiles((prev) =>
        prev.map((f) => {
          if (f.status !== "uploading") return f;
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
          f.status === "uploading" ? { ...f, status: "error" as FileStatus, error: msg } : f,
        ),
      );
    } finally {
      setIsSubmitting(false);
      setBatchProgress(0);
    }
  }, [files, isSubmitting]);

  const retryFailed = useCallback(async () => {
    const failedFiles = files.filter((f) => f.status === "error");
    if (failedFiles.length === 0 || isSubmitting) return;

    setIsSubmitting(true);
    setBatchProgress(0);

    setFiles((prev) =>
      prev.map((f) =>
        f.status === "error" ? { ...f, status: "uploading", progress: 0, error: undefined } : f,
      ),
    );

    try {
      const result = await captureService.batchUploadWithProgress(
        failedFiles.map((f) => f.file),
        (percent) => setBatchProgress(percent),
      );

      const fileResults = result.files;
      const resultByName = new Map<string, BatchUploadFileResult>();
      for (const r of fileResults) {
        resultByName.set(r.filename, r);
      }

      setFiles((prev) =>
        prev.map((f) => {
          if (f.status !== "uploading") return f;
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
          f.status === "uploading" ? { ...f, status: "error" as FileStatus, error: msg } : f,
        ),
      );
    } finally {
      setIsSubmitting(false);
      setBatchProgress(0);
    }
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

  // Poll for status updates on processing documents
  useEffect(() => {
    const processingFiles = files.filter((f) => f.status === "processing" && f.document);
    if (processingFiles.length === 0) return;

    const interval = setInterval(async () => {
      for (const f of processingFiles) {
        if (!f.document) continue;
        try {
          const updated = await captureService.getDocument(f.document.id);
          const isDone = updated.status === "ready_for_review" || updated.status === "approved" || updated.status === "rejected" || updated.status === "draft";
          const isFailed = updated.status === "failed";
          setFiles((prev) => prev.map((pf) =>
            pf.document?.id === f.document!.id
              ? { ...pf, status: isFailed ? "error" : isDone ? "done" : "processing", document: updated, error: isFailed ? updated.error_message || "Processing failed" : undefined }
              : pf
          ));
        } catch {
          // Silently ignore polling errors
        }
      }
    }, POLL_INTERVAL);

    return () => clearInterval(interval);
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
          accept=".jpg,.jpeg,.png,.tiff,.tif,.bmp,.pdf"
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
            <p className="mt-1 text-sm text-slate-400">Supports JPG, JPEG, PNG, TIFF, BMP, PDF — up to 25MB each — max {MAX_BATCH_SIZE} files per batch</p>
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
                    {f.file.name.endsWith(".pdf") ? <FileText size={20} className="text-red-500" /> : <ImageIcon size={20} className="text-blue-500" />}
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
                    {f.status === "processing" && f.document && (
                      <p className="mt-0.5 text-xs font-medium text-indigo-600">
                        Processing... {f.document.status || "queued"}
                      </p>
                    )}
                    {f.status === "done" && f.document && (
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
