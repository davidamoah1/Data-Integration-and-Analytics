'use client';

import Link from 'next/link';
import { ArrowRight } from 'lucide-react';
import { Reveal } from '@/components/landing/Reveal';

export function CTA() {
  return (
    <section className="py-24 lg:py-32">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <Reveal>
          <div className="rounded-lg border border-border bg-card px-8 py-16 text-center sm:px-16 lg:py-20">
            <div className="relative">
              <h2 className="text-3xl font-bold tracking-tight text-foreground sm:text-4xl">
                Start working with your data today.
              </h2>
              <p className="mx-auto mt-6 max-w-2xl text-lg text-muted-foreground">
                Join organizations across healthcare, education, business, government, and research who use DataFlow to transform how they work with data.
              </p>

              <div className="mt-10 flex flex-col items-center justify-center gap-3 sm:flex-row">
                <Link
                  href="/signup"
                  className="inline-flex h-11 items-center justify-center rounded-md bg-primary px-8 text-sm font-semibold text-primary-foreground transition-colors hover:bg-primary/90"
                >
                  Start Free
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Link>
                <Link
                  href="/demo"
                  className="inline-flex h-11 items-center justify-center rounded-md border border-border bg-background px-8 text-sm font-semibold text-foreground transition-colors hover:bg-accent"
                >
                  Request Demo
                </Link>
              </div>

              <p className="mt-6 text-sm text-muted-foreground">
                No credit card required · Free 14-day trial · Cancel anytime
              </p>
            </div>
          </div>
        </Reveal>
      </div>
    </section>
  );
}
