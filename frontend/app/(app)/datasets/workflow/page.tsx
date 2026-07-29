"use client";

import { useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { Upload, FileText, AlertCircle, CheckCircle2, Loader2, XCircle, ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Alert } from "@/components/ui/Alert";
import { workflowService } from "@/services/workflow/workflowService";
import type { WorkflowState } from "@/types/workflow";
import { WorkflowTimeline } from "@/features/dataset-workflow/WorkflowTimeline";
import { QualityReportView } from "@/features/dataset-workflow/QualityReportView";
import { IndustryDetectionView } from "@/features/dataset-workflow/IndustryDetectionView";
import { InsightCards } from "@/features/dataset-workflow/InsightCards";
import { DashboardPreview } from "@/features/dataset-workflow/DashboardPreview";
import { ProfileSummary } from "@/features/dataset-workflow/ProfileSummary";

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

export default function DatasetWorkflowPage() {
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [workflow, setWorkflow] = useState<WorkflowState | null>(null);
  const [activeTab, setActiveTab] = useState<string>("timeline");

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setError(null);
    }
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setFile(e.dataTransfer.files[0]);
      setError(null);
    }
  }, []);

  const handleRun = async () => {
    if (!file) return;
    setLoading(true);
    setError(null);
    try {
      const result = await workflowService.runWorkflow(file);
      setWorkflow(result);
      setActiveTab("timeline");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to run workflow";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const handleRetry = async (stage: string) => {
    if (!workflow) return;
    try {
      const result = await workflowService.retryStage(workflow.workflow_id, stage);
      setWorkflow(result);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to retry stage";
      setError(msg);
    }
  };

  const tabs = [
    { id: "timeline", label: "Timeline" },
    { id: "profile", label: "Profile" },
    { id: "quality", label: "Quality" },
    { id: "industry", label: "Industry" },
    { id: "insights", label: "Insights" },
    { id: "dashboard", label: "Dashboard" },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Dataset Intelligence Workflow</h1>
        <p className="text-muted-foreground mt-1">
          Upload a dataset to automatically profile, assess quality, detect industry, generate insights, and recommend dashboards.
        </p>
      </div>

      {!workflow && (
        <Card>
          <CardHeader>
            <CardTitle>Upload Dataset</CardTitle>
            <CardDescription>CSV or Excel files supported</CardDescription>
          </CardHeader>
          <CardContent>
            <div
              onDrop={handleDrop}
              onDragOver={(e) => e.preventDefault()}
              className="border-2 border-dashed border-muted-foreground/25 rounded-lg p-12 text-center hover:border-muted-foreground/50 transition-colors cursor-pointer"
              onClick={() => document.getElementById("file-input")?.click()}
            >
              {file ? (
                <div className="flex flex-col items-center gap-2">
                  <FileText className="h-12 w-12 text-primary" />
                  <p className="font-medium">{file.name}</p>
                  <p className="text-sm text-muted-foreground">
                    {(file.size / 1024 / 1024).toFixed(2)} MB
                  </p>
                </div>
              ) : (
                <div className="flex flex-col items-center gap-2">
                  <Upload className="h-12 w-12 text-muted-foreground" />
                  <p className="font-medium">Drag and drop or click to upload</p>
                  <p className="text-sm text-muted-foreground">CSV, XLS, XLSX</p>
                </div>
              )}
              <input
                id="file-input"
                type="file"
                accept=".csv,.xlsx,.xls"
                onChange={handleFileSelect}
                className="hidden"
              />
            </div>

            {error && (
              <Alert variant="destructive" className="mt-4">
                <AlertCircle className="h-4 w-4" />
                <span>{error}</span>
              </Alert>
            )}

            <Button
              onClick={handleRun}
              disabled={!file || loading}
              className="mt-4 w-full"
            >
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Processing...
                </>
              ) : (
                <>
                  <ArrowRight className="mr-2 h-4 w-4" />
                  Run Intelligence Workflow
                </>
              )}
            </Button>
          </CardContent>
        </Card>
      )}

      {workflow && (
        <>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <FileText className="h-5 w-5 text-primary" />
              <span className="font-medium">{workflow.dataset_name}</span>
              {workflow.is_complete ? (
                <Badge variant="default" className="bg-green-600">
                  <CheckCircle2 className="mr-1 h-3 w-3" /> Complete
                </Badge>
              ) : workflow.has_errors ? (
                <Badge variant="destructive">
                  <XCircle className="mr-1 h-3 w-3" /> Errors
                </Badge>
              ) : (
                <Badge variant="secondary">
                  <Loader2 className="mr-1 h-3 w-3 animate-spin" /> Processing
                </Badge>
              )}
            </div>
            <Button variant="outline" size="sm" onClick={() => { setWorkflow(null); setFile(null); }}>
              New Upload
            </Button>
          </div>

          <div className="flex gap-2 border-b">
            {tabs.map((tab) => {
              const stageMap: Record<string, string> = {
                profile: "profiled",
                quality: "quality_checked",
                industry: "industry_identified",
                insights: "insights_generated",
                dashboard: "dashboard_ready",
              };
              const stageKey = stageMap[tab.id];
              const stageData = stageKey ? workflow.stages[stageKey] : null;
              const isReady = !stageData || stageData.status === "completed";

              return (
                <button
                  key={tab.id}
                  onClick={() => isReady && setActiveTab(tab.id)}
                  disabled={!isReady}
                  className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
                    activeTab === tab.id
                      ? "border-primary text-primary"
                      : isReady
                        ? "border-transparent text-muted-foreground hover:text-foreground"
                        : "border-transparent text-muted-foreground/40 cursor-not-allowed"
                  }`}
                >
                  {tab.label}
                </button>
              );
            })}
          </div>

          <div className="mt-4">
            {activeTab === "timeline" && (
              <WorkflowTimeline workflow={workflow} onRetry={handleRetry} />
            )}
            {activeTab === "profile" && workflow.stages.profiled?.status === "completed" && (
              <ProfileSummary workflowId={workflow.workflow_id} />
            )}
            {activeTab === "quality" && workflow.stages.quality_checked?.status === "completed" && (
              <QualityReportView workflowId={workflow.workflow_id} />
            )}
            {activeTab === "industry" && workflow.stages.industry_identified?.status === "completed" && (
              <IndustryDetectionView workflowId={workflow.workflow_id} />
            )}
            {activeTab === "insights" && workflow.stages.insights_generated?.status === "completed" && (
              <InsightCards workflowId={workflow.workflow_id} />
            )}
            {activeTab === "dashboard" && workflow.stages.dashboard_ready?.status === "completed" && (
              <DashboardPreview workflowId={workflow.workflow_id} />
            )}
          </div>
        </>
      )}
    </div>
  );
}
