import { Briefcase, Microscope, GraduationCap, Landmark, UserCog } from 'lucide-react';
import { Reveal } from './Reveal';

const audiences = [
  {
    icon: Briefcase,
    title: 'Businesses',
    description: 'Understand performance and make better decisions with clear, reliable analytics.',
  },
  {
    icon: Microscope,
    title: 'Researchers',
    description: 'Analyze data and generate reliable findings backed by rigorous statistical methods.',
  },
  {
    icon: GraduationCap,
    title: 'Universities',
    description: 'Support teaching and research with an accessible, professional analytics environment.',
  },
  {
    icon: Landmark,
    title: 'Government',
    description: 'Understand communities and improve policies with transparent, data-driven insight.',
  },
  {
    icon: UserCog,
    title: 'Analysts',
    description: 'Reduce manual analytics work and spend more time on high-value interpretation.',
  },
];

export function Audience() {
  return (
    <section className="bg-slate-50 py-24">
      <div className="mx-auto max-w-7xl px-6">
        <Reveal className="mx-auto max-w-2xl text-center">
          <span className="text-sm font-semibold uppercase tracking-wider text-blue-600">Who it&apos;s for</span>
          <h2 className="mt-3 text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
            Built for every kind of data-driven team
          </h2>
          <p className="mt-4 text-lg text-slate-600">
            Whatever your role, DataFlow adapts to how you work.
          </p>
        </Reveal>

        <div className="mt-14 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-5">
          {audiences.map((a, i) => (
            <Reveal key={a.title} delay={i * 80}>
              <div className="group h-full rounded-2xl bg-white border border-slate-200 p-6 text-center transition-all duration-300 hover:-translate-y-1 hover:shadow-xl hover:shadow-blue-100/50">
                <div className="mx-auto mb-4 inline-flex h-12 w-12 items-center justify-center rounded-full bg-gradient-to-br from-blue-600 to-indigo-500 text-white shadow-md shadow-blue-500/30 transition-transform duration-300 group-hover:scale-110">
                  <a.icon size={22} />
                </div>
                <h3 className="text-base font-semibold text-slate-900">{a.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-slate-600">{a.description}</p>
              </div>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}
