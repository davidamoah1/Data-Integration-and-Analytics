"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Award,
  Users,
  Building2,
  GraduationCap,
  TrendingUp,
  Calendar,
  Download,
  FileText,
  Presentation,
  Filter,
  X,
  RefreshCw,
  Loader2,
  Search,
  ChevronLeft,
  ChevronRight,
  CheckCircle2,
  AlertCircle,
  BarChart3,
  Lightbulb,
  Hash,
  Clock,
} from "lucide-react";
import {
  approvedAnalyticsService,
  type ApprovedAnalyticsSummary,
  type ApprovedCertificateRecord,
  type ApprovedFilterOptions,
  type ApprovedAnalyticsFilters,
} from "@/services/certificates/approvedAnalyticsService";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Select } from "@/components/ui/Select";
import { Input } from "@/components/ui/Input";
import { Badge } from "@/components/ui/Badge";
import { toast } from "@/components/ui/Toaster";

const NOT_AVAILABLE = "Not Available";
const CHART_COLORS = [
  "#6366f1", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6",
  "#ec4899", "#14b8a6", "#f97316", "#3b82f6", "#84cc16",
  "#06b6d4", "#a855f7", "#eab308", "#rose-500", "#slate-600",
];

function formatLabel(key: string): string {
  return key.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

function formatDate(iso: string | null): string {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  } catch {
    return iso;
  }
}

