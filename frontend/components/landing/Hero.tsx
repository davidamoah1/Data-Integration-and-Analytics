import Link from 'next/link';
import { ArrowRight, TrendingUp, BarChart3, PieChart } from 'lucide-react';
import { Button } from '@/components/ui/Button';

export function Hero() {
  return (
    <section className="relative overflow-hidden bg-slate-950 pt-28 pb-20 md:pt-36 md:pb-24">
      {/* Network mesh background image - hidden on mobile for performance */}
      <div
        className="absolute inset-x-0 top-0 -z-20 hidden h-[700px] bg-cover bg-center md:block"
        style={{ backgroundImage: 'url(/hero-bg.jpg)' }}
      />

      {/* Floating decorative blobs */}
      <div className="absolute left-[10%] top-[20%] -z-10 h-72 w-72 rounded-full bg-blue-500/10 blur-3xl animate-pulse-glow" />
      <div className="absolute right-[15%] top-[30%] -z-10 h-96 w-96 rounded-full bg-indigo-500/10 blur-3xl animate-pulse-glow" style={{ animationDelay: '2s' }} />
      <div className="absolute left-[40%] bottom-[10%] -z-10 h-80 w-80 rounded-full bg-purple-500/8 blur-3xl animate-pulse-glow" style={{ animationDelay: '4s' }} />

      <div className="absolute inset-x-0 bottom-0 -z-10 h-40 bg-gradient-to-b from-transparent to-white" />

      <div className="relative mx-auto max-w-7xl px-4 md:px-6">
        <div className="mx-auto max-w-3xl text-center">
          <div className="animate-fade-in-up mb-6 inline-flex items-center gap-2 rounded-full border border-blue-400/30 bg-blue-500/10 px-4 py-1.5 text-sm font-medium text-blue-300 shadow-sm shadow-blue-900/30 backdrop-blur-sm">
            <span className="relative flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-blue-400 opacity-75" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-blue-400" />
            </span>
            Trusted analytics for businesses, researchers &amp; institutions
          </div>

          <h1
            className="animate-fade-in-up text-4xl font-bold tracking-tight text-white sm:text-5xl lg:text-6xl"
            style={{ animationDelay: '80ms' }}
          >
            Transform Your Data Into{' '}
            <span className="bg-gradient-to-r from-blue-400 via-blue-300 to-indigo-300 bg-clip-text text-transparent">
              Meaningful Decisions
            </span>
          </h1>

          <p
            className="animate-fade-in-up mx-auto mt-6 max-w-2xl text-lg leading-relaxed text-slate-300"
            style={{ animationDelay: '160ms' }}
          >
            Easier than Excel. More powerful than traditional BI. DataFlow guides you
            through complete workflows — from raw data to professional reports — in minutes, not hours.
          </p>

          <div
            className="animate-fade-in-up mt-10 flex flex-col items-center justify-center gap-4 sm:flex-row"
            style={{ animationDelay: '240ms' }}
          >
            <Link href="/signup">
              <Button size="lg" className="gap-2 px-8 shadow-lg shadow-blue-600/25 transition-transform hover:-translate-y-0.5">
                Get Started Free <ArrowRight size={18} />
              </Button>
            </Link>
            <a href="#features">
              <Button size="lg" variant="outline" className="border-white/20 bg-white/5 px-8 text-white transition-transform hover:-translate-y-0.5 hover:bg-white/10 hover:text-white">
                Explore Features
              </Button>
            </a>
          </div>

          <div
            className="animate-fade-in-up mt-8 flex items-center justify-center gap-6 text-xs font-medium text-slate-400"
            style={{ animationDelay: '320ms' }}
          >
            <span>No credit card required</span>
            <span className="h-1 w-1 rounded-full bg-slate-600" />
            <span>Free to get started</span>
            <span className="h-1 w-1 rounded-full bg-slate-600" />
            <span>Cancel anytime</span>
          </div>
        </div>

        {/* Dashboard preview mockup */}
        <div className="animate-fade-in-up mx-auto mt-16 max-w-5xl" style={{ animationDelay: '400ms' }}>
          {/* Glow behind mockup */}
          <div className="absolute left-1/2 top-1/2 -z-10 h-[400px] w-[600px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-blue-500/10 blur-3xl" />
          <div className="group rounded-2xl border border-slate-200 bg-white p-2 shadow-2xl shadow-slate-300/50 ring-1 ring-slate-900/5 transition-all duration-500 hover:shadow-blue-200/50 hover:ring-blue-200/50">
            <div className="rounded-xl bg-slate-50 p-6">
              {/* Fake window bar */}
              <div className="mb-4 flex items-center gap-2">
                <div className="h-2.5 w-2.5 rounded-full bg-red-400" />
                <div className="h-2.5 w-2.5 rounded-full bg-yellow-400" />
                <div className="h-2.5 w-2.5 rounded-full bg-green-400" />
                <span className="ml-3 text-xs font-medium text-slate-400">
                  DataFlow — Analytics Workspace
                </span>
              </div>

              <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
                {/* KPI cards */}
                {[
                  { label: 'Revenue Growth', value: '+24.8%', icon: TrendingUp, color: 'text-green-600 bg-green-50' },
                  { label: 'Active Records', value: '128,450', icon: BarChart3, color: 'text-blue-600 bg-blue-50' },
                  { label: 'Data Quality', value: '98.2%', icon: PieChart, color: 'text-purple-600 bg-purple-50' },
                ].map((kpi) => (
                  <div
                    key={kpi.label}
                    className="rounded-xl border border-slate-200 bg-white p-4 transition-transform hover:-translate-y-0.5 hover:shadow-md"
                  >
                    <div className={`mb-3 inline-flex h-9 w-9 items-center justify-center rounded-lg ${kpi.color}`}>
                      <kpi.icon size={18} />
                    </div>
                    <p className="text-xs font-medium text-slate-500">{kpi.label}</p>
                    <p className="mt-1 text-2xl font-bold text-slate-900">{kpi.value}</p>
                  </div>
                ))}
              </div>

              <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-3">
                {/* Chart mockup */}
                <div className="col-span-2 rounded-xl border border-slate-200 bg-white p-5">
                  <p className="mb-4 text-sm font-semibold text-slate-700">Monthly Performance Trend</p>
                  <div className="flex h-40 items-end gap-3">
                    {[40, 65, 45, 80, 60, 95, 70, 100, 85, 110, 90, 120].map((h, i) => (
                      <div
                        key={i}
                        className="animate-bar-grow flex-1 rounded-t-md bg-gradient-to-t from-blue-600 to-blue-400"
                        style={{ height: `${h / 1.2}px`, animationDelay: `${500 + i * 40}ms` }}
                      />
                    ))}
                  </div>
                </div>

                {/* Report mockup */}
                <div className="rounded-xl border border-slate-200 bg-white p-5">
                  <p className="mb-4 text-sm font-semibold text-slate-700">Report Summary</p>
                  <div className="space-y-3">
                    {[85, 60, 95, 40].map((w, i) => (
                      <div key={i} className="space-y-1">
                        <div className="h-2 w-full rounded-full bg-slate-100">
                          <div
                            className="h-2 rounded-full bg-gradient-to-r from-blue-500 to-indigo-500"
                            style={{ width: `${w}%` }}
                          />
                        </div>
                      </div>
                    ))}
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
