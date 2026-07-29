import { FileWarning, Clock, PuzzleIcon, TrendingDown } from 'lucide-react';
import { Reveal } from './Reveal';

const problems = [
  {
    icon: FileWarning,
    title: 'Scattered data',
    description: 'Information locked in different files, spreadsheets, and systems with no single source of truth.',
  },
  {
    icon: Clock,
    title: 'Manual reporting',
    description: 'Hours spent building reports by hand instead of focusing on the decisions that matter.',
  },
  {
    icon: PuzzleIcon,
    title: 'Disconnected tools',
    description: 'Cleaning, analysis, visualization, and reporting spread across multiple, incompatible tools.',
  },
  {
    icon: TrendingDown,
    title: 'Slow decisions',
    description: 'Difficult analysis and complex workflows delay the insights leaders need to act quickly.',
  },
];

export function Problem() {
  return (
    <section className="relative overflow-hidden bg-white py-24">
      <div className="absolute inset-0 -z-10 bg-gradient-to-b from-slate-50/50 to-white" />
      <div className="mx-auto max-w-7xl px-6">
        <Reveal className="mx-auto max-w-2xl text-center">
          <span className="text-sm font-semibold uppercase tracking-wider text-red-500">The problem</span>
          <h2 className="mt-3 text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
            Organizations struggle to turn data into action
          </h2>
          <p className="mt-4 text-lg text-slate-600">
            Most teams are stuck juggling disconnected tools and manual work just to answer
            simple questions about their own data.
          </p>
        </Reveal>

        <div className="mt-14 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {problems.map((problem, i) => (
            <Reveal key={problem.title} delay={i * 80}>
              <div className="group h-full rounded-2xl border border-slate-200 bg-slate-50 p-6 transition-all duration-300 hover:-translate-y-1 hover:border-red-200 hover:bg-white hover:shadow-lg hover:shadow-red-100/50">
                <div className="mb-4 inline-flex h-11 w-11 items-center justify-center rounded-xl bg-red-100 text-red-600 transition-transform duration-300 group-hover:scale-110 group-hover:rotate-3">
                  <problem.icon size={22} />
                </div>
                <h3 className="text-base font-semibold text-slate-900">{problem.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-slate-600">{problem.description}</p>
              </div>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}
