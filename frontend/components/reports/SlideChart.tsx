'use client';

import { useMemo } from 'react';

interface ChartDataPoint {
  x?: string | number;
  y?: string | number;
  [key: string]: unknown;
}

interface SlideChartProps {
  chartType: string;
  data: ChartDataPoint[];
  xAxis?: string;
  yAxis?: string;
  series?: { name?: string; field?: string; color?: string }[];
  height?: number;
}

const COLORS = [
  '#0f3460', '#16a34a', '#f59e0b', '#dc2626',
  '#8b5cf6', '#06b6d4', '#ec4899', '#eab308',
];

export function SlideChart({
  chartType,
  data,
  xAxis = 'x',
  yAxis = 'y',
  series,
  height = 280,
}: SlideChartProps) {
  const chartData = useMemo(() => {
    if (!data || data.length === 0) return [];
    return data.slice(0, 20);
  }, [data]);

  const seriesList = useMemo(() => {
    if (series && series.length > 0) {
      return series.slice(0, 5).map((s, i) => ({
        name: s.name || yAxis || 'Value',
        field: s.field || 'y',
        color: s.color || COLORS[i % COLORS.length],
      }));
    }
    return [{ name: yAxis || 'Value', field: 'y', color: COLORS[0] }];
  }, [series, yAxis]);

  if (chartData.length === 0) {
    return (
      <div
        className="flex items-center justify-center rounded-xl border-2 border-dashed border-slate-300 dark:border-slate-700"
        style={{ height }}
      >
        <p className="text-sm text-muted-foreground">No chart data available</p>
      </div>
    );
  }

  // ── Pie / Donut ──────────────────────────────────────────────
  if (chartType === 'pie' || chartType === 'donut') {
    const total = chartData.reduce((sum, d) => {
      const v = Number(d.y ?? 0);
      return sum + (isNaN(v) ? 0 : v);
    }, 0);
    if (total === 0) {
      return (
        <div
          className="flex items-center justify-center rounded-xl border-2 border-dashed border-slate-300 dark:border-slate-700"
          style={{ height }}
        >
          <p className="text-sm text-muted-foreground">All values are zero</p>
        </div>
      );
    }

    let cumulative = 0;
    const radius = height * 0.35;
    const cx = height / 2;
    const cy = height / 2;
    const innerRadius = chartType === 'donut' ? radius * 0.55 : 0;

    const slices = chartData.map((d, i) => {
      const value = Number(d.y ?? 0);
      const pct = value / total;
      const startAngle = cumulative * 2 * Math.PI - Math.PI / 2;
      cumulative += pct;
      const endAngle = cumulative * 2 * Math.PI - Math.PI / 2;

      const x1 = cx + radius * Math.cos(startAngle);
      const y1 = cy + radius * Math.sin(startAngle);
      const x2 = cx + radius * Math.cos(endAngle);
      const y2 = cy + radius * Math.sin(endAngle);
      const largeArc = pct > 0.5 ? 1 : 0;

      let path = `M ${x1} ${y1} A ${radius} ${radius} 0 ${largeArc} 1 ${x2} ${y2}`;
      if (innerRadius > 0) {
        const ix1 = cx + innerRadius * Math.cos(endAngle);
        const iy1 = cy + innerRadius * Math.sin(endAngle);
        const ix2 = cx + innerRadius * Math.cos(startAngle);
        const iy2 = cy + innerRadius * Math.sin(startAngle);
        path += ` L ${ix1} ${iy1} A ${innerRadius} ${innerRadius} 0 ${largeArc} 0 ${ix2} ${iy2} Z`;
      } else {
        path += ` L ${cx} ${cy} Z`;
      }

      return { path, color: COLORS[i % COLORS.length], label: String(d.x ?? d[xAxis] ?? ''), value, pct };
    });

    return (
      <div className="flex items-center gap-6" style={{ height }}>
        <svg width={height} height={height} className="shrink-0">
          {slices.map((s, i) => (
            <path key={i} d={s.path} fill={s.color} stroke="white" strokeWidth={1.5} />
          ))}
        </svg>
        <div className="flex flex-col gap-1.5 overflow-auto">
          {slices.map((s, i) => (
            <div key={i} className="flex items-center gap-2 text-xs">
              <span className="h-3 w-3 shrink-0 rounded" style={{ background: s.color }} />
              <span className="truncate text-slate-700 dark:text-slate-300">{s.label}</span>
              <span className="ml-auto font-semibold text-slate-900 dark:text-slate-100">
                {s.value.toLocaleString()} ({(s.pct * 100).toFixed(1)}%)
              </span>
            </div>
          ))}
        </div>
      </div>
    );
  }

  // ── Bar / Column ─────────────────────────────────────────────
  if (chartType === 'bar' || chartType === 'area' || !['line', 'scatter'].includes(chartType)) {
    const categories = chartData.map((d) => String(d.x ?? d[xAxis] ?? ''));
    const allValues = chartData.flatMap((d) =>
      seriesList.map((s) => {
        const v = Number(d[s.field] ?? d.y ?? 0);
        return isNaN(v) ? 0 : v;
      })
    );
    const maxVal = Math.max(...allValues, 0);
    const minVal = Math.min(...allValues, 0);
    const range = maxVal - minVal || 1;

    const chartWidth = 600;
    const padding = { top: 20, right: 20, bottom: 40, left: 50 };
    const plotW = chartWidth - padding.left - padding.right;
    const plotH = height - padding.top - padding.bottom;
    const barGroupWidth = plotW / categories.length;
    const barWidth = barGroupWidth / seriesList.length * 0.8;

    return (
      <svg width="100%" height={height} viewBox={`0 0 ${chartWidth} ${height}`} preserveAspectRatio="xMidYMid meet">
        {/* Y-axis grid lines */}
        {[0, 0.25, 0.5, 0.75, 1].map((t) => {
          const y = padding.top + plotH * (1 - t);
          const val = minVal + range * t;
          return (
            <g key={t}>
              <line x1={padding.left} y1={y} x2={chartWidth - padding.right} y2={y} stroke="#e2e8f0" strokeWidth={1} />
              <text x={padding.left - 8} y={y + 4} textAnchor="end" fontSize={10} fill="#64748b">
                {val >= 1000 ? `${(val / 1000).toFixed(1)}k` : val.toFixed(0)}
              </text>
            </g>
          );
        })}

        {/* Bars */}
        {categories.map((cat, i) => (
          <g key={i}>
            {seriesList.map((s, si) => {
              const v = Number(chartData[i][s.field] ?? chartData[i].y ?? 0);
              const safeV = isNaN(v) ? 0 : v;
              const barH = (safeV - minVal) / range * plotH;
              const x = padding.left + i * barGroupWidth + si * barWidth + barGroupWidth * 0.1;
              const y = padding.top + plotH - barH;
              return (
                <rect
                  key={si}
                  x={x}
                  y={y}
                  width={barWidth}
                  height={barH}
                  fill={s.color}
                  rx={2}
                />
              );
            })}
            <text
              x={padding.left + i * barGroupWidth + barGroupWidth / 2}
              y={height - padding.bottom + 16}
              textAnchor="middle"
              fontSize={10}
              fill="#64748b"
            >
              {cat.length > 12 ? cat.slice(0, 10) + '…' : cat}
            </text>
          </g>
        ))}

        {/* X-axis line */}
        <line x1={padding.left} y1={padding.top + plotH} x2={chartWidth - padding.right} y2={padding.top + plotH} stroke="#94a3b8" strokeWidth={1.5} />

        {/* Legend */}
        {seriesList.length > 1 && (
          <g transform={`translate(${padding.left}, 4)`}>
            {seriesList.map((s, i) => (
              <g key={i} transform={`translate(${i * 120}, 0)`}>
                <rect width={12} height={12} fill={s.color} rx={2} />
                <text x={16} y={10} fontSize={10} fill="#475569">{s.name}</text>
              </g>
            ))}
          </g>
        )}
      </svg>
    );
  }

  // ── Line Chart ───────────────────────────────────────────────
  if (chartType === 'line') {
    const categories = chartData.map((d) => String(d.x ?? d[xAxis] ?? ''));
    const allValues = chartData.flatMap((d) =>
      seriesList.map((s) => {
        const v = Number(d[s.field] ?? d.y ?? 0);
        return isNaN(v) ? 0 : v;
      })
    );
    const maxVal = Math.max(...allValues, 0);
    const minVal = Math.min(...allValues, 0);
    const range = maxVal - minVal || 1;

    const chartWidth = 600;
    const padding = { top: 20, right: 20, bottom: 40, left: 50 };
    const plotW = chartWidth - padding.left - padding.right;
    const plotH = height - padding.top - padding.bottom;
    const stepX = plotW / Math.max(categories.length - 1, 1);

    return (
      <svg width="100%" height={height} viewBox={`0 0 ${chartWidth} ${height}`} preserveAspectRatio="xMidYMid meet">
        {/* Y-axis grid lines */}
        {[0, 0.25, 0.5, 0.75, 1].map((t) => {
          const y = padding.top + plotH * (1 - t);
          const val = minVal + range * t;
          return (
            <g key={t}>
              <line x1={padding.left} y1={y} x2={chartWidth - padding.right} y2={y} stroke="#e2e8f0" strokeWidth={1} />
              <text x={padding.left - 8} y={y + 4} textAnchor="end" fontSize={10} fill="#64748b">
                {val >= 1000 ? `${(val / 1000).toFixed(1)}k` : val.toFixed(0)}
              </text>
            </g>
          );
        })}

        {/* Lines */}
        {seriesList.map((s, si) => {
          const points = chartData.map((d, i) => {
            const v = Number(d[s.field] ?? d.y ?? 0);
            const safeV = isNaN(v) ? 0 : v;
            const x = padding.left + i * stepX;
            const y = padding.top + plotH - ((safeV - minVal) / range) * plotH;
            return `${x},${y}`;
          });
          return (
            <g key={si}>
              <polyline
                points={points.join(' ')}
                fill="none"
                stroke={s.color}
                strokeWidth={2.5}
                strokeLinejoin="round"
                strokeLinecap="round"
              />
              {points.map((p, i) => {
                const [x, y] = p.split(',').map(Number);
                return <circle key={i} cx={x} cy={y} r={3} fill={s.color} />;
              })}
            </g>
          );
        })}

        {/* X-axis labels */}
        {categories.map((cat, i) => (
          <text
            key={i}
            x={padding.left + i * stepX}
            y={height - padding.bottom + 16}
            textAnchor="middle"
            fontSize={10}
            fill="#64748b"
          >
            {cat.length > 12 ? cat.slice(0, 10) + '…' : cat}
          </text>
        ))}

        {/* X-axis line */}
        <line x1={padding.left} y1={padding.top + plotH} x2={chartWidth - padding.right} y2={padding.top + plotH} stroke="#94a3b8" strokeWidth={1.5} />

        {/* Legend */}
        {seriesList.length > 1 && (
          <g transform={`translate(${padding.left}, 4)`}>
            {seriesList.map((s, i) => (
              <g key={i} transform={`translate(${i * 120}, 0)`}>
                <line x1={0} y1={6} x2={12} y2={6} stroke={s.color} strokeWidth={2.5} />
                <text x={16} y={10} fontSize={10} fill="#475569">{s.name}</text>
              </g>
            ))}
          </g>
        )}
      </svg>
    );
  }

  // ── Scatter ──────────────────────────────────────────────────
  if (chartType === 'scatter') {
    const allValues = chartData.flatMap((d) => {
      const v = Number(d.y ?? 0);
      return isNaN(v) ? 0 : v;
    });
    const maxVal = Math.max(...allValues, 0);
    const minVal = Math.min(...allValues, 0);
    const range = maxVal - minVal || 1;

    const chartWidth = 600;
    const padding = { top: 20, right: 20, bottom: 40, left: 50 };
    const plotW = chartWidth - padding.left - padding.right;
    const plotH = height - padding.top - padding.bottom;

    return (
      <svg width="100%" height={height} viewBox={`0 0 ${chartWidth} ${height}`} preserveAspectRatio="xMidYMid meet">
        {[0, 0.25, 0.5, 0.75, 1].map((t) => {
          const y = padding.top + plotH * (1 - t);
          const val = minVal + range * t;
          return (
            <g key={t}>
              <line x1={padding.left} y1={y} x2={chartWidth - padding.right} y2={y} stroke="#e2e8f0" strokeWidth={1} />
              <text x={padding.left - 8} y={y + 4} textAnchor="end" fontSize={10} fill="#64748b">
                {val.toFixed(0)}
              </text>
            </g>
          );
        })}
        {chartData.map((d, i) => {
          const v = Number(d.y ?? 0);
          const safeV = isNaN(v) ? 0 : v;
          const x = padding.left + (i / Math.max(chartData.length - 1, 1)) * plotW;
          const y = padding.top + plotH - ((safeV - minVal) / range) * plotH;
          return <circle key={i} cx={x} cy={y} r={4} fill={COLORS[0]} opacity={0.7} />;
        })}
        <line x1={padding.left} y1={padding.top + plotH} x2={chartWidth - padding.right} y2={padding.top + plotH} stroke="#94a3b8" strokeWidth={1.5} />
      </svg>
    );
  }

  return null;
}
