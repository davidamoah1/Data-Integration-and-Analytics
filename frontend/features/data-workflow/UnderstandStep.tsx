'use client';

import { Database, BarChart3, Shield, Globe, AlertTriangle } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { formatNumber, formatPercent } from '@/lib/utils';
import type { DatasetProfile, QualityReport, IndustryResult } from '@/types/workflow';

interface Props {
  profile: DatasetProfile | null;
  quality: QualityReport | null;
  industry: IndustryResult | null;
  onContinue: () => void;
}

export function UnderstandStep({ profile, quality, industry, onContinue }: Props) {
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

  return (
    <div className="space-y-6">
      {/* Dataset Summary */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-2 text-muted-foreground text-sm mb-1">
              <Database className="h-4 w-4" />
              <span>Rows</span>
            </div>
            <p className="text-2xl font-bold">{formatNumber(profile.row_count)}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-2 text-muted-foreground text-sm mb-1">
              <BarChart3 className="h-4 w-4" />
              <span>Columns</span>
            </div>
            <p className="text-2xl font-bold">{profile.column_count}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-2 text-muted-foreground text-sm mb-1">
              <Shield className="h-4 w-4" />
              <span>Data Quality</span>
            </div>
            <div className="flex items-baseline gap-2">
              <p className="text-2xl font-bold">{qualityScore?.toFixed(0) ?? '—'}</p>
              <span className="text-sm text-muted-foreground">/100</span>
              <Badge
                className={
                  trafficLight === 'green'
                    ? 'bg-green-600 text-white'
                    : trafficLight === 'yellow'
                      ? 'bg-yellow-500 text-white'
                      : 'bg-red-600 text-white'
                }
              >
                {qualityGrade}
              </Badge>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-2 text-muted-foreground text-sm mb-1">
              <Globe className="h-4 w-4" />
              <span>Detected Sector</span>
            </div>
            <p className="text-2xl font-bold capitalize">{industry?.industry ?? 'Unknown'}</p>
            {industry?.confidence != null && (
              <p className="text-xs text-muted-foreground mt-0.5">
                {formatPercent(industry.confidence)} confidence
              </p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Quality Dimensions */}
      {quality?.score && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Quality Dimensions</CardTitle>
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
                <div key={dim.label} className="text-center">
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
                        className={dim.value >= 80 ? 'text-green-600' : dim.value >= 60 ? 'text-yellow-500' : 'text-red-500'}
                      />
                    </svg>
                    <span className="absolute inset-0 flex items-center justify-center text-xs font-semibold">
                      {dim.value.toFixed(0)}
                    </span>
                  </div>
                  <p className="mt-1 text-xs text-muted-foreground">{dim.label}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Key Issues */}
      {quality && quality.error_count + quality.warning_count > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-yellow-500" />
              Issues Found
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex gap-3 mb-3">
              {quality.error_count > 0 && (
                <Badge variant="destructive">{quality.error_count} errors</Badge>
              )}
              {quality.warning_count > 0 && (
                <Badge variant="secondary">{quality.warning_count} warnings</Badge>
              )}
              {quality.info_count > 0 && (
                <Badge variant="outline">{quality.info_count} info</Badge>
              )}
            </div>
            <p className="text-sm text-muted-foreground">{quality.summary}</p>
            {quality.recommendations.length > 0 && (
              <ul className="mt-3 space-y-1">
                {quality.recommendations.slice(0, 5).map((rec, i) => (
                  <li key={i} className="text-sm flex items-start gap-2">
                    <span className="text-primary mt-0.5">-</span>
                    <span>{rec}</span>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>
      )}

      {/* Missing Data */}
      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
        <Card>
          <CardContent className="pt-6 text-center">
            <p className="text-sm text-muted-foreground">Missing Values</p>
            <p className="text-xl font-bold">{formatPercent(profile.missing_percentage)}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6 text-center">
            <p className="text-sm text-muted-foreground">Duplicate Records</p>
            <p className="text-xl font-bold">{formatNumber(profile.duplicate_rows)}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6 text-center">
            <p className="text-sm text-muted-foreground">Outliers Detected</p>
            <p className="text-xl font-bold">{formatNumber(profile.total_outliers)}</p>
          </CardContent>
        </Card>
      </div>

      <Button onClick={onContinue} size="lg" className="w-full">
        Continue to Clean Data
      </Button>
    </div>
  );
}
