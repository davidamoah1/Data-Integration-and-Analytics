import { X, Check } from 'lucide-react';
import { Reveal } from './Reveal';

const traditional = [
  'Multiple tools required',
  'Manual data cleaning',
  'Complex, technical workflows',
  'Steep learning curve',
];

const dataflow = [
  'One integrated solution',
  'Automated data preparation',
  'Guided, step-by-step analytics',
  'Simple, accessible experience',
];

export function Comparison() {
  return (
    <section className="relative overflow-hidden bg-white py-24">
      <div className="absolute inset-0 -z-10 bg-grid-slate opacity-20 [mask-image:radial-gradient(ellipse_60%_50%_at_50%_50%,#000_30%,transparent_100%)]" />
      <div className="mx-auto max-w-5xl px-6">
        <Reveal className="mx-auto max-w-2xl text-center">
          <span className="text-sm font-semibold uppercase tracking-wider text-blue-600">Why DataFlow</span>
          <h2 className="mt-3 text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
            A simpler way to work with data
          </h2>
          <p className="mt-4 text-lg text-slate-600">
            See how DataFlow compares to the traditional, tool-heavy approach.
          </p>
        </Reveal>

        <div className="mt-14 grid grid-cols-1 gap-6 md:grid-cols-2">
          <Reveal>
            <div className="h-full rounded-2xl border border-slate-200 bg-slate-50 p-8 transition-shadow hover:shadow-md">
              <h3 className="mb-6 text-sm font-semibold uppercase tracking-wide text-slate-500">
                Traditional approach
              </h3>
              <ul className="space-y-4">
                {traditional.map((item) => (
                  <li key={item} className="flex items-start gap-3">
                    <span className="mt-0.5 flex h-5 w-5 flex-shrink-0 items-center justify-center rounded-full bg-red-100 text-red-500">
                      <X size={12} />
                    </span>
                    <span className="text-sm text-slate-600">{item}</span>
                  </li>
                ))}
              </ul>
            </div>
          </Reveal>

          <Reveal delay={120}>
            <div className="relative h-full overflow-hidden rounded-2xl border-2 border-blue-600 bg-gradient-to-br from-blue-50 to-indigo-50 p-8 shadow-xl shadow-blue-200/50 transition-shadow hover:shadow-2xl hover:shadow-blue-300/50">
              <div className="absolute -right-8 -top-8 h-32 w-32 rounded-full bg-blue-400/20 blur-2xl" />
              <h3 className="relative mb-6 text-sm font-semibold uppercase tracking-wide text-blue-700">
                DataFlow
              </h3>
              <ul className="relative space-y-4">
                {dataflow.map((item) => (
                  <li key={item} className="flex items-start gap-3">
                    <span className="mt-0.5 flex h-5 w-5 flex-shrink-0 items-center justify-center rounded-full bg-blue-600 text-white shadow-sm shadow-blue-500/40">
                      <Check size={12} />
                    </span>
                    <span className="text-sm font-medium text-slate-800">{item}</span>
                  </li>
                ))}
              </ul>
            </div>
          </Reveal>
        </div>
      </div>
    </section>
  );
}
