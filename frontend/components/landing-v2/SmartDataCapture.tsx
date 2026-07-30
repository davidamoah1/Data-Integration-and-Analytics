'use client';

import { useEffect, useState } from 'react';
import { Reveal } from '@/components/landing/Reveal';

const steps = [
  { label: 'Paper Form', icon: 'M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z M14 2v6h6 M16 13H8 M16 17H8 M10 9H8' },
  { label: 'Phone Camera', icon: 'M23 19a2 2 0 01-2 2H3a2 2 0 01-2-2V8a2 2 0 012-2h4l2-3h6l2 3h4a2 2 0 012 2z M12 17a4 4 0 100-8 4 4 0 000 8z' },
  { label: 'Data Capture', icon: 'M3 3v18h18 M9 9h6 M9 13h6 M9 17h4' },
  { label: 'Validation', icon: 'M22 11.08V12a10 10 0 11-5.93-9.14 M22 4L12 14.01l-3-3' },
  { label: 'Review', icon: 'M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z M12 9a3 3 0 100 6 3 3 0 000-6z' },
  { label: 'Structured Data', icon: 'M3 3h18v18H3z M3 9h18 M3 15h18 M9 3v18 M15 3v18' },
  { label: 'Dashboard', icon: 'M3 3v18h18 M7 14l4-4 4 4 5-5' },
];

export function SmartDataCapture() {
  const [active, setActive] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setActive((prev) => (prev + 1) % steps.length);
    }, 2200);
    return () => clearInterval(interval);
  }, []);

  return (
    <section className="bg-slate-50/50 py-24 lg:py-32">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <Reveal className="mx-auto max-w-2xl text-center">
          <p className="text-sm font-semibold uppercase tracking-wider text-blue-600">Smart Data Capture</p>
          <h2 className="mt-3 text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
            Capture data from existing documents with minimal manual work
          </h2>
          <p className="mt-4 text-lg text-slate-600">
            Turn paper forms, printed records, and scanned documents into clean, structured data — ready for analysis.
          </p>
        </Reveal>

        {/* Desktop: horizontal flow */}
        <Reveal className="mt-16 hidden lg:block" delay={200}>
          <div className="relative">
            <div className="absolute top-10 left-0 right-0 h-0.5 bg-slate-200" />
            <div
              className="absolute top-10 left-0 h-0.5 bg-gradient-to-r from-blue-500 to-violet-500 transition-all duration-500"
              style={{ width: `${(active / (steps.length - 1)) * 100}%` }}
            />
            <div className="relative flex justify-between">
              {steps.map((step, i) => (
                <div key={step.label} className="flex flex-col items-center" style={{ width: `${100 / steps.length}%` }}>
                  <div className={`flex h-10 w-10 items-center justify-center rounded-full border-2 transition-all duration-500 ${
                    i <= active
                      ? 'border-blue-500 bg-blue-500 text-white shadow-lg shadow-blue-500/30'
                      : 'border-slate-300 bg-white text-slate-400'
                  }`}>
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4">
                      <path d={step.icon} />
                    </svg>
                  </div>
                  <span className={`mt-3 text-xs font-medium transition-colors ${i <= active ? 'text-slate-900' : 'text-slate-400'}`}>
                    {step.label}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </Reveal>

        {/* Mobile: vertical */}
        <Reveal className="mt-12 lg:hidden" delay={200}>
          <div className="space-y-1">
            {steps.map((step, i) => (
              <div key={step.label} className="flex items-center gap-4">
                <div className="flex flex-col items-center">
                  <div className={`flex h-10 w-10 items-center justify-center rounded-full border-2 transition-all ${
                    i <= active ? 'border-blue-500 bg-blue-500 text-white' : 'border-slate-300 bg-white text-slate-400'
                  }`}>
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4">
                      <path d={step.icon} />
                    </svg>
                  </div>
                  {i < steps.length - 1 && <div className={`h-8 w-0.5 ${i < active ? 'bg-blue-500' : 'bg-slate-200'}`} />}
                </div>
                <span className={`text-sm font-medium ${i <= active ? 'text-slate-900' : 'text-slate-400'}`}>{step.label}</span>
              </div>
            ))}
          </div>
        </Reveal>

        {/* Demo preview */}
        <Reveal className="mt-12" delay={300}>
          <div className="mx-auto max-w-3xl overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-xl">
            <div className="grid sm:grid-cols-2">
              {/* Before: paper form */}
              <div className="border-b border-slate-200 p-6 sm:border-b-0 sm:border-r">
                <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">Input</p>
                <div className="mt-4 rounded-lg border border-slate-200 bg-slate-50 p-4">
                  <div className="space-y-3">
                    <div>
                      <div className="h-3 w-20 rounded bg-slate-300" />
                      <div className="mt-1 h-5 w-32 rounded bg-slate-200" />
                    </div>
                    <div>
                      <div className="h-3 w-16 rounded bg-slate-300" />
                      <div className="mt-1 h-5 w-24 rounded bg-slate-200" />
                    </div>
                    <div>
                      <div className="h-3 w-24 rounded bg-slate-300" />
                      <div className="mt-1 h-5 w-28 rounded bg-slate-200" />
                    </div>
                  </div>
                </div>
                <p className="mt-3 text-center text-xs text-slate-500">Paper document</p>
              </div>

              {/* After: structured data */}
              <div className="p-6">
                <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">Output</p>
                <div className="mt-4 space-y-3">
                  {[
                    { field: 'Patient Name', value: 'Kwame Mensah', confidence: 98 },
                    { field: 'Date of Birth', value: '1985-03-15', confidence: 95 },
                    { field: 'Diagnosis', value: 'Hypertension', confidence: 92 },
                  ].map((row, i) => (
                    <div key={row.field} className={`flex items-center justify-between rounded-lg border p-3 transition-all ${active >= 5 ? 'border-emerald-200 bg-emerald-50/50' : 'border-slate-200'}`} style={{ transitionDelay: `${i * 100}ms` }}>
                      <div>
                        <p className="text-xs text-slate-500">{row.field}</p>
                        <p className="text-sm font-semibold text-slate-900">{row.value}</p>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="h-1.5 w-16 rounded-full bg-slate-200">
                          <div className="h-1.5 rounded-full bg-emerald-500" style={{ width: active >= 5 ? `${row.confidence}%` : '0%', transitionDelay: `${i * 100}ms` }} />
                        </div>
                        <span className="text-xs font-bold text-emerald-600">{row.confidence}%</span>
                      </div>
                    </div>
                  ))}
                </div>
                <p className="mt-3 text-center text-xs text-slate-500">Structured, validated data</p>
              </div>
            </div>
          </div>
        </Reveal>
      </div>
    </section>
  );
}
