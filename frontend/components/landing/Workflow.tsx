import { Upload, Brush, LineChart, Lightbulb, FileText, Target } from 'lucide-react';
import { Reveal } from './Reveal';

const steps = [
  { icon: Upload, label: 'Upload Data' },
  { icon: Brush, label: 'Prepare Data' },
  { icon: LineChart, label: 'Analyze Information' },
  { icon: Lightbulb, label: 'Discover Insights' },
  { icon: FileText, label: 'Create Reports' },
  { icon: Target, label: 'Make Decisions' },
];

export function Workflow() {
  return (
    <section id="workflow" className="bg-slate-50 py-24">
      <div className="mx-auto max-w-7xl px-6">
        <Reveal className="mx-auto max-w-2xl text-center">
          <span className="text-sm font-semibold uppercase tracking-wider text-blue-600">How it works</span>
          <h2 className="mt-3 text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
            From raw data to confident decisions
          </h2>
          <p className="mt-4 text-lg text-slate-600">
            A clear, guided process that takes you from upload to action.
          </p>
        </Reveal>

        <div className="relative mt-14">
          <div className="absolute left-0 right-0 top-8 hidden h-px bg-gradient-to-r from-transparent via-slate-300 to-transparent lg:block" />
          <div className="grid grid-cols-2 gap-6 sm:grid-cols-3 lg:grid-cols-6">
            {steps.map((step, i) => (
              <Reveal key={step.label} delay={i * 90}>
                <div className="group relative flex flex-col items-center text-center">
                  <div className="relative z-10 mb-4 flex h-16 w-16 items-center justify-center rounded-2xl border border-slate-200 bg-white text-blue-600 shadow-sm transition-all duration-300 group-hover:-translate-y-1 group-hover:border-blue-300 group-hover:shadow-lg group-hover:shadow-blue-200/60">
                    <step.icon size={26} />
                    <span className="absolute -right-1.5 -top-1.5 flex h-6 w-6 items-center justify-center rounded-full bg-blue-600 text-[11px] font-bold text-white shadow-sm">
                      {i + 1}
                    </span>
                  </div>
                  <p className="text-sm font-medium text-slate-800">{step.label}</p>
                </div>
              </Reveal>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
