'use client';

import { useState } from 'react';
import { Database, BarChart3, Shield, Globe, AlertTriangle, Table2, Layers, Search } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { formatNumber, formatPercent } from '@/lib/utils';
import type { DatasetProfile, QualityReport, IndustryResult } from '@/types/workflow';

interface Props {
  profile: DatasetProfile | null;
  quality: QualityReport | null;
  industry: IndustryResult | null;
  onContinue: () => void;
}

export function UnderstandStep({ profile, quality, industry, onContinue }: Props) {
  const [activeTab, setActiveTab] = useState<'overview' | 'columns' | 'issues'>('overview');
  const [columnSearch, setColumnSearch] = useState('');

  if (!profile) {
    return (
      <Card>
        <CardContent className="py-12 text-center text-muted-foreground">
          Processing your data... Profile will appear here once complete.
        </CardContent>
      </Card>
    );
  }

  const qualityScore = quality?.score?.overall ?? profile.overall_quality_score;
  const qualityGrade = quality?.score?.grade ?? 'N/A';
  const trafficLight = quality?.score?.traffic_light ?? 'yellow';

  const filteredColumns = (profile.columns || []).filter((col) =>
    col.name.toLowerCase().includes(columnSearch.toLowerCase()) ||
    col.dtype.toLowerCase().includes(columnSearch.toLowerCase())
  );

  return (
    <div className="space-y-6">
      {/* Navigation Tabs */}
      <div className="flex items-center justify-between border-b border-border pb-3">
        <div className="flex gap-2">
          <button
            onClick={() => setActiveTab('overview')}
            className={`flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
              activeTab === 'overview'
                ? 'bg-primary text-primary-foreground shadow-sm'
                : 'text-muted-foreground hover:text-foreground hover:bg-muted/50'
            }`}
          >
            <Layers className="h-4 w-4" />
            Executive Overview
          </button>
          <button
            onClick={() => setActiveTab('columns')}
            className={`flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
              activeTab === 'columns'
                ? 'bg-primary text-primary-foreground shadow-sm'
                : 'text-muted-foreground hover:text-foreground hover:bg-muted/50'
            }`}
          >
            <Table2 className="h-4 w-4" />
            Schema & Columns ({profile.column_count})
          </button>
          <button
            onClick={() => setActiveTab('issues')}
            className={`flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
              activeTab === 'issues'
                ? 'bg-primary text-primary-foreground shadow-sm'
                : 'text-muted-foreground hover:text-foreground hover:bg-muted/50'
            }`}
          >
            <AlertTriangle className="h-4 w-4" />
            Quality Audit ({quality ? quality.findings.length : 0})
          </button>
        </div>

        <Button onClick={onContinue} size="sm">
          Continue to Clean Data &rarr;
        </Button>
      </div>

      {/* TAB 1: OVERVIEW */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* Dataset Summary */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center gap-2 text-muted-foreground text-sm mb-1">
                  <Database className="h-4 w-4 text-primary" />
                  <span>Total Records</span>
                </div>
                <p className="text-2xl font-bold">{formatNumber(profile.row_count)}</p>
                <p className="text-xs text-muted-foreground mt-1">
                  Memory: ~{(profile.memory_mb || 0).toFixed(1)} MB
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center gap-2 text-muted-foreground text-sm mb-1">
                  <BarChart3 className="h-4 w-4 text-blue-500" />
                  <span>Columns</span>
                </div>
                <p className="text-2xl font-bold">{profile.column_count}</p>
                <p className="text-xs text-muted-foreground mt-1">
                  {profile.columns?.filter((c) => c.dtype.includes('int') || c.dtype.includes('float')).length || 0} numeric,{' '}
                  {profile.columns?.filter((c) => !c.dtype.includes('int') && !c.dtype.includes('float')).length || 0} categorical
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center gap-2 text-muted-foreground text-sm mb-1">
                  <Shield className="h-4 w-4 text-emerald-500" />
                  <span>Data Quality</span>
                </div>
                <div className="flex items-baseline gap-2">
                  <p className="text-2xl font-bold">{qualityScore != null ? qualityScore.toFixed(0) : '—'}</p>
                  <span className="text-sm text-muted-foreground">/100</span>
                  <Badge
                    className={
                      trafficLight === 'green'
                        ? 'bg-emerald-600 text-white'
                        : trafficLight === 'yellow'
                          ? 'bg-amber-500 text-white'
                          : 'bg-rose-600 text-white'
                    }
                  >
                    Grade {qualityGrade}
                  </Badge>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center gap-2 text-muted-foreground text-sm mb-1">
                  <Globe className="h-4 w-4 text-indigo-500" />
                  <span>Detected Sector</span>
                </div>
                <p className="text-2xl font-bold capitalize">{industry?.industry ?? 'General'}</p>
                {industry?.confidence != null && (
                  <p className="text-xs text-muted-foreground mt-0.5">
                    {formatPercent(industry.confidence)} model confidence
                  </p>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Quality Dimensions */}
          {quality?.score && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Quality Integrity Dimensions</CardTitle>
                <CardDescription>Comprehensive ISO-compliant data health evaluation</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-5 gap-4">
                  {[
                    { label: 'Completeness', value: quality.score.completeness },
                    { label: 'Validity', value: quality.score.validity },
                    { label: 'Uniqueness', value: quality.score.uniqueness },
                    { label: 'Consistency', value: quality.score.consistency },
                    { label: 'Timeliness', value: quality.score.timeliness },
                  ].map((dim) => (
                    <div key={dim.label} className="text-center p-3 rounded-lg bg-muted/30 border">
                      <div className="relative mx-auto h-16 w-16">
                        <svg viewBox="0 0 36 36" className="h-16 w-16 -rotate-90">
                          <circle
                            cx="18"
                            cy="18"
                            r="15.5"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth="3"
                            className="text-muted/30"
                          />
                          <circle
                            cx="18"
                            cy="18"
                            r="15.5"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth="3"
                            strokeDasharray={`${(dim.value / 100) * 97.4} 97.4`}
                            className={dim.value >= 80 ? 'text-emerald-600' : dim.value >= 60 ? 'text-amber-500' : 'text-rose-500'}
                          />
                        </svg>
                        <span className="absolute inset-0 flex items-center justify-center text-xs font-semibold">
                          {dim.value.toFixed(0)}%
                        </span>
                      </div>
                      <p className="mt-2 text-xs font-medium">{dim.label}</p>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Missing, Duplicates & Outliers cards */}
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            <Card>
              <CardContent className="pt-6 text-center">
                <p className="text-xs uppercase tracking-wider text-muted-foreground font-semibold">Missing Values</p>
                <p className="text-2xl font-bold mt-1 text-amber-600">
                  {formatNumber(profile.total_missing)}
                </p>
                <p className="text-xs text-muted-foreground mt-0.5">
                  {formatPercent(profile.missing_percentage)} of all cells
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6 text-center">
                <p className="text-xs uppercase tracking-wider text-muted-foreground font-semibold">Duplicate Records</p>
                <p className="text-2xl font-bold mt-1 text-indigo-600">
                  {formatNumber(profile.duplicate_rows)}
                </p>
                <p className="text-xs text-muted-foreground mt-0.5">
                  {formatPercent(profile.duplicate_percentage)} of total rows
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6 text-center">
                <p className="text-xs uppercase tracking-wider text-muted-foreground font-semibold">Outliers Flagged</p>
                <p className="text-2xl font-bold mt-1 text-rose-600">
                  {formatNumber(profile.total_outliers)}
                </p>
                <p className="text-xs text-muted-foreground mt-0.5">
                  Identified via IQR & z-score
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      )}

      {/* TAB 2: SCHEMA & COLUMNS */}
      {activeTab === 'columns' && (
        <Card>
          <CardHeader>
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div>
                <CardTitle className="text-base">Attribute Profiles & Schema</CardTitle>
                <CardDescription>Detailed statistical distributions per column</CardDescription>
              </div>
              <div className="relative w-full sm:w-64">
                <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Filter columns..."
                  value={columnSearch}
                  onChange={(e) => setColumnSearch(e.target.value)}
                  className="pl-9 h-9 text-xs"
                />
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="rounded-lg border overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead className="bg-muted/50 border-b font-medium text-muted-foreground">
                  <tr>
                    <th className="p-3">Column Name</th>
                    <th className="p-3">Data Type</th>
                    <th className="p-3">Completeness</th>
                    <th className="p-3">Uniqueness</th>
                    <th className="p-3">Distinct Values</th>
                    <th className="p-3">Summary / Range</th>
                    <th className="p-3">Quality</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {filteredColumns.map((col) => (
                    <tr key={col.name} className="hover:bg-muted/30 transition-colors">
                      <td className="p-3 font-semibold text-foreground flex items-center gap-2">
                        {col.name}
                        {col.is_sensitive && (
                          <Badge variant="destructive" className="text-[10px] px-1.5 py-0">
                            {col.sensitive_type || 'PII'}
                          </Badge>
                        )}
                      </td>
                      <td className="p-3 font-mono text-muted-foreground">{col.dtype}</td>
                      <td className="p-3">
                        <div className="flex items-center gap-2">
                          <div className="w-16 h-1.5 bg-muted rounded-full overflow-hidden">
                            <div
                              className={`h-full ${
                                col.null_percentage === 0
                                  ? 'bg-emerald-500'
                                  : col.null_percentage < 10
                                    ? 'bg-amber-500'
                                    : 'bg-rose-500'
                              }`}
                              style={{ width: `${Math.max(0, 100 - col.null_percentage)}%` }}
                            />
                          </div>
                          <span>{(100 - col.null_percentage).toFixed(0)}%</span>
                        </div>
                      </td>
                      <td className="p-3">{(col.uniqueness * 100).toFixed(1)}%</td>
                      <td className="p-3">{formatNumber(col.unique_count)}</td>
                      <td className="p-3 text-muted-foreground">
                        {col.min_value != null && col.max_value != null
                          ? `${col.min_value.toFixed(1)} – ${col.max_value.toFixed(1)} (avg: ${col.mean_value?.toFixed(1)})`
                          : col.top_values
                            ? Object.keys(col.top_values).slice(0, 2).join(', ')
                            : '—'}
                      </td>
                      <td className="p-3">
                        <span
                          className={`inline-flex px-2 py-0.5 rounded-full text-[10px] font-semibold ${
                            col.quality_score >= 80
                              ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300'
                              : col.quality_score >= 60
                                ? 'bg-amber-50 text-amber-700 dark:bg-amber-950/40 dark:text-amber-300'
                                : 'bg-rose-50 text-rose-700 dark:bg-rose-950/40 dark:text-rose-300'
                          }`}
                        >
                          {col.quality_score.toFixed(0)}/100
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}

      {/* TAB 3: QUALITY AUDIT */}
      {activeTab === 'issues' && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-amber-500" />
              Automated Data Integrity Audit
            </CardTitle>
            <CardDescription>{quality?.summary || 'Detailed findings generated during data profiling'}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {quality && quality.findings.length > 0 ? (
              <div className="space-y-3">
                {quality.findings.map((f, i) => (
                  <div
                    key={i}
                    className="p-4 rounded-lg border bg-card flex flex-col md:flex-row md:items-center justify-between gap-3"
                  >
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <Badge
                          variant={
                            f.severity === 'critical' || f.severity === 'error'
                              ? 'destructive'
                              : f.severity === 'warning'
                                ? 'secondary'
                                : 'outline'
                          }
                          className="capitalize text-[11px]"
                        >
                          {f.severity}
                        </Badge>
                        <span className="font-semibold text-sm">{f.check_name}</span>
                        {f.column && <span className="text-xs text-muted-foreground font-mono">[{f.column}]</span>}
                      </div>
                      <p className="text-xs text-muted-foreground">{f.message}</p>
                      {f.suggested_fix && (
                        <p className="text-xs text-primary font-medium">Recommended Fix: {f.suggested_fix}</p>
                      )}
                    </div>
                    <div className="text-right shrink-0">
                      <span className="text-xs font-semibold text-muted-foreground">
                        {f.affected_rows} rows affected
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="py-8 text-center text-sm text-emerald-600 font-medium">
                No quality defects or critical anomalies were detected!
              </div>
            )}
          </CardContent>
        </Card>
      )}

      <Button onClick={onContinue} size="lg" className="w-full">
        Proceed to Clean Data &rarr;
      </Button>
    </div>
  );
}

