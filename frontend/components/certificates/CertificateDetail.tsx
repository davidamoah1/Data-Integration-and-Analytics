'use client';

import { useCallback, useEffect, useState } from 'react';
import {
  X, Loader2, CheckCircle2, AlertCircle, AlertTriangle, TrendingUp,
  ShieldCheck, ShieldAlert, Lightbulb, Edit2, FileText, Presentation,
  Download, RefreshCw, FileCheck, Eye, ScanLine, BarChart3,
} from 'lucide-react';
import {
  certificateService,
  type Certificate,
  type CertificateField,
} from '@/services/certificates/certificateService';
import { Button } from '@/components/ui/Button';
import { CertificateCharts } from './CertificateCharts';
import { toast } from '@/components/ui/Toaster';

type WorkflowPhase = 'loading' | 'extracted' | 'analyzing' | 'analyzed' | 'error';

interface DetailData {
  certificate: Certificate;
  fields: CertificateField[];
  analysis: {
    document_type: string | null;
    document_type_label: string | null;
    classification_confidence: number | null;
    overall_confidence: number | null;
    summary: string;
    verification_status: string;
    is_duplicate: boolean;
    duplicate_of_id: number | null;
    completeness: {
      total_fields: number;
      required_fields: number;
      required_filled: number;
      optional_fields: number;
      optional_filled: number;
      completeness_pct: number;
      overall_pct: number;
      missing_required: string[];
      missing_optional: string[];
    };
    consistency_checks: {
      check_name: string;
      description: string;
      passed: boolean;
      severity: string;
      detail: string;
    }[];
    academic_performance: {
      gpa: string | null;
      grade: string | null;
      qualification: string | null;
      programme: string | null;
      has_performance_data: boolean;
      summary: string;
    };
    anomalies: {
      anomaly_type: string;
      field_name: string | null;
      description: string;
      severity: string;
    }[];
    recommendations: {
      action: string;
      description: string;
      priority: string;
    }[];
    field_analysis: {
      field_name: string;
      field_label: string;
      value: string | null;
      raw_value: string | null;
      confidence: number;
      is_low_confidence: boolean;
      is_present: boolean;
      is_required: boolean;
      is_valid: boolean;
      validation_message: string | null;
      was_corrected: boolean;
    }[];
  };
}

const FIELD_CATEGORIES = {
  'Personal Information': ['full_name', 'student_id', 'certificate_id', 'date_of_birth', 'candidate_name', 'name'],
  'Institution': ['institution_name', 'institution_type', 'campus', 'location', 'country', 'university', 'school'],
  'Academic Information': ['qualification', 'programme', 'course', 'field_of_study', 'major', 'specialization', 'class', 'division', 'grade', 'gpa', 'cgpa', 'graduation_date', 'completion_date', 'academic_year', 'degree'],
  'Certificate Information': ['certificate_title', 'certificate_number', 'issue_date', 'issuing_authority', 'signatories', 'accreditation', 'registration_number', 'qr_code', 'reference_number'],
};

function categorizeField(fieldName: string): string {
  const lower = fieldName.toLowerCase();
  for (const [category, keywords] of Object.entries(FIELD_CATEGORIES)) {
    if (keywords.some((k) => lower.includes(k))) return category;
  }
  return 'Other Information';
}

function displayValue(value: string | null): string {
  if (!value || value === 'null' || value === 'undefined' || value === 'NaN' || value.trim() === '') {
    return 'Not detected';
  }
  return value;
}

function getErrorMessage(err: unknown): string {
  const e = err as { status?: number; message?: string };
  if (e?.status) {
    switch (e.status) {
      case 400: return 'Bad request — the server could not process the file.';
      case 401: return 'Authentication required — please log in again.';
      case 403: return 'You do not have permission to perform this action.';
      case 404: return 'Certificate not found — it may have been deleted.';
      case 413: return 'File is too large — please upload a smaller file.';
      case 422: return 'Validation error — the file format is not supported.';
      case 429: return 'Too many requests — please wait and try again.';
      case 500: return 'Server error — please try again later.';
      case 502:
      case 503:
      case 504: return 'Backend service unavailable — please try again later.';
    }
  }
  if (e?.message?.includes('Network') || e?.message?.includes('fetch')) {
    return 'Network error — unable to connect to the server.';
  }
  return e?.message || 'An unexpected error occurred.';
}