export default function ApprovedCertificateAnalyticsPage() {
  const [summary, setSummary] = useState<ApprovedAnalyticsSummary | null>(null);
  const [records, setRecords] = useState<ApprovedCertificateRecord[]>([]);
  const [recordsTotal, setRecordsTotal] = useState(0);
  const [filterOptions, setFilterOptions] = useState<ApprovedFilterOptions | null>(null);
  const [loading, setLoading] = useState(true);
  const [recordsLoading, setRecordsLoading] = useState(false);
  const [exporting, setExporting] = useState<string | null>(null);
  const [showFilters, setShowFilters] = useState(false);

  const [filters, setFilters] = useState<ApprovedAnalyticsFilters>({});
  const [search, setSearch] = useState("");
  const [sortBy, setSortBy] = useState("approved_at");
  const [sortOrder, setSortOrder] = useState("desc");
  const [page, setPage] = useState(0);
  const pageSize = 25;

  const fetchSummary = useCallback(async () => {
    setLoading(true);
    try {
      const data = await approvedAnalyticsService.getSummary(filters);
      setSummary(data);
    } catch (err: any) {
      toast.error(err.message || "Failed to load analytics");
    } finally {
      setLoading(false);
    }
  }, [filters]);

  const fetchRecords = useCallback(async () => {
    setRecordsLoading(true);
    try {
      const data = await approvedAnalyticsService.getRecords({
        ...filters,
        search: search || undefined,
        sort_by: sortBy,
        sort_order: sortOrder,
        limit: pageSize,
        offset: page * pageSize,
      });
      setRecords(data.records);
      setRecordsTotal(data.total);
    } catch (err: any) {
      toast.error(err.message || "Failed to load records");
    } finally {
      setRecordsLoading(false);
    }
  }, [filters, search, sortBy, sortOrder, page]);

  const fetchFilterOptions = useCallback(async () => {
    try {
      const data = await approvedAnalyticsService.getFilters();
      setFilterOptions(data);
    } catch {
      // silent fail
    }
  }, []);

  useEffect(() => {
    fetchSummary();
    fetchFilterOptions();
  }, [fetchSummary, fetchFilterOptions]);

  useEffect(() => {
    fetchRecords();
  }, [fetchRecords]);

  const handleExport = async (format: "csv" | "xlsx") => {
    setExporting(format);
    try {
      if (format === "csv") {
        await approvedAnalyticsService.exportCsv(filters);
      } else {
        await approvedAnalyticsService.exportXlsx(filters);
      }
      toast.success(`Exported as ${format.toUpperCase()}`);
    } catch (err: any) {
      toast.error(err.message || `Export failed`);
    } finally {
      setExporting(null);
    }
  };

  const handlePresentation = async () => {
    setExporting("pptx");
    try {
      await approvedAnalyticsService.downloadPresentation(filters);
      toast.success("Presentation downloaded");
    } catch (err: any) {
      toast.error(err.message || "Presentation download failed");
    } finally {
      setExporting(null);
    }
  };

  const handleReport = async () => {
    setExporting("report");
    try {
      await approvedAnalyticsService.downloadReport(filters);
      toast.success("Report downloaded successfully");
    } catch (err: any) {
      toast.error(err.message || "Report generation failed");
    } finally {
      setExporting(null);
    }
  };

  const clearFilters = () => {
    setFilters({});
    setSearch("");
    setPage(0);
  };

  const hasActiveFilters = Object.values(filters).some((v) => v);

  const totalPages = Math.ceil(recordsTotal / pageSize);

  return (
    <div className="space-y-6 p-4 sm:p-6 w-full max-w-full overflow-x-hidden">
      {/* Executive Header & Action Toolbar */}
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between pb-4 border-b border-slate-200/80">
        <div>
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-indigo-50 border border-indigo-100 text-indigo-600 shadow-sm">
              <Award className="h-5 w-5" />
            </div>
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-slate-900">
                  Approved Certificate Analytics
                </h1>
                <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2.5 py-0.5 text-xs font-semibold text-emerald-700 border border-emerald-200">
                  <CheckCircle2 className="h-3 w-3 text-emerald-600" />
                  Verified Only
                </span>
              </div>
              <p className="mt-0.5 text-xs sm:text-sm text-slate-500">
                Official analytics and verified credential distribution computed exclusively from approved records
              </p>
            </div>
          </div>
        </div>

        {/* Action Toolbar - Consistent button designs */}
        <div className="flex flex-wrap items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleReport}
            disabled={exporting !== null}
            className="gap-1.5 text-xs sm:text-sm"
            title="Download detailed report"
          >
            {exporting === "report" ? (
              <Loader2 className="h-3.5 w-3.5 sm:h-4 sm:w-4 animate-spin" />
            ) : (
              <FileText className="h-3.5 w-3.5 sm:h-4 sm:w-4" />
            )}
            Report
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={() => handleExport("xlsx")}
            disabled={exporting !== null}
            className="gap-1.5 text-xs sm:text-sm"
            title="Export to Excel (.xlsx)"
          >
            {exporting === "xlsx" ? (
              <Loader2 className="h-3.5 w-3.5 sm:h-4 sm:w-4 animate-spin" />
            ) : (
              <Download className="h-3.5 w-3.5 sm:h-4 sm:w-4" />
            )}
            Excel
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={() => handleExport("csv")}
            disabled={exporting !== null}
            className="gap-1.5 text-xs sm:text-sm"
            title="Export to CSV (.csv)"
          >
            {exporting === "csv" ? (
              <Loader2 className="h-3.5 w-3.5 sm:h-4 sm:w-4 animate-spin" />
            ) : (
              <Download className="h-3.5 w-3.5 sm:h-4 sm:w-4" />
            )}
            CSV
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={handlePresentation}
            disabled={exporting !== null}
            className="gap-1.5 text-xs sm:text-sm"
            title="Download PowerPoint presentation (.pptx)"
          >
            {exporting === "pptx" ? (
              <Loader2 className="h-3.5 w-3.5 sm:h-4 sm:w-4 animate-spin" />
            ) : (
              <Presentation className="h-3.5 w-3.5 sm:h-4 sm:w-4" />
            )}
            PowerPoint
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowFilters(!showFilters)}
            className="gap-1.5 text-xs sm:text-sm"
          >
            <Filter className="h-3.5 w-3.5 sm:h-4 sm:w-4" />
            Filters
            {hasActiveFilters && (
              <Badge variant="default" className="ml-1 px-1.5 py-0 text-xs">
                {Object.values(filters).filter(Boolean).length}
              </Badge>
            )}
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={() => { fetchSummary(); fetchRecords(); }}
            disabled={loading}
            className="gap-1.5 text-xs sm:text-sm"
            title="Refresh analytics data"
          >
            <RefreshCw className={`h-3.5 w-3.5 sm:h-4 sm:w-4 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </Button>
        </div>
      </div>

      {/* Filters panel */}
      {showFilters && (
        <Card className="border-indigo-100/80 bg-slate-50/50 shadow-sm">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Filter className="h-4 w-4 text-indigo-600" />
                <CardTitle className="text-sm font-semibold text-slate-800">Dataset Scope Filters</CardTitle>
              </div>
              {hasActiveFilters && (
                <Button variant="ghost" size="sm" onClick={clearFilters} className="text-xs text-rose-600 hover:text-rose-700">
                  <X className="h-3.5 w-3.5 mr-1" /> Reset all
                </Button>
              )}
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 gap-4 md:grid-cols-3 lg:grid-cols-4">
              <div>
                <label className="mb-1 block text-xs font-medium text-slate-600">Certificate Name</label>
                <Select
                  value={filters.certificate_name || ""}
                  onChange={(e) => { setFilters({ ...filters, certificate_name: e.target.value || undefined }); setPage(0); }}
                >
                  <option value="">All</option>
                  {filterOptions?.certificate_names.map((n) => (
                    <option key={n} value={n}>{n}</option>
                  ))}
                </Select>
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-slate-600">Certificate Type</label>
                <Select
                  value={filters.certificate_type || ""}
                  onChange={(e) => { setFilters({ ...filters, certificate_type: e.target.value || undefined }); setPage(0); }}
                >
                  <option value="">All</option>
                  {filterOptions?.certificate_types.map((t) => (
                    <option key={t} value={t}>{t}</option>
                  ))}
                </Select>
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-slate-600">Issuing Organization</label>
                <Select
                  value={filters.issuing_organization || ""}
                  onChange={(e) => { setFilters({ ...filters, issuing_organization: e.target.value || undefined }); setPage(0); }}
                >
                  <option value="">All</option>
                  {filterOptions?.issuing_organizations.map((o) => (
                    <option key={o} value={o}>{o}</option>
                  ))}
                </Select>
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-slate-600">Course</label>
                <Select
                  value={filters.course || ""}
                  onChange={(e) => { setFilters({ ...filters, course: e.target.value || undefined }); setPage(0); }}
                >
                  <option value="">All</option>
                  {filterOptions?.courses.map((c) => (
                    <option key={c} value={c}>{c}</option>
                  ))}
                </Select>
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-slate-600">Recipient</label>
                <Select
                  value={filters.recipient || ""}
                  onChange={(e) => { setFilters({ ...filters, recipient: e.target.value || undefined }); setPage(0); }}
                >
                  <option value="">All</option>
                  {filterOptions?.recipients.map((r) => (
                    <option key={r} value={r}>{r}</option>
                  ))}
                </Select>
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-slate-600">Date From</label>
                <Input
                  type="date"
                  value={filters.date_from || ""}
                  onChange={(e) => { setFilters({ ...filters, date_from: e.target.value || undefined }); setPage(0); }}
                />
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-slate-600">Date To</label>
                <Input
                  type="date"
                  value={filters.date_to || ""}
                  onChange={(e) => { setFilters({ ...filters, date_to: e.target.value || undefined }); setPage(0); }}
                />
              </div>
              <div>
                <label className="mb-1 block text-xs font-medium text-slate-600">Year</label>
                <Select
                  value={filters.year ? String(filters.year) : ""}
                  onChange={(e) => { setFilters({ ...filters, year: e.target.value ? Number(e.target.value) : undefined }); setPage(0); }}
                >
                  <option value="">All years</option>
                  {summary?.trends &&
                    Object.keys(summary.trends).map((y) => (
                      <option key={y} value={y}>{y}</option>
                    ))}
                </Select>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* KPI Cards */}
      {loading ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="h-8 w-8 animate-spin text-indigo-600" />
        </div>
      ) : summary ? (
        <>
          {summary.total === 0 ? (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-16">
                <AlertCircle className="mb-3 h-10 w-10 text-slate-400" />
                <p className="text-lg font-medium text-slate-600">No approved certificates found</p>
                <p className="mt-1 text-sm text-slate-400">
                  Approve certificates in Certificate Intelligence to see analytics here.
                </p>
              </CardContent>
            </Card>
          ) : (
            <>
              {/* KPI grid */}
              <div className="grid grid-cols-2 gap-2.5 sm:gap-4 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
                <KPICard
                  icon={<Award className="h-5 w-5" />}
                  label="Total Approved"
                  value={summary.kpis.total_approved}
                  color="indigo"
                />
                <KPICard
                  icon={<Users className="h-5 w-5" />}
                  label="Unique Recipients"
                  value={summary.kpis.unique_recipients}
                  color="emerald"
                />
                <KPICard
                  icon={<Hash className="h-5 w-5" />}
                  label="Certificate Types"
                  value={summary.kpis.certificate_types}
                  color="amber"
                />
                <KPICard
                  icon={<Building2 className="h-5 w-5" />}
                  label="Issuing Organizations"
                  value={summary.kpis.issuing_organizations}
                  color="purple"
                />
                <KPICard
                  icon={<GraduationCap className="h-5 w-5" />}
                  label="Courses"
                  value={summary.kpis.courses}
                  color="blue"
                />
                <KPICard
                  icon={<TrendingUp className="h-5 w-5" />}
                  label="Avg Certs / Person"
                  value={summary.kpis.avg_certs_per_person}
                  color="teal"
                />
                <KPICard
                  icon={<Calendar className="h-5 w-5" />}
                  label="Completed This Year"
                  value={summary.kpis.completed_this_year}
                  color="orange"
                />
                <KPICard
                  icon={<Clock className="h-5 w-5" />}
                  label="Completed This Month"
                  value={summary.kpis.completed_this_month}
                  color="rose"
                />
                <KPICard
                  icon={<Calendar className="h-5 w-5" />}
                  label="Earliest Completion"
                  value={formatDate(summary.kpis.earliest_completion_date)}
                  color="slate"
                />
                <KPICard
                  icon={<Calendar className="h-5 w-5" />}
                  label="Latest Completion"
                  value={formatDate(summary.kpis.latest_completion_date)}
                  color="cyan"
                />
              </div>

              {/* Insights */}
              {summary.insights.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-base">
                      <Lightbulb className="h-5 w-5 text-amber-500" />
                      Key Insights
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ul className="space-y-2">
                      {summary.insights.map((insight, i) => (
                        <li key={i} className="flex items-start gap-2 text-sm text-slate-700">
                          <span className="mt-1.5 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-amber-400" />
                          {insight}
                        </li>
                      ))}
                    </ul>
                  </CardContent>
                </Card>
              )}

              {/* Charts row 1: By Type (pie) + By Name (bar) */}
              <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
                <ChartCard title="Certificates by Type" icon={<BarChart3 className="h-5 w-5" />}>
                  <DonutChart data={summary.by_type} />
                </ChartCard>
                <ChartCard title="Top Certificate Names" icon={<Award className="h-5 w-5" />}>
                  <BarChart data={sliceDict(summary.by_name, 10)} />
                </ChartCard>
              </div>

              {/* Charts row 2: By Issuer + Trends */}
              <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
                <ChartCard title="Top Issuing Organizations" icon={<Building2 className="h-5 w-5" />}>
                  <BarChart data={sliceDict(summary.by_issuer, 10)} />
                </ChartCard>
                <ChartCard title="Completion Trends by Year" icon={<TrendingUp className="h-5 w-5" />}>
                  <BarChart data={summary.trends} orientation="vertical" />
                </ChartCard>
              </div>

              {/* Charts row 3: By Course + Certs per Person */}
              <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
                <ChartCard title="Top Courses" icon={<GraduationCap className="h-5 w-5" />}>
                  <BarChart data={sliceDict(summary.by_course, 10)} />
                </ChartCard>
                <ChartCard title="Certificates per Person" icon={<Users className="h-5 w-5" />}>
                  <BarChart data={summary.certs_per_person} />
                </ChartCard>
              </div>

              {/* Data quality */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-base">
                    <CheckCircle2 className="h-5 w-5 text-green-500" />
                    Data Quality Assessment
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <DataQualityBars dataQuality={summary.data_quality} />
                </CardContent>
              </Card>

              {/* Top recipients */}
              {summary.recipients.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-base">
                      <Users className="h-5 w-5 text-indigo-500" />
                      Top Recipients by Approved Certificates
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      {summary.recipients.slice(0, 10).map((r, i) => (
                        <div
                          key={r.name}
                          className="flex items-center justify-between rounded-lg border px-4 py-2.5"
                        >
                          <div className="flex items-center gap-3">
                            <span className="flex h-7 w-7 items-center justify-center rounded-full bg-indigo-100 text-xs font-bold text-indigo-700">
                              {i + 1}
                            </span>
                            <span className="text-sm font-medium text-slate-700">{r.name}</span>
                          </div>
                          <Badge variant="default">
                            {r.approved_certificates} cert{r.approved_certificates !== 1 ? "s" : ""}
                          </Badge>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Records table */}
              <Card className="overflow-hidden">
                <CardHeader className="pb-3">
                  <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                    <CardTitle className="text-base">Approved Certificate Records</CardTitle>
                    <div className="flex flex-wrap items-center gap-2">
                      <div className="relative flex-1 sm:flex-none">
                        <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-slate-400" />
                        <Input
                          placeholder="Search..."
                          value={search}
                          onChange={(e) => { setSearch(e.target.value); setPage(0); }}
                          className="h-9 w-full sm:w-48 pl-8 text-sm"
                        />
                      </div>
                      <Select
                        value={sortBy}
                        onChange={(e) => setSortBy(e.target.value)}
                        className="h-9 flex-1 sm:flex-none sm:w-44 text-sm"
                      >
                        <option value="approved_at">Sort: Approved Date</option>
                        <option value="recipient">Sort: Recipient</option>
                        <option value="certificate_name">Sort: Certificate Name</option>
                        <option value="issuing_organization">Sort: Organization</option>
                        <option value="completion_date">Sort: Completion Date</option>
                      </Select>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setSortOrder(sortOrder === "asc" ? "desc" : "asc")}
                        className="shrink-0"
                      >
                        {sortOrder === "desc" ? "↓" : "↑"}
                      </Button>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  {recordsLoading ? (
                    <div className="flex justify-center py-10">
                      <Loader2 className="h-6 w-6 animate-spin text-indigo-600" />
                    </div>
                  ) : records.length === 0 ? (
                    <div className="py-10 text-center text-sm text-slate-400">
                      No records found
                    </div>
                  ) : (
                    <>
                      <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                          <thead>
                            <tr className="border-b text-left text-xs font-medium text-slate-500">
                              <th className="pb-2 pr-4">Recipient</th>
                              <th className="pb-2 pr-4">Certificate</th>
                              <th className="pb-2 pr-4">Type</th>
                              <th className="pb-2 pr-4">Organization</th>
                              <th className="pb-2 pr-4">Date</th>
                              <th className="pb-2 pr-4">Approved</th>
                            </tr>
                          </thead>
                          <tbody>
                            {records.map((r) => (
                              <tr key={r.id} className="border-b last:border-0 hover:bg-slate-50">
                                <td className="py-2.5 pr-4 font-medium text-slate-700">
                                  {r.recipient}
                                </td>
                                <td className="py-2.5 pr-4 text-slate-600">
                                  {r.certificate_name}
                                </td>
                                <td className="py-2.5 pr-4 text-slate-600">
                                  {r.certificate_type}
                                </td>
                                <td className="py-2.5 pr-4 text-slate-600">
                                  {r.issuing_organization}
                                </td>
                                <td className="py-2.5 pr-4 text-slate-600">
                                  {r.completion_date}
                                </td>
                                <td className="py-2.5 pr-4 text-slate-500">
                                  {formatDate(r.approved_at)}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                      {/* Pagination */}
                      <div className="mt-4 flex items-center justify-between">
                        <span className="text-xs text-slate-500">
                          Showing {page * pageSize + 1}–{Math.min((page + 1) * pageSize, recordsTotal)} of {recordsTotal}
                        </span>
                        <div className="flex items-center gap-1">
                          <Button
                            variant="outline"
                            size="sm"
                            disabled={page === 0}
                            onClick={() => setPage(page - 1)}
                          >
                            <ChevronLeft className="h-4 w-4" />
                          </Button>
                          <span className="px-2 text-xs text-slate-500">
                            {page + 1} / {totalPages || 1}
                          </span>
                          <Button
                            variant="outline"
                            size="sm"
                            disabled={page >= totalPages - 1}
                            onClick={() => setPage(page + 1)}
                          >
                            <ChevronRight className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>
                    </>
                  )}
                </CardContent>
              </Card>
            </>
          )}
        </>
      ) : null}
    </div>
  );
}

// ── Helper components ─────────────────────────────────────────────────────

function sliceDict(d: Record<string, number>, n: number): Record<string, number> {
  return Object.fromEntries(Object.entries(d).slice(0, n));
}

const COLOR_MAP: Record<string, string> = {
  indigo: "bg-indigo-50 text-indigo-600",
  emerald: "bg-emerald-50 text-emerald-600",
  amber: "bg-amber-50 text-amber-600",
  purple: "bg-purple-50 text-purple-600",
  blue: "bg-blue-50 text-blue-600",
  teal: "bg-teal-50 text-teal-600",
  orange: "bg-orange-50 text-orange-600",
  rose: "bg-rose-50 text-rose-600",
  slate: "bg-slate-50 text-slate-600",
  cyan: "bg-cyan-50 text-cyan-600",
};

function KPICard({
  icon,
  label,
  value,
  color,
}: {
  icon: React.ReactNode;
  label: string;
  value: string | number;
  color: string;
}) {
  return (
    <Card className="overflow-hidden">
      <CardContent className="p-3 sm:p-4">
        <div className="flex items-start sm:items-center justify-between gap-2">
          <div className="min-w-0 flex-1">
            <p className="truncate text-xs font-medium text-slate-500" title={label}>{label}</p>
            <p className="mt-1 text-lg sm:text-2xl font-bold text-slate-800 truncate">{value}</p>
          </div>
          <div className={`flex h-8 w-8 sm:h-10 sm:w-10 shrink-0 items-center justify-center rounded-lg ${COLOR_MAP[color] || COLOR_MAP.indigo}`}>
            {icon}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function ChartCard({ title, icon, children }: { title: string; icon: React.ReactNode; children: React.ReactNode }) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center gap-2 text-base">
          {icon}
          {title}
        </CardTitle>
      </CardHeader>
      <CardContent>{children}</CardContent>
    </Card>
  );
}

function BarChart({
  data,
  orientation = "horizontal",
}: {
  data: Record<string, number>;
  orientation?: "horizontal" | "vertical";
}) {
  const entries = Object.entries(data).filter(([k]) => k !== NOT_AVAILABLE);
  const allEntries = Object.entries(data);
  if (allEntries.length === 0) {
    return <div className="py-8 text-center text-sm text-slate-400">No data available</div>;
  }
  const maxVal = Math.max(...allEntries.map(([, v]) => v), 1);

  if (orientation === "vertical") {
    return (
      <div className="flex items-end justify-around gap-2" style={{ height: 200 }}>
        {allEntries.map(([key, val], i) => (
          <div key={key} className="flex flex-1 flex-col items-center justify-end">
            <span className="mb-1 text-xs font-medium text-slate-600">{val}</span>
            <div
              className="w-full rounded-t transition-all"
              style={{
                height: `${(val / maxVal) * 160}px`,
                backgroundColor: CHART_COLORS[i % CHART_COLORS.length],
              }}
            />
            <span className="mt-1 text-xs text-slate-500 truncate max-w-full" title={key}>{key}</span>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {allEntries.map(([key, val], i) => (
        <div key={key} className="flex items-center gap-2.5 sm:gap-3">
          <span className="w-28 sm:w-40 shrink-0 truncate text-xs text-slate-600 font-medium" title={key}>
            {key}
          </span>
          <div className="relative h-6 flex-1 rounded bg-slate-100">
            <div
              className="absolute left-0 top-0 h-full rounded transition-all"
              style={{
                width: `${(val / maxVal) * 100}%`,
                backgroundColor: CHART_COLORS[i % CHART_COLORS.length],
              }}
            />
          </div>
          <span className="w-7 sm:w-8 shrink-0 text-right text-xs font-medium text-slate-700">{val}</span>
        </div>
      ))}
    </div>
  );
}

function DonutChart({ data }: { data: Record<string, number> }) {
  const entries = Object.entries(data);
  if (entries.length === 0) {
    return <div className="py-8 text-center text-sm text-slate-400">No data available</div>;
  }
  const total = entries.reduce((sum, [, v]) => sum + v, 0);

  let cumulative = 0;
  const segments = entries.map(([key, val], i) => {
    const pct = (val / total) * 100;
    const offset = cumulative;
    cumulative += pct;
    return { key, val, pct, offset, color: CHART_COLORS[i % CHART_COLORS.length] };
  });

  return (
    <div className="flex flex-col sm:flex-row items-center justify-center sm:justify-start gap-5 sm:gap-6">
      <div className="relative h-36 w-36 sm:h-40 sm:w-40 shrink-0">
        <svg viewBox="0 0 100 100" className="h-full w-full -rotate-90">
          {segments.map((seg, i) => {
            const circumference = 2 * Math.PI * 40;
            const dash = (seg.pct / 100) * circumference;
            const gap = circumference - dash;
            const offset = (seg.offset / 100) * circumference;
            return (
              <circle
                key={i}
                cx="50"
                cy="50"
                r="40"
                fill="none"
                stroke={seg.color}
                strokeWidth="12"
                strokeDasharray={`${dash} ${gap}`}
                strokeDashoffset={-offset}
              />
            );
          })}
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-xl sm:text-2xl font-bold text-slate-800">{total}</span>
          <span className="text-[11px] sm:text-xs text-slate-500">Total</span>
        </div>
      </div>
      <div className="w-full sm:flex-1 space-y-2">
        {segments.map((seg) => (
          <div key={seg.key} className="flex items-center justify-between gap-2 text-xs">
            <div className="flex items-center gap-2 min-w-0 flex-1">
              <span className="h-3 w-3 shrink-0 rounded" style={{ backgroundColor: seg.color }} />
              <span className="truncate text-slate-600 font-medium" title={seg.key}>{seg.key}</span>
            </div>
            <div className="flex items-center gap-1.5 shrink-0 text-right">
              <span className="font-semibold text-slate-800">{seg.val}</span>
              <span className="text-slate-400 text-[11px]">({seg.pct.toFixed(0)}%)</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function DataQualityBars({
  dataQuality,
}: {
  dataQuality: ApprovedAnalyticsSummary["data_quality"];
}) {
  const fields = [
    { label: "Recipient", key: "recipient_identified" as const },
    { label: "Certificate Name", key: "certificate_name_identified" as const },
    { label: "Completion Date", key: "completion_date_identified" as const },
    { label: "Institution", key: "institution_identified" as const },
    { label: "Certificate Number", key: "certificate_number_identified" as const },
    { label: "Course", key: "course_identified" as const },
  ];
  const total = dataQuality.total || 1;

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {fields.map((f) => {
        const count = dataQuality[f.key];
        const pct = (count / total) * 100;
        return (
          <div key={f.key}>
            <div className="mb-1 flex items-center justify-between text-xs">
              <span className="font-medium text-slate-600">{f.label}</span>
              <span className="text-slate-500">
                {count} / {dataQuality.total} ({pct.toFixed(0)}%)
              </span>
            </div>
            <div className="h-2 rounded-full bg-slate-100">
              <div
                className={`h-full rounded-full transition-all ${
                  pct >= 80 ? "bg-green-500" : pct >= 50 ? "bg-amber-500" : "bg-red-500"
                }`}
                style={{ width: `${pct}%` }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}
