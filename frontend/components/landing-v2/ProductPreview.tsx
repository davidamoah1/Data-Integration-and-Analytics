'use client';

import { useState, useEffect } from 'react';
import { Reveal } from '@/components/landing/Reveal';

const studios = [
  {
    name: 'Analytics Studio',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4">
        <path d="M3 3v18h18" /><path d="M7 14l4-4 4 4 5-5" />
      </svg>
    ),
    preview: {
      title: 'Interactive Dashboards',
      description: 'Build live dashboards with drag-and-drop widgets, real-time KPIs, and shareable links.',
      metrics: [
        { label: 'Widgets', value: '24' },
        { label: 'Data Sources', value: '7' },
        { label: 'Refresh Rate', value: '30s' },
      ],
      visual: 'chart',
    },
  },
  {
    name: 'Research Studio',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4">
        <circle cx="11" cy="11" r="8" /><path d="M21 21l-4.35-4.35" />
      </svg>
    ),
    preview: {
      title: 'Hypothesis-Driven Research',
      description: 'Define research questions, generate hypotheses, run statistical tests, and publish findings.',
      metrics: [
        { label: 'Experiments', value: '12' },
        { label: 'P-Value', value: '0.03' },
        { label: 'Confidence', value: '97%' },
      ],
      visual: 'research',
    },
  },
  {
    name: 'Healthcare Studio',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4">
        <path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0016.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 002 8.5c0 2.29 1.51 4.04 3 5.5l7 7z" />
      </svg>
    ),
    preview: {
      title: 'Patient Outcomes Analytics',
      description: 'Track patient outcomes, monitor treatment efficacy, and generate compliance reports.',
      metrics: [
        { label: 'Patients', value: '8,420' },
        { label: 'Recovery Rate', value: '94%' },
        { label: 'Avg Stay', value: '3.2d' },
      ],
      visual: 'healthcare',
    },
  },
  {
    name: 'Education Studio',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4">
        <path d="M22 10v6M2 10l10-5 10 5-10 5z" /><path d="M6 12v5c3 3 9 3 12 0v-5" />
      </svg>
    ),
    preview: {
      title: 'Student Performance Tracking',
      description: 'Monitor student progress, identify at-risk learners, and measure institutional effectiveness.',
      metrics: [
        { label: 'Students', value: '12,300' },
        { label: 'Pass Rate', value: '87%' },
        { label: 'Engagement', value: '92%' },
      ],
      visual: 'education',
    },
  },
  {
    name: 'Business Studio',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4">
        <rect x="2" y="7" width="20" height="14" rx="2" /><path d="M16 21V5a2 2 0 00-2-2h-4a2 2 0 00-2 2v16" />
      </svg>
    ),
    preview: {
      title: 'Business Intelligence',
      description: 'Sales performance, inventory tracking, financial analysis, and operational dashboards.',
      metrics: [
        { label: 'Revenue', value: '$4.2M' },
        { label: 'Margin', value: '23%' },
        { label: 'Growth', value: '+15%' },
      ],
      visual: 'business',
    },
  },
  {
    name: 'Report Studio',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4">
        <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" /><path d="M14 2v6h6" />
      </svg>
    ),
    preview: {
      title: 'Presentation-Ready Reports',
      description: 'Generate executive reports, interactive dashboards, PowerPoint, PDF, and Word documents.',
      metrics: [
        { label: 'Formats', value: '5' },
        { label: 'Templates', value: '40+' },
        { label: 'Auto-Gen', value: 'Yes' },
      ],
      visual: 'report',
    },
  },
  {
    name: 'Automation Studio',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4">
        <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" />
      </svg>
    ),
    preview: {
      title: 'Workflow Automation',
      description: 'Schedule data pipelines, trigger reports, and orchestrate multi-step analytics workflows.',
      metrics: [
        { label: 'Workflows', value: '36' },
        { label: 'Scheduled', value: '24' },
        { label: 'Success', value: '99.2%' },
      ],
      visual: 'automation',
    },
  },
  {
    name: 'Data Integration Studio',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4">
        <ellipse cx="12" cy="5" rx="9" ry="3" /><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3" /><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5" />
      </svg>
    ),
    preview: {
      title: 'Connect Any Data Source',
      description: 'Integrate databases, APIs, spreadsheets, cloud storage, and streaming sources.',
      metrics: [
        { label: 'Connectors', value: '20+' },
        { label: 'Sources', value: '15' },
        { label: 'Real-time', value: 'Yes' },
      ],
      visual: 'integration',
    },
  },
];

