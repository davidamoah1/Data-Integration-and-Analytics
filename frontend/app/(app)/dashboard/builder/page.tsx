'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/stores/authStore';
import { RouteGuard } from '@/components/auth/RouteGuard';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Input } from '@/components/ui/Input';
import { WidgetRenderer } from '@/components/widgets/WidgetRenderer';
import { dashboardCompositionService } from '@/services/dashboard/dashboardCompositionService';
import type { ComposedDashboard, ComposedWidget, DashboardTemplate } from '@/types';
import {
  LayoutDashboard, Sparkles, Plus, Trash2, Building2,
  GraduationCap, Heart, FlaskConical, Globe2, Search,
} from 'lucide-react';

const INDUSTRY_ICONS: Record<string, typeof Heart> = {
  healthcare: Heart,
  education: GraduationCap,
  business: Building2,
  research: FlaskConical,
  generic: Globe2,
};

export default function DashboardBuilderPage() {
  return (
    <RouteGuard permission="dashboard.manage">
      <DashboardBuilderContent />
    </RouteGuard>
  );
}

function DashboardBuilderContent() {
  const router = useRouter();
  const { user } = useAuthStore();
  const [templates, setTemplates] = useState<DashboardTemplate[]>([]);
  const [availableWidgets, setAvailableWidgets] = useState<ComposedWidget[]>([]);
  const [composedDashboard, setComposedDashboard] = useState<ComposedDashboard | null>(null);
  const [selectedIndustry, setSelectedIndustry] = useState(user?.industry || 'generic');
  const [dashboardName, setDashboardName] = useState('');
  const [dashboardDesc, setDashboardDesc] = useState('');
  const [widgetFilter, setWidgetFilter] = useState('');
  const [loading, setLoading] = useState(true);
  const [composing, setComposing] = useState(false);

  useEffect(() => {
    async function load() {
      try {
        const [tmpls, widgets] = await Promise.all([
          dashboardCompositionService.listTemplates(),
          dashboardCompositionService.listWidgetsByIndustry(selectedIndustry),
        ]);
        setTemplates(tmpls);
        setAvailableWidgets(widgets);
      } catch {
        // ignore
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [selectedIndustry]);

  async function composeFromTemplate(template: DashboardTemplate) {
    setComposing(true);
    try {
      const result = await dashboardCompositionService.composeDashboard({
        name: template.name,
        industry: template.industry,
        widget_keys: template.widget_keys,
        description: template.description,
      });
      setComposedDashboard(result);
      setDashboardName(result.name);
      setDashboardDesc(result.description || '');
    } catch {
      // ignore
    } finally {
      setComposing(false);
    }
  }

  async function composeCustom() {
    setComposing(true);
    try {
      const result = await dashboardCompositionService.composeDashboard({
        name: dashboardName || 'Custom Dashboard',
        industry: selectedIndustry,
        description: dashboardDesc,
      });
      setComposedDashboard(result);
    } catch {
      // ignore
    } finally {
      setComposing(false);
    }
  }

  async function addWidget(widgetKey: string) {
    if (!composedDashboard) return;
    try {
      const updated = await dashboardCompositionService.addWidget(
        composedDashboard.dashboard_id,
        widgetKey,
      );
      setComposedDashboard(updated);
    } catch {
      // ignore
    }
  }

  async function removeWidget(widgetKey: string) {
    if (!composedDashboard) return;
    try {
      const updated = await dashboardCompositionService.removeWidget(
        composedDashboard.dashboard_id,
        widgetKey,
      );
      setComposedDashboard(updated);
    } catch {
      // ignore
    }
  }

  const filteredWidgets = availableWidgets.filter((w) =>
    w.title.toLowerCase().includes(widgetFilter.toLowerCase()) ||
    w.key.toLowerCase().includes(widgetFilter.toLowerCase()),
  );

  const groupedWidgets = filteredWidgets.reduce<Record<string, ComposedWidget[]>>((acc, w) => {
    if (!acc[w.group]) acc[w.group] = [];
    acc[w.group].push(w);
    return acc;
  }, {});

  if (loading) {
    return <div className="animate-pulse text-muted-foreground">Loading dashboard builder...</div>;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="flex items-center gap-2 text-2xl font-bold">
          <LayoutDashboard className="h-6 w-6" />
          Dashboard Builder
        </h1>
        <p className="mt-1 text-muted-foreground">
          Compose dashboards from reusable widgets, adapted by industry.
        </p>
      </div>

      {/* Industry Selector */}
      <div className="flex flex-wrap gap-2">
        {Object.entries(INDUSTRY_ICONS).map(([industry, Icon]) => (
          <button
            key={industry}
            onClick={() => setSelectedIndustry(industry)}
            className={`flex items-center gap-2 rounded-lg border px-4 py-2 text-sm font-medium capitalize transition-colors ${
              selectedIndustry === industry
                ? 'border-primary bg-primary text-primary-foreground'
                : 'border-border bg-background hover:bg-accent'
            }`}
          >
            <Icon className="h-4 w-4" />
            {industry}
          </button>
        ))}
      </div>

      {/* Templates */}
      {!composedDashboard && (
        <div>
          <h2 className="mb-4 text-lg font-semibold">Industry Templates</h2>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {templates
              .filter((t) => t.industry === selectedIndustry || selectedIndustry === 'generic')
              .map((template) => {
                const Icon = INDUSTRY_ICONS[template.industry] || Globe2;
                return (
                  <Card key={template.industry} className="cursor-pointer hover:border-primary" >
                    <CardContent
                      className="p-6"
                      onClick={() => !composing && composeFromTemplate(template)}
                    >
                      <div className="flex items-start justify-between">
                        <div>
                          <Icon className="mb-2 h-8 w-8 text-primary" />
                          <p className="font-medium">{template.name}</p>
                          <p className="mt-1 text-sm text-muted-foreground">
                            {template.description}
                          </p>
                          <Badge className="mt-2">{template.widget_count} widgets</Badge>
                        </div>
                        <Sparkles className="h-5 w-5 text-muted-foreground" />
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
          </div>
        </div>
      )}

      {/* Custom compose */}
      {!composedDashboard && (
        <Card>
          <CardHeader>
            <CardTitle>Compose Custom Dashboard</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <label className="text-sm font-medium">Dashboard Name</label>
                <Input
                  value={dashboardName}
                  onChange={(e) => setDashboardName(e.target.value)}
                  placeholder="My Custom Dashboard"
                  className="mt-1"
                />
              </div>
              <div>
                <label className="text-sm font-medium">Description</label>
                <Input
                  value={dashboardDesc}
                  onChange={(e) => setDashboardDesc(e.target.value)}
                  placeholder="Optional description"
                  className="mt-1"
                />
              </div>
            </div>
            <Button onClick={composeCustom} disabled={composing}>
              <Plus className="mr-2 h-4 w-4" />
              {composing ? 'Composing...' : 'Compose from All Industry Widgets'}
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Composed Dashboard Preview */}
      {composedDashboard && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-bold">{composedDashboard.name}</h2>
              <p className="text-sm text-muted-foreground">
                {composedDashboard.description} · {composedDashboard.widgets.length} widgets · Industry: {composedDashboard.industry}
              </p>
            </div>
            <Button
              variant="outline"
              onClick={() => setComposedDashboard(null)}
            >
              Start Over
            </Button>
          </div>

          {/* Widget groups */}
          {Object.entries(composedDashboard.layout).map(([group, widgetKeys]) => (
            <div key={group}>
              <div className="mb-3 flex items-center justify-between">
                <h3 className="text-lg font-semibold">{group}</h3>
                <Badge variant="secondary">{widgetKeys.length} widgets</Badge>
              </div>
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                {widgetKeys.map((key) => {
                  const widget = composedDashboard.widgets.find((w) => w.key === key);
                  if (!widget) return null;
                  return (
                    <div key={key} className="relative group">
                      <WidgetRenderer widget={widget} dashboardId={composedDashboard.dashboard_id} />
                      <button
                        onClick={() => removeWidget(key)}
                        className="absolute right-2 top-2 rounded-md bg-destructive/10 p-1 opacity-0 transition-opacity group-hover:opacity-100 hover:bg-destructive/20"
                      >
                        <Trash2 className="h-4 w-4 text-destructive" />
                      </button>
                    </div>
                  );
                })}
              </div>
            </div>
          ))}

          {/* Add widgets panel */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Plus className="h-5 w-5" />
                Add Widgets
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="relative mb-4 max-w-sm">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  placeholder="Search widgets..."
                  value={widgetFilter}
                  onChange={(e) => setWidgetFilter(e.target.value)}
                  className="pl-10"
                />
              </div>
              <div className="space-y-4">
                {Object.entries(groupedWidgets).map(([group, widgets]) => (
                  <div key={group}>
                    <p className="mb-2 text-sm font-medium text-muted-foreground">{group}</p>
                    <div className="flex flex-wrap gap-2">
                      {widgets.map((widget) => (
                        <button
                          key={widget.key}
                          onClick={() => addWidget(widget.key)}
                          className="flex items-center gap-2 rounded-lg border border-border bg-background px-3 py-2 text-sm hover:border-primary hover:bg-accent"
                        >
                          <Plus className="h-3 w-3" />
                          {widget.title}
                          <Badge variant="outline" className="ml-1 text-xs">
                            {widget.widget_type}
                          </Badge>
                        </button>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
