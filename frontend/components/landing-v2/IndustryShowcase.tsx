'use client';

import { useState } from 'react';
import { Reveal } from '@/components/landing/Reveal';

const industries = [
  {
    name: 'Healthcare',
    icon: 'M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0016.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 002 8.5c0 2.29 1.51 4.04 3 5.5l7 7z',
    kpis: [
      { label: 'Patient Outcomes', value: '94%' },
      { label: 'Avg Wait Time', value: '12 min' },
      { label: 'Bed Occupancy', value: '78%' },
    ],
    charts: [65, 72, 58, 81, 90, 85, 77],
    terminology: ['Patients', 'Treatments', 'Wards', 'Discharges'],
    description: 'Track patient outcomes, monitor treatment efficacy, and ensure compliance with health standards.',
  },
  {
    name: 'Education',
    icon: 'M22 10v6M2 10l10-5 10 5-10 5z M6 12v5c3 3 9 3 12 0v-5',
    kpis: [
      { label: 'Pass Rate', value: '87%' },
      { label: 'Enrollment', value: '12,300' },
      { label: 'Engagement', value: '92%' },
    ],
    charts: [45, 68, 72, 85, 79, 88, 91],
    terminology: ['Students', 'Courses', 'Grades', 'Assessments'],
    description: 'Monitor student performance, identify at-risk learners, and measure institutional effectiveness.',
  },
  {
    name: 'Business',
    icon: 'M3 3v18h18M7 14l4-4 4 4 5-5',
    kpis: [
      { label: 'Revenue', value: '$4.2M' },
      { label: 'Growth', value: '+15%' },
      { label: 'Margin', value: '23%' },
    ],
    charts: [55, 62, 70, 68, 82, 88, 95],
    terminology: ['Revenue', 'Customers', 'Pipeline', 'Forecast'],
    description: 'Sales performance, inventory tracking, financial analysis, and operational dashboards.',
  },
  {
    name: 'Government',
    icon: 'M3 21h18M3 10h18M5 6l7-3 7 3M4 10v11M20 10v11M8 14v3M12 14v3M16 14v3',
    kpis: [
      { label: 'Service Delivery', value: '96%' },
      { label: 'Citizen Satisfaction', value: '4.2/5' },
      { label: 'Projects On Track', value: '82%' },
    ],
    charts: [72, 75, 68, 80, 85, 82, 88],
    terminology: ['Citizens', 'Services', 'Departments', 'Programs'],
    description: 'Monitor public service delivery, track program outcomes, and report on citizen satisfaction.',
  },
  {
    name: 'NGOs',
    icon: 'M12 2v20M2 12h20',
    kpis: [
      { label: 'Beneficiaries', value: '48K' },
      { label: 'Fund Utilization', value: '89%' },
      { label: 'Impact Score', value: '4.6/5' },
    ],
    charts: [40, 55, 62, 70, 78, 85, 90],
    terminology: ['Beneficiaries', 'Programs', 'Donors', 'Impact'],
    description: 'Track program impact, manage donor reporting, and measure outcomes against funding goals.',
  },
  {
    name: 'Banking',
    icon: 'M3 10h18M5 6h14a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2V8a2 2 0 012-2zM7 10v6M11 10v6M15 10v6M19 10v6',
    kpis: [
      { label: 'NPL Ratio', value: '2.1%' },
      { label: 'ROE', value: '14.5%' },
      { label: 'Capital Adequacy', value: '18.2%' },
    ],
    charts: [80, 75, 82, 78, 85, 88, 92],
    terminology: ['Loans', 'Deposits', 'Risk', 'Compliance'],
    description: 'Monitor loan portfolios, track risk metrics, and generate regulatory compliance reports.',
  },
  {
    name: 'Retail',
    icon: 'M3 9l1-5h16l1 5M4 9v11h16V9M9 13h6',
    kpis: [
      { label: 'Sales', value: '$2.8M' },
      { label: 'Inventory Turn', value: '4.2x' },
      { label: 'Customer Retention', value: '76%' },
    ],
    charts: [60, 72, 65, 80, 88, 75, 92],
    terminology: ['Products', 'Sales', 'Inventory', 'Customers'],
    description: 'Track sales performance, manage inventory, and analyze customer behavior across channels.',
  },
  {
    name: 'Manufacturing',
    icon: 'M2 20h20M4 20V8l8-5 8 5v12M9 20v-6h6v6',
    kpis: [
      { label: 'OEE', value: '84%' },
      { label: 'Downtime', value: '3.2%' },
      { label: 'Quality Rate', value: '97.5%' },
    ],
    charts: [70, 75, 82, 78, 85, 80, 88],
    terminology: ['Production', 'Quality', 'Downtime', 'Throughput'],
    description: 'Monitor production efficiency, track quality metrics, and optimize supply chain operations.',
  },
  {
    name: 'Agriculture',
    icon: 'M12 2C8 6 8 12 12 12s4-6 0-10zM12 12c-4 0-8 2-8 6h16c0-4-4-6-8-6z',
    kpis: [
      { label: 'Yield', value: '4.8 t/ha' },
      { label: 'Water Usage', value: '-18%' },
      { label: 'Crop Health', value: '91%' },
    ],
    charts: [50, 60, 72, 68, 80, 85, 90],
    terminology: ['Crops', 'Yield', 'Weather', 'Soil'],
    description: 'Monitor crop health, track yields, and optimize resource usage across farming operations.',
  },
];

