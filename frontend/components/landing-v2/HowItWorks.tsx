'use client';

import { useEffect, useState } from 'react';
import { Reveal } from '@/components/landing/Reveal';

const steps = [
  { label: 'Upload', icon: 'M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M17 8l-5-5-5 5M12 3v12' },
  { label: 'Prepare', icon: 'M14.7 6.3a1 1 0 010 1.4l-1 1-2-2 1-1a1 1 0 011.4 0l.6.6zM11.7 9.3l-6 6L4 20l4.7-1.7 6-6-3-3z' },
  { label: 'Validate', icon: 'M22 11.08V12a10 10 0 11-5.93-9.14M22 4L12 14.01l-3-3' },
  { label: 'Analyze', icon: 'M3 3v18h18M7 14l4-4 4 4 5-5' },
  { label: 'Visualize', icon: 'M18 20V10M12 20V4M6 20v-6' },
  { label: 'Present', icon: 'M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z M14 2v6h6' },
  { label: 'Decide', icon: 'M9 12l2 2 4-4M21 12a9 9 0 11-18 0 9 9 0 0118 0z' },
];

export function HowItWorks() {
  const [activeStep, setActiveStep] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setActiveStep((prev) => (prev + 1) % steps.length);
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  return (
    <section className="py-24 lg:py-32">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <Reveal className="mx-auto max-w-2xl text-center">
          <p className="text-sm font-semibold uppercase tracking-wider text-blue-600">How It Works</p>
          <h2 className="mt-3 text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
            One guided workflow from start to finish
          </h2>
          <p className="mt-4 text-lg text-slate-600">
            From raw data to confident decisions in seven steps — all within a single platform.
          </p>
        </Reveal>

        {/* Desktop: horizontal flow */}
        <Reveal className="mt-16 hidden lg:block" delay={200}>
          <div className="relative">
            {/* Connecting line */}
            <div className="absolute top-12 left-0 right-0 h-0.5 bg-slate-200" />
            <div
              className="absolute top-12 left-0 h-0.5 bg-gradient-to-r from-blue-500 to-violet-500 transition-all duration-500"
              style={{ width: `${(activeStep / (steps.length - 1)) * 100}%` }}
            />

            <div className="relative flex justify-between">
              {steps.map((step, i) => (
                <div key={step.label} className="flex flex-col items-center" style={{ width: `${100 / steps.length}%` }}>
                  <div
                    className={`flex h-12 w-12 items-center justify-center rounded-full border-2 transition-all duration-500 ${
                      i <= activeStep
                        ? 'border-blue-500 bg-blue-500 text-white shadow-lg shadow-blue-500/30'
                        : 'border-slate-300 bg-white text-slate-400'
                    }`}
                  >
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-5 w-5">
                      <path d={step.icon} />
                    </svg>
                  </div>
                  <span className={`mt-3 text-sm font-medium transition-colors ${i <= activeStep ? 'text-slate-900' : 'text-slate-400'}`}>
                    {step.label}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </Reveal>

        {/* Mobile: vertical flow */}
        <Reveal className="mt-12 lg:hidden" delay={200}>
          <div className="space-y-1">
            {steps.map((step, i) => (
              <div key={step.label} className="flex items-center gap-4">
                <div className="flex flex-col items-center">
                  <div className={`flex h-10 w-10 items-center justify-center rounded-full border-2 transition-all ${
                    i <= activeStep ? 'border-blue-500 bg-blue-500 text-white' : 'border-slate-300 bg-white text-slate-400'
                  }`}>
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4">
                      <path d={step.icon} />
                    </svg>
                  </div>
                  {i < steps.length - 1 && <div className={`h-8 w-0.5 ${i < activeStep ? 'bg-blue-500' : 'bg-slate-200'}`} />}
                </div>
                <span className={`text-sm font-medium ${i <= activeStep ? 'text-slate-900' : 'text-slate-400'}`}>{step.label}</span>
              </div>
            ))}
          </div>
        </Reveal>
      </div>
    </section>
  );
}
