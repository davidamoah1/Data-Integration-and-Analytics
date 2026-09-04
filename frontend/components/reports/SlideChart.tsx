'use client';

import { useMemo } from 'react';
import { cleanMojibake } from '@/lib/utils';

interface ChartDataPoint {
  x?: string | number;
  y?: string | number;
  value?: string | number;
  pct?: number;
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
  '#0f3460', // deep navy
  '#16a34a', // emerald
  '#f59e0b', // amber
  '#2563eb', // royal blue
  '#dc2626', // crimson
  '#8b5cf6', // purple
  '#06b6d4', // cyan
  '#ec4899', // pink
  '#10b981', // teal
  '#f97316', // orange
];

export function SlideChart({
  chartType,
  data,
  xAxis = 'x',
  yAxis = 'y',
  series,
  height = 280,
}: SlideChartProps) {
  const normalizedType = useMemo(() => {
    return (chartType || '').toLowerCase().trim().replace(/[-_ ]/g, '');
  }, [chartType]);

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

  // ── 1. Pie / Donut Chart ──────────────────────────────────────
  const isDonut = normalizedType === 'donutchart' || normalizedType === 'donut';
  const isPie = normalizedType === 'piechart' || normalizedType === 'pie';

  if (isDonut || isPie) {
    const total = chartData.reduce((sum, d) => {
      const v = Number(d.y ?? d.value ?? 0);
      return sum + (isNaN(v) ? 0 : Math.max(0, v));
    }, 0);

    if (total === 0) {
      return (
        <div
          className="flex items-center justify-center rounded-xl border-2 border-dashed border-slate-300 dark:border-slate-700"
          style={{ height }}
        >
          <p className="text-xs text-muted-foreground">All values are zero</p>
        </div>
      );
    }

    const size = Math.min(height, 240);
    const radius = size * 0.38;
    const cx = size / 2;
    const cy = size / 2;
    const innerRadius = isDonut ? radius * 0.58 : 0;

    let cumulative = 0;
    const slices = chartData.map((d, i) => {
      const value = Math.max(0, Number(d.y ?? d.value ?? 0));
      const pct = total > 0 ? value / total : 0;
      const startAngle = cumulative * 2 * Math.PI - Math.PI / 2;
      cumulative += pct;
      const endAngle = cumulative * 2 * Math.PI - Math.PI / 2;

      const rawLabel = String(d.x ?? d[xAxis] ?? d.label ?? `Segment ${i + 1}`);
      const label = cleanMojibake(rawLabel);

      // Handle full circle edge case (e.g. 1 slice = 100%)
      if (pct >= 0.999) {
        return {
          isFullCircle: true,
          path: '',
          color: COLORS[i % COLORS.length],
          label,
          value,
          pct,
        };
      }

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

      return {
        isFullCircle: false,
        path,
        color: COLORS[i % COLORS.length],
        label,
        value,
        pct,
      };
    });

    return (
      <div className="flex items-center gap-4 w-full" style={{ height }}>
        <svg width={size} height={size} className="shrink-0">
          {slices.map((s, i) => {
            if (s.isFullCircle) {
              return (
                <g key={i}>
                  <circle cx={cx} cy={cy} r={radius} fill={s.color} />
                  {innerRadius > 0 && <circle cx={cx} cy={cy} r={innerRadius} fill="white" className="dark:fill-slate-900" />}
                </g>
              );
            }
            return (
              <path
                key={i}
                d={s.path}
                fill={s.color}
                stroke="#ffffff"
                className="dark:stroke-slate-900"
                strokeWidth={2}
              />
            );
          })}
          {isDonut && (
            <g className="select-none pointer-events-none">
              <text
                x={cx}
                y={cy - 2}
                textAnchor="middle"
                className="fill-foreground font-bold text-sm"
              >
                {total >= 10000 ? `${(total / 1000).toFixed(1)}k` : total.toLocaleString()}
              </text>
              <text
                x={cx}
                y={cy + 13}
                textAnchor="middle"
                className="fill-muted-foreground text-[10px] uppercase tracking-wider font-medium"
              >
                Total
              </text>
            </g>
          )}
        </svg>

        {/* Legend */}
        <div className="flex flex-col gap-1.5 overflow-y-auto max-h-[220px] pr-2 flex-1">
          {slices.map((s, i) => (
            <div key={i} className="flex items-center justify-between gap-2 text-xs py-0.5 border-b border-border/30 last:border-0">
              <div className="flex items-center gap-1.5 min-w-0">
                <span className="h-2.5 w-2.5 shrink-0 rounded-full" style={{ background: s.color }} />
                <span className="truncate text-slate-700 dark:text-slate-300 max-w-[120px]" title={s.label}>
                  {s.label}
                </span>
              </div>
              <div className="shrink-0 text-right">
                <span className="font-semibold text-slate-900 dark:text-slate-100 mr-1.5">
                  {s.value.toLocaleString()}
                </span>
                <span className="text-[10px] text-muted-foreground font-mono">
                  ({(s.pct * 100).toFixed(1)}%)
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  // ── 2. Histogram (Binned Statistical Distribution) ───────────
  if (normalizedType === 'histogram') {
    const bins = chartData.map((d, i) => {
      const rawLabel = String(d.x ?? d[xAxis] ?? `Bin ${i + 1}`);
      const count = Math.max(0, Number(d.y ?? d.value ?? 0));
      return {
        label: cleanMojibake(rawLabel),
        count: isNaN(count) ? 0 : count,
      };
    });

    const maxCount = Math.max(...bins.map((b) => b.count), 1);
    const chartWidth = 600;
    const padding = { top: 28, right: 24, bottom: 44, left: 44 };
    const plotW = chartWidth - padding.left - padding.right;
    const plotH = height - padding.top - padding.bottom;
    const binW = plotW / Math.max(bins.length, 1);
    const barW = Math.max(binW - 1.5, 2);

    // Calculate curve points for density/KDE line
    const curvePoints = bins.map((b, i) => ({
      x: padding.left + (i + 0.5) * binW,
      y: padding.top + plotH - (b.count / maxCount) * plotH,
    }));

    let kdePath = '';
    if (curvePoints.length > 1) {
      kdePath = `M ${curvePoints[0].x} ${curvePoints[0].y}`;
      for (let i = 0; i < curvePoints.length - 1; i++) {
        const p0 = curvePoints[Math.max(i - 1, 0)];
        const p1 = curvePoints[i];
        const p2 = curvePoints[i + 1];
        const p3 = curvePoints[Math.min(i + 2, curvePoints.length - 1)];

        const cp1x = p1.x + (p2.x - p0.x) / 6;
        const cp1y = p1.y + (p2.y - p0.y) / 6;
        const cp2x = p2.x - (p3.x - p1.x) / 6;
        const cp2y = p2.y - (p3.y - p1.y) / 6;

        kdePath += ` C ${cp1x} ${cp1y}, ${cp2x} ${cp2y}, ${p2.x} ${p2.y}`;
      }
    }

    return (
      <svg width="100%" height={height} viewBox={`0 0 ${chartWidth} ${height}`} preserveAspectRatio="xMidYMid meet">
        <defs>
          <linearGradient id="histGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#2563eb" stopOpacity="0.9" />
            <stop offset="100%" stopColor="#0f3460" stopOpacity="0.7" />
          </linearGradient>
        </defs>

        {/* Y-axis grid lines */}
        {[0, 0.25, 0.5, 0.75, 1].map((t) => {
          const y = padding.top + plotH * (1 - t);
          const val = maxCount * t;
          return (
            <g key={t}>
              <line x1={padding.left} y1={y} x2={chartWidth - padding.right} y2={y} stroke="#e2e8f0" strokeDasharray="3 3" strokeWidth={1} />
              <text x={padding.left - 8} y={y + 3.5} textAnchor="end" fontSize={10} fill="#64748b" className="font-mono">
                {val >= 1000 ? `${(val / 1000).toFixed(1)}k` : Math.round(val)}
              </text>
            </g>
          );
        })}

        {/* Adjacent Histogram Bins */}
        {bins.map((b, i) => {
          const barH = (b.count / maxCount) * plotH;
          const x = padding.left + i * binW + 0.75;
          const y = padding.top + plotH - barH;
          return (
            <g key={i}>
              <rect
                x={x}
                y={y}
                width={barW}
                height={Math.max(barH, 0)}
                fill="url(#histGradient)"
                stroke="#1e3a8a"
                strokeWidth={0.75}
                rx={1.5}
              />
              {b.count > 0 && (
                <text
                  x={x + barW / 2}
                  y={y - 6}
                  textAnchor="middle"
                  fontSize={10}
                  fontWeight="600"
                  fill="#1e40af"
                  className="dark:fill-blue-400"
                >
                  {b.count}
                </text>
              )}
              <text
                x={x + barW / 2}
                y={height - padding.bottom + 16}
                textAnchor="middle"
                fontSize={9}
                fill="#64748b"
                className="font-mono"
              >
                {b.label}
              </text>
            </g>
          );
        })}

        {/* KDE Density Curve */}
        {kdePath && (
          <path
            d={kdePath}
            fill="none"
            stroke="#f59e0b"
            strokeWidth={2.5}
            strokeLinecap="round"
          />
        )}

        {/* X-axis line */}
        <line x1={padding.left} y1={padding.top + plotH} x2={chartWidth - padding.right} y2={padding.top + plotH} stroke="#94a3b8" strokeWidth={1.5} />

        {/* Density line indicator */}
        <g transform={`translate(${chartWidth - padding.right - 120}, 10)`}>
          <line x1={0} y1={5} x2={16} y2={5} stroke="#f59e0b" strokeWidth={2.5} />
          <text x={22} y={8} fontSize={10} fill="#475569" fontWeight="500">
            Density Curve
          </text>
        </g>
      </svg>
    );
  }

  // ── 3. Horizontal Bar Chart ──────────────────────────────────
  if (normalizedType === 'horizontalbar') {
    const items = chartData.map((d, i) => {
      const rawLabel = String(d.x ?? d[xAxis] ?? `Item ${i + 1}`);
      const val = Number(d.y ?? d.value ?? 0);
      return {
        label: cleanMojibake(rawLabel),
        value: isNaN(val) ? 0 : val,
      };
    });

    const maxVal = Math.max(...items.map((it) => it.value), 1);
    const chartWidth = 600;
    const labelWidth = 110;
    const padding = { top: 16, right: 48, bottom: 20, left: labelWidth + 12 };
    const plotW = chartWidth - padding.left - padding.right;
    const plotH = height - padding.top - padding.bottom;
    const rowH = plotH / Math.max(items.length, 1);
    const barH = Math.min(rowH * 0.65, 20);

    return (
      <svg width="100%" height={height} viewBox={`0 0 ${chartWidth} ${height}`} preserveAspectRatio="xMidYMid meet">
        {/* Grid lines */}
        {[0, 0.25, 0.5, 0.75, 1].map((t) => {
          const x = padding.left + plotW * t;
          const val = maxVal * t;
          return (
            <g key={t}>
              <line x1={x} y1={padding.top} x2={x} y2={padding.top + plotH} stroke="#e2e8f0" strokeDasharray="3 3" strokeWidth={1} />
              <text x={x} y={padding.top + plotH + 14} textAnchor="middle" fontSize={9} fill="#64748b">
                {val >= 1000 ? `${(val / 1000).toFixed(1)}k` : Math.round(val)}
              </text>
            </g>
          );
        })}

        {/* Bars */}
        {items.map((item, i) => {
          const barW = (item.value / maxVal) * plotW;
          const y = padding.top + i * rowH + (rowH - barH) / 2;
          const color = COLORS[i % COLORS.length];
          return (
            <g key={i}>
              <text
                x={padding.left - 10}
                y={y + barH / 2 + 3.5}
                textAnchor="end"
                fontSize={10}
                fill="#475569"
                className="font-medium"
              >
                {item.label.length > 15 ? item.label.slice(0, 13) + '…' : item.label}
              </text>
              <rect
                x={padding.left}
                y={y}
                width={Math.max(barW, 2)}
                height={barH}
                fill={color}
                rx={3}
              />
              <text
                x={padding.left + barW + 6}
                y={y + barH / 2 + 3.5}
                fontSize={10}
                fontWeight="600"
                fill="#334155"
              >
                {item.value >= 1000 ? `${(item.value / 1000).toFixed(1)}k` : item.value.toLocaleString()}
              </text>
            </g>
          );
        })}

        {/* Y Axis Line */}
        <line x1={padding.left} y1={padding.top} x2={padding.left} y2={padding.top + plotH} stroke="#94a3b8" strokeWidth={1.5} />
      </svg>
    );
  }

  // ── 4. Line Chart ────────────────────────────────────────────
  if (normalizedType === 'linechart' || normalizedType === 'line') {
    const categories = chartData.map((d) => cleanMojibake(String(d.x ?? d[xAxis] ?? '')));
    const allValues = chartData.flatMap((d) =>
      seriesList.map((s) => {
        const v = Number(d[s.field] ?? d.y ?? 0);
        return isNaN(v) ? 0 : v;
      })
    );
    const maxVal = Math.max(...allValues, 0);
    const minVal = Math.min(...allValues, 0);
    const range = maxVal - minVal || 1;

    const shouldRotate = categories.length > 5 || categories.some((c) => c.length > 5);
    const paddingBottom = shouldRotate ? 60 : 36;
    const chartWidth = 600;
    const padding = { top: 22, right: 20, bottom: paddingBottom, left: 48 };
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
                return (
                  <circle
                    key={i}
                    cx={x}
                    cy={y}
                    r={3.5}
                    fill={s.color}
                    stroke="#ffffff"
                    strokeWidth={1.5}
                  />
                );
              })}
            </g>
          );
        })}

        {/* X-axis labels (Rotated to prevent text collision) */}
        {categories.map((cat, i) => {
          const labelX = padding.left + i * stepX;
          const labelY = height - padding.bottom + (shouldRotate ? 14 : 16);
          const display = cat.length > 14 ? cat.slice(0, 12) + '…' : cat;
          return (
            <text
              key={i}
              x={labelX}
              y={labelY}
              transform={shouldRotate ? `rotate(-35, ${labelX}, ${labelY})` : undefined}
              textAnchor={shouldRotate ? 'end' : 'middle'}
              fontSize={10}
              fill="#64748b"
            >
              {display}
            </text>
          );
        })}

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

  // ── 5. Scatter Plot ──────────────────────────────────────────
  if (normalizedType === 'scatterplot' || normalizedType === 'scatter') {
    const allValues = chartData.flatMap((d) => {
      const v = Number(d.y ?? 0);
      return isNaN(v) ? 0 : v;
    });
    const maxVal = Math.max(...allValues, 0);
    const minVal = Math.min(...allValues, 0);
    const range = maxVal - minVal || 1;

    const chartWidth = 600;
    const padding = { top: 20, right: 20, bottom: 40, left: 48 };
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
          return (
            <circle
              key={i}
              cx={x}
              cy={y}
              r={5}
              fill={COLORS[0]}
              stroke="#ffffff"
              strokeWidth={1.5}
              opacity={0.85}
            />
          );
        })}
        <line x1={padding.left} y1={padding.top + plotH} x2={chartWidth - padding.right} y2={padding.top + plotH} stroke="#94a3b8" strokeWidth={1.5} />
      </svg>
    );
  }

  // ── 6. Vertical Bar / Column Chart (Default Fallback) ────────
  const categories = chartData.map((d) => cleanMojibake(String(d.x ?? d[xAxis] ?? '')));
  const allValues = chartData.flatMap((d) =>
    seriesList.map((s) => {
      const v = Number(d[s.field] ?? d.y ?? 0);
      return isNaN(v) ? 0 : v;
    })
  );
  const maxVal = Math.max(...allValues, 0);
  const minVal = Math.min(...allValues, 0);
  const range = maxVal - minVal || 1;

  // Rotate labels 35 degrees if crowded or long, avoiding text overlap
  const shouldRotate = categories.length > 5 || categories.some((c) => c.length > 5);
  const paddingBottom = shouldRotate ? 64 : 36;

  const chartWidth = 600;
  const padding = { top: 22, right: 20, bottom: paddingBottom, left: 48 };
  const plotW = chartWidth - padding.left - padding.right;
  const plotH = height - padding.top - padding.bottom;
  const barGroupWidth = plotW / Math.max(categories.length, 1);
  const barWidth = (barGroupWidth / seriesList.length) * 0.75;

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
            const barH = ((safeV - minVal) / range) * plotH;
            const x = padding.left + i * barGroupWidth + si * barWidth + barGroupWidth * 0.125;
            const y = padding.top + plotH - barH;
            return (
              <g key={si}>
                <rect
                  x={x}
                  y={y}
                  width={barWidth}
                  height={Math.max(barH, 0)}
                  fill={s.color}
                  rx={3}
                />
                {/* Optional bar top value for smaller datasets */}
                {categories.length <= 8 && safeV > 0 && (
                  <text
                    x={x + barWidth / 2}
                    y={y - 4}
                    textAnchor="middle"
                    fontSize={9}
                    fill="#64748b"
                    className="font-medium"
                  >
                    {safeV >= 1000 ? `${(safeV / 1000).toFixed(1)}k` : safeV}
                  </text>
                )}
              </g>
            );
          })}

          {/* X-axis category label with rotation if crowded */}
          {(() => {
            const labelX = padding.left + i * barGroupWidth + barGroupWidth / 2;
            const labelY = height - padding.bottom + (shouldRotate ? 14 : 16);
            const displayLabel = cat.length > 14 ? cat.slice(0, 12) + '…' : cat;
            return (
              <text
                x={labelX}
                y={labelY}
                transform={shouldRotate ? `rotate(-35, ${labelX}, ${labelY})` : undefined}
                textAnchor={shouldRotate ? 'end' : 'middle'}
                fontSize={10}
                fill="#64748b"
              >
                {displayLabel}
              </text>
            );
          })()}
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
