'use client';

import { useMemo } from 'react';
import type { CertificateField } from '@/services/certificates/certificateService';

interface ChartData {
  label: string;
  value: number;
  color?: string;
}

interface CertificateChartsProps {
  fields: CertificateField[];
  dashboardData?: {
    by_type?: Record<string, number>;
    by_verification?: Record<string, number>;
    by_institution?: Record<string, number>;
    by_year?: Record<string, number>;
    total?: number;
  };
}

const COLORS = [
  '#6366f1', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6',
  '#ec4899', '#14b8a6', '#f97316', '#3b82f6', '#84cc16',
];

function formatLabel(key: string): string {
  return key.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}

function extractNumericValue(value: string | null): number | null {
  if (!value) return null;
  const match = value.match(/(\d+\.?\d*)/);
  if (!match) return null;
  const num = parseFloat(match[1]);
  return isNaN(num) ? null : num;
}

export function CertificateCharts({ fields, dashboardData }: CertificateChartsProps) {
  const charts = useMemo(() => {
    const result: { title: string; type: 'bar' | 'donut' | 'line'; data: ChartData[]; description: string }[] = [];

    // 1. Field confidence distribution (bar chart)
    const confidenceBuckets = { high: 0, medium: 0, low: 0 };
    fields.forEach((f) => {
      if (!f.value) return;
      if (f.confidence_score >= 0.8) confidenceBuckets.high++;
      else if (f.confidence_score >= 0.5) confidenceBuckets.medium++;
      else confidenceBuckets.low++;
    });
    const totalConfident = confidenceBuckets.high + confidenceBuckets.medium + confidenceBuckets.low;
    if (totalConfident > 0) {
      result.push({
        title: 'Extraction Confidence Distribution',
        type: 'donut',
        description: 'Confidence levels of extracted fields',
        data: [
          { label: 'High (≥80%)', value: confidenceBuckets.high, color: '#10b981' },
          { label: 'Medium (50-79%)', value: confidenceBuckets.medium, color: '#f59e0b' },
          { label: 'Low (<50%)', value: confidenceBuckets.low, color: '#ef4444' },
        ],
      });
    }

    // 2. Numeric fields bar chart (GPA, scores, etc.)
    const numericFields = fields.filter(
      (f) => f.value && extractNumericValue(f.value) !== null &&
      /gpa|cgpa|score|grade|mark|percentage|credit/i.test(f.field_name)
    );
    if (numericFields.length >= 2) {
      result.push({
        title: 'Academic Metrics',
        type: 'bar',
        description: 'Numeric values extracted from the certificate',
        data: numericFields.map((f, i) => ({
          label: formatLabel(f.field_name),
          value: extractNumericValue(f.value) || 0,
          color: COLORS[i % COLORS.length],
        })),
      });
    }

    // 3. Dashboard distribution charts
    if (dashboardData?.by_type && Object.keys(dashboardData.by_type).length > 0) {
      result.push({
        title: 'Certificates by Type',
        type: 'bar',
        description: 'Distribution of certificate types in your organization',
        data: Object.entries(dashboardData.by_type).map(([k, v], i) => ({
          label: formatLabel(k),
          value: v,
          color: COLORS[i % COLORS.length],
        })),
      });
    }

    if (dashboardData?.by_verification && Object.keys(dashboardData.by_verification).length > 0) {
      const total = dashboardData.total || Object.values(dashboardData.by_verification).reduce((a, b) => a + b, 0);
      if (total > 0) {
        result.push({
          title: 'Verification Status',
          type: 'donut',
          description: 'Verification status across all certificates',
          data: Object.entries(dashboardData.by_verification).map(([k, v], i) => ({
            label: formatLabel(k),
            value: v,
            color: COLORS[i % COLORS.length],
          })),
        });
      }
    }

    if (dashboardData?.by_institution && Object.keys(dashboardData.by_institution).length > 0) {
      result.push({
        title: 'Certificates by Institution',
        type: 'bar',
        description: 'Institution distribution',
        data: Object.entries(dashboardData.by_institution).map(([k, v], i) => ({
          label: k,
          value: v,
          color: COLORS[i % COLORS.length],
        })),
      });
    }

    if (dashboardData?.by_year && Object.keys(dashboardData.by_year).length > 1) {
      const sortedYears = Object.entries(dashboardData.by_year).sort((a, b) => a[0].localeCompare(b[0]));
      result.push({
        title: 'Certificates by Year',
        type: 'line',
        description: 'Certificate issuance trends over time',
        data: sortedYears.map(([k, v]) => ({
          label: k,
          value: v,
          color: '#6366f1',
        })),
      });
    }

    return result;
  }, [fields, dashboardData]);

  if (charts.length === 0) {
    return (
      <div className="rounded-xl border border-slate-200 bg-white p-6 text-center">
        <p className="text-sm text-slate-500">
          No meaningful chart can be generated from the available certificate data.
        </p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
      {charts.map((chart, idx) => (
        <div key={idx} className="rounded-xl border border-slate-200 bg-white p-5">
          <h4 className="text-sm font-semibold text-slate-900">{chart.title}</h4>
          <p className="text-xs text-slate-500 mb-4">{chart.description}</p>
          {chart.type === 'bar' && <BarChart data={chart.data} />}
          {chart.type === 'donut' && <DonutChart data={chart.data} />}
          {chart.type === 'line' && <LineChart data={chart.data} />}
        </div>
      ))}
    </div>
  );
}

function BarChart({ data }: { data: ChartData[] }) {
  const maxVal = Math.max(...data.map((d) => d.value), 1);
  return (
    <div className="space-y-3">
      {data.map((d, i) => (
        <div key={i} className="flex items-center gap-3">
          <span className="text-xs text-slate-600 w-32 truncate" title={d.label}>{d.label}</span>
          <div className="flex-1 h-7 bg-slate-100 rounded-md overflow-hidden relative">
            <div
              className="h-full rounded-md transition-all duration-500 flex items-center justify-end pr-2"
              style={{ width: `${(d.value / maxVal) * 100}%`, backgroundColor: d.color || COLORS[i % COLORS.length] }}
            >
              <span className="text-xs font-medium text-white">{d.value}</span>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

function DonutChart({ data }: { data: ChartData[] }) {
  const total = data.reduce((sum, d) => sum + d.value, 0);
  if (total === 0) return null;
  let cumulative = 0;
  const segments = data.map((d, i) => {
    const pct = (d.value / total) * 100;
    const offset = cumulative;
    cumulative += pct;
    return { ...d, pct, offset, color: d.color || COLORS[i % COLORS.length] };
  });

  const radius = 60;
  const circumference = 2 * Math.PI * radius;

  return (
    <div className="flex items-center gap-6">
      <svg width="160" height="160" viewBox="0 0 160 160" className="flex-shrink-0">
        <circle cx="80" cy="80" r={radius} fill="none" stroke="#f1f5f9" strokeWidth="20" />
        {segments.map((s, i) => (
          <circle
            key={i}
            cx="80"
            cy="80"
            r={radius}
            fill="none"
            stroke={s.color}
            strokeWidth="20"
            strokeDasharray={`${(s.pct / 100) * circumference} ${circumference}`}
            strokeDashoffset={`${-(s.offset / 100) * circumference}`}
            transform="rotate(-90 80 80)"
            className="transition-all duration-500"
          />
        ))}
        <text x="80" y="76" textAnchor="middle" className="text-2xl font-bold fill-slate-900">{total}</text>
        <text x="80" y="92" textAnchor="middle" className="text-xs fill-slate-500">Total</text>
      </svg>
      <div className="space-y-2 flex-1">
        {segments.map((s, i) => (
          <div key={i} className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-sm flex-shrink-0" style={{ backgroundColor: s.color }} />
            <span className="text-xs text-slate-600 flex-1">{s.label}</span>
            <span className="text-xs font-medium text-slate-900">{s.value} ({s.pct.toFixed(0)}%)</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function LineChart({ data }: { data: ChartData[] }) {
  const maxVal = Math.max(...data.map((d) => d.value), 1);
  const width = 300;
  const height = 120;
  const padding = 30;
  const chartWidth = width - padding * 2;
  const chartHeight = height - padding * 2;
  const stepX = data.length > 1 ? chartWidth / (data.length - 1) : 0;

  const points = data.map((d, i) => ({
    x: padding + i * stepX,
    y: padding + chartHeight - (d.value / maxVal) * chartHeight,
    ...d,
  }));

  const pathD = points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ');
  const areaD = `${pathD} L ${padding + chartWidth} ${padding + chartHeight} L ${padding} ${padding + chartHeight} Z`;

  return (
    <div className="w-full overflow-x-auto">
      <svg width={width} height={height} className="min-w-full">
        <defs>
          <linearGradient id="lineGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#6366f1" stopOpacity="0.3" />
            <stop offset="100%" stopColor="#6366f1" stopOpacity="0" />
          </linearGradient>
        </defs>
        <path d={areaD} fill="url(#lineGradient)" />
        <path d={pathD} fill="none" stroke="#6366f1" strokeWidth="2" />
        {points.map((p, i) => (
          <g key={i}>
            <circle cx={p.x} cy={p.y} r="3" fill="#6366f1" />
            <text x={p.x} y={height - 8} textAnchor="middle" className="text-xs fill-slate-500">{p.label}</text>
            <text x={p.x} y={p.y - 8} textAnchor="middle" className="text-xs fill-slate-700 font-medium">{p.value}</text>
          </g>
        ))}
      </svg>
    </div>
  );
}
