"use client";

import { CheckCircle2, XCircle, Loader2, Clock, AlertCircle } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import type { WorkflowState } from "@/types/workflow";

const STAGE_LABELS: Record<string, string> = {
  uploaded: "Uploaded",
  validated: "Validated",
  profiled: "Profiled",
  quality_checked: "Quality Checked",
  semantically_analyzed: "Semantic Analysis",
  industry_identified: "Industry Detection",
  metadata_generated: "Metadata Generated",
  knowledge_extracted: "Knowledge Extraction",
  insights_generated: "Smart Insights",
  dashboard_ready: "Dashboard Ready",
  analysis_complete: "Analysis Complete",
};

const STAGE_ORDER = [
  "uploaded",
  "validated",
  "profiled",
  "quality_checked",
  "semantically_analyzed",
  "industry_identified",
  "metadata_generated",
  "knowledge_extracted",
  "insights_generated",
  "dashboard_ready",
  "analysis_complete",
];

interface Props {
  workflow: WorkflowState;
  onRetry: (stage: string) => void;
}

export function WorkflowTimeline({ workflow, onRetry }: Props) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Processing Timeline</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-1">
          {STAGE_ORDER.map((stageKey, idx) => {
            const stage = workflow.stages[stageKey];
            if (!stage) return null;

            const isLast = idx === STAGE_ORDER.length - 1;

            return (
              <div key={stageKey} className="flex gap-4">
                <div className="flex flex-col items-center">
                  <div className="flex h-8 w-8 items-center justify-center rounded-full border-2">
                    {stage.status === "completed" && (
                      <CheckCircle2 className="h-5 w-5 text-green-600" />
                    )}
                    {stage.status === "running" && (
                      <Loader2 className="h-5 w-5 text-blue-600 animate-spin" />
                    )}
                    {stage.status === "failed" && (
                      <XCircle className="h-5 w-5 text-red-600" />
                    )}
                    {stage.status === "pending" && (
                      <Clock className="h-4 w-4 text-muted-foreground" />
                    )}
                    {stage.status === "skipped" && (
                      <AlertCircle className="h-4 w-4 text-muted-foreground" />
                    )}
                  </div>
                  {!isLast && (
                    <div className={`w-0.5 h-12 ${stage.status === "completed" ? "bg-green-600" : "bg-border"}`} />
                  )}
                </div>

                <div className="flex-1 pb-8">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium">{STAGE_LABELS[stageKey] || stageKey}</p>
                      <p className="text-sm text-muted-foreground capitalize">{stage.status}</p>
                    </div>
                    <div className="flex items-center gap-3">
                      {stage.duration_seconds != null && stage.duration_seconds > 0 && (
                        <span className="text-xs text-muted-foreground">
                          {stage.duration_seconds.toFixed(2)}s
                        </span>
                      )}
                      {stage.status === "failed" && (
                        <Button size="sm" variant="outline" onClick={() => onRetry(stageKey)}>
                          Retry
                        </Button>
                      )}
                    </div>
                  </div>

                  {stage.error && (
                    <p className="text-sm text-red-600 mt-1">{stage.error}</p>
                  )}

                  {stage.status === "completed" && stage.result && Object.keys(stage.result).length > 0 && (
                    <div className="mt-2 text-sm text-muted-foreground">
                      {stageKey === "uploaded" && (
                        <span>
                          {String(stage.result.row_count || 0).replace(/\B(?=(\d{3})+(?!\d))/g, ",")} rows,{" "}
                          {String(stage.result.column_count || 0)} columns
                        </span>
                      )}
                      {stageKey === "profiled" && (
                        <span>Quality score: {Number(stage.result.overall_quality_score || 0).toFixed(1)}/100</span>
                      )}
                      {stageKey === "quality_checked" && !!stage.result.score && (
                        <span>
                          Score: {Number((stage.result.score as Record<string, number>).overall || 0).toFixed(1)}/100
                          {" — "}
                          {(stage.result.score as Record<string, string>).grade}
                        </span>
                      )}
                      {stageKey === "industry_identified" && (
                        <span>
                          {String(stage.result.industry || "unknown")} ({Number(stage.result.confidence || 0).toFixed(0)}% confidence)
                        </span>
                      )}
                      {stageKey === "insights_generated" && (
                        <span>{String(stage.result.total_insights || 0)} insights generated</span>
                      )}
                      {stageKey === "dashboard_ready" && (
                        <span>{stage.result.recommended ? "Dashboard recommended" : "No recommendation"}</span>
                      )}
                      {stageKey === "analysis_complete" && (
                        <span>Workflow complete</span>
                      )}
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
