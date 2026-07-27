"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Skeleton } from "@/components/ui/Skeleton";
import { workflowService } from "@/services/workflow/workflowService";
import type { QualityReport } from "@/types/workflow";

interface Props {
  workflowId: string;
}

const SEVERITY_COLORS: Record<string, string> = {
  critical: "bg-red-600 text-white",
  error: "bg-red-500 text-white",
  warning: "bg-yellow-500 text-white",
  info: "bg-blue-500 text-white",
};

export function QualityReportView({ workflowId }: Props) {
  const [report, setReport] = useState<QualityReport | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    workflowService.getQuality(workflowId).then((data) => {
      setReport(data);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, [workflowId]);

  if (loading) return <Skeleton className="h-96" />;
  if (!report) return <p className="text-muted-foreground">Quality report not available</p>;

  const score = report.score;

  return (
    <div className="space-y-4">
      {score && (
        <div className="grid grid-cols-2 md:grid-cols-6 gap-4">
          <Card>
            <CardContent className="pt-6 text-center">
              <p className="text-sm text-muted-foreground">Overall</p>
              <p className="text-3xl font-bold">{score.overall.toFixed(1)}</p>
              <Badge className={`mt-1 ${score.traffic_light === "green" ? "bg-green-600" : score.traffic_light === "yellow" ? "bg-yellow-500" : "bg-red-600"}`}>
                Grade {score.grade}
              </Badge>
            </CardContent>
          </Card>
          {[
            { label: "Completeness", value: score.completeness },
            { label: "Validity", value: score.validity },
            { label: "Uniqueness", value: score.uniqueness },
            { label: "Consistency", value: score.consistency },
            { label: "Timeliness", value: score.timeliness },
          ].map((metric) => (
            <Card key={metric.label}>
              <CardContent className="pt-6 text-center">
                <p className="text-sm text-muted-foreground">{metric.label}</p>
                <p className="text-2xl font-bold">{metric.value.toFixed(1)}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Summary</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm">{report.summary}</p>
          <div className="flex gap-4 mt-3">
            <Badge variant="destructive">{report.error_count} errors</Badge>
            <Badge variant="secondary">{report.warning_count} warnings</Badge>
            <Badge variant="outline">{report.info_count} info</Badge>
          </div>
        </CardContent>
      </Card>

      {report.recommendations.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Recommendations</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2">
              {report.recommendations.map((rec, i) => (
                <li key={i} className="text-sm flex items-start gap-2">
                  <span className="text-primary">→</span>
                  <span>{rec}</span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Findings ({report.findings.length})</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {report.findings.map((finding, i) => (
              <div key={i} className="border rounded-lg p-4">
                <div className="flex items-start justify-between mb-2">
                  <div>
                    <div className="flex items-center gap-2">
                      <Badge className={SEVERITY_COLORS[finding.severity] || "bg-gray-500"}>
                        {finding.severity}
                      </Badge>
                      <span className="text-sm font-medium capitalize">{finding.check_name.replace(/_/g, " ")}</span>
                      {finding.column && (
                        <Badge variant="outline">{finding.column}</Badge>
                      )}
                    </div>
                  </div>
                  <span className="text-xs text-muted-foreground">
                    {finding.affected_rows} rows ({finding.affected_pct.toFixed(1)}%)
                  </span>
                </div>
                <p className="text-sm">{finding.message}</p>
                {finding.business_impact && (
                  <p className="text-sm text-muted-foreground mt-1">
                    <span className="font-medium">Impact:</span> {finding.business_impact}
                  </p>
                )}
                {finding.suggested_fix && (
                  <p className="text-sm text-green-700 mt-1">
                    <span className="font-medium">Fix:</span> {finding.suggested_fix}
                  </p>
                )}
                {finding.sample_values.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-1">
                    {finding.sample_values.map((v, j) => (
                      <Badge key={j} variant="outline" className="text-xs">
                        {String(v)}
                      </Badge>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
