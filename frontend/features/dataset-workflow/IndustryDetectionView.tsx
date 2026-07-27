"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Alert } from "@/components/ui/Alert";
import { Skeleton } from "@/components/ui/Skeleton";
import { AlertCircle, Building2 } from "lucide-react";
import { workflowService } from "@/services/workflow/workflowService";
import type { IndustryResult } from "@/types/workflow";

interface Props {
  workflowId: string;
}

export function IndustryDetectionView({ workflowId }: Props) {
  const [result, setResult] = useState<IndustryResult | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    workflowService.getIndustry(workflowId).then((data) => {
      setResult(data);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, [workflowId]);

  if (loading) return <Skeleton className="h-64" />;
  if (!result) return <p className="text-muted-foreground">Industry detection not available</p>;

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Building2 className="h-5 w-5" />
            Detected Industry
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-4">
            <div>
              <p className="text-3xl font-bold capitalize">{result.industry}</p>
              <p className="text-sm text-muted-foreground">
                Confidence: {result.confidence.toFixed(1)}%
              </p>
            </div>
            <div className="flex-1">
              <div className="h-4 bg-muted rounded-full overflow-hidden">
                <div
                  className={`h-full ${result.confidence >= 85 ? "bg-green-600" : result.confidence >= 70 ? "bg-yellow-500" : "bg-red-500"}`}
                  style={{ width: `${Math.min(result.confidence, 100)}%` }}
                />
              </div>
              <div className="flex justify-between text-xs mt-1 text-muted-foreground">
                <span>0%</span>
                <span>70% (threshold)</span>
                <span>100%</span>
              </div>
            </div>
          </div>

          {result.needs_confirmation && (
            <Alert variant="destructive" className="mt-4">
              <AlertCircle className="h-4 w-4" />
              <span>
                Industry detection confidence is below 70%. Please confirm the correct industry
                to generate a sector-specific dashboard.
              </span>
            </Alert>
          )}
        </CardContent>
      </Card>

      {result.detected_entities.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Detected Business Entities</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {result.detected_entities.map((entity) => (
                <Badge key={entity} variant="default" className="capitalize">
                  {entity.replace(/_/g, " ")}
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {result.alternative_candidates.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Alternative Industry Candidates</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {result.alternative_candidates.map((alt) => (
                <div key={alt.industry} className="flex items-center justify-between">
                  <span className="capitalize">{alt.industry}</span>
                  <Badge variant="secondary">{alt.votes.toFixed(1)} votes</Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
