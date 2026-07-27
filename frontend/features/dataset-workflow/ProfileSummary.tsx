"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Skeleton } from "@/components/ui/Skeleton";
import { Badge } from "@/components/ui/Badge";
import { workflowService } from "@/services/workflow/workflowService";
import type { DatasetProfile } from "@/types/workflow";

interface Props {
  workflowId: string;
}

export function ProfileSummary({ workflowId }: Props) {
  const [profile, setProfile] = useState<DatasetProfile | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    workflowService.getProfile(workflowId).then((data) => {
      setProfile(data);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, [workflowId]);

  if (loading) return <Skeleton className="h-96" />;
  if (!profile) return <p className="text-muted-foreground">Profile not available</p>;

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <p className="text-sm text-muted-foreground">Rows</p>
            <p className="text-2xl font-bold">{profile.row_count.toLocaleString()}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <p className="text-sm text-muted-foreground">Columns</p>
            <p className="text-2xl font-bold">{profile.column_count}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <p className="text-sm text-muted-foreground">Quality Score</p>
            <p className="text-2xl font-bold">{profile.overall_quality_score.toFixed(1)}/100</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <p className="text-sm text-muted-foreground">Memory</p>
            <p className="text-2xl font-bold">{profile.memory_mb.toFixed(1)} MB</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <p className="text-sm text-muted-foreground">Completeness</p>
            <p className="text-xl font-semibold">{profile.overall_completeness.toFixed(1)}%</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <p className="text-sm text-muted-foreground">Uniqueness</p>
            <p className="text-xl font-semibold">{profile.overall_uniqueness.toFixed(1)}%</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <p className="text-sm text-muted-foreground">Duplicates</p>
            <p className="text-xl font-semibold">{profile.duplicate_rows} ({profile.duplicate_percentage.toFixed(1)}%)</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <p className="text-sm text-muted-foreground">Outliers</p>
            <p className="text-xl font-semibold">{profile.total_outliers}</p>
          </CardContent>
        </Card>
      </div>

      {profile.sensitive_columns.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Sensitive Columns Detected</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {profile.sensitive_columns.map((col) => (
                <Badge key={col} variant="destructive">{col}</Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {profile.candidate_primary_keys.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Candidate Primary Keys</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {profile.candidate_primary_keys.map((col) => (
                <Badge key={col} variant="default">{col}</Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Column Details</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-left">
                  <th className="pb-2 font-medium">Column</th>
                  <th className="pb-2 font-medium">Type</th>
                  <th className="pb-2 font-medium">Null %</th>
                  <th className="pb-2 font-medium">Unique</th>
                  <th className="pb-2 font-medium">Cardinality</th>
                  <th className="pb-2 font-medium">Quality</th>
                  <th className="pb-2 font-medium">Pattern</th>
                </tr>
              </thead>
              <tbody>
                {profile.columns.map((col) => (
                  <tr key={col.name} className="border-b">
                    <td className="py-2 font-medium">{col.name}</td>
                    <td className="py-2 text-muted-foreground">{col.dtype}</td>
                    <td className="py-2">{col.null_percentage.toFixed(1)}%</td>
                    <td className="py-2">{col.unique_count}</td>
                    <td className="py-2 capitalize">{col.cardinality}</td>
                    <td className="py-2">{col.quality_score.toFixed(1)}</td>
                    <td className="py-2 text-muted-foreground">{col.pattern}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {profile.correlations.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Correlations</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {profile.correlations.map((corr, i) => (
                <div key={i} className="flex items-center justify-between text-sm">
                  <span>{corr.column_1} ↔ {corr.column_2}</span>
                  <div className="flex items-center gap-2">
                    <span className="font-mono">{corr.correlation.toFixed(3)}</span>
                    <Badge variant={corr.direction === "positive" ? "default" : "secondary"}>
                      {corr.strength} {corr.direction}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
