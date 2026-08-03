"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import {
  Loader2, CheckCircle2, XCircle, Clock, Ban, RotateCw,
  Database, FileText, ScanLine, Upload, Download, Activity,
} from "lucide-react";
import { jobService, type Job, type JobStatus, type JobSummary } from "@/services/jobs/jobService";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { cn } from "@/lib/utils";
import { toast } from "@/components/ui/Toaster";

const STATUS_CONFIG: Record<JobStatus, { label: string; variant: "default" | "secondary" | "destructive" | "success" | "warning" | "outline"; icon: typeof Loader2 }> = {
  pending: { label: "Pending", variant: "secondary", icon: Clock },
  running: { label: "Running", variant: "warning", icon: Loader2 },
  completed: { label: "Completed", variant: "success", icon: CheckCircle2 },
  failed: { label: "Failed", variant: "destructive", icon: XCircle },
  cancelled: { label: "Cancelled", variant: "outline", icon: Ban },
};

const JOB_TYPE_ICONS: Record<string, typeof Database> = {
  etl_run: Database,
  ocr_batch: ScanLine,
  report_gen: FileText,
  data_import: Upload,
  export: Download,
  custom: Activity,
};

function formatDuration(seconds: number | null): string {
  if (seconds === null) return "—";
  if (seconds < 60) return `${seconds.toFixed(1)}s`;
  const mins = Math.floor(seconds / 60);
  const secs = Math.round(seconds % 60);
  return `${mins}m ${secs}s`;
}

