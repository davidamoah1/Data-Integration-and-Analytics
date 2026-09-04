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
  CleanPreviewData,
  AutoDashboardSpec,
  ReportConfig,
} from '@/types/workflow';
import { workflowService } from '@/services/workflow/workflowService';
import { datasetService } from '@/services/datasets/datasetService';
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
  const [errorMessage, setErrorMessage] = useState<string>('');
  const [processingMessage, setProcessingMessage] = useState<string>('');
  const [workflowState, setWorkflowState] = useState<WorkflowState | null>(null);

  // Data from workflow stages
  const [profile, setProfile] = useState<DatasetProfile | null>(null);
  const [quality, setQuality] = useState<QualityReport | null>(null);
  const [industry, setIndustry] = useState<IndustryResult | null>(null);
  const [insights, setInsights] = useState<InsightsResult | null>(null);
  const [dashboard, setDashboard] = useState<DashboardRecommendation | null>(null);
  const [autoDashboard, setAutoDashboard] = useState<AutoDashboardSpec | null>(null);

  // Clean step state
  const [cleanPreview, setCleanPreview] = useState<CleanPreviewData | null>(null);
  const [transformations, setTransformations] = useState<TransformationRecord[]>([]);
  const [isApplyingFix, setIsApplyingFix] = useState(false);

  // Visualize step
  const [isSavingDashboard, setIsSavingDashboard] = useState(false);
  const [savedDashboardId, setSavedDashboardId] = useState<number | null>(null);

  // Report step
  const [isGeneratingReport, setIsGeneratingReport] = useState(false);
  const [reportId, setReportId] = useState<number | null>(null);
  const [hasDownloadedReport, setHasDownloadedReport] = useState(false);

  // Present step
  const [isGeneratingPresentation, setIsGeneratingPresentation] = useState(false);
  const [presentationReady, setPresentationReady] = useState(false);

  // === Upload Step ===
  const handleFileSelected = useCallback((f: File) => {
    setFile(f);
    setHasError(false);
    setErrorMessage('');
  }, []);

  const handleStartProcessing = useCallback(async () => {
    if (!file) return;
    setIsProcessing(true);
    setHasError(false);
    setProcessingMessage('Uploading and analyzing dataset...');
    setStepStatuses((prev) => ({ ...prev, upload: 'active' }));

    try {
      // Run the full workflow
      const result = await workflowService.runWorkflow(file, false, (message, progress) => {
        setProcessingMessage(`${message} (${Math.round(progress * 100)}%)`);
      });
      setWorkflowState(result);

      // Mark upload complete, move to understand
      setStepStatuses((prev) => ({ ...prev, upload: 'completed', understand: 'active' }));
      setProcessingMessage('Loading analysis results & intelligence profiles...');

      // Load the detail data
      if (result.workflow_id) {
        const [
          profileData,
          qualityData,
          industryData,
          insightsData,
          dashboardData,
          autoDashData,
          cleanPreviewData,
          cleanHistData,
        ] = await Promise.allSettled([
          workflowService.getProfile(result.workflow_id),
          workflowService.getQuality(result.workflow_id),
          workflowService.getIndustry(result.workflow_id),
          workflowService.getInsights(result.workflow_id),
          workflowService.getDashboard(result.workflow_id),
          workflowService.getAutoDashboard(result.workflow_id),
          workflowService.getCleaningPreview(result.workflow_id),
          workflowService.getCleaningHistory(result.workflow_id),
        ]);

        if (profileData.status === 'fulfilled') setProfile(profileData.value);
        if (qualityData.status === 'fulfilled') setQuality(qualityData.value);
        if (industryData.status === 'fulfilled') setIndustry(industryData.value);
        if (insightsData.status === 'fulfilled') setInsights(insightsData.value);
        if (dashboardData.status === 'fulfilled') setDashboard(dashboardData.value);
        if (autoDashData.status === 'fulfilled') setAutoDashboard(autoDashData.value);
        if (cleanPreviewData.status === 'fulfilled') setCleanPreview(cleanPreviewData.value);
        if (cleanHistData.status === 'fulfilled' && cleanHistData.value.transformations) {
          setTransformations(cleanHistData.value.transformations);
        }
      }

      setCurrentStep('understand');
      setProcessingMessage('');
      toast.success('Dataset processed and analyzed successfully!');
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Failed to process dataset';
      setStepStatuses((prev) => ({ ...prev, upload: 'error' }));
      setHasError(true);
      setErrorMessage(msg);
      setProcessingMessage('');
      toast.error(msg);
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
  const handleRefreshPreview = useCallback(async () => {
    if (!workflowState?.workflow_id) return;
    try {
      const preview = await workflowService.getCleaningPreview(workflowState.workflow_id);
      setCleanPreview(preview);
    } catch (e) {
      // Quiet fail on background refresh
    }
  }, [workflowState]);

  const handleApplyFix = useCallback(async (finding: QualityFinding) => {
    if (!workflowState?.workflow_id) {
      toast.error('No active workflow session');
      return;
    }
    setIsApplyingFix(true);
    try {
      let action = 'fill_missing';
      let method: string | undefined = 'median';
      const chk = finding.check_name.toLowerCase();
      if (chk.includes('duplicate')) {
        action = 'remove_duplicates';
      } else if (chk.includes('outlier')) {
        action = 'cap_outliers';
      } else if (chk.includes('type') || chk.includes('numeric')) {
        action = 'convert_type';
      } else if (chk.includes('date')) {
        action = 'parse_dates';
      }

      const res = await workflowService.applyCleaningTransformation(workflowState.workflow_id, {
        check_name: finding.check_name,
        column: finding.column ?? undefined,
        action,
        method,
      });

      // Fetch live clean preview and updated history
      const [preview, hist] = await Promise.allSettled([
        workflowService.getCleaningPreview(workflowState.workflow_id),
        workflowService.getCleaningHistory(workflowState.workflow_id),
      ]);
      if (preview.status === 'fulfilled') setCleanPreview(preview.value);
      if (hist.status === 'fulfilled') setTransformations(hist.value.transformations);

      toast.success(`Applied fix: ${res.description || finding.suggested_fix || finding.check_name}`);
    } catch (err: any) {
      toast.error(err?.message || 'Failed to apply cleaning transformation');
    } finally {
      setIsApplyingFix(false);
    }
  }, [workflowState]);

  const handleUndoTransformation = useCallback(async (id: string) => {
    if (!workflowState?.workflow_id) return;
    setIsApplyingFix(true);
    try {
      await workflowService.undoCleaningTransformation(workflowState.workflow_id, id);
      const [preview, hist] = await Promise.allSettled([
        workflowService.getCleaningPreview(workflowState.workflow_id),
        workflowService.getCleaningHistory(workflowState.workflow_id),
      ]);
      if (preview.status === 'fulfilled') setCleanPreview(preview.value);
      if (hist.status === 'fulfilled') setTransformations(hist.value.transformations);
      toast.success('Transformation successfully reverted');
    } catch (err: any) {
      toast.error(err?.message || 'Failed to undo transformation');
    } finally {
      setIsApplyingFix(false);
    }
  }, [workflowState]);

  const handleApplyAllSuggested = useCallback(async () => {
    if (!workflowState?.workflow_id) return;
    setIsApplyingFix(true);
    try {
      const res = await workflowService.applyAllCleaningTransformations(
        workflowState.workflow_id,
        quality?.findings,
      );
      const [preview, hist] = await Promise.allSettled([
        workflowService.getCleaningPreview(workflowState.workflow_id),
        workflowService.getCleaningHistory(workflowState.workflow_id),
      ]);
      if (preview.status === 'fulfilled') setCleanPreview(preview.value);
      if (hist.status === 'fulfilled') setTransformations(hist.value.transformations);
      toast.success(`Successfully applied ${res.applied_count} automated cleaning fixes!`);
    } catch (err: any) {
      toast.error(err?.message || 'Failed to batch apply fixes');
    } finally {
      setIsApplyingFix(false);
    }
  }, [workflowState, quality]);

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
      toast.success(`Analysis computed for: "${question}"`);
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
        dashboard_config: (autoDashboard as any) || dashboard.dashboard_config || undefined,
        kpis: (autoDashboard?.kpis || []) as unknown as Array<Record<string, unknown>>,
        recommendations: quality?.recommendations ?? [],
        alerts: [],
      });
      setSavedDashboardId(result.dashboard_id);
      toast.success('Dashboard configuration saved to library!');
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to save dashboard');
    } finally {
      setIsSavingDashboard(false);
    }
  }, [dashboard, autoDashboard, file, industry, quality]);

  // === Report Step ===
  const handleGenerateReport = useCallback(async (config: ReportConfig) => {
    if (!workflowState?.workflow_id) return;
    setIsGeneratingReport(true);
    try {
      await workflowService.generateReportPdf(workflowState.workflow_id, config, true);
      setReportId(1);
      setHasDownloadedReport(true);
      toast.success('Executive Decision PDF report generated and downloaded!');
    } catch (err: any) {
      toast.error(err?.message || 'Failed to generate PDF report');
    } finally {
      setIsGeneratingReport(false);
    }
  }, [workflowState]);

  // === Present Step ===
  const handleGeneratePresentation = useCallback(async (template: string, title: string) => {
    if (!workflowState?.workflow_id) return;
    setIsGeneratingPresentation(true);
    try {
      await workflowService.generatePresentation(workflowState.workflow_id, template, title, true);
      setPresentationReady(true);
      toast.success('Widescreen PowerPoint presentation (.pptx) generated and downloaded!');
    } catch (err: any) {
      toast.error(err?.message || 'Failed to generate presentation');
    } finally {
      setIsGeneratingPresentation(false);
    }
  }, [workflowState]);

  const handleDownloadPresentationAgain = useCallback(async () => {
    if (!workflowState?.workflow_id) return;
    setIsGeneratingPresentation(true);
    try {
      await workflowService.generatePresentation(
        workflowState.workflow_id,
        'executive',
        file?.name || 'Dataset Analysis',
        true,
      );
      toast.success('Downloaded PowerPoint presentation');
    } catch (err: any) {
      toast.error(err?.message || 'Failed to download presentation');
    } finally {
      setIsGeneratingPresentation(false);
    }
  }, [workflowState, file]);

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
    setAutoDashboard(null);
    setCleanPreview(null);
    setTransformations([]);
    setSavedDashboardId(null);
    setReportId(null);
    setHasDownloadedReport(false);
    setPresentationReady(false);
    setErrorMessage('');
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
              This may take a few moments for deep statistical analysis
            </p>
          </div>
        </div>
      )}

      {/* Error state with Try Again */}
      {hasError && !isProcessing && currentStep === 'upload' && file && (
        <div className="flex flex-col items-center gap-4 py-8">
          <div className="text-center">
            <p className="font-medium text-rose-600">
              {errorMessage || "We couldn't process this dataset. Please try again."}
            </p>
            <p className="text-sm text-muted-foreground mt-1">
              If the problem persists, verify the file format or try a smaller sample.
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
          cleanPreview={cleanPreview}
          onRefreshPreview={handleRefreshPreview}
        />
      )}

      {currentStep === 'analyze' && (
        <AnalyzeStep
          workflowId={workflowState?.workflow_id}
          insights={insights}
          industry={industry?.industry ?? 'general'}
          onAskQuestion={handleAskQuestion}
          onContinue={() => completeAndAdvance('analyze', 'visualize')}
        />
      )}

      {currentStep === 'visualize' && (
        <VisualizeStep
          dashboard={dashboard}
          autoDashboard={autoDashboard}
          profile={profile}
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
          hasDownloadedReport={hasDownloadedReport}
        />
      )}

      {currentStep === 'present' && (
        <PresentStep
          datasetName={file?.name ?? 'Dataset'}
          onGeneratePresentation={handleGeneratePresentation}
          onDownloadPresentation={handleDownloadPresentationAgain}
          onStartOver={handleStartOver}
          isGenerating={isGeneratingPresentation}
          presentationReady={presentationReady}
        />
      )}
    </div>
  );
}
