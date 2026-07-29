import { Quote, Star } from 'lucide-react';
import { Reveal } from './Reveal';

const testimonials = [
  {
    quote: 'DataFlow cut our monthly reporting time from two days to under an hour. The Ministry reports are now ready before the deadline, every single month.',
    name: 'Dr. Abena Owusu',
    role: 'Hospital Administrator',
    org: 'Korle Bu Teaching Hospital',
    initials: 'AO',
    color: 'bg-red-100 text-red-700',
  },
  {
    quote: 'As a researcher, I used to spend weeks cleaning survey data in SPSS. With DataFlow, the cleaning, stats, and charts are done in an afternoon. It transformed my dissertation process.',
    name: 'Kwame Mensah',
    role: 'PhD Candidate, Statistics',
    org: 'University of Ghana',
    initials: 'KM',
    color: 'bg-purple-100 text-purple-700',
  },
  {
    quote: 'Our board meetings used to start with outdated numbers. Now we have a live executive dashboard that updates in real-time. The board is impressed, and decisions happen faster.',
    name: 'Sarah Johnson',
    role: 'COO',
    org: 'Atlantic Logistics',
    initials: 'SJ',
    color: 'bg-blue-100 text-blue-700',
  },
];

export function Testimonials() {
  return (
    <section className="relative overflow-hidden bg-white py-24">
      <div className="absolute inset-0 -z-10 bg-grid-slate opacity-20 [mask-image:radial-gradient(ellipse_60%_50%_at_50%_50%,#000_30%,transparent_100%)]" />

      <div className="relative mx-auto max-w-7xl px-6">
        <Reveal className="mx-auto max-w-2xl text-center">
          <span className="text-sm font-semibold uppercase tracking-wider text-blue-600">Testimonials</span>
          <h2 className="mt-3 text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
            What our early users say
          </h2>
          <p className="mt-4 text-lg text-slate-600">
            Teams across healthcare, research, and business are already working smarter with DataFlow.
          </p>
        </Reveal>

        <div className="mt-14 grid grid-cols-1 gap-6 md:grid-cols-3">
          {testimonials.map((t, i) => (
            <Reveal key={t.name} delay={i * 100}>
              <div className="group flex h-full flex-col justify-between rounded-2xl border border-slate-200 bg-white p-6 shadow-sm transition-all duration-300 hover:-translate-y-1 hover:border-blue-200 hover:shadow-xl hover:shadow-blue-100/50">
                <div>
                  <div className="mb-4 flex items-center justify-between">
                    <Quote className="text-blue-200" size={28} />
                    <div className="flex gap-0.5">
                      {Array.from({ length: 5 }).map((_, idx) => (
                        <Star key={idx} size={14} className="fill-amber-400 text-amber-400" />
                      ))}
                    </div>
                  </div>
                  <p className="text-sm leading-relaxed text-slate-700">
                    &ldquo;{t.quote}&rdquo;
                  </p>
                </div>
                <div className="mt-6 flex items-center gap-3 border-t border-slate-100 pt-4">
                  <div className={`flex h-10 w-10 items-center justify-center rounded-full text-sm font-bold ${t.color}`}>
                    {t.initials}
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-slate-900">{t.name}</p>
                    <p className="text-xs text-slate-500">{t.role}, {t.org}</p>
                  </div>
                </div>
              </div>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}
