'use client';

import { useEffect, useState, useCallback } from 'react';
import {
  FileText, CheckCircle2, XCircle, Save, Eye, AlertCircle,
  Loader2, RotateCcw, Database, ChevronRight, AlertTriangle,
} from 'lucide-react';
import {
  captureService,
  type CaptureDocument,
  type CaptureField,
  type CaptureDocumentType,
} from '@/services/capture/captureService';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Input } from '@/components/ui/Input';
import { cn } from '@/lib/utils';
import { toast } from '@/components/ui/Toaster';

const STATUS_BADGE: Record<string, { label: string; color: string }> = {
  ready_for_review: { label: 'Ready for Review', color: 'bg-amber-100 text-amber-700' },
  approved: { label: 'Approved', color: 'bg-green-100 text-green-700' },
  rejected: { label: 'Rejected', color: 'bg-red-100 text-red-700' },
  draft: { label: 'Draft', color: 'bg-purple-100 text-purple-700' },
  failed: { label: 'Failed', color: 'bg-red-100 text-red-700' },
  uploaded: { label: 'Processing', color: 'bg-blue-100 text-blue-700' },
  preprocessing: { label: 'Processing', color: 'bg-blue-100 text-blue-700' },
  classifying: { label: 'Processing', color: 'bg-blue-100 text-blue-700' },
  extracting: { label: 'Processing', color: 'bg-blue-100 text-blue-700' },
  validating: { label: 'Processing', color: 'bg-blue-100 text-blue-700' },
};

const DATA_TYPE_ICONS: Record<string, string> = {
  text: '📝',
  number: '🔢',
  date: '📅',
  phone: '📞',
  email: '✉️',
  currency: '💰',
  enum: '📋',
};

interface DocumentReviewPanelProps {
  documentId: number;
  onApproved?: () => void;
  onRejected?: () => void;
}

