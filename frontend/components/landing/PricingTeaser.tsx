import { Sparkles } from 'lucide-react';
import { Reveal } from './Reveal';

export function PricingTeaser() {
  return (
    <section id="pricing" className="relative overflow-hidden bg-slate-50 py-20">
      <div className="absolute inset-0 -z-10 bg-grid-slate opacity-30 [mask-image:radial-gradient(ellipse_50%_60%_at_50%_50%,#000_30%,transparent_100%)]" />
      <Reveal className="relative mx-auto max-w-3xl px-6 text-center">
        <div className="mx-auto mb-4 inline-flex h-12 w-12 items-center justify-center rounded-full bg-gradient-to-br from-blue-600 to-indigo-500 text-white shadow-md shadow-blue-500/30">
          <Sparkles size={22} />
        </div>
        <h2 className="text-2xl font-bold text-slate-900">Pricing — Coming Soon</h2>
        <p className="mt-3 text-slate-600">
          We&apos;re finalizing flexible plans for businesses, researchers, and institutions
          of every size. Get started for free today and we&apos;ll notify you when pricing launches.
        </p>
      </Reveal>
    </section>
  );
}
