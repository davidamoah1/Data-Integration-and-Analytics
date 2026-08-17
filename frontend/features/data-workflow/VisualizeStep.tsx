'use client';

import { LayoutDashboard, Eye, Plus, Save } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import type { DashboardRecommendation } from '@/types/workflow';

interface Props {
  dashboard: DashboardRecommendation | null;
  onSaveDashboard: () => void;
  onContinue: () => void;
  isSaving: boolean;
  savedDashboardId: number | null;
}

export function VisualizeStep({ dashboard, onSaveDashboard, onContinue, isSaving, savedDashboardId }: Props) {
  if (!dashboard) {
    return (
      <Card>
        <CardContent className="py-12 text-center text-muted-foreground">
          Generating visualization recommendations...
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Dashboard Recommendation Header */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="rounded-full bg-primary/10 p-3">
                <LayoutDashboard className="h-5 w-5 text-primary" />
              </div>
              <div>
                <p className="font-medium">Recommended Dashboard</p>
                <p className="text-sm text-muted-foreground">
                  Based on your data structure and sector ({dashboard.industry})
                </p>
              </div>
            </div>
            {!savedDashboardId && (
              <Button onClick={onSaveDashboard} disabled={isSaving}>
                <Save className="mr-2 h-4 w-4" />
                {isSaving ? 'Saving...' : 'Save Dashboard'}
              </Button>
            )}
            {savedDashboardId && (
              <Badge variant="default" className="bg-green-600">Saved</Badge>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Recommended Charts */}
      {dashboard.recommended_charts && dashboard.recommended_charts.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Recommended Visualizations</CardTitle>
            <CardDescription>
              Charts selected based on your data types and relationships
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {dashboard.recommended_charts.map((chart, i) => (
                <div
                  key={i}
                  className="rounded-lg border p-4 hover:border-primary/50 transition-colors"
                >
                  <div className="flex items-center gap-2 mb-2">
                    <Badge variant="outline" className="text-xs capitalize">
                      {chart.type}
                    </Badge>
                  </div>
                  <p className="font-medium text-sm">{chart.title}</p>
                  {chart.reasoning && (
                    <p className="text-xs text-muted-foreground mt-1">{chart.reasoning}</p>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Available Measures & Dimensions */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {dashboard.available_measures && dashboard.available_measures.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Measures (Numeric)</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                {dashboard.available_measures.map((m, i) => (
                  <Badge key={i} variant="outline">
                    {m.display || m.column}
                  </Badge>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
        {dashboard.available_dimensions && dashboard.available_dimensions.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Dimensions (Categories)</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                {dashboard.available_dimensions.map((d, i) => (
                  <Badge key={i} variant="secondary">
                    {d.display || d.column}
                  </Badge>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Time & Geo Fields */}
      {((dashboard.time_fields && dashboard.time_fields.length > 0) ||
        (dashboard.geo_fields && dashboard.geo_fields.length > 0)) && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {dashboard.time_fields && dashboard.time_fields.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-sm">Time Fields</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-2">
                  {dashboard.time_fields.map((t, i) => (
                    <Badge key={i} variant="outline">{t.display || t.column}</Badge>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
          {dashboard.geo_fields && dashboard.geo_fields.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-sm">Geographic Fields</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-2">
                  {dashboard.geo_fields.map((g, i) => (
                    <Badge key={i} variant="outline">{g.display || g.column}</Badge>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      )}

      <Button onClick={onContinue} size="lg" className="w-full">
        Continue to Report
      </Button>
    </div>
  );
}
