"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import {
  Upload, File as FileIcon, Download, Trash2, Loader2, Search,
  HardDrive, Cloud, CheckCircle2,
} from "lucide-react";
import { fileService, type FileRecord } from "@/services/storage/fileService";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { cn } from "@/lib/utils";
import { toast } from "@/components/ui/Toaster";

function formatSize(bytes: number | null): string {
  if (bytes === null) return "—";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(1)} GB`;
}

function formatDate(iso: string | null): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleString([], {
    month: "short", day: "numeric", hour: "2-digit", minute: "2-digit",
  });
}

function getBackendIcon(backend: string) {
  if (backend === "local") return HardDrive;
  return Cloud;
}

export function FileManager() {
  const [files, setFiles] = useState<FileRecord[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [search, setSearch] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  const loadFiles = useCallback(async () => {
    try {
      const data = await fileService.list({ limit: 100 });
      setFiles(data.files);
      setTotal(data.total);
    } catch {
      // Silent fail
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadFiles();
  }, [loadFiles]);

  const handleUpload = async (file: File) => {
    setUploading(true);
    try {
      await fileService.upload(file);
      toast.success(`Uploaded: ${file.name}`);
      loadFiles();
    } catch {
      toast.error("Upload failed");
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (fileId: string, filename: string) => {
    try {
      await fileService.delete(fileId);
      toast.success(`Deleted: ${filename}`);
      loadFiles();
    } catch {
      toast.error("Delete failed");
    }
  };

  const handleDownload = (fileId: string, filename: string) => {
    const url = fileService.downloadUrl(fileId);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.click();
  };

  const filtered = search
    ? files.filter((f) => f.filename.toLowerCase().includes(search.toLowerCase()))
    : files;

  return (
    <div className="space-y-4">
      {/* Upload zone */}
      <Card
        className="cursor-pointer border-dashed border-2 hover:border-primary/50 transition-colors"
        onClick={() => inputRef.current?.click()}
      >
        <CardContent className="flex flex-col items-center justify-center py-10 text-center">
          <input
            ref={inputRef}
            type="file"
            className="hidden"
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) handleUpload(file);
              e.target.value = "";
            }}
          />
          {uploading ? (
            <>
              <Loader2 className="h-8 w-8 animate-spin text-primary mb-3" />
              <p className="text-sm font-medium">Uploading...</p>
            </>
          ) : (
            <>
              <Upload className="h-8 w-8 text-muted-foreground mb-3" />
              <p className="text-sm font-medium">Click to upload a file</p>
              <p className="text-xs text-muted-foreground mt-1">
                Files are stored in object storage, not in the database
              </p>
            </>
          )}
        </CardContent>
      </Card>

      {/* Stats + search */}
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Badge variant="secondary">{total} files</Badge>
          {files.length > 0 && (
            <Badge variant="outline">
              {files[0].storage_backend === "local" ? (
                <><HardDrive className="h-3 w-3 mr-1" />Local</>
              ) : (
                <><Cloud className="h-3 w-3 mr-1" />{files[0].storage_backend}</>
              )}
            </Badge>
          )}
        </div>
        <div className="relative">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search files..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="rounded-md border bg-background pl-8 pr-3 py-1.5 text-sm w-48 focus:outline-none focus:ring-1 focus:ring-primary"
          />
        </div>
      </div>

      {/* File list */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <FileIcon className="h-4 w-4" />
            Stored Files
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          ) : filtered.length === 0 ? (
            <div className="py-12 text-center text-sm text-muted-foreground">
              No files found.
            </div>
          ) : (
            <div className="divide-y">
              {filtered.map((file) => {
                const BackendIcon = getBackendIcon(file.storage_backend);
                return (
                  <div
                    key={file.id}
                    className="flex items-center gap-3 p-4 hover:bg-muted/30 transition-colors"
                  >
                    <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-muted">
                      <FileIcon className="h-4 w-4 text-muted-foreground" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-sm truncate">{file.filename}</span>
                        {file.is_public && (
                          <Badge variant="success" className="shrink-0 text-xs">
                            <CheckCircle2 className="h-3 w-3 mr-1" />Public
                          </Badge>
                        )}
                      </div>
                      <div className="flex items-center gap-3 mt-0.5 text-xs text-muted-foreground">
                        <span>{formatSize(file.file_size)}</span>
                        <span className="flex items-center gap-0.5">
                          <BackendIcon className="h-3 w-3" />
                          {file.storage_backend}
                        </span>
                        <span>{file.mime_type || "unknown"}</span>
                        <span>{formatDate(file.created_at)}</span>
                      </div>
                    </div>
                    <div className="flex items-center gap-1 shrink-0">
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => handleDownload(file.file_id, file.filename)}
                        className="h-8 px-2"
                      >
                        <Download className="h-3.5 w-3.5" />
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => handleDelete(file.file_id, file.filename)}
                        className="h-8 px-2 text-destructive hover:text-destructive"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </Button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
