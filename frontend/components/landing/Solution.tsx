import { Brush, LineChart, LayoutDashboard, Sigma, FileText } from 'lucide-react';
import { Reveal } from './Reveal';

const pillars = [
  {
    icon: Brush,
    title: 'Data Preparation',
    description: 'Clean and organize data easily, with automated detection of missing values, duplicates, and errors.',
  },
  {
    icon: LineChart,
    title: 'Analytics',
    description: 'Discover trends and patterns across your datasets without writing a single line of code.',
  },
  {
    icon: LayoutDashboard,
    title: 'Visualization',
    description: 'Create meaningful dashboards that communicate insights clearly to any audience.',
  },
  {
    icon: Sigma,
    title: 'Statistics',
    description: 'Perform professional statistical analysis with full interpretation and assumption checking.',
  },
  {
    icon: FileText,
    title: 'Reporting',
    description: 'Generate presentation-ready reports and slides in minutes, not days.',
  },
];

export function Solution() {
  return (
    <section id="solutions" className="relative overflow-hidden bg-slate-50 py-24">
      <div className="absolute inset-0 -z-10 bg-grid-slate opacity-40 [mask-image:radial-gradient(ellipse_60%_50%_at_50%_50%,#000_30%,transparent_100%)]" />

      <div className="relative mx-auto max-w-7xl px-6">
        <Reveal className="mx-auto max-w-2xl text-center">
          <span className="text-sm font-semibold uppercase tracking-wider text-blue-600">The solution</span>
          <h2 className="mt-3 text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
            One platform for your entire data journey
          </h2>
          <p className="mt-4 text-lg text-slate-600">
            From raw files to finished reports — everything you need lives in a single,
            integrated workspace.
          </p>
        </Reveal>

        <div className="mt-14 grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-5">
          {pillars.map((pillar, i) => (
            <Reveal key={pillar.title} delay={i * 80} className="relative">
              <div className="group h-full rounded-2xl border border-slate-200 bg-white p-6 shadow-sm transition-all duration-300 hover:-translate-y-1 hover:border-blue-200 hover:shadow-xl hover:shadow-blue-100/60">
                <div className="mb-4 inline-flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-blue-600 to-indigo-500 text-white shadow-md shadow-blue-500/30 transition-transform duration-300 group-hover:scale-110">
                  <pillar.icon size={20} />
                </div>
                <h3 className="text-base font-semibold text-slate-900">{pillar.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-slate-600">{pillar.description}</p>
              </div>
              {i < pillars.length - 1 && (
                <div className="absolute right-[-13px] top-1/2 hidden h-px w-6 -translate-y-1/2 bg-gradient-to-r from-slate-300 to-transparent lg:block" />
              )}
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}
