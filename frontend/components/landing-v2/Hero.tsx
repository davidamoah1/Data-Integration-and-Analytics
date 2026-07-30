'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';

const kpiCards = [
  { label: 'Revenue', value: '$2.4M', change: '+12.5%', positive: true },
  { label: 'Active Users', value: '48,290', change: '+8.2%', positive: true },
  { label: 'Data Points', value: '1.2B', change: '+24.1%', positive: true },
];

const chartBars = [40, 65, 52, 78, 61, 89, 73, 95, 82, 67, 54, 71];

export function Hero() {
  const [mounted, setMounted] = useState(false);
  const [activeKpi, setActiveKpi] = useState(0);
  const [barHeights, setBarHeights] = useState<number[]>(chartBars.map(() => 0));

  useEffect(() => {
    setMounted(true);
    const timer = setTimeout(() => setBarHeights(chartBars), 300);
    const interval = setInterval(() => {
      setActiveKpi((prev) => (prev + 1) % kpiCards.length);
    }, 3000);
    return () => {
      clearTimeout(timer);
      clearInterval(interval);
    };
  }, []);

  return (
    <section className="relative overflow-hidden pt-32 pb-20 sm:pt-36 lg:pt-40 lg:pb-28">
      {/* Background */}
      <div className="absolute inset-0 -z-10 mesh-gradient" />
      <div className="absolute inset-0 -z-10 bg-dot-pattern opacity-40" />
      <div className="absolute -top-40 right-0 -z-10 h-[500px] w-[500px] rounded-full bg-blue-500/10 blur-[120px]" />
      <div className="absolute -bottom-40 left-0 -z-10 h-[400px] w-[400px] rounded-full bg-violet-500/10 blur-[100px]" />

      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="grid items-center gap-12 lg:grid-cols-2 lg:gap-16">
          {/* Left: Content */}
          <div className={mounted ? 'animate-slide-in-left' : 'opacity-0'}>
            {/* Badge */}
            <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white/80 px-4 py-1.5 text-sm font-medium text-slate-600 shadow-sm backdrop-blur-sm">
              <span className="flex h-2 w-2 rounded-full bg-emerald-500 animate-pulse-soft" />
              Trusted by organizations across 8 industries
            </div>

            {/* Headline */}
            <h1 className="text-4xl font-bold tracking-tight text-slate-900 sm:text-5xl lg:text-6xl">
              Transform Data Into{' '}
              <span className="gradient-text">Decisions.</span>
            </h1>

            {/* Subheadline */}
            <p className="mt-6 max-w-xl text-lg leading-relaxed text-slate-600">
              One platform for collecting, preparing, analyzing, visualizing, reporting, and presenting data across healthcare, education, business, government, research, and more.
            </p>

            {/* CTAs */}
            <div className="mt-8 flex flex-col gap-3 sm:flex-row">
              <Link
                href="/signup"
                className="inline-flex h-12 items-center justify-center rounded-xl bg-gradient-to-r from-blue-600 to-violet-600 px-7 text-base font-semibold text-white shadow-lg shadow-blue-600/25 transition-all hover:shadow-xl hover:shadow-blue-600/30 hover:brightness-110"
              >
                Start Free
                <svg className="ml-2 h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M5 12h14M13 5l7 7-7 7" />
                </svg>
              </Link>
              <Link
                href="/demo"
                className="inline-flex h-12 items-center justify-center rounded-xl border border-slate-300 bg-white px-7 text-base font-semibold text-slate-700 shadow-sm transition-all hover:border-slate-400 hover:bg-slate-50"
              >
                Book a Demo
              </Link>
            </div>

            {/* Trust indicators */}
            <div className="mt-10 flex items-center gap-6 text-sm text-slate-500">
              <div className="flex items-center gap-2">
                <svg className="h-4 w-4 text-emerald-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M22 11.08V12a10 10 0 11-5.93-9.14" />
                  <path d="M22 4L12 14.01l-3-3" />
                </svg>
                No credit card required
              </div>
              <div className="flex items-center gap-2">
                <svg className="h-4 w-4 text-emerald-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M22 11.08V12a10 10 0 11-5.93-9.14" />
                  <path d="M22 4L12 14.01l-3-3" />
                </svg>
                Free 14-day trial
              </div>
            </div>
          </div>

          {/* Right: Animated product showcase */}
          <div className={mounted ? 'animate-slide-in-right' : 'opacity-0'}>
            <div className="relative">
              {/* Browser frame */}
              <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-2xl shadow-slate-900/10">
                {/* Browser bar */}
                <div className="flex items-center gap-2 border-b border-slate-100 bg-slate-50 px-4 py-3">
                  <div className="flex gap-1.5">
                    <div className="h-3 w-3 rounded-full bg-red-400" />
                    <div className="h-3 w-3 rounded-full bg-amber-400" />
                    <div className="h-3 w-3 rounded-full bg-emerald-400" />
                  </div>
                  <div className="ml-3 flex-1 rounded-md bg-white px-3 py-1 text-xs text-slate-400 border border-slate-200">
                    app.dataflow.io/dashboard
                  </div>
                </div>

                {/* Dashboard content */}
                <div className="p-5">
                  {/* KPI cards */}
                  <div className="grid grid-cols-3 gap-3">
                    {kpiCards.map((kpi, i) => (
                      <div
                        key={kpi.label}
                        className={`rounded-xl border p-3 transition-all duration-500 ${
                          activeKpi === i
                            ? 'border-blue-300 bg-blue-50/50 shadow-md shadow-blue-100'
                            : 'border-slate-200 bg-white'
                        }`}
                      >
                        <p className="text-xs font-medium text-slate-500">{kpi.label}</p>
                        <p className="mt-1 text-lg font-bold text-slate-900">{kpi.value}</p>
                        <p className={`text-xs font-semibold ${kpi.positive ? 'text-emerald-600' : 'text-red-600'}`}>
                          {kpi.change}
                        </p>
                      </div>
                    ))}
                  </div>

                  {/* Chart */}
                  <div className="mt-4 rounded-xl border border-slate-200 p-4">
                    <div className="flex items-center justify-between">
                      <p className="text-sm font-semibold text-slate-700">Monthly Performance</p>
                      <div className="flex gap-1.5">
                        <span className="rounded-md bg-blue-100 px-2 py-0.5 text-xs font-medium text-blue-700">Revenue</span>
                        <span className="rounded-md bg-violet-100 px-2 py-0.5 text-xs font-medium text-violet-700">Growth</span>
                      </div>
                    </div>
                    <div className="mt-4 flex h-32 items-end gap-1.5">
                      {barHeights.map((h, i) => (
                        <div key={i} className="flex flex-1 flex-col gap-0.5">
                          <div
                            className="rounded-t bg-gradient-to-t from-blue-500 to-blue-400 transition-all duration-700 ease-out"
                            style={{ height: `${h}%` }}
                          />
                          <div
                            className="rounded-b bg-gradient-to-t from-violet-400 to-violet-300 transition-all duration-700 ease-out"
                            style={{ height: `${h * 0.4}%` }}
                          />
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Workflow animation */}
                  <div className="mt-4 flex items-center gap-2 rounded-xl border border-slate-200 bg-slate-50/50 p-3">
                    <div className="flex items-center gap-2 text-xs font-medium text-slate-600">
                      <div className="flex h-6 w-6 items-center justify-center rounded-lg bg-blue-100 text-blue-600">
                        <svg className="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M17 8l-5-5-5 5M12 3v12" />
                        </svg>
                      </div>
                      <span>Upload</span>
                    </div>
                    <div className="h-px flex-1 bg-gradient-to-r from-blue-300 to-violet-300 relative overflow-hidden">
                      <div className="absolute inset-0 animate-flow-right bg-gradient-to-r from-transparent via-blue-500 to-transparent" />
                    </div>
                    <div className="flex items-center gap-2 text-xs font-medium text-slate-600">
                      <span>Process</span>
                      <div className="flex h-6 w-6 items-center justify-center rounded-lg bg-violet-100 text-violet-600">
                        <svg className="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <path d="M3 3v18h18" />
                          <path d="M7 14l4-4 4 4 5-5" />
                        </svg>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Floating report card */}
              <div className="absolute -bottom-6 -left-6 hidden rounded-xl border border-slate-200 bg-white p-4 shadow-xl sm:block animate-float">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-emerald-100">
                    <svg className="h-5 w-5 text-emerald-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" />
                      <path d="M14 2v6h6M16 13H8M16 17H8M10 9H8" />
                    </svg>
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-slate-900">Report Generated</p>
                    <p className="text-xs text-slate-500">Q4 Executive Summary</p>
                  </div>
                </div>
              </div>

              {/* Floating dataset card */}
              <div className="absolute -top-4 -right-4 hidden rounded-xl border border-slate-200 bg-white p-3 shadow-xl sm:block animate-bounce-subtle">
                <div className="flex items-center gap-2">
                  <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-100">
                    <svg className="h-4 w-4 text-blue-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <ellipse cx="12" cy="5" rx="9" ry="3" />
                      <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3" />
                      <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5" />
                    </svg>
                  </div>
                  <div>
                    <p className="text-xs font-semibold text-slate-900">Dataset Uploaded</p>
                    <p className="text-xs text-slate-500">12,847 records</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
