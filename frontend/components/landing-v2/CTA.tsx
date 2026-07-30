'use client';

import Link from 'next/link';
import { Reveal } from '@/components/landing/Reveal';

export function CTA() {
  return (
    <section className="py-24 lg:py-32">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <Reveal>
          <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 px-8 py-16 text-center sm:px-16 lg:py-24">
            {/* Background effects */}
            <div className="absolute -top-40 -left-40 h-80 w-80 rounded-full bg-blue-500/20 blur-3xl" />
            <div className="absolute -bottom-40 -right-40 h-80 w-80 rounded-full bg-violet-500/20 blur-3xl" />
            <div className="absolute inset-0 bg-dot-pattern opacity-10" />

            <div className="relative">
              <h2 className="text-3xl font-bold tracking-tight text-white sm:text-4xl lg:text-5xl">
                Turn your data into{' '}
                <span className="bg-gradient-to-r from-blue-400 to-violet-400 bg-clip-text text-transparent">
                  meaningful decisions.
                </span>
              </h2>
              <p className="mx-auto mt-6 max-w-2xl text-lg text-slate-300">
                Join organizations across healthcare, education, business, government, and research who use DataFlow to transform how they work with data.
              </p>

              <div className="mt-10 flex flex-col items-center justify-center gap-3 sm:flex-row">
                <Link
                  href="/signup"
                  className="inline-flex h-12 items-center justify-center rounded-xl bg-white px-8 text-base font-semibold text-slate-900 shadow-lg transition-all hover:shadow-xl hover:bg-slate-100"
                >
                  Start Free
                  <svg className="ml-2 h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M5 12h14M13 5l7 7-7 7" />
                  </svg>
                </Link>
                <Link
                  href="/demo"
                  className="inline-flex h-12 items-center justify-center rounded-xl border border-white/20 bg-white/5 px-8 text-base font-semibold text-white backdrop-blur-sm transition-all hover:bg-white/10"
                >
                  Request Demo
                </Link>
              </div>

              <p className="mt-6 text-sm text-slate-400">
                No credit card required &middot; Free 14-day trial &middot; Cancel anytime
              </p>
            </div>
          </div>
        </Reveal>
      </div>
    </section>
  );
}