function PreviewVisual({ type }: { type: string }) {
  switch (type) {
    case 'chart':
      return (
        <div className="flex h-32 items-end gap-2">
          {[50, 72, 45, 88, 61, 79, 53, 92].map((h, i) => (
            <div key={i} className="flex-1 rounded-t bg-gradient-to-t from-blue-500 to-blue-400 animate-bar-grow" style={{ height: `${h}%`, animationDelay: `${i * 80}ms` }} />
          ))}
        </div>
      );
    case 'research':
      return (
        <div className="space-y-3">
          <div className="flex items-center justify-between rounded-lg bg-slate-50 p-3">
            <span className="text-xs font-medium text-slate-600">Hypothesis Test</span>
            <span className="rounded-md bg-emerald-100 px-2 py-0.5 text-xs font-semibold text-emerald-700">Supported</span>
          </div>
          <div className="flex items-center justify-between rounded-lg bg-slate-50 p-3">
            <span className="text-xs font-medium text-slate-600">Statistical Power</span>
            <span className="text-xs font-bold text-slate-900">0.87</span>
          </div>
          <div className="flex items-center justify-between rounded-lg bg-slate-50 p-3">
            <span className="text-xs font-medium text-slate-600">Effect Size</span>
            <span className="text-xs font-bold text-slate-900">0.42</span>
          </div>
        </div>
      );
    case 'healthcare':
      return (
        <div className="space-y-2">
          <div className="flex items-center gap-3 rounded-lg bg-slate-50 p-3">
            <div className="h-2 w-full rounded-full bg-slate-200">
              <div className="h-2 rounded-full bg-emerald-500" style={{ width: '94%' }} />
            </div>
            <span className="text-xs font-bold text-slate-700">94%</span>
          </div>
          <div className="grid grid-cols-3 gap-2">
            <div className="rounded-lg bg-blue-50 p-2 text-center">
              <p className="text-xs text-slate-500">ICU</p>
              <p className="text-sm font-bold text-slate-900">12</p>
            </div>
            <div className="rounded-lg bg-violet-50 p-2 text-center">
              <p className="text-xs text-slate-500">Ward</p>
              <p className="text-sm font-bold text-slate-900">48</p>
            </div>
            <div className="rounded-lg bg-emerald-50 p-2 text-center">
              <p className="text-xs text-slate-500">Discharged</p>
              <p className="text-sm font-bold text-slate-900">156</p>
            </div>
          </div>
        </div>
      );
    case 'education':
      return (
        <div className="space-y-2">
          {['Mathematics', 'Science', 'English', 'History'].map((subject, i) => (
            <div key={subject} className="flex items-center gap-3">
              <span className="w-20 text-xs font-medium text-slate-600">{subject}</span>
              <div className="h-2 flex-1 rounded-full bg-slate-200">
                <div className="h-2 rounded-full bg-gradient-to-r from-blue-500 to-violet-500" style={{ width: `${[88, 92, 79, 85][i]}%` }} />
              </div>
              <span className="text-xs font-bold text-slate-700">{[88, 92, 79, 85][i]}%</span>
            </div>
          ))}
        </div>
      );
    case 'business':
      return (
        <div className="grid grid-cols-2 gap-3">
          <div className="rounded-lg bg-slate-50 p-3">
            <p className="text-xs text-slate-500">Q1 Revenue</p>
            <p className="text-lg font-bold text-slate-900">$1.2M</p>
            <p className="text-xs font-semibold text-emerald-600">+18%</p>
          </div>
          <div className="rounded-lg bg-slate-50 p-3">
            <p className="text-xs text-slate-500">Q2 Revenue</p>
            <p className="text-lg font-bold text-slate-900">$1.5M</p>
            <p className="text-xs font-semibold text-emerald-600">+25%</p>
          </div>
          <div className="rounded-lg bg-slate-50 p-3">
            <p className="text-xs text-slate-500">Q3 Revenue</p>
            <p className="text-lg font-bold text-slate-900">$1.8M</p>
            <p className="text-xs font-semibold text-emerald-600">+20%</p>
          </div>
          <div className="rounded-lg bg-slate-50 p-3">
            <p className="text-xs text-slate-500">Q4 Revenue</p>
            <p className="text-lg font-bold text-slate-900">$2.1M</p>
            <p className="text-xs font-semibold text-emerald-600">+17%</p>
          </div>
        </div>
      );
    case 'report':
      return (
        <div className="space-y-2">
          {['Executive Summary', 'Financial Analysis', 'Performance Metrics', 'Recommendations'].map((section, i) => (
            <div key={section} className="flex items-center gap-3 rounded-lg border border-slate-200 p-2.5 animate-tab-fade" style={{ animationDelay: `${i * 100}ms` }}>
              <div className="flex h-7 w-7 items-center justify-center rounded-md bg-blue-100 text-xs font-bold text-blue-600">{i + 1}</div>
              <span className="text-xs font-medium text-slate-700">{section}</span>
              <div className="ml-auto flex gap-1">
                <span className="rounded bg-emerald-100 px-1.5 py-0.5 text-[10px] font-semibold text-emerald-700">PDF</span>
                <span className="rounded bg-blue-100 px-1.5 py-0.5 text-[10px] font-semibold text-blue-700">PPT</span>
              </div>
            </div>
          ))}
        </div>
      );
    case 'automation':
      return (
        <div className="space-y-2">
          {['Fetch Data', 'Clean & Validate', 'Run Analysis', 'Generate Report', 'Send Email'].map((step, i) => (
            <div key={step} className="flex items-center gap-3">
              <div className={`flex h-7 w-7 items-center justify-center rounded-full text-xs font-bold ${i < 3 ? 'bg-emerald-500 text-white' : i === 3 ? 'bg-blue-500 text-white animate-pulse-soft' : 'bg-slate-200 text-slate-400'}`}>
                {i < 3 ? '✓' : i + 1}
              </div>
              <span className={`text-xs font-medium ${i <= 3 ? 'text-slate-700' : 'text-slate-400'}`}>{step}</span>
            </div>
          ))}
        </div>
      );
    case 'integration':
      return (
        <div className="grid grid-cols-3 gap-2">
          {['PostgreSQL', 'MySQL', 'MongoDB', 'REST API', 'S3', 'Google Drive', 'Excel', 'CSV', 'Stream'].map((source) => (
            <div key={source} className="rounded-lg border border-slate-200 bg-slate-50 p-2 text-center">
              <p className="text-xs font-medium text-slate-700">{source}</p>
            </div>
          ))}
        </div>
      );
    default:
      return null;
  }
}