export function IndustryShowcase() {
  const [active, setActive] = useState(0);
  const industry = industries[active];

  return (
    <section className="bg-slate-50/50 py-24 lg:py-32">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <Reveal className="mx-auto max-w-2xl text-center">
          <p className="text-sm font-semibold uppercase tracking-wider text-blue-600">Industry Showcase</p>
          <h2 className="mt-3 text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
            Built for your sector
          </h2>
          <p className="mt-4 text-lg text-slate-600">
            Select an industry to see how DataFlow adapts its dashboards, KPIs, and terminology.
          </p>
        </Reveal>

        {/* Industry selector */}
        <Reveal className="mt-12" delay={200}>
          <div className="flex flex-wrap justify-center gap-2">
            {industries.map((ind, i) => (
              <button
                key={ind.name}
                onClick={() => setActive(i)}
                className={`inline-flex items-center gap-2 rounded-full px-4 py-2 text-sm font-medium transition-all ${
                  active === i
                    ? 'bg-slate-900 text-white shadow-md'
                    : 'bg-white text-slate-600 border border-slate-200 hover:border-slate-300 hover:text-slate-900'
                }`}
              >
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4">
                  <path d={ind.icon} />
                </svg>
                {ind.name}
              </button>
            ))}
          </div>
        </Reveal>

        {/* Preview panel */}
        <Reveal className="mt-10" delay={300}>
          <div key={active} className="animate-tab-fade overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-xl shadow-slate-900/5">
            <div className="grid lg:grid-cols-[1fr_1.2fr]">
              {/* Left: description and terminology */}
              <div className="border-b border-slate-200 p-8 lg:border-b-0 lg:border-r">
                <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-blue-500 to-violet-500 text-white shadow-lg shadow-blue-500/20">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-7 w-7">
                    <path d={industry.icon} />
                  </svg>
                </div>
                <h3 className="mt-5 text-2xl font-bold text-slate-900">{industry.name}</h3>
                <p className="mt-3 text-sm leading-relaxed text-slate-600">{industry.description}</p>

                {/* Terminology tags */}
                <div className="mt-6">
                  <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">Platform Terminology</p>
                  <div className="mt-3 flex flex-wrap gap-2">
                    {industry.terminology.map((term) => (
                      <span key={term} className="rounded-lg bg-slate-100 px-3 py-1.5 text-xs font-medium text-slate-700">
                        {term}
                      </span>
                    ))}
                  </div>
                </div>
              </div>

              {/* Right: KPIs and chart */}
              <div className="p-8">
                {/* KPIs */}
                <div className="grid grid-cols-3 gap-3">
                  {industry.kpis.map((kpi) => (
                    <div key={kpi.label} className="rounded-xl border border-slate-200 bg-slate-50/50 p-4">
                      <p className="text-xs font-medium text-slate-500">{kpi.label}</p>
                      <p className="mt-1 text-xl font-bold text-slate-900">{kpi.value}</p>
                    </div>
                  ))}
                </div>

                {/* Chart */}
                <div className="mt-6 rounded-xl border border-slate-200 p-5">
                  <div className="flex items-center justify-between">
                    <p className="text-sm font-semibold text-slate-700">Weekly Trend</p>
                    <span className="rounded-md bg-blue-100 px-2 py-0.5 text-xs font-medium text-blue-700">{industry.name}</span>
                  </div>
                  <div className="mt-4 flex h-40 items-end gap-2">
                    {industry.charts.map((h, i) => (
                      <div key={i} className="flex-1 group relative">
                        <div
                          className="rounded-t bg-gradient-to-t from-blue-500 to-violet-400 transition-all duration-700 ease-out"
                          style={{ height: `${h}%`, transitionDelay: `${i * 60}ms` }}
                        />
                        <div className="absolute -top-7 left-1/2 -translate-x-1/2 rounded bg-slate-900 px-2 py-0.5 text-[10px] font-medium text-white opacity-0 transition-opacity group-hover:opacity-100">
                          {h}%
                        </div>
                      </div>
                    ))}
                  </div>
                  <div className="mt-2 flex justify-between text-xs text-slate-400">
                    {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map((day) => (
                      <span key={day}>{day}</span>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </Reveal>
      </div>
    </section>
  );
}
