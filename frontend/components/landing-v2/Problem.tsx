'use client';

import { Reveal } from '@/components/landing/Reveal';

const problems = [
  {
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="h-6 w-6">
        <rect x="3" y="3" width="18" height="18" rx="2" /><path d="M3 9h18M3 15h18M9 3v18M15 3v18" />
      </svg>
    ),
    title: 'Disconnected spreadsheets',
    description: 'Data scattered across files, departments, and systems with no single source of truth.',
  },
  {
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="h-6 w-6">
        <circle cx="12" cy="12" r="10" /><path d="M12 6v6l4 2" />
      </svg>
    ),
    title: 'Hours spent on reports',
    description: 'Manual data preparation and formatting consume time that should go to analysis.',
  },
  {
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="h-6 w-6">
        <path d="M17 1l4 4-4 4" /><path d="M3 11V9a4 4 0 014-4h14" /><path d="M7 23l-4-4 4-4" /><path d="M21 13v2a4 4 0 01-4 4H3" />
      </svg>
    ),
    title: 'Repeated analysis',
    description: 'The same questions answered over and over because insights are not captured or shared.',
  },
  {
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="h-6 w-6">
        <rect x="3" y="3" width="18" height="18" rx="2" /><path d="M9 9h6v6H9z" />
      </svg>
    ),
    title: 'Dashboards built manually',
    description: 'Every new question requires a developer to build a new dashboard from scratch.',
  },
  {
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="h-6 w-6">
        <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" /><path d="M14 2v6h6" /><path d="M16 13H8M16 17H8M10 9H8" />
      </svg>
    ),
    title: 'Data re-entered from paper',
    description: 'Valuable information locked in paper forms, requiring manual transcription and validation.',
  },
];

export function Problem() {
  return (
    <section className="bg-slate-50/50 py-24 lg:py-32">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <Reveal className="mx-auto max-w-2xl text-center">
          <p className="text-sm font-semibold uppercase tracking-wider text-blue-600">The Challenge</p>
          <h2 className="mt-3 text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
            Data work is fragmented and slow
          </h2>
          <p className="mt-4 text-lg text-slate-600">
            Organizations across every sector face the same fundamental problem: turning raw data into decisions takes too long, costs too much, and relies on too many manual steps.
          </p>
        </Reveal>

        <div className="mt-16 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {problems.map((problem, i) => (
            <Reveal key={problem.title} delay={i * 100}>
              <div className="card-hover h-full rounded-2xl border border-slate-200 bg-white p-6">
                <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-red-50 text-red-500">
                  {problem.icon}
                </div>
                <h3 className="mt-4 text-lg font-semibold text-slate-900">{problem.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-slate-600">{problem.description}</p>
              </div>
            </Reveal>
          ))}

          {/* Solution card */}
          <Reveal delay={500}>
            <div className="flex h-full flex-col justify-center rounded-2xl bg-gradient-to-br from-blue-600 to-violet-600 p-6 text-white">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-white/20">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-6 w-6">
                  <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" />
                </svg>
              </div>
              <h3 className="mt-4 text-lg font-semibold">The unified solution</h3>
              <p className="mt-2 text-sm leading-relaxed text-blue-100">
                DataFlow brings collecting, preparing, analyzing, visualizing, and reporting into one guided workflow — from raw data to presentation-ready decisions.
              </p>
            </div>
          </Reveal>
        </div>
      </div>
    </section>
  );
}
