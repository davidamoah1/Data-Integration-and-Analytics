"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Skeleton } from "@/components/ui/Skeleton";
import { TrendingUp, TrendingDown, AlertTriangle, Info, Sparkles, BarChart3 } from "lucide-react";
import { workflowService } from "@/services/workflow/workflowService";
import type { InsightsResult } from "@/types/workflow";

interface Props {
  workflowId: string;
}

const SEVERITY_CONFIG: Record<string, { icon: typeof Info; color: string; bg: string }> = {
  critical: { icon: AlertTriangle, color: "text-red-600", bg: "bg-red-50" },
  warning: { icon: AlertTriangle, color: "text-yellow-600", bg: "bg-yellow-50" },
  positive: { icon: TrendingUp, color: "text-green-600", bg: "bg-green-50" },
  info: { icon: Info, color: "text-blue-600", bg: "bg-blue-50" },
};

const TYPE_ICONS: Record<string, typeof Info> = {
  anomaly: AlertTriangle,
  trend: TrendingUp,
  correlation: BarChart3,
  dominance: Info,
  quality: AlertTriangle,
  distribution: BarChart3,
  comparison: Info,
};

export function InsightCards({ workflowId }: Props) {
  const [data, setData] = useState<InsightsResult | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    workflowService.getInsights(workflowId).then((d) => {
      setData(d);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, [workflowId]);

  if (loading) return <Skeleton className="h-96" />;
  if (!data) return <p className="text-muted-foreground">Insights not available</p>;

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Sparkles className="h-5 w-5" />
            Executive Summary
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm">{data.executive_summary}</p>
          <p className="text-sm text-muted-foreground mt-2">
            {data.total_insights} insight{data.total_insights !== 1 ? "s" : ""} generated
          </p>
        </CardContent>
      </Card>

      <div className="grid gap-4 md:grid-cols-2">
        {data.insights.map((insight, i) => {
          const config = SEVERITY_CONFIG[insight.severity] || SEVERITY_CONFIG.info;
          const Icon = TYPE_ICONS[insight.type] || config.icon;
          const SeverityIcon = config.icon;

          return (
            <Card key={i}>
              <CardContent className="pt-6">
                <div className="flex items-start gap-3">
                  <div className={`flex h-10 w-10 items-center justify-center rounded-lg ${config.bg}`}>
                    <Icon className={`h-5 w-5 ${config.color}`} />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <Badge variant="outline" className="capitalize text-xs">
                        {insight.type}
                      </Badge>
                      <SeverityIcon className={`h-3 w-3 ${config.color}`} />
                    </div>
                    <p className="font-medium">{insight.title}</p>
                    <p className="text-sm text-muted-foreground mt-1">{insight.description}</p>
                    {insight.recommendation && (
                      <p className="text-sm mt-2 flex items-start gap-1">
                        <TrendingUp className="h-3 w-3 text-green-600 mt-0.5 flex-shrink-0" />
                        <span><span className="font-medium">Action:</span> {insight.recommendation}</span>
                      </p>
                    )}
                    {insight.value !== null && insight.metric && (
                      <p className="text-xs text-muted-foreground mt-1">
                        Metric: {insight.metric} = {insight.value.toFixed(2)}
                      </p>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
