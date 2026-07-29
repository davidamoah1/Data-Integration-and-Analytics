'use client';

import { useState } from 'react';
import { LayoutDashboard, Table2, FileBarChart, Brush } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Reveal } from './Reveal';

const screenshots = [
  {
    id: 'dashboard',
    label: 'Dashboard',
    icon: LayoutDashboard,
    description: 'A real-time view of your key metrics and trends.',
  },
  {
    id: 'workspace',
    label: 'Analytics Workspace',
    icon: Table2,
    description: 'Explore, filter, and calculate directly on your data.',
  },
  {
    id: 'reports',
    label: 'Reports',
    icon: FileBarChart,
    description: 'Presentation-ready reports generated in a few clicks.',
  },
  {
    id: 'quality',
    label: 'Data Quality',
    icon: Brush,
    description: 'See exactly what was detected and cleaned in your dataset.',
  },
];

export function Screenshots() {
  const [active, setActive] = useState(screenshots[0].id);
  const current = screenshots.find((s) => s.id === active)!;

  return (
    <section className="bg-slate-50 py-24">
      <div className="mx-auto max-w-6xl px-6">
        <Reveal className="mx-auto max-w-2xl text-center">
          <span className="text-sm font-semibold uppercase tracking-wider text-blue-600">Product tour</span>
          <h2 className="mt-3 text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
            See the platform in action
          </h2>
          <p className="mt-4 text-lg text-slate-600">
            A closer look at the tools your team will use every day.
          </p>
        </Reveal>

        <Reveal delay={100} className="mt-10 flex flex-wrap justify-center gap-2">
          {screenshots.map((s) => (
            <button
              key={s.id}
              onClick={() => setActive(s.id)}
              className={cn(
                'inline-flex items-center gap-2 rounded-full px-4 py-2 text-sm font-medium transition-all duration-200',
                active === s.id
                  ? 'bg-blue-600 text-white shadow-md shadow-blue-500/30'
                  : 'bg-white text-slate-600 border border-slate-200 hover:border-blue-300 hover:text-blue-600',
              )}
            >
              <s.icon size={16} />
              {s.label}
            </button>
          ))}
        </Reveal>

        <Reveal delay={180}>
          <div className="mt-8 rounded-2xl border border-slate-200 bg-white p-2 shadow-2xl shadow-slate-300/40">
            <div className="overflow-hidden rounded-xl bg-gradient-to-br from-slate-50 to-slate-100">
              {/* Window bar */}
              <div className="flex items-center gap-2 border-b border-slate-200 bg-white px-4 py-3">
                <div className="h-2.5 w-2.5 rounded-full bg-red-400" />
                <div className="h-2.5 w-2.5 rounded-full bg-yellow-400" />
                <div className="h-2.5 w-2.5 rounded-full bg-green-400" />
                <span className="ml-3 text-xs font-medium text-slate-400">DataFlow — {current.label}</span>
              </div>

              {/* Content area */}
              <div className="aspect-video p-6">
                {active === 'dashboard' && (
                  <div className="grid h-full grid-cols-3 gap-4">
                    {[
                      { label: 'Total Records', value: '12,840', color: 'from-blue-500 to-blue-400' },
                      { label: 'Data Quality', value: '98.2%', color: 'from-green-500 to-green-400' },
                      { label: 'Active Users', value: '342', color: 'from-purple-500 to-purple-400' },
                    ].map((kpi) => (
                      <div key={kpi.label} className="rounded-lg border border-slate-200 bg-white p-4">
                        <p className="text-xs text-slate-500">{kpi.label}</p>
                        <p className={`mt-1 bg-gradient-to-r ${kpi.color} bg-clip-text text-2xl font-bold text-transparent`}>{kpi.value}</p>
                        <div className="mt-2 h-1.5 w-full rounded-full bg-slate-100">
                          <div className={`h-1.5 w-3/4 rounded-full bg-gradient-to-r ${kpi.color}`} />
                        </div>
                      </div>
                    ))}
                    <div className="col-span-3 rounded-lg border border-slate-200 bg-white p-4">
                      <p className="mb-3 text-xs font-semibold text-slate-600">Monthly Trend</p>
                      <div className="flex h-24 items-end gap-2">
                        {[40, 65, 45, 80, 60, 95, 70, 100, 85, 110, 90, 120].map((h, i) => (
                          <div key={i} className="flex-1 rounded-t bg-gradient-to-t from-blue-600 to-blue-400" style={{ height: `${h * 0.6}px` }} />
                        ))}
                      </div>
                    </div>
                  </div>
                )}

                {active === 'workspace' && (
                  <div className="h-full rounded-lg border border-slate-200 bg-white overflow-hidden">
                    <div className="grid grid-cols-8 gap-px bg-slate-200 text-xs">
                      {['ID', 'Name', 'Region', 'Value', 'Status', 'Date', 'Owner', 'Score'].map((h) => (
                        <div key={h} className="bg-slate-50 px-2 py-2 font-semibold text-slate-600">{h}</div>
                      ))}
                      {Array.from({ length: 6 }).map((_, row) => (
                        <div key={row} className="contents">
                          {Array.from({ length: 8 }).map((_, col) => (
                            <div key={col} className="bg-white px-2 py-2 text-slate-500">
                              {col === 0 && `#${1000 + row}`}
                              {col === 1 && ['Accra', 'Kumasi', 'Takoradi', 'Tamale', 'Cape Coast', 'Ho'][row]}
                              {col === 2 && ['Greater Accra', 'Ashanti', 'Western', 'Northern', 'Central', 'Volta'][row]}
                              {col === 3 && `${(Math.random() * 1000).toFixed(0)}`}
                              {col === 4 && <span className={`rounded-full px-2 py-0.5 text-[10px] ${row % 3 === 0 ? 'bg-green-100 text-green-700' : row % 3 === 1 ? 'bg-amber-100 text-amber-700' : 'bg-red-100 text-red-700'}`}>{row % 3 === 0 ? 'Active' : row % 3 === 1 ? 'Pending' : 'Error'}</span>}
                              {col === 5 && `2025-07-${String(15 + row).padStart(2, '0')}`}
                              {col === 6 && ['J. Doe', 'A. Smith', 'K. Lee', 'M. Chen', 'R. Patel', 'S. Brown'][row]}
                              {col === 7 && `${(0.5 + Math.random() * 0.5).toFixed(2)}`}
                            </div>
                          ))}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {active === 'reports' && (
                  <div className="grid h-full grid-cols-2 gap-4">
                    <div className="rounded-lg border border-slate-200 bg-white p-4">
                      <div className="mb-3 h-4 w-32 rounded bg-slate-200" />
                      <div className="space-y-2">
                        <div className="h-2 w-full rounded bg-slate-100" />
                        <div className="h-2 w-5/6 rounded bg-slate-100" />
                        <div className="h-2 w-4/6 rounded bg-slate-100" />
                      </div>
                      <div className="mt-4 grid grid-cols-2 gap-2">
                        <div className="h-20 rounded bg-gradient-to-br from-blue-50 to-indigo-50" />
                        <div className="h-20 rounded bg-gradient-to-br from-green-50 to-emerald-50" />
                      </div>
                    </div>
                    <div className="rounded-lg border border-slate-200 bg-white p-4">
                      <div className="mb-3 flex items-center justify-between">
                        <div className="h-4 w-24 rounded bg-slate-200" />
                        <div className="flex gap-1">
                          <div className="h-6 w-12 rounded bg-blue-100" />
                          <div className="h-6 w-14 rounded bg-green-100" />
                        </div>
                      </div>
                      <div className="flex h-32 items-center justify-center rounded-lg bg-slate-50">
                        <div className="flex h-24 items-end gap-3">
                          {[60, 80, 45, 90, 70, 100].map((h, i) => (
                            <div key={i} className="w-8 rounded-t bg-gradient-to-t from-blue-600 to-indigo-400" style={{ height: `${h * 0.7}px` }} />
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {active === 'quality' && (
                  <div className="h-full space-y-3">
                    {[
                      { label: 'Missing Values', count: 142, total: 12840, color: 'bg-amber-500', pct: '98.9%' },
                      { label: 'Duplicates', count: 23, total: 12840, color: 'bg-blue-500', pct: '99.8%' },
                      { label: 'Format Errors', count: 8, total: 12840, color: 'bg-red-500', pct: '99.9%' },
                      { label: 'Outliers Detected', count: 15, total: 12840, color: 'bg-purple-500', pct: '99.9%' },
                    ].map((item) => (
                      <div key={item.label} className="flex items-center gap-4 rounded-lg border border-slate-200 bg-white p-3">
                        <div className={`flex h-8 w-8 items-center justify-center rounded-lg ${item.color}/10`}>
                          <div className={`h-2 w-2 rounded-full ${item.color}`} />
                        </div>
                        <div className="flex-1">
                          <div className="flex items-center justify-between">
                            <p className="text-xs font-medium text-slate-700">{item.label}</p>
                            <p className="text-xs text-slate-500">{item.count} found · {item.pct} clean</p>
                          </div>
                          <div className="mt-1.5 h-1.5 w-full rounded-full bg-slate-100">
                            <div className={`h-1.5 rounded-full ${item.color}`} style={{ width: item.pct }} />
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        </Reveal>
      </div>
    </section>
  );
}
