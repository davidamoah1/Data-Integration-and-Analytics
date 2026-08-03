"use client";

import { useEffect, useState, useRef } from "react";
import { Loader2, CheckCircle2, XCircle, Ban } from "lucide-react";
import { jobService, type JobPollResponse } from "@/services/jobs/jobService";
import { cn } from "@/lib/utils";

/**
 * Inline job progress tracker — polls a job and shows a compact progress indicator.
 * Use this in pages that create jobs (e.g., capture upload, report generation).
 *
 * Usage:
 *   <JobProgressTracker jobId={123} onComplete={() => refreshData()} />
 */
export function JobProgressTracker({
  jobId,
  onComplete,
  onError,
  pollIntervalMs = 2000,
  className,
}: {
  jobId: number;
  onComplete?: (result: JobPollResponse) => void;
  onError?: (error: string) => void;
  pollIntervalMs?: number;
  className?: string;
}) {
  const [poll, setPoll] = useState<JobPollResponse | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    if (!jobId) return;

    let cancelled = false;

    const pollJob = async () => {
      try {
        const data = await jobService.pollJob(jobId);
        if (cancelled) return;
        setPoll(data);

        if (data.status === "completed") {
          if (intervalRef.current) clearInterval(intervalRef.current);
          onComplete?.(data);
        } else if (data.status === "failed") {
          if (intervalRef.current) clearInterval(intervalRef.current);
          onError?.(data.error || "Job failed");
        } else if (data.status === "cancelled") {
          if (intervalRef.current) clearInterval(intervalRef.current);
        }
      } catch {
        // Silent poll failure
      }
    };

    pollJob();
    intervalRef.current = setInterval(pollJob, pollIntervalMs);

    return () => {
      cancelled = true;
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [jobId, pollIntervalMs, onComplete, onError]);

  if (!poll) {
    return (
      <div className={cn("flex items-center gap-2 text-sm text-muted-foreground", className)}>
        <Loader2 className="h-4 w-4 animate-spin" />
        Starting...
      </div>
    );
  }

  const pct = Math.round(poll.progress * 100);
  const isRunning = poll.status === "running" || poll.status === "pending";
  const isCompleted = poll.status === "completed";
  const isFailed = poll.status === "failed";
  const isCancelled = poll.status === "cancelled";

  return (
    <div className={cn("space-y-1.5", className)}>
      <div className="flex items-center gap-2 text-sm">
        {isRunning && <Loader2 className="h-4 w-4 animate-spin text-warning" />}
        {isCompleted && <CheckCircle2 className="h-4 w-4 text-green-500" />}
        {isFailed && <XCircle className="h-4 w-4 text-destructive" />}
        {isCancelled && <Ban className="h-4 w-4 text-muted-foreground" />}
        <span className={cn(
          "font-medium",
          isCompleted && "text-green-600",
          isFailed && "text-destructive",
          isCancelled && "text-muted-foreground",
        )}>
          {poll.progress_message || (isRunning ? "Processing..." : poll.status.charAt(0).toUpperCase() + poll.status.slice(1))}
        </span>
        {isRunning && <span className="text-muted-foreground">{pct}%</span>}
      </div>

      {isRunning && (
        <div className="h-1.5 w-full rounded-full bg-muted overflow-hidden">
          <div
            className="h-full rounded-full bg-primary transition-all duration-500"
            style={{ width: `${pct}%` }}
          />
        </div>
      )}

      {isFailed && poll.error && (
        <p className="text-xs text-destructive">{poll.error}</p>
      )}
    </div>
  );
}
