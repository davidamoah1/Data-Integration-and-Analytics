'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { ArrowRight, Check } from 'lucide-react';

const capabilities = [
  'Upload CSV, Excel, PDF, or documents',
  'Automatic field extraction & classification',
  'Visualizations chosen based on your data',
  'Reports and presentations in one click',
];

export function Hero() {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  return (
    <section className="relative overflow-hidden pt-32 pb-20 sm:pt-36 lg:pt-40 lg:pb-28">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="grid items-center gap-12 lg:grid-cols-2 lg:gap-16">
          {/* Left: Content */}
          <div className={mounted ? 'animate-fade-in-up' : 'opacity-0'}>
            <h1 className="text-4xl font-bold tracking-tight text-foreground sm:text-5xl lg:text-6xl">
              From raw data to decisions,
              <br />
              <span className="text-primary">in one platform.</span>
            </h1>

            <p className="mt-6 max-w-xl text-lg leading-relaxed text-muted-foreground">
              Upload your data or documents. DataFlow automatically extracts, classifies, analyzes, and visualizes them — then generates reports and presentations you can share.
            </p>

            {/* Capability list */}
            <ul className="mt-8 space-y-3">
              {capabilities.map((cap) => (
                <li key={cap} className="flex items-center gap-3 text-sm text-muted-foreground">
                  <Check className="h-4 w-4 shrink-0 text-primary" />
                  {cap}
                </li>
              ))}
            </ul>

            {/* CTAs */}
            <div className="mt-10 flex flex-col gap-3 sm:flex-row">
              <Link
                href="/signup"
                className="inline-flex h-11 items-center justify-center rounded-md bg-primary px-6 text-sm font-semibold text-primary-foreground transition-colors hover:bg-primary/90"
              >
                Start Free
                <ArrowRight className="ml-2 h-4 w-4" />
              </Link>
              <Link
                href="/demo"
                className="inline-flex h-11 items-center justify-center rounded-md border border-border bg-background px-6 text-sm font-semibold text-foreground transition-colors hover:bg-accent"
              >
                Book a Demo
              </Link>
            </div>

            <p className="mt-6 text-sm text-muted-foreground">
              No credit card required · Free 14-day trial
            </p>
          </div>

          {/* Right: Product UI preview */}
          <div className={mounted ? 'animate-fade-in-up' : 'opacity-0'}>
            <div className="overflow-hidden rounded-lg border border-border bg-card shadow-sm">
              {/* Browser bar */}
              <div className="flex items-center gap-2 border-b border-border bg-muted/50 px-4 py-2.5">
                <div className="flex gap-1.5">
                  <div className="h-2.5 w-2.5 rounded-full bg-muted-foreground/30" />
                  <div className="h-2.5 w-2.5 rounded-full bg-muted-foreground/30" />
                  <div className="h-2.5 w-2.5 rounded-full bg-muted-foreground/30" />
                </div>
                <div className="ml-3 flex-1 rounded-md bg-background px-3 py-1 text-xs text-muted-foreground border border-border">
                  app.dataflow.io/dashboard
                </div>
              </div>

              {/* Dashboard preview */}
              <div className="p-5">
                {/* Page title */}
                <div className="mb-4">
                  <p className="text-sm font-semibold text-foreground">Dashboard Overview</p>
                  <p className="text-xs text-muted-foreground">Your data at a glance</p>
                </div>

                {/* Summary metrics */}
                <div className="grid grid-cols-3 gap-3">
                  <div className="rounded-md border border-border bg-background p-3">
                    <p className="text-xs text-muted-foreground">Datasets</p>
                    <p className="mt-1 text-xl font-bold text-foreground">12</p>
                  </div>
                  <div className="rounded-md border border-border bg-background p-3">
                    <p className="text-xs text-muted-foreground">Documents</p>
                    <p className="mt-1 text-xl font-bold text-foreground">48</p>
                  </div>
                  <div className="rounded-md border border-border bg-background p-3">
                    <p className="text-xs text-muted-foreground">Reports</p>
                    <p className="mt-1 text-xl font-bold text-foreground">7</p>
                  </div>
                </div>

                {/* Data table preview */}
                <div className="mt-4 rounded-md border border-border">
                  <div className="border-b border-border bg-muted/30 px-3 py-2">
                    <p className="text-xs font-medium text-foreground">Recent Datasets</p>
                  </div>
                  <div className="divide-y divide-border">
                    {[
                      { name: 'Q4 Sales Data', type: 'CSV', rows: '12,847' },
                      { name: 'Patient Records', type: 'PDF', rows: '320' },
                      { name: 'Survey Results', type: 'Excel', rows: '1,204' },
                    ].map((row) => (
                      <div key={row.name} className="flex items-center justify-between px-3 py-2.5 text-xs">
                        <div className="flex items-center gap-2">
                          <span className="font-medium text-foreground">{row.name}</span>
                          <span className="rounded bg-muted px-1.5 py-0.5 text-[10px] text-muted-foreground">{row.type}</span>
                        </div>
                        <span className="text-muted-foreground">{row.rows} rows</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Workflow steps */}
                <div className="mt-4 flex items-center gap-2 rounded-md border border-border bg-muted/20 px-3 py-2.5">
                  <span className="text-xs font-medium text-foreground">Upload</span>
                  <div className="h-px flex-1 bg-border" />
                  <span className="text-xs font-medium text-foreground">Analyze</span>
                  <div className="h-px flex-1 bg-border" />
                  <span className="text-xs font-medium text-foreground">Report</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
