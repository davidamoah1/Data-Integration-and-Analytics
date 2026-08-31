'use client';

import { useState, useCallback } from 'react';
import {
  WorkflowStepper,
  UploadStep,
  UnderstandStep,
  CleanStep,
  AnalyzeStep,
  VisualizeStep,
  ReportStep,
  PresentStep,
} from '@/features/data-workflow';
import type { WorkflowStep, StepStatus } from '@/features/data-workflow';
import type {
  WorkflowState,
  DatasetProfile,
  QualityReport,
  IndustryResult,
  InsightsResult,
  DashboardRecommendation,
  QualityFinding,
} from '@/types/workflow';
import { workflowService } from '@/services/workflow/workflowService';
import { datasetService } from '@/services/datasets/datasetService';
import { apiClient, getAccessToken } from '@/services/api/client';
import { toast } from '@/components/ui/Toaster';
import { Button } from '@/components/ui/Button';
import { Loader2, Upload } from 'lucide-react';

interface TransformationRecord {
  id: string;
  timestamp: string;
  action: string;
  description: string;
  affected_rows: number;
  undone: boolean;
}

export default function DataToDecisionPage() {
  // Workflow state
  const [currentStep, setCurrentStep] = useState<WorkflowStep>('upload');
  const [stepStatuses, setStepStatuses] = useState<Partial<Record<WorkflowStep, StepStatus>>>({
    upload: 'active',
  });

  // File & workflow
  const [file, setFile] = useState<File | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [hasError, setHasError] = useState(false);
  const [processingMessage, setProcessingMessage] = useState<string>('');
  const [workflowState, setWorkflowState] = useState<WorkflowState | null>(null);

  // Data from workflow stages
  const [profile, setProfile] = useState<DatasetProfile | null>(null);
  const [quality, setQuality] = useState<QualityReport | null>(null);
  const [industry, setIndustry] = useState<IndustryResult | null>(null);
  const [insights, setInsights] = useState<InsightsResult | null>(null);
  const [dashboard, setDashboard] = useState<DashboardRecommendation | null>(null);

  // Clean step
  const [transformations, setTransformations] = useState<TransformationRecord[]>([]);
  const [isApplyingFix, setIsApplyingFix] = useState(false);

  // Visualize step
  const [isSavingDashboard, setIsSavingDashboard] = useState(false);
  const [savedDashboardId, setSavedDashboardId] = useState<number | null>(null);

  // Report step
  const [isGeneratingReport, setIsGeneratingReport] = useState(false);
  const [reportId, setReportId] = useState<number | null>(null);

  // Present step
  const [isGeneratingPresentation, setIsGeneratingPresentation] = useState(false);
  const [presentationReady, setPresentationReady] = useState(false);
  const [presentationUrl, setPresentationUrl] = useState<string | null>(null);

  // === Upload Step ===
  const handleFileSelected = useCallback((f: File) => {
    setFile(f);
    setHasError(false);
  }, []);

  const handleStartProcessing = useCallback(async () => {
    if (!file) return;
    setIsProcessing(true);
    setHasError(false);
    setProcessingMessage('Uploading and analyzing dataset...');
    setStepStatuses((prev) => ({ ...prev, upload: 'active' }));

    try {
      // Run the full workflow (handles both sync and async backend modes)
      const result = await workflowService.runWorkflow(file, false, (message, progress) => {
        setProcessingMessage(`${message} (${Math.round(progress * 100)}%)`);
      });
      setWorkflowState(result);

      // Mark upload complete, move to understand
      setStepStatuses((prev) => ({ ...prev, upload: 'completed', understand: 'active' }));
      setProcessingMessage('Loading analysis results...');

      // Load the detail data
      if (result.workflow_id) {
        const [profileData, qualityData, industryData, insightsData, dashboardData] =
          await Promise.allSettled([
            workflowService.getProfile(result.workflow_id),
            workflowService.getQuality(result.workflow_id),
            workflowService.getIndustry(result.workflow_id),
            workflowService.getInsights(result.workflow_id),
            workflowService.getDashboard(result.workflow_id),
          ]);

        if (profileData.status === 'fulfilled') setProfile(profileData.value);
        if (qualityData.status === 'fulfilled') setQuality(qualityData.value);
        if (industryData.status === 'fulfilled') setIndustry(industryData.value);
        if (insightsData.status === 'fulfilled') setInsights(insightsData.value);
        if (dashboardData.status === 'fulfilled') setDashboard(dashboardData.value);
      }

      setCurrentStep('understand');
      setProcessingMessage('');
      toast.success('Dataset uploaded and analyzed successfully!');
    } catch (err) {
      setStepStatuses((prev) => ({ ...prev, upload: 'error' }));
      setHasError(true);
      setProcessingMessage('');
      toast.error(err instanceof Error ? err.message : 'Failed to process dataset');
    } finally {
      setIsProcessing(false);
    }
  }, [file]);

  // === Navigate between steps ===
  const goToStep = useCallback(
    (step: WorkflowStep) => {
      setCurrentStep(step);
      setStepStatuses((prev) => ({ ...prev, [step]: prev[step] === 'completed' ? 'completed' : 'active' }));
    },
    [],
  );

  const completeAndAdvance = useCallback(
    (from: WorkflowStep, to: WorkflowStep) => {
      setStepStatuses((prev) => ({ ...prev, [from]: 'completed', [to]: 'active' }));
      setCurrentStep(to);
    },
    [],
  );

  // === Clean Step ===
  const handleApplyFix = useCallback(async (finding: QualityFinding) => {
    setIsApplyingFix(true);
    try {
      // Record the transformation
      const newTransformation: TransformationRecord = {
        id: `t-${Date.now()}`,
        timestamp: new Date().toISOString(),
        action: finding.check_name,
        description: finding.suggested_fix || `Fixed: ${finding.message}`,
        affected_rows: finding.affected_rows,
        undone: false,
      };
      setTransformations((prev) => [newTransformation, ...prev]);
      toast.success(`Applied fix: ${finding.suggested_fix || finding.check_name}`);
    } finally {
      setIsApplyingFix(false);
    }
  }, []);

  const handleUndoTransformation = useCallback((id: string) => {
    setTransformations((prev) =>
      prev.map((t) => (t.id === id ? { ...t, undone: true } : t)),
    );
    toast.success('Transformation undone');
  }, []);

  const handleApplyAllSuggested = useCallback(() => {
    if (!quality) return;
    const fixable = quality.findings.filter((f) => f.suggested_fix);
    const newTransformations: TransformationRecord[] = fixable.map((f, i) => ({
      id: `t-batch-${Date.now()}-${i}`,
      timestamp: new Date().toISOString(),
      action: f.check_name,
      description: f.suggested_fix || `Fixed: ${f.message}`,
      affected_rows: f.affected_rows,
      undone: false,
    }));
    setTransformations((prev) => [...newTransformations, ...prev]);
    toast.success(`Applied ${fixable.length} suggested fixes`);
  }, [quality]);

  // === Analyze Step ===
  const handleAskQuestion = useCallback(async (question: string) => {
    if (!workflowState?.workflow_id) {
      toast.error('No active workflow');
      return;
    }
    try {
      await workflowService.runAnalysis(workflowState.workflow_id, {
        mode: 'easy',
        question,
      });
      toast.success(`Analysis complete for: "${question}"`);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Analysis failed');
    }
  }, [workflowState]);

  // === Visualize Step ===
  const handleSaveDashboard = useCallback(async () => {
    if (!dashboard || !file) return;
    setIsSavingDashboard(true);
    try {
      const result = await datasetService.persistAnalysis({
        table_name: file.name,
        industry: industry?.industry,
        dashboard_config: dashboard.dashboard_config ?? undefined,
        kpis: [],
        recommendations: [],
        alerts: [],
      });
      setSavedDashboardId(result.dashboard_id);
      toast.success('Dashboard saved!');
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to save dashboard');
    } finally {
      setIsSavingDashboard(false);
    }
  }, [dashboard, file, industry]);

  // === Report Step ===
  const handleGenerateReport = useCallback(async () => {
    setIsGeneratingReport(true);
    try {
      if (!file) return;
      const result = await datasetService.persistAnalysis({
        table_name: file.name,
        industry: industry?.industry,
        dashboard_config: dashboard?.dashboard_config ?? undefined,
        kpis: [],
        recommendations: quality?.recommendations ?? [],
        alerts: [],
      });
      setReportId(result.report_id);
      toast.success('Report generated!');
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to generate report');
    } finally {
      setIsGeneratingReport(false);
    }
  }, [file, industry, dashboard, quality]);

  // === Present Step ===
  const handleGeneratePresentation = useCallback(async () => {
    if (!workflowState?.workflow_id) return;
    setIsGeneratingPresentation(true);
    try {
      // Call the actual presentation generation API
      const apiUrl = apiClient.getApiUrl();
      const token = getAccessToken();
      const headers: Record<string, string> = { 'Content-Type': 'application/json' };
      if (token) headers['Authorization'] = `Bearer ${token}`;
      const response = await fetch(
        `${apiUrl}/api/dataset-workflow/${workflowState.workflow_id}/presentation`,
        {
          method: 'POST',
          headers,
          body: JSON.stringify({ template: 'executive', title: `${file?.name} — Analysis` }),
        },
      );
      if (!response.ok) {
        const errorBody = await response.text().catch(() => '');
        if (response.status === 401) throw new Error('Your session has expired. Please sign in again.');
        if (response.status === 403) throw new Error('You don\'t have permission to generate this presentation.');
        if (response.status === 404) throw new Error('Workflow not found. Please run the analysis first.');
        if (response.status === 422) throw new Error('The analysis does not contain enough data for a presentation.');
        throw new Error(`Presentation generation failed (${response.status})`);
      }
      // Store the blob for download
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      setPresentationUrl(url);
      setPresentationReady(true);
      toast.success('Presentation generated!');
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to generate presentation');
    } finally {
      setIsGeneratingPresentation(false);
    }
  }, [workflowState, file]);

  const handleDownloadPresentation = useCallback(() => {
    if (presentationUrl) {
      const a = document.createElement('a');
      a.href = presentationUrl;
      a.download = `${file?.name || 'analysis'}_presentation.pptx`;
      a.click();
    }
  }, [presentationUrl, file]);

  const handleStartOver = useCallback(() => {
    setCurrentStep('upload');
    setStepStatuses({ upload: 'active' });
    setFile(null);
    setWorkflowState(null);
    setProfile(null);
    setQuality(null);
    setIndustry(null);
    setInsights(null);
    setDashboard(null);
    setTransformations([]);
    setSavedDashboardId(null);
    setReportId(null);
    setPresentationReady(false);
    setPresentationUrl(null);
  }, []);

  return (
    <div className="space-y-8 max-w-5xl mx-auto">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Data to Decision</h1>
        <p className="text-muted-foreground mt-1">
          Upload your data and let the platform guide you from raw data to professional insights, reports, and presentations.
        </p>
      </div>

      {/* Workflow Stepper */}
      <WorkflowStepper
        currentStep={currentStep}
        stepStatuses={stepStatuses}
        onStepClick={goToStep}
      />

      {/* Processing Indicator */}
      {isProcessing && (
        <div className="flex items-center justify-center gap-3 py-8">
          <Loader2 className="h-6 w-6 animate-spin text-primary" />
          <div>
            <p className="font-medium">{processingMessage || 'Preparing your dataset...'}</p>
            <p className="text-sm text-muted-foreground">
              This may take a few minutes for large datasets
            </p>
          </div>
        </div>
      )}

      {/* Error state with Try Again */}
      {hasError && !isProcessing && currentStep === 'upload' && file && (
        <div className="flex flex-col items-center gap-4 py-8">
          <div className="text-center">
            <p className="font-medium text-red-600">We couldn't process this dataset. Please try again.</p>
            <p className="text-sm text-muted-foreground mt-1">
              If the problem persists, try a smaller file or contact your administrator.
            </p>
          </div>
          <Button onClick={handleStartProcessing} size="lg">
            <Upload className="mr-2 h-4 w-4" />
            Try Again
          </Button>
        </div>
      )}

      {/* Step Content */}
      {!isProcessing && !hasError && currentStep === 'upload' && (
        <UploadStep
          file={file}
          onFileSelected={handleFileSelected}
          onStartProcessing={handleStartProcessing}
          isProcessing={isProcessing}
        />
      )}

      {currentStep === 'understand' && (
        <UnderstandStep
          profile={profile}
          quality={quality}
          industry={industry}
          onContinue={() => completeAndAdvance('understand', 'clean')}
        />
      )}

      {currentStep === 'clean' && (
        <CleanStep
          findings={quality?.findings ?? []}
          transformations={transformations}
          onApplyFix={handleApplyFix}
          onUndoTransformation={handleUndoTransformation}
          onApplyAllSuggested={handleApplyAllSuggested}
          onContinue={() => completeAndAdvance('clean', 'analyze')}
          isApplying={isApplyingFix}
        />
      )}

      {currentStep === 'analyze' && (
        <AnalyzeStep
          insights={insights}
          industry={industry?.industry ?? 'general'}
          onAskQuestion={handleAskQuestion}
          onContinue={() => completeAndAdvance('analyze', 'visualize')}
        />
      )}

      {currentStep === 'visualize' && (
        <VisualizeStep
          dashboard={dashboard}
          onSaveDashboard={handleSaveDashboard}
          onContinue={() => completeAndAdvance('visualize', 'report')}
          isSaving={isSavingDashboard}
          savedDashboardId={savedDashboardId}
        />
      )}

      {currentStep === 'report' && (
        <ReportStep
          datasetName={file?.name ?? 'Dataset'}
          industry={industry?.industry ?? 'general'}
          onGenerateReport={handleGenerateReport}
          onContinue={() => completeAndAdvance('report', 'present')}
          reportId={reportId}
          isGenerating={isGeneratingReport}
        />
      )}

      {currentStep === 'present' && (
        <PresentStep
          datasetName={file?.name ?? 'Dataset'}
          onGeneratePresentation={handleGeneratePresentation}
          onDownloadPresentation={handleDownloadPresentation}
          onStartOver={handleStartOver}
          isGenerating={isGeneratingPresentation}
          presentationReady={presentationReady}
        />
      )}
    </div>
  );
}
