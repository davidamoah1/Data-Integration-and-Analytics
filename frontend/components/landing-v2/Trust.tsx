'use client';

import { Shield, FileCheck, Users, Lock, TrendingUp } from 'lucide-react';
import { Reveal } from '@/components/landing/Reveal';
import { AnimatedCounter } from './AnimatedCounter';

const trustFeatures = [
  {
    title: 'Enterprise Security',
    description: 'Data encrypted in transit and at rest with industry-standard protocols.',
    icon: Shield,
  },
  {
    title: 'Audit Trails',
    description: 'Every action is logged with user, timestamp, and context for full traceability.',
    icon: FileCheck,
  },
  {
    title: 'Role-Based Access',
    description: 'Granular permissions ensure users only see and act on data they are authorized to access.',
    icon: Users,
  },
  {
    title: 'Data Privacy',
    description: 'Tenant isolation and data segregation keep each organization\'s data separate and secure.',
    icon: Lock,
  },
  {
    title: 'Scalable Architecture',
    description: 'Built to handle growing data volumes and user counts without performance degradation.',
    icon: TrendingUp,
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
          <p className="text-sm font-semibold uppercase tracking-wider text-primary">Trust & Security</p>
          <h2 className="mt-3 text-3xl font-bold tracking-tight text-foreground sm:text-4xl">
            Enterprise-ready from day one
          </h2>
          <p className="mt-4 text-lg text-muted-foreground">
            Built with security, privacy, and reliability as foundational principles.
          </p>
        </Reveal>

        {/* Stats */}
        <Reveal className="mt-12" delay={200}>
          <div className="grid grid-cols-2 gap-4 rounded-lg border border-border bg-card p-8 lg:grid-cols-4">
            {stats.map((stat) => (
              <div key={stat.label} className="text-center">
                <p className="text-3xl font-bold text-foreground sm:text-4xl">
                  <AnimatedCounter value={stat.value} suffix={stat.suffix} decimals={stat.decimals} />
                </p>
                <p className="mt-1 text-sm text-muted-foreground">{stat.label}</p>
              </div>
            ))}
          </div>
        </Reveal>

        {/* Trust features */}
        <div className="mt-12 grid gap-5 sm:grid-cols-2 lg:grid-cols-5">
          {trustFeatures.map((feature, i) => {
            const Icon = feature.icon;
            return (
              <Reveal key={feature.title} delay={i * 80}>
                <div className="card-hover h-full rounded-md border border-border bg-card p-6">
                  <div className="flex h-10 w-10 items-center justify-center rounded-md bg-muted text-primary">
                    <Icon className="h-5 w-5" />
                  </div>
                  <h3 className="mt-4 text-sm font-semibold text-foreground">{feature.title}</h3>
                  <p className="mt-2 text-xs leading-relaxed text-muted-foreground">{feature.description}</p>
                </div>
              </Reveal>
            );
          })}
        </div>
      </div>
    </section>
  );
}