export function DocumentReviewPanel({ documentId, onApproved, onRejected }: DocumentReviewPanelProps) {
  const [doc, setDoc] = useState<CaptureDocument | null>(null);
  const [fields, setFields] = useState<CaptureField[]>([]);
  const [docTypes, setDocTypes] = useState<CaptureDocumentType[]>([]);
  const [loading, setLoading] = useState(true);
  const [editingField, setEditingField] = useState<number | null>(null);
  const [editValue, setEditValue] = useState('');
  const [saving, setSaving] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [showOcrText, setShowOcrText] = useState(false);

  const loadDocument = useCallback(async () => {
    try {
      setLoading(true);
      const d = await captureService.getDocument(documentId);
      setDoc(d);
      setFields(d.fields || []);
      const typesRes = await captureService.getDocumentTypes();
      setDocTypes(typesRes.document_types);
    } catch {
      toast.error('Failed to load document');
    } finally {
      setLoading(false);
    }
  }, [documentId]);

  useEffect(() => {
    loadDocument();
  }, [loadDocument]);

  const handleEditField = (field: CaptureField) => {
    setEditingField(field.id);
    setEditValue(field.value || '');
  };

  const handleSaveField = async (fieldId: number) => {
    setSaving(true);
    try {
      const updated = await captureService.updateField(documentId, fieldId, editValue);
      setFields((prev) => prev.map((f) => (f.id === fieldId ? updated : f)));
      setEditingField(null);
      toast.success('Field updated');
    } catch {
      toast.error('Failed to update field');
    } finally {
      setSaving(false);
    }
  };

  const handleSetDocumentType = async (docType: string) => {
    try {
      const updated = await captureService.setDocumentType(documentId, docType);
      setDoc(updated);
      toast.success('Document type updated');
      loadDocument(); // Reload to get re-extracted fields
    } catch {
      toast.error('Failed to set document type');
    }
  };

  const handleApprove = async () => {
    setActionLoading(true);
    try {
      const updated = await captureService.approveDocument(documentId);
      setDoc(updated);
      toast.success('Document approved');
      onApproved?.();
    } catch {
      toast.error('Failed to approve document');
    } finally {
      setActionLoading(false);
    }
  };

  const handleReject = async () => {
    setActionLoading(true);
    try {
      const updated = await captureService.rejectDocument(documentId);
      setDoc(updated);
      toast.success('Document rejected');
      onRejected?.();
    } catch {
      toast.error('Failed to reject document');
    } finally {
      setActionLoading(false);
    }
  };

  const handleSaveDraft = async () => {
    setActionLoading(true);
    try {
      const updated = await captureService.saveDraft(documentId);
      setDoc(updated);
      toast.success('Draft saved');
    } catch {
      toast.error('Failed to save draft');
    } finally {
      setActionLoading(false);
    }
  };

  const handleRetry = async () => {
    setActionLoading(true);
    try {
      const updated = await captureService.retryDocument(documentId);
      setDoc(updated);
      toast.success('Retrying document processing');
      loadDocument();
    } catch {
      toast.error('Failed to retry');
    } finally {
      setActionLoading(false);
    }
  };

  const handleExport = async () => {
    setActionLoading(true);
    try {
      const result = await captureService.exportToDataset(documentId);
      toast.success(`Exported ${result.field_count} fields to ${result.dataset_name}`);
    } catch (err: any) {
      toast.error(err.message || 'Failed to export');
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-16">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!doc) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center">
        <AlertCircle className="mb-4 h-12 w-12 text-muted-foreground" />
        <p className="text-muted-foreground">Document not found</p>
      </div>
    );
  }

  const statusInfo = STATUS_BADGE[doc.status] || { label: doc.status, color: 'bg-slate-100 text-slate-600' };
  const isApproved = doc.status === 'approved';
  const isRejected = doc.status === 'rejected';
  const canReview = doc.status === 'ready_for_review' || doc.status === 'draft';
  const isFailed = doc.status === 'failed';
  const lowConfidenceFields = fields.filter((f) => f.is_low_confidence);
  const invalidFields = fields.filter((f) => !f.is_valid);

  return (
    <div className="space-y-4">
      {/* Document header */}
      <Card>
        <CardContent className="p-4">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-3">
              <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10">
                <FileText className="h-6 w-6 text-primary" />
              </div>
              <div>
                <h3 className="font-semibold">{doc.filename}</h3>
                <div className="mt-1 flex items-center gap-2">
                  <Badge variant="outline" className={cn('text-xs', statusInfo.color)}>
                    {statusInfo.label}
                  </Badge>
                  {doc.document_type_label && (
                    <Badge variant="secondary" className="text-xs">{doc.document_type_label}</Badge>
                  )}
                  {doc.industry && (
                    <Badge variant="outline" className="text-xs capitalize">{doc.industry}</Badge>
                  )}
                </div>
              </div>
            </div>
            <div className="text-right text-xs text-muted-foreground">
              {doc.overall_confidence !== null && (
                <p>Confidence: <span className={cn(
                  'font-semibold',
                  doc.overall_confidence >= 0.8 ? 'text-green-600' : doc.overall_confidence >= 0.5 ? 'text-amber-600' : 'text-red-600'
                )}>{Math.round(doc.overall_confidence * 100)}%</span></p>
              )}
              {doc.page_count > 1 && <p>{doc.page_count} pages</p>}
            </div>
          </div>

          {/* Error message */}
          {isFailed && doc.error_message && (
            <div className="mt-3 flex items-start gap-2 rounded-lg border border-red-200 bg-red-50 p-3 dark:border-red-900 dark:bg-red-950/30">
              <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-red-600" />
              <div>
                <p className="text-sm font-medium text-red-700">Processing Failed</p>
                <p className="text-xs text-red-600">{doc.error_message}</p>
              </div>
            </div>
          )}

          {/* Document type confirmation */}
          {doc.needs_type_confirmation && (
            <div className="mt-3 rounded-lg border border-amber-200 bg-amber-50 p-3 dark:border-amber-900 dark:bg-amber-950/30">
              <p className="mb-2 text-sm font-medium text-amber-700">
                ⚠️ Please confirm the document type:
              </p>
              <select
                className="w-full rounded border px-3 py-1.5 text-sm"
                value={doc.document_type || ''}
                onChange={(e) => handleSetDocumentType(e.target.value)}
              >
                <option value="">Select type...</option>
                {docTypes.map((t) => (
                  <option key={t.key} value={t.key}>{t.label} ({t.industry})</option>
                ))}
              </select>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Warnings */}
      {(lowConfidenceFields.length > 0 || invalidFields.length > 0) && canReview && (
        <div className="flex items-center gap-2 rounded-lg border border-amber-200 bg-amber-50 p-3 dark:border-amber-900 dark:bg-amber-950/30">
          <AlertTriangle className="h-4 w-4 text-amber-600" />
          <p className="text-sm text-amber-700">
            {lowConfidenceFields.length > 0 && `${lowConfidenceFields.length} low-confidence field(s)`}
            {lowConfidenceFields.length > 0 && invalidFields.length > 0 && ' · '}
            {invalidFields.length > 0 && `${invalidFields.length} invalid field(s)`}
            — please review before approving
          </p>
        </div>
      )}

      {/* Extracted fields */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Extracted Fields ({fields.length})</CardTitle>
        </CardHeader>
        <CardContent>
          {fields.length === 0 ? (
            <p className="py-8 text-center text-sm text-muted-foreground">
              No fields extracted. {isFailed ? 'Processing failed.' : 'Try retrying or set document type manually.'}
            </p>
          ) : (
            <div className="space-y-2">
              {fields.map((field) => (
                <div
                  key={field.id}
                  className={cn(
                    'flex items-center justify-between rounded-lg border p-3 transition-colors',
                    field.is_low_confidence && 'border-amber-200 bg-amber-50/50 dark:border-amber-900',
                    !field.is_valid && 'border-red-200 bg-red-50/50 dark:border-red-900',
                    editingField === field.id && 'border-primary bg-primary/5'
                  )}
                >
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="text-xs">{DATA_TYPE_ICONS[field.data_type] || '📝'}</span>
                      <span className="text-xs font-medium text-muted-foreground">{field.field_label}</span>
                      {field.is_low_confidence && (
                        <Badge variant="outline" className="text-[10px] text-amber-600">Low Confidence</Badge>
                      )}
                      {field.was_corrected && (
                        <Badge variant="outline" className="text-[10px] text-blue-600">Corrected</Badge>
                      )}
                      {!field.is_valid && (
                        <Badge variant="outline" className="text-[10px] text-red-600">Invalid</Badge>
                      )}
                    </div>
                    {editingField === field.id ? (
                      <div className="mt-2 flex items-center gap-2">
                        <Input
                          value={editValue}
                          onChange={(e) => setEditValue(e.target.value)}
                          className="h-8 text-sm"
                          autoFocus
                          onKeyDown={(e) => {
                            if (e.key === 'Enter') handleSaveField(field.id);
                            if (e.key === 'Escape') setEditingField(null);
                          }}
                        />
                        <Button size="sm" onClick={() => handleSaveField(field.id)} disabled={saving} className="h-8 gap-1">
                          {saving ? <Loader2 size={12} className="animate-spin" /> : <Save size={12} />}
                          Save
                        </Button>
                        <Button size="sm" variant="outline" onClick={() => setEditingField(null)} className="h-8">
                          Cancel
                        </Button>
                      </div>
                    ) : (
                      <>
                        <p className="mt-1 text-sm font-medium">
                          {field.value || <span className="italic text-muted-foreground">— empty —</span>}
                        </p>
                        {field.validation_message && (
                          <p className="mt-0.5 text-xs text-amber-600">{field.validation_message}</p>
                        )}
                        <div className="mt-0.5 flex items-center gap-2 text-[10px] text-muted-foreground">
                          <span>Confidence: {Math.round(field.confidence_score * 100)}%</span>
                          {field.raw_value !== field.value && field.was_corrected && (
                            <span className="italic">Original: &quot;{field.raw_value}&quot;</span>
                          )}
                        </div>
                      </>
                    )}
                  </div>
                  {editingField !== field.id && canReview && (
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => handleEditField(field)}
                      className="text-xs"
                    >
                      Edit
                    </Button>
                  )}
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Extracted tables */}
      {doc.extracted_tables && doc.extracted_tables.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Extracted Tables ({doc.extracted_tables.length})</CardTitle>
          </CardHeader>
          <CardContent>
            {doc.extracted_tables.map((table: any, i: number) => (
              <div key={i} className="mb-4 overflow-auto rounded-lg border">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="border-b bg-muted/50">
                      {(table.headers || []).map((h: string, j: number) => (
                        <th key={j} className="px-2 py-1 text-left font-semibold">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {(table.rows || []).map((row: any[], j: number) => (
                      <tr key={j} className="border-b">
                        {row.map((cell, k: number) => (
                          <td key={k} className="px-2 py-1">{String(cell)}</td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {/* OCR text toggle */}
      {doc.raw_ocr_text && (
        <Card>
          <CardHeader>
            <button
              onClick={() => setShowOcrText(!showOcrText)}
              className="flex items-center gap-2 text-left"
            >
              <Eye className="h-4 w-4 text-muted-foreground" />
              <CardTitle className="text-base">Raw OCR Text</CardTitle>
              <ChevronRight className={cn('h-4 w-4 text-muted-foreground transition-transform', showOcrText && 'rotate-90')} />
            </button>
          </CardHeader>
          {showOcrText && (
            <CardContent>
              <pre className="max-h-64 overflow-auto whitespace-pre-wrap rounded-lg border bg-muted/30 p-3 text-xs">
                {doc.raw_ocr_text}
              </pre>
            </CardContent>
          )}
        </Card>
      )}

      {/* Action bar */}
      <div className="sticky bottom-0 flex items-center justify-between rounded-lg border bg-background p-3 shadow-lg">
        <div className="flex items-center gap-2">
          {isFailed && (
            <Button variant="outline" size="sm" onClick={handleRetry} disabled={actionLoading} className="gap-1">
              <RotateCcw size={14} /> Retry
            </Button>
          )}
          {canReview && (
            <>
              <Button variant="outline" size="sm" onClick={handleSaveDraft} disabled={actionLoading} className="gap-1">
                <Save size={14} /> Save Draft
              </Button>
              <Button variant="destructive" size="sm" onClick={handleReject} disabled={actionLoading} className="gap-1">
                <XCircle size={14} /> Reject
              </Button>
              <Button size="sm" onClick={handleApprove} disabled={actionLoading || invalidFields.length > 0} className="gap-1">
                {actionLoading ? <Loader2 size={14} className="animate-spin" /> : <CheckCircle2 size={14} />}
                Approve
              </Button>
            </>
          )}
        </div>
        {isApproved && (
          <Button size="sm" onClick={handleExport} disabled={actionLoading} className="gap-1">
            {actionLoading ? <Loader2 size={14} className="animate-spin" /> : <Database size={14} />}
            Export to Dataset
          </Button>
        )}
      </div>
    </div>
  );
}
