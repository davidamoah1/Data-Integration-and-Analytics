import type { Metadata } from 'next';
import Link from 'next/link';
import { Navbar } from '@/components/landing/Navbar';
import { Footer } from '@/components/landing/Footer';
import { Features } from '@/components/landing/Features';
import { Button } from '@/components/ui/Button';
import { ArrowRight } from 'lucide-react';

export const metadata: Metadata = {
  title: 'Features — DataFlow',
  description: 'Explore the powerful capabilities of DataFlow — smart data preparation, analytics workspace, industry dashboards, statistical analysis, predictive analysis, and professional reports.',
};

export default function FeaturesPage() {
  return (
    <main className="min-h-screen bg-background">
      <Navbar />

      <section className="mx-auto max-w-4xl px-4 pt-32 pb-12 text-center md:px-6">
        <span className="text-sm font-semibold uppercase tracking-wider text-blue-600">Capabilities</span>
        <h1 className="mt-3 text-4xl font-bold tracking-tight text-slate-900 sm:text-5xl">
          Everything you need, built in
        </h1>
        <p className="mx-auto mt-4 max-w-2xl text-lg text-slate-600">
          Powerful capabilities that work together, so your team spends less time
          wrangling data and more time making decisions.
        </p>
        <div className="mt-8">
          <Link href="/signup">
            <Button size="lg" className="gap-2">
              Get Started Free <ArrowRight size={18} />
            </Button>
          </Link>
        </div>
      </section>

      <Features />

      <Footer />
    </main>
  );
}
