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
            <div className="flex aspect-video items-center justify-center rounded-xl bg-gradient-to-br from-slate-50 to-slate-100">
              <div className="text-center transition-opacity duration-300">
                <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-white shadow-md">
                  <current.icon size={32} className="text-blue-500" />
                </div>
                <p className="text-sm font-medium text-slate-500">{current.description}</p>
              </div>
            </div>
          </div>
        </Reveal>
      </div>
    </section>
  );
}
