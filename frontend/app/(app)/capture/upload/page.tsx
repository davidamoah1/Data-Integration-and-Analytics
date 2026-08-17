"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { Upload, FileText, Image as ImageIcon, Loader2, X, CheckCircle2, AlertCircle, RotateCw, Clock } from "lucide-react";
import { captureService, type CaptureDocument } from "@/services/capture/captureService";
import { Button } from "@/components/ui/Button";

const MAX_FILE_SIZE = 25 * 1024 * 1024; // 25MB
const ACCEPTED_EXTS = ["jpg", "jpeg", "png", "tiff", "tif", "bmp", "pdf"];
const POLL_INTERVAL = 3000; // 3 seconds

interface UploadedFile {
  file: File;
  status: "pending" | "uploading" | "processing" | "done" | "error";
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
    setFiles((prev) => [...prev, ...newFiles]);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    handleFiles(e.dataTransfer.files);
  }, [handleFiles]);

  const uploadOne = async (index: number) => {
    setFiles((prev) => prev.map((f, i) => (i === index ? { ...f, status: "uploading", progress: 0, error: undefined } : f)));
    try {
      const doc = await captureService.uploadDocumentWithProgress(files[index].file, (percent) => {
        setFiles((prev) => prev.map((f, i) => (i === index ? { ...f, progress: percent } : f)));
      });
      // Document is uploaded and processing started in background
      const isProcessing = doc.status === "uploaded" || doc.status === "preprocessing" || doc.status === "extracting" || doc.status === "classifying" || doc.status === "validating";
      setFiles((prev) => prev.map((f, i) => (i === index ? {
        ...f,
        status: isProcessing ? "processing" : "done",
        document: doc,
        progress: 100,
        jobId: (doc as any).job_id ?? null,
      } : f)));
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Upload failed";
      setFiles((prev) => prev.map((f, i) => (i === index ? { ...f, status: "error", error: msg } : f)));
    }
  };

  const uploadAll = async () => {
    for (let i = 0; i < files.length; i++) {
      if (files[i].status === "pending") {
        await uploadOne(i);
      }
    }
  };

  const removeFile = (index: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const retryFile = (index: number) => {
    setFiles((prev) => prev.map((f, i) => (i === index ? { ...f, status: "pending", error: undefined } : f)));
    uploadOne(index);
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

  return (
    <div className="min-h-screen bg-slate-50 py-8">
      <div className="mx-auto max-w-4xl px-6">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-slate-900">Upload Documents</h1>
          <p className="text-sm text-slate-500">Upload photos, scans, or PDFs for automatic data extraction</p>
        </div>

        {/* Drop zone */}
        <div
          onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={handleDrop}
          onClick={() => inputRef.current?.click()}
          className={`cursor-pointer rounded-2xl border-2 border-dashed p-12 text-center transition-colors ${
            isDragging ? "border-indigo-500 bg-indigo-50" : "border-slate-300 bg-white hover:border-indigo-400 hover:bg-slate-50"
          }`}
        >
          <input
            ref={inputRef}
            type="file"
            multiple
            accept=".jpg,.jpeg,.png,.tiff,.tif,.bmp,.pdf"
            className="hidden"
            onChange={(e) => e.target.files && handleFiles(e.target.files)}
          />
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-indigo-100">
            <Upload size={28} className="text-indigo-600" />
          </div>
          <p className="text-lg font-medium text-slate-700">Drop files here or click to browse</p>
          <p className="mt-1 text-sm text-slate-400">Supports JPG, JPEG, PNG, TIFF, BMP, PDF — up to 25MB each</p>
        </div>

        {/* File list */}
        {files.length > 0 && (
          <div className="mt-6 space-y-3">
            {files.map((f, i) => (
              <div key={i} className="flex items-center gap-4 rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
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
                  {f.status === "pending" && (
                    <Button size="sm" variant="outline" onClick={() => uploadOne(i)}>Upload</Button>
                  )}
                  {f.status === "uploading" && <Loader2 size={20} className="animate-spin text-indigo-500" />}
                  {f.status === "processing" && <Clock size={20} className="text-indigo-400 animate-pulse" />}
                  {f.status === "done" && <CheckCircle2 size={20} className="text-green-500" />}
                  {f.status === "error" && (
                    <>
                      <AlertCircle size={20} className="text-red-500" />
                      <button
                        onClick={() => retryFile(i)}
                        className="text-slate-400 hover:text-indigo-500"
                        title="Retry upload"
                      >
                        <RotateCw size={16} />
                      </button>
                    </>
                  )}
                </div>
                <button onClick={() => removeFile(i)} className="shrink-0 text-slate-300 hover:text-slate-500">
                  <X size={18} />
                </button>
              </div>
            ))}

            {/* Actions */}
            <div className="flex items-center justify-between pt-2">
              <p className="text-sm text-slate-500">
                {doneCount} done, {pendingCount} pending{uploadingCount > 0 ? `, ${uploadingCount} uploading` : ""}{processingCount > 0 ? `, ${processingCount} processing` : ""}{errorCount > 0 ? `, ${errorCount} failed` : ""}
              </p>
              <div className="flex gap-3">
                {pendingCount > 0 && (
                  <Button onClick={uploadAll} className="gap-2">
                    <Upload size={16} /> Upload All ({pendingCount})
                  </Button>
                )}
                {doneCount > 0 && (
                  <Button variant="outline" onClick={() => router.push("/capture/review")}>
                    Go to Review Queue
                  </Button>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
