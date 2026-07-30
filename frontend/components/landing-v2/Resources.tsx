'use client';

import Link from 'next/link';
import { Reveal } from '@/components/landing/Reveal';

const resources = [
  {
    title: 'Documentation',
    description: 'Comprehensive guides, API references, and tutorials.',
    icon: 'M4 19.5A2.5 2.5 0 016.5 17H20M6.5 2H20v20H6.5A2.5 2.5 0 014 19.5v-15A2.5 2.5 0 016.5 2z',
    href: '/docs',
  },
  {
    title: 'Learning Center',
    description: 'Step-by-step courses on data analysis and reporting.',
    icon: 'M22 10v6M2 10l10-5 10 5-10 5z M6 12v5c3 3 9 3 12 0v-5',
    href: '/learn',
  },
  {
    title: 'Templates',
    description: 'Pre-built templates for dashboards, reports, and workflows.',
    icon: 'M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z M14 2v6h6',
    href: '/templates',
  },
  {
    title: 'Example Projects',
    description: 'Real-world projects showing how organizations use DataFlow.',
    icon: 'M3 3v18h18M7 14l4-4 4 4 5-5',
    href: '/examples',
  },
  {
    title: 'Community',
    description: 'Connect with other users, share insights, and get help.',
    icon: 'M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2M9 11a4 4 0 100-8 4 4 0 000 8z M23 21v-2a4 4 0 00-3-3.87M16 3.13a4 4 0 010 7.75',
    href: '/community',
  },
  {
    title: 'API Reference',
    description: 'Full REST API documentation for developers and integrators.',
    icon: 'M16 18l6-6-6-6M8 6l-6 6 6 6',
    href: '/api-reference',
  },
];

export function Resources() {
  return (
    <section className="bg-slate-50/50 py-24 lg:py-32">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <Reveal className="mx-auto max-w-2xl text-center">
          <p className="text-sm font-semibold uppercase tracking-wider text-blue-600">Resources</p>
          <h2 className="mt-3 text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
            Everything you need to succeed
          </h2>
          <p className="mt-4 text-lg text-slate-600">
            Documentation, learning materials, and community support to help you get the most from DataFlow.
          </p>
        </Reveal>

        <div className="mt-16 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {resources.map((resource, i) => (
            <Reveal key={resource.title} delay={i * 80}>
              <Link
                href={resource.href}
                className="card-hover group flex h-full items-start gap-4 rounded-2xl border border-slate-200 bg-white p-6"
              >
                <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-blue-50 to-violet-50 text-blue-600">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-5 w-5">
                    <path d={resource.icon} />
                  </svg>
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <h3 className="text-base font-semibold text-slate-900">{resource.title}</h3>
                    <svg className="h-4 w-4 text-slate-400 transition-transform group-hover:translate-x-1 group-hover:text-blue-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M5 12h14M13 5l7 7-7 7" />
                    </svg>
                  </div>
                  <p className="mt-1.5 text-sm leading-relaxed text-slate-600">{resource.description}</p>
                </div>
              </Link>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}
