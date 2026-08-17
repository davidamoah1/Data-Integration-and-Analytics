"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  Award,
  Upload,
  Search,
  Download,
  FileText,
  CheckCircle2,
  Clock,
  AlertCircle,
  XCircle,
  ShieldCheck,
  ShieldAlert,
  Loader2,
  FileCheck,
  BarChart3,
  ArrowRight,
  Filter,
  X,
} from "lucide-react";
import { certificateService, type CertificateDashboard, type Certificate } from "@/services/certificates/certificateService";
import { Button } from "@/components/ui/Button";

const STATUS_LABELS: Record<string, string> = {
  uploaded: "Uploaded",
  preprocessing: "Preprocessing",
  extracting: "Extracting",
  classifying: "Classifying",
  validating: "Validating",
  ready_for_review: "Ready for Review",
  approved: "Approved",
  rejected: "Rejected",
  draft: "Draft",
  failed: "Failed",
};

const STATUS_COLORS: Record<string, string> = {
  uploaded: "bg-slate-100 text-slate-600",
  preprocessing: "bg-blue-100 text-blue-700",
  extracting: "bg-blue-100 text-blue-700",
  classifying: "bg-blue-100 text-blue-700",
  validating: "bg-blue-100 text-blue-700",
  ready_for_review: "bg-amber-100 text-amber-700",
  approved: "bg-green-100 text-green-700",
  rejected: "bg-red-100 text-red-700",
  draft: "bg-purple-100 text-purple-700",
  failed: "bg-red-100 text-red-700",
};

const VERIFICATION_LABELS: Record<string, string> = {
  not_verified: "Not Verified",
  extraction_complete: "Extraction Complete",
  verification_pending: "Verification Pending",
  verified: "Verified",
  verification_failed: "Verification Failed",
};

const VERIFICATION_COLORS: Record<string, string> = {
  not_verified: "bg-slate-100 text-slate-600",
  extraction_complete: "bg-blue-100 text-blue-700",
  verification_pending: "bg-amber-100 text-amber-700",
  verified: "bg-green-100 text-green-700",
  verification_failed: "bg-red-100 text-red-700",
};

