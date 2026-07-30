'use client';

import { Reveal } from '@/components/landing/Reveal';

const templates = [
  { name: 'Hospital Executive Dashboard', industry: 'Healthcare', icon: 'M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0016.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 002 8.5c0 2.29 1.51 4.04 3 5.5l7 7z', color: 'bg-emerald-100 text-emerald-600' },
  { name: 'Research Analysis', industry: 'Research', icon: 'M9 12l2 2 4-4M21 12a9 9 0 11-18 0 9 9 0 0118 0z', color: 'bg-violet-100 text-violet-600' },
  { name: 'Sales Performance', industry: 'Business', icon: 'M3 3v18h18M7 14l4-4 4 4 5-5', color: 'bg-blue-100 text-blue-600' },
  { name: 'Education Performance', industry: 'Education', icon: 'M22 10v6M2 10l10-5 10 5-10 5z', color: 'bg-amber-100 text-amber-600' },
  { name: 'Inventory Management', industry: 'Retail', icon: 'M3 9l1-5h16l1 5M4 9v11h16V9', color: 'bg-cyan-100 text-cyan-600' },
  { name: 'Laboratory Results', industry: 'Healthcare', icon: 'M9 2v6M15 2v6M9 8h6M10 14l2 2 4-4', color: 'bg-rose-100 text-rose-600' },
  { name: 'Financial Overview', industry: 'Banking', icon: 'M3 10h18M5 6h14a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2V8a2 2 0 012-2z', color: 'bg-indigo-100 text-indigo-600' },
  { name: 'Government Population Analysis', industry: 'Government', icon: 'M3 21h18M3 10h18M5 6l7-3 7 3', color: 'bg-slate-100 text-slate-600' },
];

export function TemplateLibrary() {
  return (
    <section className="bg-slate-50/50 py-24 lg:py-32">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <Reveal className="mx-auto max-w-2xl text-center">
          <p className="text-sm font-semibold uppercase tracking-wider text-blue-600">Template Library</p>
          <h2 className="mt-3 text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
            Start from a template, not a blank page
          </h2>
          <p className="mt-4 text-lg text-slate-600">
            Pre-built templates for common analytics workflows across industries.
          </p>
        </Reveal>

        <div className="mt-16 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {templates.map((tpl, i) => (
            <Reveal key={tpl.name} delay={i * 80}>
              <div className="card-hover group h-full overflow-hidden rounded-2xl border border-slate-200 bg-white">
                {/* Preview area */}
                <div className="relative h-32 overflow-hidden bg-slate-50">
                  <div className="absolute inset-0 bg-dot-pattern opacity-30" />
                  <div className="absolute inset-0 flex items-center justify-center">
                    <div className={`flex h-12 w-12 items-center justify-center rounded-xl ${tpl.color}`}>
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-6 w-6">
                        <path d={tpl.icon} />
                      </svg>
                    </div>
                  </div>
                  {/* Mini chart preview */}
                  <div className="absolute bottom-0 left-0 right-0 flex h-12 items-end gap-1 px-4 pb-2">
                    {[40, 60, 45, 70, 55, 80].map((h, j) => (
                      <div key={j} className="flex-1 rounded-t bg-slate-200 group-hover:bg-blue-200 transition-colors" style={{ height: `${h}%` }} />
                    ))}
                  </div>
                </div>
                {/* Content */}
                <div className="p-4">
                  <span className="inline-block rounded-md bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-500">{tpl.industry}</span>
                  <h3 className="mt-2 text-sm font-semibold text-slate-900">{tpl.name}</h3>
                </div>
              </div>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}
