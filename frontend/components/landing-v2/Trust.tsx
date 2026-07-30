'use client';

import { Reveal } from '@/components/landing/Reveal';
import { AnimatedCounter } from './AnimatedCounter';

const trustFeatures = [
  {
    title: 'Enterprise Security',
    description: 'Data encrypted in transit and at rest with industry-standard protocols.',
    icon: 'M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z',
  },
  {
    title: 'Audit Trails',
    description: 'Every action is logged with user, timestamp, and context for full traceability.',
    icon: 'M9 11l3 3L22 4M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11',
  },
  {
    title: 'Role-Based Access',
    description: 'Granular permissions ensure users only see and act on data they are authorized to access.',
    icon: 'M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2M12 11a4 4 0 100-8 4 4 0 000 8z',
  },
  {
    title: 'Data Privacy',
    description: 'Tenant isolation and data segregation keep each organization\'s data separate and secure.',
    icon: 'M12 2v20M2 12h20',
  },
  {
    title: 'Scalable Architecture',
    description: 'Built to handle growing data volumes and user counts without performance degradation.',
    icon: 'M3 3v18h18M7 14l4-4 4 4 5-5',
  },
];

const stats = [
  { value: 99.9, suffix: '%', label: 'Uptime', decimals: 1 },
  { value: 8, suffix: '', label: 'Industries served', decimals: 0 },
  { value: 20, suffix: '+', label: 'Data connectors', decimals: 0 },
  { value: 5, suffix: '', label: 'Report formats', decimals: 0 },
];

export function Trust() {
  return (
    <section className="py-24 lg:py-32">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <Reveal className="mx-auto max-w-2xl text-center">
          <p className="text-sm font-semibold uppercase tracking-wider text-blue-600">Trust & Security</p>
          <h2 className="mt-3 text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
            Enterprise-ready from day one
          </h2>
          <p className="mt-4 text-lg text-slate-600">
            Built with security, privacy, and reliability as foundational principles.
          </p>
        </Reveal>

        {/* Stats */}
        <Reveal className="mt-12" delay={200}>
          <div className="grid grid-cols-2 gap-4 rounded-2xl border border-slate-200 bg-white p-8 lg:grid-cols-4">
            {stats.map((stat) => (
              <div key={stat.label} className="text-center">
                <p className="text-3xl font-bold gradient-text sm:text-4xl">
                  <AnimatedCounter value={stat.value} suffix={stat.suffix} decimals={stat.decimals} />
                </p>
                <p className="mt-1 text-sm text-slate-500">{stat.label}</p>
              </div>
            ))}
          </div>
        </Reveal>

        {/* Trust features */}
        <div className="mt-12 grid gap-5 sm:grid-cols-2 lg:grid-cols-5">
          {trustFeatures.map((feature, i) => (
            <Reveal key={feature.title} delay={i * 80}>
              <div className="card-hover h-full rounded-2xl border border-slate-200 bg-white p-6">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-50 text-blue-600">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-5 w-5">
                    <path d={feature.icon} />
                  </svg>
                </div>
                <h3 className="mt-4 text-sm font-semibold text-slate-900">{feature.title}</h3>
                <p className="mt-2 text-xs leading-relaxed text-slate-600">{feature.description}</p>
              </div>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}
