import { Quote } from 'lucide-react';
import { Reveal } from './Reveal';

const placeholders = [1, 2, 3];

export function Testimonials() {
  return (
    <section className="bg-white py-24">
      <div className="mx-auto max-w-7xl px-6">
        <Reveal className="mx-auto max-w-2xl text-center">
          <span className="text-sm font-semibold uppercase tracking-wider text-blue-600">Testimonials</span>
          <h2 className="mt-3 text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
            What our early users say
          </h2>
          <p className="mt-4 text-lg text-slate-600">
            Testimonials from businesses, researchers, and institutions will appear here.
          </p>
        </Reveal>

        <div className="mt-14 grid grid-cols-1 gap-6 md:grid-cols-3">
          {placeholders.map((i) => (
            <Reveal key={i} delay={i * 80}>
              <div className="flex h-full flex-col justify-between rounded-2xl border border-dashed border-slate-300 bg-slate-50/60 p-6 transition-colors hover:border-slate-400 hover:bg-slate-50">
                <Quote className="mb-4 text-slate-300" size={28} />
                <p className="text-sm italic text-slate-400">
                  Customer testimonial coming soon.
                </p>
                <div className="mt-6 flex items-center gap-3">
                  <div className="h-10 w-10 rounded-full bg-slate-200" />
                  <div>
                    <p className="text-sm font-medium text-slate-400">Organization name</p>
                    <p className="text-xs text-slate-400">Role, Industry</p>
                  </div>
                </div>
              </div>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}
