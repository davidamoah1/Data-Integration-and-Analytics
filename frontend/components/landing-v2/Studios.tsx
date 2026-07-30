'use client';

import { useState } from 'react';
import { Reveal } from '@/components/landing/Reveal';

const studios = [
  {
    name: 'Analytics Studio',
    purpose: 'Interactive dashboards and exploratory data analysis',
    capabilities: ['Drag-and-drop dashboards', 'Real-time KPIs', 'Custom chart builder', 'Shareable links'],
    users: 'Data analysts, business analysts, executives',
    value: 'Turn raw data into interactive visual insights in minutes, not days.',
    icon: 'M3 3v18h18M7 14l4-4 4 4 5-5',
    color: 'from-blue-500 to-blue-600',
  },
  {
    name: 'Research Studio',
    purpose: 'Hypothesis-driven research and statistical analysis',
    capabilities: ['Hypothesis testing', 'Statistical models', 'Research project management', 'Publication-ready output'],
    users: 'Researchers, statisticians, academics',
    value: 'Design experiments, run tests, and produce publication-ready findings.',
    icon: 'M9 12l2 2 4-4M21 12a9 9 0 11-18 0 9 9 0 0118 0z',
    color: 'from-violet-500 to-violet-600',
  },
  {
    name: 'Healthcare Studio',
    purpose: 'Patient outcomes and clinical performance tracking',
    capabilities: ['Patient analytics', 'Treatment tracking', 'Compliance reporting', 'Outcome measurement'],
    users: 'Hospital administrators, clinicians, health officers',
    value: 'Improve patient care with data-driven clinical decisions.',
    icon: 'M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0016.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 002 8.5c0 2.29 1.51 4.04 3 5.5l7 7z',
    color: 'from-emerald-500 to-emerald-600',
  },
  {
    name: 'Education Studio',
    purpose: 'Student performance and institutional effectiveness',
    capabilities: ['Student tracking', 'Course analytics', 'At-risk identification', 'Institutional reporting'],
    users: 'Educators, administrators, curriculum designers',
    value: 'Identify at-risk students early and measure what works.',
    icon: 'M22 10v6M2 10l10-5 10 5-10 5z',
    color: 'from-amber-500 to-amber-600',
  },
  {
    name: 'Business Intelligence Studio',
    purpose: 'Sales, finance, and operations dashboards',
    capabilities: ['Sales dashboards', 'Financial analysis', 'Inventory tracking', 'Forecasting'],
    users: 'Business leaders, managers, analysts',
    value: 'Monitor every aspect of your business in real time.',
    icon: 'M3 3v18h18M7 14l4-4 4 4 5-5',
    color: 'from-cyan-500 to-cyan-600',
  },
  {
    name: 'Data Integration Studio',
    purpose: 'Connect, transform, and pipeline data from any source',
    capabilities: ['20+ connectors', 'ETL pipelines', 'Real-time streaming', 'Data transformation'],
    users: 'Data engineers, IT teams, developers',
    value: 'Unify scattered data sources into one clean, reliable pipeline.',
    icon: 'M21 12a9 9 0 11-18 0 9 9 0 0118 0z M3 12h6M15 12h6',
    color: 'from-rose-500 to-rose-600',
  },
  {
    name: 'Report Studio',
    purpose: 'Presentation-ready reports in multiple formats',
    capabilities: ['Executive reports', 'PowerPoint export', 'PDF generation', 'Word documents'],
    users: 'Executives, managers, consultants',
    value: 'Generate presentation-ready reports with one click.',
    icon: 'M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z M14 2v6h6',
    color: 'from-indigo-500 to-indigo-600',
  },
  {
    name: 'Automation Studio',
    purpose: 'Schedule and orchestrate analytics workflows',
    capabilities: ['Workflow builder', 'Scheduled pipelines', 'Trigger-based automation', 'Alert notifications'],
    users: 'Operations teams, data engineers, analysts',
    value: 'Automate repetitive data work and focus on decisions.',
    icon: 'M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4',
    color: 'from-fuchsia-500 to-fuchsia-600',
  },
];

export function Studios() {
  const [selected, setSelected] = useState<number | null>(null);

  return (
    <section className="py-24 lg:py-32">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <Reveal className="mx-auto max-w-2xl text-center">
          <p className="text-sm font-semibold uppercase tracking-wider text-blue-600">Studios</p>
          <h2 className="mt-3 text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
            Dedicated workspaces for every workflow
          </h2>
          <p className="mt-4 text-lg text-slate-600">
            Each studio is purpose-built for specific tasks and users, yet connected within one platform.
          </p>
        </Reveal>

        <div className="mt-16 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {studios.map((studio, i) => (
            <Reveal key={studio.name} delay={i * 80}>
              <button
                onClick={() => setSelected(selected === i ? null : i)}
                className="card-hover group h-full w-full rounded-2xl border border-slate-200 bg-white p-6 text-left"
              >
                <div className={`flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br ${studio.color} text-white shadow-lg`}>
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-6 w-6">
                    <path d={studio.icon} />
                  </svg>
                </div>
                <h3 className="mt-4 text-base font-semibold text-slate-900">{studio.name}</h3>
                <p className="mt-2 text-sm leading-relaxed text-slate-600">{studio.purpose}</p>
                <div className="mt-4 flex items-center gap-1 text-sm font-medium text-blue-600 opacity-0 transition-opacity group-hover:opacity-100">
                  Learn more
                  <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M5 12h14M13 5l7 7-7 7" />
                  </svg>
                </div>
              </button>
            </Reveal>
          ))}
        </div>

        {/* Detail panel */}
        {selected !== null && (
          <Reveal className="mt-6">
            <div key={selected} className="animate-tab-fade overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-xl">
              <div className="grid lg:grid-cols-3">
                <div className={`bg-gradient-to-br ${studios[selected].color} p-8 text-white`}>
                  <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-white/20">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-7 w-7">
                      <path d={studios[selected].icon} />
                    </svg>
                  </div>
                  <h3 className="mt-4 text-2xl font-bold">{studios[selected].name}</h3>
                  <p className="mt-2 text-sm text-white/80">{studios[selected].purpose}</p>
                </div>

                <div className="p-8 lg:col-span-2">
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">Capabilities</p>
                    <div className="mt-3 grid grid-cols-2 gap-2">
                      {studios[selected].capabilities.map((cap) => (
                        <div key={cap} className="flex items-center gap-2 text-sm text-slate-700">
                          <svg className="h-4 w-4 text-emerald-500 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <path d="M22 11.08V12a10 10 0 11-5.93-9.14M22 4L12 14.01l-3-3" />
                          </svg>
                          {cap}
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="mt-6 grid gap-4 sm:grid-cols-2">
                    <div className="rounded-xl bg-slate-50 p-4">
                      <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">Typical Users</p>
                      <p className="mt-2 text-sm text-slate-700">{studios[selected].users}</p>
                    </div>
                    <div className="rounded-xl bg-slate-50 p-4">
                      <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">Business Value</p>
                      <p className="mt-2 text-sm text-slate-700">{studios[selected].value}</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </Reveal>
        )}
      </div>
    </section>
  );
}
