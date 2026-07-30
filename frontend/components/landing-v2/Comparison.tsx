'use client';

import { Reveal } from '@/components/landing/Reveal';

const traditionalSteps = [
  { label: 'Collect', detail: 'Manual data entry from multiple sources' },
  { label: 'Clean', detail: 'Hours of spreadsheet formatting' },
  { label: 'Analyze', detail: 'Repeat analysis in different tools' },
  { label: 'Report', detail: 'Manually build charts and tables' },
  { label: 'Present', detail: 'Copy-paste into slides and documents' },
];

export function Comparison() {
  return (
    <section className="bg-slate-50/50 py-24 lg:py-32">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <Reveal className="mx-auto max-w-2xl text-center">
          <p className="text-sm font-semibold uppercase tracking-wider text-blue-600">Workflow Comparison</p>
          <h2 className="mt-3 text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
            One guided workflow vs. five disconnected steps
          </h2>
        </Reveal>

        <div className="mt-16 grid gap-6 lg:grid-cols-2">
          {/* Traditional */}
          <Reveal>
            <div className="h-full rounded-2xl border border-slate-200 bg-white p-8">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-red-50 text-red-500">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-5 w-5">
                    <path d="M18 6L6 18M6 6l12 12" />
                  </svg>
                </div>
                <h3 className="text-lg font-semibold text-slate-900">Traditional Process</h3>
              </div>
              <div className="mt-6 space-y-4">
                {traditionalSteps.map((step, i) => (
                  <div key={step.label} className="flex items-start gap-3">
                    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-slate-100 text-sm font-bold text-slate-400">
                      {i + 1}
                    </div>
                    <div>
                      <p className="text-sm font-semibold text-slate-700">{step.label}</p>
                      <p className="text-xs text-slate-500">{step.detail}</p>
                    </div>
                    {i < traditionalSteps.length - 1 && (
                      <svg className="mt-2 h-4 w-4 text-slate-300" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M12 5v14M19 12l-7 7-7-7" />
                      </svg>
                    )}
                  </div>
                ))}
              </div>
              <div className="mt-6 rounded-xl bg-red-50 p-4">
                <p className="text-sm font-medium text-red-700">Result: Slow, inconsistent, and effort-intensive</p>
              </div>
            </div>
          </Reveal>

          {/* DataFlow */}
          <Reveal delay={200}>
            <div className="relative h-full overflow-hidden rounded-2xl bg-gradient-to-br from-slate-900 to-slate-800 p-8 text-white">
              <div className="absolute -top-20 -right-20 h-60 w-60 rounded-full bg-blue-500/20 blur-3xl" />
              <div className="relative">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-white/10 text-blue-400">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-5 w-5">
                      <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" />
                    </svg>
                  </div>
                  <h3 className="text-lg font-semibold">DataFlow Platform</h3>
                </div>

                <div className="mt-8 rounded-xl bg-white/5 p-6">
                  <p className="text-sm font-semibold text-blue-300">One guided workflow</p>
                  <div className="mt-4 flex flex-wrap items-center gap-2">
                    {['Upload', 'Prepare', 'Validate', 'Analyze', 'Visualize', 'Present', 'Decide'].map((step, i) => (
                      <div key={step} className="flex items-center gap-2">
                        <span className="rounded-lg bg-white/10 px-3 py-1.5 text-xs font-medium text-white">{step}</span>
                        {i < 6 && <svg className="h-3 w-3 text-blue-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M5 12h14M13 5l7 7-7 7" /></svg>}
                      </div>
                    ))}
                  </div>
                </div>

                <div className="mt-6 space-y-3">
                  <div className="flex items-center gap-3">
                    <svg className="h-5 w-5 text-emerald-400 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M22 11.08V12a10 10 0 11-5.93-9.14M22 4L12 14.01l-3-3" /></svg>
                    <span className="text-sm text-slate-300">Reduced effort with automation at every step</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <svg className="h-5 w-5 text-emerald-400 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M22 11.08V12a10 10 0 11-5.93-9.14M22 4L12 14.01l-3-3" /></svg>
                    <span className="text-sm text-slate-300">Consistent quality with validated pipelines</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <svg className="h-5 w-5 text-emerald-400 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M22 11.08V12a10 10 0 11-5.93-9.14M22 4L12 14.01l-3-3" /></svg>
                    <span className="text-sm text-slate-300">Faster decisions with presentation-ready output</span>
                  </div>
                </div>

                <div className="mt-6 rounded-xl bg-emerald-500/10 p-4 border border-emerald-500/20">
                  <p className="text-sm font-medium text-emerald-300">Result: From raw data to decisions in one continuous flow</p>
                </div>
              </div>
            </div>
          </Reveal>
        </div>
      </div>
    </section>
  );
}