interface CertificateDetailProps {
  certificateId: number;
  onClose: () => void;
  dashboardData?: {
    by_type?: Record<string, number>;
    by_verification?: Record<string, number>;
    by_institution?: Record<string, number>;
    by_year?: Record<string, number>;
    total?: number;
  };
}

export function CertificateDetail({ certificateId, onClose, dashboardData }: CertificateDetailProps) {
  const [phase, setPhase] = useState<WorkflowPhase>('loading');
  const [detailData, setDetailData] = useState<DetailData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [editingFieldId, setEditingFieldId] = useState<number | null>(null);
  const [editValue, setEditValue] = useState('');
  const [editSaving, setEditSaving] = useState(false);
  const [reportLoading, setReportLoading] = useState(false);
  const [presentationLoading, setPresentationLoading] = useState(false);
  const [showAnalysis, setShowAnalysis] = useState(false);

  const loadDetail = useCallback(async () => {
    setPhase('loading');
    setError(null);
    try {
      const data = await certificateService.getDetail(certificateId);
      setDetailData(data as DetailData);
      setPhase('extracted');
    } catch (err) {
      setError(getErrorMessage(err));
      setPhase('error');
    }
  }, [certificateId]);

  useEffect(() => {
    loadDetail();
  }, [loadDetail]);

  const handleAnalyze = () => {
    setShowAnalysis(true);
    setPhase('analyzing');
    setTimeout(() => {
      setPhase('analyzed');
    }, 600);
  };

  const handleSaveEdit = async (fieldId: number) => {
    setEditSaving(true);
    try {
      await certificateService.correctField(certificateId, fieldId, editValue);
      setEditingFieldId(null);
      await loadDetail();
      toast.success('Field updated successfully');
    } catch (err) {
      toast.error(getErrorMessage(err));
    } finally {
      setEditSaving(false);
    }
  };

  const handleGenerateReport = async () => {
    setReportLoading(true);
    try {
      await certificateService.exportCsv();
      toast.success('Report downloaded successfully');
    } catch (err) {
      toast.error(getErrorMessage(err));
    } finally {
      setReportLoading(false);
    }
  };

  const handleDownloadReport = async () => {
    setReportLoading(true);
    try {
      await certificateService.getReport();
      toast.success('Report generated — downloading...');
      await certificateService.exportXlsx();
    } catch (err) {
      toast.error(getErrorMessage(err));
    } finally {
      setReportLoading(false);
    }
  };

  const handleGeneratePresentation = async () => {
    setPresentationLoading(true);
    try {
      await certificateService.downloadPresentation();
      toast.success('Presentation downloaded successfully');
    } catch (err) {
      toast.error(getErrorMessage(err));
    } finally {
      setPresentationLoading(false);
    }
  };

  const fieldsByCategory = detailData?.fields
    ? detailData.fields.reduce((acc, field) => {
        const cat = categorizeField(field.field_name);
        if (!acc[cat]) acc[cat] = [];
        acc[cat].push(field);
        return acc;
      }, {} as Record<string, CertificateField[]>)
    : {};

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4" onClick={onClose}>
      <div
        className="max-h-[92vh] w-full max-w-5xl overflow-y-auto rounded-2xl bg-white shadow-2xl"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-label="Certificate details"
      >
        {phase === 'loading' && (
          <div className="flex flex-col items-center justify-center py-20">
            <Loader2 className="h-8 w-8 animate-spin text-indigo-600" />
            <p className="mt-3 text-sm text-slate-600">Loading certificate details...</p>
          </div>
        )}

        {phase === 'error' && (
          <div className="flex flex-col items-center justify-center py-20 px-6 text-center">
            <AlertCircle className="h-10 w-10 text-red-500 mb-4" />
            <h3 className="text-lg font-semibold text-slate-900">Failed to load certificate</h3>
            <p className="mt-1 text-sm text-slate-500 max-w-sm">{error}</p>
            <div className="mt-6 flex gap-3">
              <Button onClick={loadDetail} variant="default">
                <RefreshCw size={16} className="mr-2" /> Try Again
              </Button>
              <Button onClick={onClose} variant="outline">
                Close
              </Button>
            </div>
          </div>
        )}

        {detailData && (phase === 'extracted' || phase === 'analyzing' || phase === 'analyzed') && (
          <div className="p-6">
            {/* Header */}
            <div className="mb-6 flex items-start justify-between">
              <div className="flex items-start gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-indigo-100 text-indigo-600 flex-shrink-0">
                  <FileText size={20} />
                </div>
                <div>
                  <h2 className="text-lg font-bold text-slate-900">{detailData.certificate.filename}</h2>
                  <p className="text-sm text-slate-500 mt-0.5">
                    {detailData.analysis.document_type_label || detailData.analysis.document_type || 'Unclassified'}
                    {detailData.analysis.is_duplicate && (
                      <span className="ml-2 inline-flex items-center gap-1 text-amber-600">
                        <AlertTriangle size={12} /> Duplicate of #{detailData.analysis.duplicate_of_id}
                      </span>
                    )}
                  </p>
                  <div className="mt-1 flex flex-wrap gap-2 text-xs">
                    <span className="text-slate-400">Type: {detailData.certificate.file_type?.toUpperCase() || '—'}</span>
                    <span className="text-slate-400">•</span>
                    <span className="text-slate-400">Status: {detailData.certificate.status?.replace(/_/g, ' ') || '—'}</span>
                    <span className="text-slate-400">•</span>
                    <span className="text-slate-400">Verification: {detailData.analysis.verification_status?.replace(/_/g, ' ') || '—'}</span>
                  </div>
                </div>
              </div>
              <button onClick={onClose} className="text-slate-400 hover:text-slate-600 p-1" aria-label="Close">
                <X size={20} />
              </button>
            </div>

            {/* Workflow Progress Bar */}
            <div className="mb-6 flex items-center gap-2 overflow-x-auto">
              {[
                { key: 'uploaded', label: 'Uploaded', icon: FileCheck, done: true },
                { key: 'extracted', label: 'Extracted', icon: ScanLine, done: true },
                { key: 'analyzed', label: 'Analyzed', icon: BarChart3, done: phase === 'analyzed' },
                { key: 'report', label: 'Report', icon: FileText, done: false },
                { key: 'presentation', label: 'Presentation', icon: Presentation, done: false },
              ].map((step, i, arr) => (
                <div key={step.key} className="flex items-center gap-2 flex-shrink-0">
                  <div className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium ${
                    step.done
                      ? 'bg-green-100 text-green-700'
                      : step.key === 'analyzed' && phase === 'analyzing'
                      ? 'bg-blue-100 text-blue-700'
                      : 'bg-slate-100 text-slate-400'
                  }`}>
                    {step.done ? <CheckCircle2 size={14} /> :
                     step.key === 'analyzed' && phase === 'analyzing' ? <Loader2 size={14} className="animate-spin" /> :
                     <step.icon size={14} />}
                    {step.label}
                  </div>
                  {i < arr.length - 1 && <div className="w-4 h-px bg-slate-200" />}
                </div>
              ))}
            </div>

            {/* Phase: Extracted — Show extracted info + Analyze button */}
            {phase === 'extracted' && (
              <>
                <div className="mb-4 rounded-xl bg-green-50 border border-green-200 p-4">
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="h-5 w-5 text-green-600 flex-shrink-0" />
                    <div>
                      <p className="text-sm font-semibold text-green-900">Certificate information extracted successfully</p>
                      <p className="text-xs text-green-700 mt-0.5">
                        Review the extracted information below. You can edit any field before analysis.
                      </p>
                    </div>
                  </div>
                </div>

                {/* Extracted Fields by Category */}
                <div className="space-y-6 mb-6">
                  {Object.entries(fieldsByCategory).map(([category, fields]) => (
                    <div key={category}>
                      <h3 className="mb-3 text-sm font-semibold text-slate-900">{category}</h3>
                      <div className="overflow-hidden rounded-xl border border-slate-200">
                        <table className="w-full text-sm">
                          <thead className="bg-slate-50 border-b border-slate-200">
                            <tr>
                              <th className="px-3 py-2 text-left font-medium text-slate-600">Field</th>
                              <th className="px-3 py-2 text-left font-medium text-slate-600">Value</th>
                              <th className="px-3 py-2 text-left font-medium text-slate-600">Confidence</th>
                              <th className="px-3 py-2 text-left font-medium text-slate-600">Status</th>
                              <th className="px-3 py-2 w-10"></th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-slate-100">
                            {fields.map((field) => {
                              const fa = detailData.analysis.field_analysis.find((f) => f.field_name === field.field_name);
                              return (
                                <tr key={field.id} className={field.is_low_confidence ? 'bg-amber-50/50' : ''}>
                                  <td className="px-3 py-2 text-slate-600 text-xs">
                                    {field.field_label}
                                    {fa?.is_required && <span className="text-red-500 ml-1">*</span>}
                                  </td>
                                  <td className="px-3 py-2 text-slate-900">
                                    {editingFieldId === field.id ? (
                                      <div className="flex items-center gap-2">
                                        <input
                                          type="text"
                                          value={editValue}
                                          onChange={(e) => setEditValue(e.target.value)}
                                          className="w-full px-2 py-1 text-sm border border-indigo-300 rounded focus:outline-none focus:ring-1 focus:ring-indigo-500"
                                          autoFocus
                                          aria-label={`Edit ${field.field_label}`}
                                        />
                                        <button
                                          onClick={() => handleSaveEdit(field.id)}
                                          disabled={editSaving}
                                          className="text-xs text-indigo-600 font-medium hover:underline disabled:opacity-50"
                                        >
                                          {editSaving ? 'Saving...' : 'Save'}
                                        </button>
                                        <button
                                          onClick={() => setEditingFieldId(null)}
                                          className="text-xs text-slate-500 hover:underline"
                                        >
                                          Cancel
                                        </button>
                                      </div>
                                    ) : (
                                      <div>
                                        <div className={displayValue(field.value) === 'Not detected' ? 'text-slate-400 italic' : ''}>
                                          {displayValue(field.value)}
                                        </div>
                                        {field.was_corrected && field.raw_value && field.raw_value !== field.value && (
                                          <div className="text-xs text-slate-400 line-through">{field.raw_value}</div>
                                        )}
                                      </div>
                                    )}
                                  </td>
                                  <td className="px-3 py-2">
                                    {field.value ? (
                                      <span className={`text-xs font-medium ${
                                        field.confidence_score >= 0.8 ? 'text-green-600' :
                                        field.confidence_score >= 0.5 ? 'text-amber-600' : 'text-red-600'
                                      }`}>
                                        {(field.confidence_score * 100).toFixed(0)}%
                                        {field.confidence_score < 0.5 && (
                                          <span className="block text-xs text-red-500">Low confidence — please verify</span>
                                        )}
                                      </span>
                                    ) : (
                                      <span className="text-xs text-slate-300">—</span>
                                    )}
                                  </td>
                                  <td className="px-3 py-2">
                                    {field.value ? (
                                      field.is_valid ? (
                                        <span className="text-xs text-green-600">Valid</span>
                                      ) : (
                                        <span className="text-xs text-red-600" title={field.validation_message || ''}>Invalid</span>
                                      )
                                    ) : (
                                      <span className="text-xs text-slate-300">—</span>
                                    )}
                                    {field.was_corrected && <span className="ml-1 text-xs text-indigo-600">Corrected</span>}
                                  </td>
                                  <td className="px-3 py-2">
                                    {editingFieldId !== field.id && field.value && (
                                      <button
                                        onClick={() => { setEditingFieldId(field.id); setEditValue(field.value || ''); }}
                                        className="text-slate-400 hover:text-indigo-600 p-1"
                                        aria-label={`Edit ${field.field_label}`}
                                      >
                                        <Edit2 size={14} />
                                      </button>
                                    )}
                                  </td>
                                </tr>
                              );
                            })}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Action Buttons */}
                <div className="sticky bottom-0 bg-white border-t border-slate-200 pt-4 pb-2 -mx-6 px-6 flex flex-col sm:flex-row gap-3 sm:justify-end">
                  <Button
                    onClick={() => { setEditingFieldId(null); }}
                    variant="outline"
                    className="w-full sm:w-auto"
                  >
                    <Edit2 size={16} className="mr-2" /> Edit Information
                  </Button>
                  <Button
                    onClick={handleAnalyze}
                    className="w-full sm:w-auto"
                    size="lg"
                  >
                    <BarChart3 size={16} className="mr-2" /> Confirm & Analyze
                  </Button>
                </div>
              </>
            )}

            {/* Phase: Analyzing */}
            {phase === 'analyzing' && (
              <div className="flex flex-col items-center justify-center py-20">
                <Loader2 className="h-10 w-10 animate-spin text-indigo-600" />
                <p className="mt-4 text-sm font-medium text-slate-700">Analyzing certificate...</p>
                <p className="text-xs text-slate-500 mt-1">Running consistency checks, anomaly detection, and generating insights</p>
              </div>
            )}

            {/* Phase: Analyzed — Full Results Dashboard */}
            {phase === 'analyzed' && showAnalysis && (
              <>
                <div className="mb-6 rounded-xl bg-indigo-50 border border-indigo-200 p-4">
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="h-5 w-5 text-indigo-600 flex-shrink-0" />
                    <p className="text-sm font-semibold text-indigo-900">Analysis complete</p>
                  </div>
                  <p className="text-sm text-slate-700 mt-2">{detailData.analysis.summary}</p>
                </div>

                {/* Summary Cards */}
                <div className="mb-6 grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="rounded-xl border border-slate-200 p-4">
                    <div className="flex items-center gap-2 mb-2">
                      <TrendingUp size={16} className="text-indigo-600" />
                      <h3 className="text-sm font-semibold text-slate-900">Completeness</h3>
                    </div>
                    <div className="text-2xl font-bold text-slate-900">{detailData.analysis.completeness.completeness_pct.toFixed(0)}%</div>
                    <div className="text-xs text-slate-500 mt-1">
                      {detailData.analysis.completeness.required_filled}/{detailData.analysis.completeness.required_fields} required fields filled
                    </div>
                    {detailData.analysis.completeness.missing_required.length > 0 && (
                      <div className="mt-2 text-xs text-amber-600">
                        Missing: {detailData.analysis.completeness.missing_required.join(', ')}
                      </div>
                    )}
                  </div>
                  <div className="rounded-xl border border-slate-200 p-4">
                    <div className="flex items-center gap-2 mb-2">
                      <ShieldCheck size={16} className="text-emerald-600" />
                      <h3 className="text-sm font-semibold text-slate-900">Confidence</h3>
                    </div>
                    <div className="text-2xl font-bold text-slate-900">
                      {detailData.analysis.overall_confidence != null
                        ? `${(detailData.analysis.overall_confidence * 100).toFixed(1)}%`
                        : '—'}
                    </div>
                    <div className="text-xs text-slate-500 mt-1">
                      Classification: {detailData.analysis.classification_confidence != null ? `${(detailData.analysis.classification_confidence * 100).toFixed(0)}%` : '—'}
                    </div>
                  </div>
                </div>

                {/* Academic Performance */}
                {detailData.analysis.academic_performance.has_performance_data && (
                  <div className="mb-6">
                    <h3 className="mb-3 text-sm font-semibold text-slate-900">Academic Performance</h3>
                    <div className="rounded-xl border border-slate-200 p-4">
                      <p className="text-sm text-slate-700">{detailData.analysis.academic_performance.summary}</p>
                    </div>
                  </div>
                )}

                {/* Consistency Checks */}
                {detailData.analysis.consistency_checks.length > 0 && (
                  <div className="mb-6">
                    <h3 className="mb-3 text-sm font-semibold text-slate-900">Consistency Checks</h3>
                    <div className="space-y-2">
                      {detailData.analysis.consistency_checks.map((check, i) => (
                        <div key={i} className={`flex items-start gap-2 rounded-lg p-3 text-sm ${
                          check.passed ? 'bg-green-50 text-green-700' :
                          check.severity === 'error' ? 'bg-red-50 text-red-700' : 'bg-amber-50 text-amber-700'
                        }`}>
                          {check.passed ? <CheckCircle2 size={16} className="mt-0.5 flex-shrink-0" /> :
                            <AlertTriangle size={16} className="mt-0.5 flex-shrink-0" />}
                          <div>
                            <div className="font-medium">{check.description}</div>
                            <div className="text-xs opacity-80 mt-0.5">{check.detail}</div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Anomalies / Warnings */}
                {detailData.analysis.anomalies.length > 0 && (
                  <div className="mb-6">
                    <h3 className="mb-3 text-sm font-semibold text-slate-900">Warnings / Items to Verify ({detailData.analysis.anomalies.length})</h3>
                    <div className="space-y-2">
                      {detailData.analysis.anomalies.map((anomaly, i) => (
                        <div key={i} className={`flex items-start gap-2 rounded-lg p-3 text-sm ${
                          anomaly.severity === 'error' ? 'bg-red-50 text-red-700' : 'bg-amber-50 text-amber-700'
                        }`}>
                          <AlertCircle size={16} className="mt-0.5 flex-shrink-0" />
                          <div>
                            <div className="font-medium">{anomaly.description}</div>
                            {anomaly.field_name && <div className="text-xs opacity-80 mt-0.5">Field: {anomaly.field_name}</div>}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Recommendations */}
                {detailData.analysis.recommendations.length > 0 && (
                  <div className="mb-6">
                    <h3 className="mb-3 text-sm font-semibold text-slate-900">Insights & Recommendations</h3>
                    <div className="space-y-2">
                      {detailData.analysis.recommendations.map((rec, i) => (
                        <div key={i} className={`flex items-start gap-2 rounded-lg p-3 text-sm ${
                          rec.priority === 'high' ? 'bg-red-50' : rec.priority === 'medium' ? 'bg-amber-50' : 'bg-green-50'
                        }`}>
                          <Lightbulb size={16} className="mt-0.5 flex-shrink-0 text-slate-600" />
                          <div>
                            <div className="font-medium text-slate-900">{rec.description}</div>
                            <div className="text-xs text-slate-500 mt-0.5">Priority: {rec.priority}</div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Verification Notice */}
                <div className="mb-6 rounded-xl border border-slate-200 bg-slate-50 p-4">
                  <div className="flex items-start gap-2">
                    <ShieldAlert size={16} className="mt-0.5 text-slate-500 flex-shrink-0" />
                    <div>
                      <p className="text-sm font-medium text-slate-700">Verification Recommended</p>
                      <p className="text-xs text-slate-500 mt-0.5">
                        Information was extracted successfully. The document contains the following indicators.
                        Verification with the issuing institution is recommended before making credential decisions.
                      </p>
                    </div>
                  </div>
                </div>

                {/* Automatic Visualizations */}
                <div className="mb-6">
                  <h3 className="mb-3 text-sm font-semibold text-slate-900">Visualizations</h3>
                  <CertificateCharts fields={detailData.fields} dashboardData={dashboardData} />
                </div>

                {/* Action Buttons: Report + Presentation */}
                <div className="sticky bottom-0 bg-white border-t border-slate-200 pt-4 pb-2 -mx-6 px-6 flex flex-col sm:flex-row gap-3 sm:justify-end">
                  <Button
                    onClick={handleDownloadReport}
                    disabled={reportLoading}
                    variant="outline"
                    className="w-full sm:w-auto"
                  >
                    {reportLoading ? <Loader2 size={16} className="mr-2 animate-spin" /> : <Download size={16} className="mr-2" />}
                    {reportLoading ? 'Generating...' : 'Generate Report'}
                  </Button>
                  <Button
                    onClick={handleGeneratePresentation}
                    disabled={presentationLoading}
                    className="w-full sm:w-auto"
                  >
                    {presentationLoading ? <Loader2 size={16} className="mr-2 animate-spin" /> : <Presentation size={16} className="mr-2" />}
                    {presentationLoading ? 'Generating...' : 'Generate Presentation'}
                  </Button>
                </div>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
