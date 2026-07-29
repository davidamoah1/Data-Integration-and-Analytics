import { ShieldCheck, Gauge, Eye, FileCheck } from 'lucide-react';
import { Reveal } from './Reveal';

const trustPoints = [
  {
    icon: ShieldCheck,
    title: 'Secure data handling',
    description: 'Your data is encrypted in transit and access is controlled through organization-level permissions.',
  },
  {
    icon: Gauge,
    title: 'Reliable analytics',
    description: 'Consistent, repeatable calculations you can depend on for critical business and research decisions.',
  },
  {
    icon: Eye,
    title: 'Transparent calculations',
    description: 'Every statistic and chart is explained clearly, so you understand exactly how results are produced.',
  },
  {
    icon: FileCheck,
    title: 'Professional reporting',
    description: 'Export polished, presentation-ready reports that hold up in front of any audience.',
  },
];

export function Trust() {
  return (
    <section className="bg-white py-24">
      <div className="mx-auto max-w-7xl px-6">
        <Reveal className="mx-auto max-w-2xl text-center">
          <span className="text-sm font-semibold uppercase tracking-wider text-green-600">Reliability</span>
          <h2 className="mt-3 text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
            Built on trust
          </h2>
          <p className="mt-4 text-lg text-slate-600">
            A platform designed to be dependable, transparent, and safe for the data
            you care about most.
          </p>
        </Reveal>

        <div className="mt-14 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {trustPoints.map((point, i) => (
            <Reveal key={point.title} delay={i * 80}>
              <div className="group h-full rounded-2xl border border-slate-200 p-6 text-center transition-all duration-300 hover:-translate-y-1 hover:border-green-200 hover:shadow-lg hover:shadow-green-100/50">
                <div className="mx-auto mb-4 inline-flex h-12 w-12 items-center justify-center rounded-full bg-green-50 text-green-600 transition-transform duration-300 group-hover:scale-110">
                  <point.icon size={22} />
                </div>
                <h3 className="text-base font-semibold text-slate-900">{point.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-slate-600">{point.description}</p>
              </div>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}
