"use client";

import { useCallback, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { Upload, FileText, Image as ImageIcon, Loader2, X, CheckCircle2, AlertCircle } from "lucide-react";
import { captureService, type CaptureDocument } from "@/services/capture/captureService";
import { Button } from "@/components/ui/Button";

interface UploadedFile {
  file: File;
  status: "pending" | "uploading" | "done" | "error";
  document?: CaptureDocument;
  error?: string;
}

export default function CaptureUploadPage() {
  const router = useRouter();
  const inputRef = useRef<HTMLInputElement>(null);
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [isDragging, setIsDragging] = useState(false);

  const handleFiles = useCallback((fileList: FileList) => {
    const accepted = Array.from(fileList).filter((f) => {
      const ext = f.name.split(".").pop()?.toLowerCase();
      return ["jpg", "jpeg", "png", "tiff", "tif", "bmp", "pdf"].includes(ext || "");
    });
    setFiles((prev) => [...prev, ...accepted.map((file) => ({ file, status: "pending" as const }))]);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    handleFiles(e.dataTransfer.files);
  }, [handleFiles]);

  const uploadOne = async (index: number) => {
    setFiles((prev) => prev.map((f, i) => (i === index ? { ...f, status: "uploading" } : f)));
    try {
      const doc = await captureService.uploadDocument(files[index].file);
      setFiles((prev) => prev.map((f, i) => (i === index ? { ...f, status: "done", document: doc } : f)));
    } catch (err: any) {
      setFiles((prev) => prev.map((f, i) => (i === index ? { ...f, status: "error", error: err.message } : f)));
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

  const pendingCount = files.filter((f) => f.status === "pending").length;
  const doneCount = files.filter((f) => f.status === "done").length;
  const errorCount = files.filter((f) => f.status === "error").length;

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
          <p className="mt-1 text-sm text-slate-400">Supports JPG, PNG, TIFF, PDF — up to 25MB each</p>
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
                  {f.status === "done" && f.document && (
                    <p className="mt-0.5 text-xs font-medium text-green-600">
                      Extracted: {f.document.document_type_label || "Unknown type"} — {f.document.status === "ready_for_review" ? "Ready for review" : f.document.status}
                    </p>
                  )}
                  {f.status === "error" && (
                    <p className="mt-0.5 text-xs font-medium text-red-600">{f.error}</p>
                  )}
                </div>
                <div className="shrink-0">
                  {f.status === "pending" && (
                    <Button size="sm" variant="outline" onClick={() => uploadOne(i)}>Upload</Button>
                  )}
                  {f.status === "uploading" && <Loader2 size={20} className="animate-spin text-indigo-500" />}
                  {f.status === "done" && <CheckCircle2 size={20} className="text-green-500" />}
                  {f.status === "error" && <AlertCircle size={20} className="text-red-500" />}
                </div>
                <button onClick={() => removeFile(i)} className="shrink-0 text-slate-300 hover:text-slate-500">
                  <X size={18} />
                </button>
              </div>
            ))}

            {/* Actions */}
            <div className="flex items-center justify-between pt-2">
              <p className="text-sm text-slate-500">
                {doneCount} done, {pendingCount} pending{errorCount > 0 ? `, ${errorCount} failed` : ""}
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