export default function CertificateIntelligencePage() {
  const [dashboard, setDashboard] = useState<CertificateDashboard | null>(null);
  const [certificates, setCertificates] = useState<Certificate[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [filterType, setFilterType] = useState("");
  const [filterStatus, setFilterStatus] = useState("");
  const [uploadResults, setUploadResults] = useState<any[] | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const loadData = useCallback(async () => {
    try {
      const [dash, search] = await Promise.all([
        certificateService.getDashboard(),
        certificateService.search({ limit: 100 }),
      ]);
      setDashboard(dash);
      setCertificates(search.certificates);
    } catch {
      // silent
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleSearch = useCallback(async () => {
    setLoading(true);
    try {
      const result = await certificateService.search({
        q: searchQuery || undefined,
        certificate_type: filterType || undefined,
        review_status: filterStatus || undefined,
        limit: 100,
      });
      setCertificates(result.certificates);
    } catch {
      // silent
    } finally {
      setLoading(false);
    }
  }, [searchQuery, filterType, filterStatus]);

  const handleUpload = useCallback(async (files: File[]) => {
    if (files.length === 0) return;
    setUploading(true);
    setUploadResults(null);
    try {
      const result = await certificateService.upload(files, `Certificate Batch ${new Date().toLocaleDateString()}`);
      setUploadResults(result.certificates);
      await loadData();
    } catch (err: any) {
      setUploadResults([{ status: "failed", error_message: err.message || "Upload failed" }]);
    } finally {
      setUploading(false);
    }
  }, [loadData]);

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    if (files.length > 0) handleUpload(files);
    e.target.value = "";
  }, [handleUpload]);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const files = Array.from(e.dataTransfer.files).filter(f =>
      /\.(pdf|jpg|jpeg|png)$/i.test(f.name)
    );
    if (files.length > 0) handleUpload(files);
  }, [handleUpload]);

  const stats = dashboard ? [
    { label: "Total Certificates", value: dashboard.total, icon: FileText, color: "text-blue-600 bg-blue-50" },
    { label: "Pending Review", value: dashboard.review_required, icon: Clock, color: "text-amber-600 bg-amber-50" },
    { label: "Approved", value: dashboard.approved, icon: CheckCircle2, color: "text-green-600 bg-green-50" },
    { label: "Failed", value: dashboard.failed, icon: AlertCircle, color: "text-red-600 bg-red-50" },
    { label: "Verified", value: dashboard.verified, icon: ShieldCheck, color: "text-emerald-600 bg-emerald-50" },
    { label: "Duplicates", value: dashboard.duplicates, icon: FileCheck, color: "text-purple-600 bg-purple-50" },
  ] : [];

  return (
    <div className="min-h-screen bg-slate-50 py-8">
      <div className="mx-auto max-w-7xl px-6">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-indigo-600 text-white shadow-lg shadow-indigo-600/20">
              <Award size={24} />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-slate-900">Certificate Intelligence</h1>
              <p className="text-sm text-slate-500">
                Upload certificates and automatically extract, validate, and analyze certificate data
              </p>
            </div>
          </div>
        </div>

        {/* Stats */}
        <div className="mb-8 grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-6">
          {stats.map((stat) => (
            <div key={stat.label} className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
              <div className={`mb-2 inline-flex h-8 w-8 items-center justify-center rounded-lg ${stat.color}`}>
                <stat.icon size={16} />
              </div>
              <div className="text-2xl font-bold text-slate-900">{stat.value}</div>
              <div className="text-xs text-slate-500">{stat.label}</div>
            </div>
          ))}
        </div>

        {/* Upload Area */}
        <div className="mb-8">
          <div
            onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`cursor-pointer rounded-xl border-2 border-dashed p-8 text-center transition-colors ${
              dragOver ? "border-indigo-500 bg-indigo-50" : "border-slate-300 bg-white hover:border-indigo-400"
            }`}
          >
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept=".pdf,.jpg,.jpeg,.png"
              onChange={handleFileSelect}
              className="hidden"
            />
            {uploading ? (
              <div className="flex flex-col items-center gap-3">
                <Loader2 className="h-8 w-8 animate-spin text-indigo-600" />
                <p className="text-sm font-medium text-slate-700">Processing certificates...</p>
              </div>
            ) : (
              <div className="flex flex-col items-center gap-3">
                <div className="flex h-12 w-12 items-center justify-center rounded-full bg-indigo-100">
                  <Upload className="h-6 w-6 text-indigo-600" />
                </div>
                <div>
                  <p className="text-sm font-medium text-slate-700">
                    Drag and drop certificates here, or click to browse
                  </p>
                  <p className="text-xs text-slate-500 mt-1">
                    Supports PDF, JPG, JPEG, PNG — up to 50 files per batch
                  </p>
                </div>
              </div>
            )}
          </div>

          {/* Upload Results */}
          {uploadResults && (
            <div className="mt-4 rounded-xl border border-slate-200 bg-white p-4">
              <div className="mb-3 flex items-center justify-between">
                <h3 className="text-sm font-semibold text-slate-900">Upload Results</h3>
                <button onClick={() => setUploadResults(null)} className="text-slate-400 hover:text-slate-600">
                  <X size={16} />
                </button>
              </div>
              <div className="space-y-2 max-h-60 overflow-y-auto">
                {uploadResults.map((r, i) => (
                  <div key={i} className="flex items-center justify-between rounded-lg bg-slate-50 px-3 py-2">
                    <span className="text-sm text-slate-700 truncate">{r.filename || `File ${i + 1}`}</span>
                    <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${
                      r.status === "failed" ? "bg-red-100 text-red-700" :
                      r.status === "ready_for_review" ? "bg-amber-100 text-amber-700" :
                      r.status === "approved" ? "bg-green-100 text-green-700" :
                      "bg-slate-100 text-slate-600"
                    }`}>
                      {STATUS_LABELS[r.status] || r.status}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Charts / Distribution */}
        {dashboard && dashboard.total > 0 && (
          <div className="mb-8 grid grid-cols-1 gap-4 lg:grid-cols-2">
            {Object.keys(dashboard.by_type).length > 0 && (
              <div className="rounded-xl border border-slate-200 bg-white p-5">
                <h3 className="mb-4 text-sm font-semibold text-slate-900">Certificates by Type</h3>
                <div className="space-y-2">
                  {Object.entries(dashboard.by_type).map(([type, count]) => (
                    <div key={type} className="flex items-center gap-3">
                      <span className="text-xs text-slate-600 w-40 truncate">{type.replace(/_/g, " ")}</span>
                      <div className="flex-1 h-6 bg-slate-100 rounded overflow-hidden">
                        <div
                          className="h-full bg-indigo-500 rounded"
                          style={{ width: `${(count / dashboard.total) * 100}%` }}
                        />
                      </div>
                      <span className="text-xs font-medium text-slate-700 w-8 text-right">{count}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
            {Object.keys(dashboard.by_verification).length > 0 && (
              <div className="rounded-xl border border-slate-200 bg-white p-5">
                <h3 className="mb-4 text-sm font-semibold text-slate-900">Verification Status</h3>
                <div className="space-y-2">
                  {Object.entries(dashboard.by_verification).map(([status, count]) => (
                    <div key={status} className="flex items-center gap-3">
                      <span className="text-xs text-slate-600 w-40 truncate">
                        {VERIFICATION_LABELS[status] || status}
                      </span>
                      <div className="flex-1 h-6 bg-slate-100 rounded overflow-hidden">
                        <div
                          className="h-full bg-emerald-500 rounded"
                          style={{ width: `${(count / dashboard.total) * 100}%` }}
                        />
                      </div>
                      <span className="text-xs font-medium text-slate-700 w-8 text-right">{count}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Search & Filters */}
        <div className="mb-4 flex flex-wrap items-center gap-3">
          <div className="relative flex-1 min-w-[200px]">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
            <input
              type="text"
              placeholder="Search by name, certificate number, institution..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSearch()}
              className="w-full pl-10 pr-4 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>
          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            className="px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="">All Types</option>
            <option value="academic_certificate">Academic Certificate</option>
            <option value="degree_certificate">Degree Certificate</option>
            <option value="diploma">Diploma</option>
            <option value="professional_certificate">Professional Certificate</option>
            <option value="training_certificate">Training Certificate</option>
            <option value="certificate_of_completion">Certificate of Completion</option>
            <option value="certificate_of_attendance">Certificate of Attendance</option>
            <option value="membership_certificate">Membership Certificate</option>
            <option value="license_certification">License/Certification</option>
          </select>
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="">All Statuses</option>
            <option value="ready_for_review">Ready for Review</option>
            <option value="approved">Approved</option>
            <option value="rejected">Rejected</option>
            <option value="failed">Failed</option>
          </select>
          <Button onClick={handleSearch} variant="secondary" size="sm">
            <Filter size={14} className="mr-1" /> Filter
          </Button>
          <div className="flex gap-2">
            <Button
              onClick={() => certificateService.exportCsv()}
              variant="secondary"
              size="sm"
              disabled={!dashboard || dashboard.total === 0}
            >
              <Download size={14} className="mr-1" /> CSV
            </Button>
            <Button
              onClick={() => certificateService.exportXlsx()}
              variant="secondary"
              size="sm"
              disabled={!dashboard || dashboard.total === 0}
            >
              <Download size={14} className="mr-1" /> XLSX
            </Button>
          </div>
        </div>

        {/* Certificate List */}
        <div className="rounded-xl border border-slate-200 bg-white overflow-hidden">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-6 w-6 animate-spin text-slate-400" />
            </div>
          ) : certificates.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-16 text-center">
              <Award className="h-12 w-12 text-slate-300 mb-3" />
              <p className="text-sm font-medium text-slate-700">No certificates yet</p>
              <p className="text-xs text-slate-500 mt-1">
                Upload your first certificate to begin extracting and analyzing certificate data.
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-slate-50 border-b border-slate-200">
                  <tr>
                    <th className="px-4 py-3 text-left font-medium text-slate-600">Filename</th>
                    <th className="px-4 py-3 text-left font-medium text-slate-600">Type</th>
                    <th className="px-4 py-3 text-left font-medium text-slate-600">Status</th>
                    <th className="px-4 py-3 text-left font-medium text-slate-600">Verification</th>
                    <th className="px-4 py-3 text-left font-medium text-slate-600">Confidence</th>
                    <th className="px-4 py-3 text-left font-medium text-slate-600">Created</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {certificates.map((cert) => (
                    <tr key={cert.id} className="hover:bg-slate-50">
                      <td className="px-4 py-3 text-slate-900 truncate max-w-xs">
                        {cert.filename}
                      </td>
                      <td className="px-4 py-3 text-slate-600">
                        {cert.document_type_label || cert.document_type || "—"}
                      </td>
                      <td className="px-4 py-3">
                        <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                          STATUS_COLORS[cert.status] || "bg-slate-100 text-slate-600"
                        }`}>
                          {STATUS_LABELS[cert.status] || cert.status}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                          VERIFICATION_COLORS[cert.verification_status] || "bg-slate-100 text-slate-600"
                        }`}>
                          {VERIFICATION_LABELS[cert.verification_status] || cert.verification_status}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-slate-600">
                        {cert.overall_confidence != null
                          ? `${(cert.overall_confidence * 100).toFixed(1)}%`
                          : "—"}
                      </td>
                      <td className="px-4 py-3 text-slate-500 text-xs">
                        {cert.created_at ? new Date(cert.created_at).toLocaleDateString() : "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Analytics Bridge */}
        {dashboard && dashboard.approved > 0 && (
          <div className="mt-8 rounded-xl border border-indigo-200 bg-indigo-50 p-5">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-indigo-600 text-white">
                  <BarChart3 size={20} />
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-slate-900">Analyze Certificate Data</h3>
                  <p className="text-xs text-slate-600">
                    Export {dashboard.approved} approved certificates to a dataset for analysis, dashboards, and reports
                  </p>
                </div>
              </div>
              <Button
                onClick={async () => {
                  try {
                    const result = await certificateService.toDataset("Certificate Analytics Dataset");
                    alert(result.message);
                  } catch (err: any) {
                    alert(err.message || "Failed to export to dataset");
                  }
                }}
                size="sm"
              >
                Export to Dataset <ArrowRight size={14} className="ml-1" />
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
