'use client';

import { useState, useEffect } from 'react';
import { Reveal } from '@/components/landing/Reveal';

const formats = [
  {
    name: 'Executive Report',
    icon: 'M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z M14 2v6h6',
    description: 'Formatted narrative report with insights, charts, and recommendations.',
    preview: 'report',
  },
  {
    name: 'Interactive Dashboard',
    icon: 'M3 3v18h18M7 14l4-4 4 4 5-5',
    description: 'Live, filterable dashboard with drill-down capabilities.',
    preview: 'dashboard',
  },
  {
    name: 'PowerPoint',
    icon: 'M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z',
    description: 'Slide deck with charts, talking points, and speaker notes.',
    preview: 'slides',
  },
  {
    name: 'PDF',
    icon: 'M6 18a2 2 0 002 2h8a2 2 0 002-2V8l-6-6H8a2 2 0 00-2 2z',
    description: 'Print-ready document with precise formatting and branding.',
    preview: 'pdf',
  },
  {
    name: 'Word Report',
    icon: 'M4 4h16v16H4z M8 8h8 M8 12h8 M8 16h5',
    description: 'Editable document for further customization and collaboration.',
    preview: 'word',
  },
];

function FormatPreview({ type }: { type: string }) {
  switch (type) {
    case 'report':
      return (
        <div className="space-y-3 p-6">
          <div className="h-6 w-3/4 rounded bg-slate-200" />
          <div className="h-3 w-full rounded bg-slate-100" />
          <div className="h-3 w-5/6 rounded bg-slate-100" />
          <div className="mt-4 grid grid-cols-2 gap-3">
            <div className="rounded-lg bg-slate-50 p-4">
              <div className="flex h-20 items-end gap-1">
                {[40, 65, 52, 78, 61].map((h, i) => (
                  <div key={i} className="flex-1 rounded-t bg-blue-400" style={{ height: `${h}%` }} />
                ))}
              </div>
            </div>
            <div className="rounded-lg bg-slate-50 p-4">
              <div className="space-y-2">
                <div className="flex justify-between"><div className="h-2 w-12 rounded bg-slate-200" /><div className="h-2 w-8 rounded bg-slate-200" /></div>
                <div className="flex justify-between"><div className="h-2 w-16 rounded bg-slate-200" /><div className="h-2 w-6 rounded bg-slate-200" /></div>
                <div className="flex justify-between"><div className="h-2 w-10 rounded bg-slate-200" /><div className="h-2 w-10 rounded bg-slate-200" /></div>
              </div>
            </div>
          </div>
          <div className="h-3 w-full rounded bg-slate-100" />
          <div className="h-3 w-4/5 rounded bg-slate-100" />
        </div>
      );
    case 'dashboard':
      return (
        <div className="p-6">
          <div className="grid grid-cols-3 gap-3">
            {[
              { label: 'Revenue', value: '$2.4M' },
              { label: 'Users', value: '48K' },
              { label: 'Growth', value: '+12%' },
            ].map((kpi) => (
              <div key={kpi.label} className="rounded-xl border border-slate-200 p-3">
                <p className="text-xs text-slate-500">{kpi.label}</p>
                <p className="text-lg font-bold text-slate-900">{kpi.value}</p>
              </div>
            ))}
          </div>
          <div className="mt-4 rounded-xl border border-slate-200 p-4">
            <div className="flex h-32 items-end gap-2">
              {[50, 72, 45, 88, 61, 79, 53, 92].map((h, i) => (
                <div key={i} className="flex-1 rounded-t bg-gradient-to-t from-blue-500 to-violet-400" style={{ height: `${h}%` }} />
              ))}
            </div>
          </div>
        </div>
      );
    case 'slides':
      return (
        <div className="p-6">
          <div className="aspect-video rounded-lg border border-slate-200 bg-slate-50 p-4">
            <div className="h-4 w-1/2 rounded bg-slate-300" />
            <div className="mt-3 grid grid-cols-2 gap-3">
              <div className="rounded bg-white p-3">
                <div className="flex h-16 items-end gap-1">
                  {[40, 65, 52, 78].map((h, i) => (
                    <div key={i} className="flex-1 rounded-t bg-blue-400" style={{ height: `${h}%` }} />
                  ))}
                </div>
              </div>
              <div className="space-y-2">
                <div className="h-2 w-full rounded bg-slate-200" />
                <div className="h-2 w-4/5 rounded bg-slate-200" />
                <div className="h-2 w-3/4 rounded bg-slate-200" />
              </div>
            </div>
          </div>
          <div className="mt-3 flex justify-center gap-1.5">
            {[0, 1, 2, 3, 4].map((i) => (
              <div key={i} className={`h-1.5 rounded-full ${i === 0 ? 'w-6 bg-blue-500' : 'w-1.5 bg-slate-300'}`} />
            ))}
          </div>
        </div>
      );
    case 'pdf':
      return (
        <div className="p-6">
          <div className="mx-auto max-w-sm rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div className="h-4 w-24 rounded bg-slate-300" />
              <div className="h-4 w-12 rounded bg-red-100" />
            </div>
            <div className="mt-4 space-y-2">
              <div className="h-3 w-full rounded bg-slate-100" />
              <div className="h-3 w-5/6 rounded bg-slate-100" />
              <div className="h-3 w-full rounded bg-slate-100" />
            </div>
            <div className="mt-4 h-24 rounded bg-slate-50 p-3">
              <div className="flex h-full items-end gap-1">
                {[30, 50, 45, 70, 55, 80].map((h, i) => (
                  <div key={i} className="flex-1 rounded-t bg-slate-300" style={{ height: `${h}%` }} />
                ))}
              </div>
            </div>
            <div className="mt-4 space-y-2">
              <div className="h-3 w-full rounded bg-slate-100" />
              <div className="h-3 w-3/4 rounded bg-slate-100" />
            </div>
          </div>
        </div>
      );
    case 'word':
      return (
        <div className="p-6">
          <div className="mx-auto max-w-sm rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
            <div className="flex items-center gap-2 border-b border-blue-100 pb-3">
              <div className="flex h-6 w-6 items-center justify-center rounded bg-blue-100 text-xs font-bold text-blue-600">W</div>
              <div className="h-4 w-20 rounded bg-slate-300" />
            </div>
            <div className="mt-4 space-y-2">
              <div className="h-4 w-2/3 rounded bg-slate-200" />
              <div className="h-3 w-full rounded bg-slate-100" />
              <div className="h-3 w-full rounded bg-slate-100" />
              <div className="h-3 w-4/5 rounded bg-slate-100" />
            </div>
            <div className="mt-3 rounded bg-blue-50 p-3">
              <div className="h-3 w-1/2 rounded bg-blue-200" />
              <div className="mt-2 h-3 w-3/4 rounded bg-blue-100" />
            </div>
            <div className="mt-3 space-y-2">
              <div className="h-3 w-full rounded bg-slate-100" />
              <div className="h-3 w-5/6 rounded bg-slate-100" />
            </div>
          </div>
        </div>
      );
    default:
      return null;
  }
}

