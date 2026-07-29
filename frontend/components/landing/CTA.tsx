import Link from 'next/link';
import { ArrowRight } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Reveal } from './Reveal';

export function CTA() {
  return (
    <section className="relative overflow-hidden bg-gradient-to-br from-blue-600 via-blue-600 to-indigo-700 py-24">
      <div className="absolute inset-0 -z-10 animate-gradient bg-gradient-to-br from-blue-500 via-indigo-600 to-blue-700 opacity-90" />
      <div className="absolute -left-20 -top-20 h-72 w-72 rounded-full bg-white/10 blur-3xl" />
      <div className="absolute -bottom-24 -right-10 h-80 w-80 rounded-full bg-indigo-400/20 blur-3xl" />

      <Reveal className="relative mx-auto max-w-4xl px-6 text-center">
        <h2 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
          Turn your data into knowledge.
        </h2>
        <p className="mx-auto mt-4 max-w-xl text-lg text-blue-100">
          Join businesses, researchers, and organizations already making better
          decisions with DataFlow.
        </p>
        <div className="mt-8 flex flex-col items-center justify-center gap-4 sm:flex-row">
          <Link href="/signup">
            <Button size="lg" variant="secondary" className="gap-2 bg-white px-8 text-blue-700 shadow-lg shadow-blue-900/20 transition-transform hover:-translate-y-0.5 hover:bg-blue-50">
              Get Started <ArrowRight size={18} />
            </Button>
          </Link>
          <a href="mailto:hello@dataflow.io?subject=Demo%20Request">
            <Button size="lg" variant="ghost" className="border border-blue-300 px-8 text-white transition-transform hover:-translate-y-0.5 hover:bg-blue-500">
              Request Demo
            </Button>
          </a>
        </div>
      </Reveal>
    </section>
  );
}
