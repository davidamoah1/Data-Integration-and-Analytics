"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Alert } from "@/components/ui/Alert";
import { Skeleton } from "@/components/ui/Skeleton";
import { LayoutDashboard, Check, Settings, X, Lightbulb } from "lucide-react";
import { workflowService } from "@/services/workflow/workflowService";
import type { DashboardRecommendation } from "@/types/workflow";

interface Props {
  workflowId: string;
}

const CHART_ICONS: Record<string, string> = {
  line_chart: "📈",
  bar_chart: "📊",
  pie_chart: "🥧",
  geo_chart: "🗺️",
  kpi_card: "🔢",
};

export function DashboardPreview({ workflowId }: Props) {
  const [data, setData] = useState<DashboardRecommendation | null>(null);
  const [loading, setLoading] = useState(true);
  const [action, setAction] = useState<"accept" | "customize" | "reject" | null>(null);

  useEffect(() => {
    workflowService.getDashboard(workflowId).then((d) => {
      setData(d);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, [workflowId]);

  if (loading) return <Skeleton className="h-96" />;
  if (!data) return <p className="text-muted-foreground">Dashboard recommendations not available</p>;

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <LayoutDashboard className="h-5 w-5" />
            Dashboard Recommendation
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-4 mb-4">
            <div>
              <p className="text-2xl font-bold capitalize">{data.industry}</p>
              <p className="text-sm text-muted-foreground">
                {data.industry_confidence.toFixed(0)}% confidence
              </p>
            </div>
            {data.recommended ? (
              <Badge variant="default" className="bg-green-600">Recommended</Badge>
            ) : (
              <Badge variant="secondary">Not Recommended</Badge>
            )}
          </div>

          <div className="bg-muted/50 rounded-lg p-4 mb-4">
            <p className="text-sm flex items-start gap-2">
              <Lightbulb className="h-4 w-4 text-yellow-600 mt-0.5 flex-shrink-0" />
              <span>{data.reasoning}</span>
            </p>
          </div>

          {data.needs_confirmation && (
            <Alert variant="destructive" className="mb-4">
              <span>{data.confirmation_reason}</span>
            </Alert>
          )}

          <div className="flex gap-3">
            <Button
              size="sm"
              variant={action === "accept" ? "default" : "outline"}
              onClick={() => setAction("accept")}
            >
              <Check className="mr-1 h-4 w-4" /> Accept
            </Button>
            <Button
              size="sm"
              variant={action === "customize" ? "default" : "outline"}
              onClick={() => setAction("customize")}
            >
              <Settings className="mr-1 h-4 w-4" /> Customize
            </Button>
            <Button
              size="sm"
              variant={action === "reject" ? "destructive" : "outline"}
              onClick={() => setAction("reject")}
            >
              <X className="mr-1 h-4 w-4" /> Reject
            </Button>
          </div>

          {action === "accept" && (
            <Alert className="mt-3">
              <Check className="h-4 w-4" />
              <span>Dashboard accepted. You can access it from the Dashboards page.</span>
            </Alert>
          )}
          {action === "customize" && (
            <Alert className="mt-3">
              <Settings className="h-4 w-4" />
              <span>Customization panel will appear here. Select which charts and KPIs to include.</span>
            </Alert>
          )}
          {action === "reject" && (
            <Alert variant="destructive" className="mt-3">
              <X className="h-4 w-4" />
              <span>Recommendation rejected. You can build a dashboard manually from the Dashboards page.</span>
            </Alert>
          )}
        </CardContent>
      </Card>

      <div className="grid grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Available Measures</CardTitle>
          </CardHeader>
          <CardContent>
            {data.available_measures.length > 0 ? (
              <div className="space-y-1">
                {data.available_measures.map((m) => (
                  <div key={m.column} className="flex items-center justify-between text-sm">
                    <span>{m.display}</span>
                    <Badge variant="outline" className="text-xs">{m.column}</Badge>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">No measures detected</p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Available Dimensions</CardTitle>
          </CardHeader>
          <CardContent>
            {data.available_dimensions.length > 0 ? (
              <div className="space-y-1">
                {data.available_dimensions.map((d) => (
                  <div key={d.column} className="flex items-center justify-between text-sm">
                    <span>{d.display}</span>
                    <Badge variant="outline" className="text-xs">{d.column}</Badge>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">No dimensions detected</p>
            )}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Recommended Charts ({data.recommended_charts.length})</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-3 md:grid-cols-2">
            {data.recommended_charts.map((chart, i) => (
              <div key={i} className="border rounded-lg p-4">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-lg">{CHART_ICONS[chart.type] || "📊"}</span>
                  <span className="font-medium text-sm">{chart.title}</span>
                  <Badge variant="outline" className="text-xs capitalize ml-auto">
                    {chart.type.replace(/_/g, " ")}
                  </Badge>
                </div>
                <p className="text-xs text-muted-foreground">{chart.reasoning}</p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