function formatTime(iso: string | null): string {
  if (!iso) return "—";
  const d = new Date(iso);
  return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

export function JobMonitor() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [summary, setSummary] = useState<JobSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<JobStatus | "all">("all");
  const pollIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const loadData = useCallback(async () => {
    try {
      const [jobList, summaryData] = await Promise.all([
        jobService.listJobs(filter === "all" ? undefined : { status: filter, limit: 100 }),
        jobService.getSummary(),
      ]);
      setJobs(jobList.jobs);
      setSummary(summaryData);
    } catch {
      // Silent fail on poll
    } finally {
      setLoading(false);
    }
  }, [filter]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Auto-poll when there are active jobs
  useEffect(() => {
    const hasActive = jobs.some((j) => j.status === "pending" || j.status === "running");
    if (hasActive) {
      pollIntervalRef.current = setInterval(loadData, 3000);
    } else if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
      pollIntervalRef.current = null;
    }
    return () => {
      if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
    };
  }, [jobs, loadData]);

  const handleCancel = async (jobId: number) => {
    try {
      await jobService.cancelJob(jobId);
      toast.success("Job cancelled");
      loadData();
    } catch {
      toast.error("Failed to cancel job");
    }
  };

  const handleRetry = async (jobId: number) => {
    try {
      await jobService.retryJob(jobId);
      toast.success("Job retried");
      loadData();
    } catch {
      toast.error("Failed to retry job");
    }
  };

  const activeCount = (summary?.running ?? 0) + (summary?.pending ?? 0);

  return (
    <div className="space-y-4">
      {/* Summary cards */}
      {summary && (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 lg:grid-cols-6">
          <SummaryCard label="Total" value={summary.total} icon={Activity} />
          <SummaryCard label="Active" value={activeCount} icon={Loader2} highlight={activeCount > 0} />
          <SummaryCard label="Completed" value={summary.completed} icon={CheckCircle2} />
          <SummaryCard label="Failed" value={summary.failed} icon={XCircle} />
          <SummaryCard label="Pending" value={summary.pending} icon={Clock} />
          <SummaryCard label="Cancelled" value={summary.cancelled} icon={Ban} />
        </div>
      )}

      {/* Filter tabs */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1">
        {(["all", "pending", "running", "completed", "failed", "cancelled"] as const).map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={cn(
              "rounded-md px-3 py-1.5 text-sm font-medium transition-colors",
              filter === f
                ? "bg-primary text-primary-foreground"
                : "bg-muted hover:bg-muted/80 text-muted-foreground",
            )}
          >
            {f.charAt(0).toUpperCase() + f.slice(1)}
          </button>
        ))}
      </div>

      {/* Job list */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Activity className="h-4 w-4" />
            Background Jobs
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          ) : jobs.length === 0 ? (
            <div className="py-12 text-center text-sm text-muted-foreground">
              No jobs found.
            </div>
          ) : (
            <div className="divide-y">
              {jobs.map((job) => (
                <JobRow
                  key={job.id}
                  job={job}
                  onCancel={handleCancel}
                  onRetry={handleRetry}
                />
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function SummaryCard({
  label,
  value,
  icon: Icon,
  highlight,
}: {
  label: string;
  value: number;
  icon: typeof Activity;
  highlight?: boolean;
}) {
  return (
    <Card className={cn(highlight && "border-warning/50 bg-warning/5")}>
      <CardContent className="flex items-center gap-3 p-3">
        <div className={cn(
          "flex h-9 w-9 items-center justify-center rounded-lg",
          highlight ? "bg-warning/15 text-warning" : "bg-muted text-muted-foreground",
        )}>
          <Icon className={cn("h-4 w-4", highlight && "animate-spin")} />
        </div>
        <div>
          <p className="text-xl font-bold leading-none">{value}</p>
          <p className="text-xs text-muted-foreground mt-1">{label}</p>
        </div>
      </CardContent>
    </Card>
  );
}

function JobRow({
  job,
  onCancel,
  onRetry,
}: {
  job: Job;
  onCancel: (id: number) => void;
  onRetry: (id: number) => void;
}) {
  const statusCfg = STATUS_CONFIG[job.status];
  const StatusIcon = statusCfg.icon;
  const TypeIcon = JOB_TYPE_ICONS[job.job_type] ?? Activity;
  const isActive = job.status === "pending" || job.status === "running";
  const progressPct = Math.round(job.progress * 100);

  return (
    <div className="flex items-start gap-3 p-4 hover:bg-muted/30 transition-colors">
      {/* Type icon */}
      <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-muted">
        <TypeIcon className="h-4 w-4 text-muted-foreground" />
      </div>

      {/* Main content */}
      <div className="flex-1 min-w-0 space-y-1.5">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="font-medium text-sm truncate">{job.name}</span>
          <Badge variant={statusCfg.variant} className="shrink-0">
            <StatusIcon className={cn("h-3 w-3 mr-1", job.status === "running" && "animate-spin")} />
            {statusCfg.label}
          </Badge>
          <span className="text-xs text-muted-foreground font-mono">{job.job_type}</span>
        </div>

        {job.description && (
          <p className="text-xs text-muted-foreground truncate">{job.description}</p>
        )}

        {/* Progress bar for active jobs */}
        {isActive && (
          <div className="space-y-1">
            <div className="h-1.5 w-full rounded-full bg-muted overflow-hidden">
              <div
                className="h-full rounded-full bg-primary transition-all duration-500"
                style={{ width: `${progressPct}%` }}
              />
            </div>
            {job.progress_message && (
              <p className="text-xs text-muted-foreground">{job.progress_message} ({progressPct}%)</p>
            )}
          </div>
        )}

        {/* Error message */}
        {job.status === "failed" && job.error && (
          <p className="text-xs text-destructive truncate">{job.error}</p>
        )}

        {/* Result summary */}
        {job.status === "completed" && job.result && (
          <p className="text-xs text-muted-foreground">
            {job.duration_seconds !== null && `Completed in ${formatDuration(job.duration_seconds)}`}
          </p>
        )}

        {/* Meta */}
        <div className="flex items-center gap-3 text-xs text-muted-foreground">
          <span>Created {formatTime(job.created_at)}</span>
          {job.started_at && <span>Started {formatTime(job.started_at)}</span>}
          {job.retries > 0 && <span>Retries: {job.retries}/{job.max_retries}</span>}
        </div>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-1 shrink-0">
        {isActive && (
          <Button
            size="sm"
            variant="ghost"
            onClick={() => onCancel(job.id)}
            className="h-8 px-2 text-destructive hover:text-destructive"
          >
            <Ban className="h-3.5 w-3.5" />
          </Button>
        )}
        {(job.status === "failed" || job.status === "cancelled") && (
          <Button
            size="sm"
            variant="ghost"
            onClick={() => onRetry(job.id)}
            className="h-8 px-2"
          >
            <RotateCw className="h-3.5 w-3.5" />
          </Button>
        )}
      </div>
    </div>
  );
}
