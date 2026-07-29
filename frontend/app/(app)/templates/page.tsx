'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { TEMPLATES } from '@/lib/workflows';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { ArrowRight, Search, Check } from 'lucide-react';
import { Input } from '@/components/ui/Input';
import { toast } from '@/components/ui/Toaster';

export default function TemplatesPage() {
  const router = useRouter();
  const [search, setSearch] = useState('');
  const [selectedIndustry, setSelectedIndustry] = useState('All');

  const industries = ['All', ...Array.from(new Set(TEMPLATES.map((t) => t.industry)))];

  const filtered = TEMPLATES.filter((t) => {
    const matchesSearch = t.name.toLowerCase().includes(search.toLowerCase()) || t.description.toLowerCase().includes(search.toLowerCase());
    const matchesIndustry = selectedIndustry === 'All' || t.industry === selectedIndustry;
    return matchesSearch && matchesIndustry;
  });

  const handleUseTemplate = (templateId: string) => {
    toast.success('Template applied! Redirecting to dashboard builder...');
    router.push('/analytics');
  };

  return (
    <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold">Template Library</h1>
          <p className="mt-1 text-muted-foreground">Start from a pre-built dashboard template tailored to your industry.</p>
        </div>

        {/* Search & Filter */}
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search templates..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-10"
            />
          </div>
          <div className="flex gap-2 overflow-x-auto">
            {industries.map((industry) => (
              <button
                key={industry}
                onClick={() => setSelectedIndustry(industry)}
                className={`whitespace-nowrap rounded-lg px-3 py-1.5 text-sm font-medium transition-colors ${
                  selectedIndustry === industry
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-muted text-muted-foreground hover:bg-muted/80'
                }`}
              >
                {industry}
              </button>
            ))}
          </div>
        </div>

        {/* Templates Grid */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {filtered.map((template) => {
            const Icon = template.icon;
            return (
              <Card key={template.id} className="flex flex-col transition-all hover:shadow-lg">
                <CardHeader>
                  <div className="flex items-center gap-3">
                    <div className={`flex h-10 w-10 items-center justify-center rounded-lg ${template.color} text-white`}>
                      <Icon className="h-5 w-5" />
                    </div>
                    <div>
                      <CardTitle className="text-base">{template.name}</CardTitle>
                      <p className="text-xs text-muted-foreground">{template.industry}</p>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="flex-1 space-y-4">
                  <p className="text-sm text-muted-foreground">{template.description}</p>

                  <div>
                    <p className="mb-1 text-xs font-semibold uppercase text-muted-foreground">KPIs</p>
                    <div className="flex flex-wrap gap-1">
                      {template.kpis.slice(0, 4).map((kpi) => (
                        <span key={kpi} className="rounded-md bg-muted px-2 py-0.5 text-xs">{kpi}</span>
                      ))}
                      {template.kpis.length > 4 && (
                        <span className="rounded-md bg-muted px-2 py-0.5 text-xs">+{template.kpis.length - 4} more</span>
                      )}
                    </div>
                  </div>

                  <div>
                    <p className="mb-1 text-xs font-semibold uppercase text-muted-foreground">Charts</p>
                    <div className="flex flex-wrap gap-1">
                      {template.charts.slice(0, 3).map((chart) => (
                        <span key={chart} className="rounded-md bg-muted px-2 py-0.5 text-xs">{chart}</span>
                      ))}
                      {template.charts.length > 3 && (
                        <span className="rounded-md bg-muted px-2 py-0.5 text-xs">+{template.charts.length - 3} more</span>
                      )}
                    </div>
                  </div>

                  <Button
                    onClick={() => handleUseTemplate(template.id)}
                    className="w-full gap-2"
                    variant="outline"
                  >
                    Use Template <ArrowRight size={16} />
                  </Button>
                </CardContent>
              </Card>
            );
          })}
        </div>

        {filtered.length === 0 && (
          <div className="flex flex-col items-center justify-center py-16 text-center">
            <Search className="mb-4 h-12 w-12 text-muted-foreground" />
            <h3 className="text-lg font-semibold">No templates found</h3>
            <p className="mt-1 text-sm text-muted-foreground">Try a different search or industry filter.</p>
          </div>
        )}
    </div>
  );
}