export function ProductPreview() {
  const [active, setActive] = useState(0);
  const [autoPlay, setAutoPlay] = useState(true);

  useEffect(() => {
    if (!autoPlay) return;
    const interval = setInterval(() => {
      setActive((prev) => (prev + 1) % studios.length);
    }, 5000);
    return () => clearInterval(interval);
  }, [autoPlay]);

  const studio = studios[active];

  return (
    <section className="py-24 lg:py-32">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <Reveal className="mx-auto max-w-2xl text-center">
          <p className="text-sm font-semibold uppercase tracking-wider text-blue-600">One Platform, Many Studios</p>
          <h2 className="mt-3 text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
            Explore the platform by workspace
          </h2>
          <p className="mt-4 text-lg text-slate-600">
            Each studio is a dedicated environment designed for specific workflows and industries.
          </p>
        </Reveal>

        <Reveal className="mt-12" delay={200}>
          <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-xl shadow-slate-900/5">
            <div className="grid lg:grid-cols-[280px_1fr]">
              {/* Tab sidebar */}
              <div className="border-b border-slate-200 bg-slate-50/50 p-3 lg:border-b-0 lg:border-r">
                <div className="flex gap-1 overflow-x-auto lg:flex-col">
                  {studios.map((s, i) => (
                    <button
                      key={s.name}
                      onClick={() => { setActive(i); setAutoPlay(false); }}
                      className={`flex shrink-0 items-center gap-2.5 rounded-lg px-3.5 py-2.5 text-sm font-medium transition-all ${
                        active === i
                          ? 'bg-white text-slate-900 shadow-sm'
                          : 'text-slate-500 hover:bg-white/60 hover:text-slate-700'
                      }`}
                    >
                      <span className={`flex h-7 w-7 items-center justify-center rounded-md transition-colors ${
                        active === i ? 'bg-blue-100 text-blue-600' : 'bg-slate-200 text-slate-500'
                      }`}>
                        {s.icon}
                      </span>
                      <span className="hidden sm:inline">{s.name}</span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Preview panel */}
              <div className="p-6 lg:p-8" key={active}>
                <div className="animate-tab-fade">
                  <h3 className="text-xl font-bold text-slate-900">{studio.preview.title}</h3>
                  <p className="mt-2 text-sm text-slate-600">{studio.preview.description}</p>

                  {/* Metrics */}
                  <div className="mt-6 grid grid-cols-3 gap-3">
                    {studio.preview.metrics.map((m) => (
                      <div key={m.label} className="rounded-xl border border-slate-200 bg-slate-50/50 p-3 text-center">
                        <p className="text-xs font-medium text-slate-500">{m.label}</p>
                        <p className="mt-1 text-lg font-bold text-slate-900">{m.value}</p>
                      </div>
                    ))}
                  </div>

                  {/* Visual */}
                  <div className="mt-6 rounded-xl border border-slate-200 p-4">
                    <PreviewVisual type={studio.preview.visual} />
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
