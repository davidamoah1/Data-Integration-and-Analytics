'use client';

import { Reveal } from '@/components/landing/Reveal';

const customers = [
  {
    type: 'Business Leaders',
    icon: 'M3 21h18M3 10h18M5 6l7-3 7 3M4 10v11M20 10v11',
    benefit: 'Real-time visibility into operations, sales, and financial performance with executive dashboards.',
  },
  {
    type: 'Researchers',
    icon: 'M9 12l2 2 4-4M21 12a9 9 0 11-18 0 9 9 0 0118 0z',
    benefit: 'Design experiments, run statistical tests, and produce publication-ready findings.',
  },
  {
    type: 'Hospitals',
    icon: 'M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0016.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 002 8.5c0 2.29 1.51 4.04 3 5.5l7 7z',
    benefit: 'Track patient outcomes, monitor treatment efficacy, and ensure compliance reporting.',
  },
  {
    type: 'Universities',
    icon: 'M22 10v6M2 10l10-5 10 5-10 5z M6 12v5c3 3 9 3 12 0v-5',
    benefit: 'Measure student performance, track institutional effectiveness, and report to stakeholders.',
  },
  {
    type: 'Government',
    icon: 'M3 21h18M3 10h18M5 6l7-3 7 3M4 10v11M20 10v11',
    benefit: 'Monitor public service delivery, track program outcomes, and report on citizen impact.',
  },
  {
    type: 'NGOs',
    icon: 'M12 2v20M2 12h20',
    benefit: 'Track program impact, manage donor reporting, and measure outcomes against goals.',
  },
  {
    type: 'Analysts',
    icon: 'M3 3v18h18M7 14l4-4 4 4 5-5',
    benefit: 'Build dashboards, run analyses, and generate reports without writing code.',
  },
  {
    type: 'Statisticians',
    icon: 'M9 12l2 2 4-4M21 12a9 9 0 11-18 0 9 9 0 0118 0z',
    benefit: 'Access statistical models, hypothesis testing, and reproducible analysis workflows.',
  },
];

export function CustomerTypes() {
  return (
    <section className="py-24 lg:py-32">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <Reveal className="mx-auto max-w-2xl text-center">
          <p className="text-sm font-semibold uppercase tracking-wider text-blue-600">Who Uses DataFlow</p>
          <h2 className="mt-3 text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
            Built for every role and organization
          </h2>
          <p className="mt-4 text-lg text-slate-600">
            From business leaders to researchers, DataFlow adapts to how each group works with data.
          </p>
        </Reveal>

        <div className="mt-16 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {customers.map((customer, i) => (
            <Reveal key={customer.type} delay={i * 80}>
              <div className="card-hover h-full rounded-2xl border border-slate-200 bg-white p-6">
                <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-slate-100 to-slate-200 text-slate-700">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="h-6 w-6">
                    <path d={customer.icon} />
                  </svg>
                </div>
                <h3 className="mt-4 text-base font-semibold text-slate-900">{customer.type}</h3>
                <p className="mt-2 text-sm leading-relaxed text-slate-600">{customer.benefit}</p>
              </div>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}
