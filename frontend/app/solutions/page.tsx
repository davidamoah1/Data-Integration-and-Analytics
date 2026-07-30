import type { Metadata } from 'next';
import Link from 'next/link';
import { Navbar } from '@/components/landing/Navbar';
import { Footer } from '@/components/landing/Footer';
import { Solution } from '@/components/landing/Solution';
import { Button } from '@/components/ui/Button';
import { ArrowRight } from 'lucide-react';

export const metadata: Metadata = {
  title: 'Solutions — DataFlow',
  description: 'One platform for your entire data journey — from raw files to finished reports, everything you need lives in a single, integrated workspace.',
};

export default function SolutionsPage() {
  return (
    <main className="min-h-screen bg-background">
      <Navbar />

      <section className="mx-auto max-w-4xl px-4 pt-32 pb-12 text-center md:px-6">
        <span className="text-sm font-semibold uppercase tracking-wider text-blue-600">The solution</span>
        <h1 className="mt-3 text-4xl font-bold tracking-tight text-slate-900 sm:text-5xl">
          One platform for your entire data journey
        </h1>
        <p className="mx-auto mt-4 max-w-2xl text-lg text-slate-600">
          From raw files to finished reports — everything you need lives in a single,
          integrated workspace.
        </p>
        <div className="mt-8">
          <Link href="/signup">
            <Button size="lg" className="gap-2">
              Get Started Free <ArrowRight size={18} />
            </Button>
          </Link>
        </div>
      </section>

      <Solution />

      <Footer />
    </main>
  );
}