export function ReportingShowcase() {
  const [active, setActive] = useState(0);
  const [autoPlay, setAutoPlay] = useState(true);

  useEffect(() => {
    if (!autoPlay) return;
    const interval = setInterval(() => {
      setActive((prev) => (prev + 1) % formats.length);
    }, 4000);
    return () => clearInterval(interval);
  }, [autoPlay]);

  return (
    <section className="py-24 lg:py-32">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <Reveal className="mx-auto max-w-2xl text-center">
          <p className="text-sm font-semibold uppercase tracking-wider text-blue-600">Reporting Showcase</p>
          <h2 className="mt-3 text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
            From analysis to presentation in one click
          </h2>
          <p className="mt-4 text-lg text-slate-600">
            Generate executive reports, interactive dashboards, slide decks, PDFs, and Word documents — all from the same data.
          </p>
        </Reveal>

        <Reveal className="mt-12" delay={200}>
          <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-xl shadow-slate-900/5">
            {/* Format tabs */}
            <div className="flex overflow-x-auto border-b border-slate-200 bg-slate-50/50">
              {formats.map((fmt, i) => (
                <button
                  key={fmt.name}
                  onClick={() => { setActive(i); setAutoPlay(false); }}
                  className={`flex shrink-0 items-center gap-2 border-b-2 px-5 py-3.5 text-sm font-medium transition-all ${
                    active === i
                      ? 'border-blue-500 text-slate-900 bg-white'
                      : 'border-transparent text-slate-500 hover:text-slate-700 hover:bg-white/50'
                  }`}
                >
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4">
                    <path d={fmt.icon} />
                  </svg>
                  {fmt.name}
                </button>
              ))}
            </div>

            {/* Preview */}
            <div key={active} className="animate-tab-fade">
              <div className="grid lg:grid-cols-[1fr_1.5fr]">
                <div className="border-b border-slate-200 p-8 lg:border-b-0 lg:border-r">
                  <h3 className="text-xl font-bold text-slate-900">{formats[active].name}</h3>
                  <p className="mt-2 text-sm text-slate-600">{formats[active].description}</p>
                  <div className="mt-6 flex items-center gap-2 text-sm font-medium text-blue-600">
                    <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" />
                    </svg>
                    Generated automatically from your analysis
                  </div>
                </div>
                <div className="bg-slate-50/30">
                  <FormatPreview type={formats[active].preview} />
                </div>
              </div>
            </div>
          </div>
        </Reveal>
      </div>
    </section>
  );
}
