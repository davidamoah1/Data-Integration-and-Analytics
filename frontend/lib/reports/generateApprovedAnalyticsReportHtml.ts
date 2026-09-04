import type {
  ApprovedAnalyticsSummary,
  ApprovedCertificateRecord,
  ApprovedAnalyticsFilters,
  ApprovedKPIs,
  ApprovedDataQuality,
} from '@/services/certificates/approvedAnalyticsService';

export interface ReportDataPayload {
  title?: string;
  organization_id?: number;
  generated_at?: string;
  generated_by?: number;
  total?: number;
  kpis?: ApprovedKPIs;
  data_quality?: ApprovedDataQuality;
  breakdowns?: {
    by_name?: Record<string, number>;
    by_type?: Record<string, number>;
    by_issuer?: Record<string, number>;
    by_course?: Record<string, number>;
    by_year?: Record<string, number>;
  };
  by_name?: Record<string, number>;
  by_type?: Record<string, number>;
  by_issuer?: Record<string, number>;
  by_course?: Record<string, number>;
  trends?: Record<string, number>;
  recipients?: { name: string; approved_certificates: number }[];
  certs_per_person?: Record<string, number>;
  filters?: Record<string, string | number | null | undefined>;
  certificates?: ApprovedCertificateRecord[];
  insights?: Array<string | { title?: string; type?: string; text?: string; severity?: string }>;
}

function escapeHtml(str: string | number | null | undefined): string {
  if (str === null || str === undefined) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function formatNum(num: number | undefined): string {
  if (num === undefined || num === null) return '0';
  return Number(num).toLocaleString();
}

function renderHorizontalBarChart(
  data: Record<string, number>,
  total: number,
  accentGradient: string = 'linear-gradient(90deg, #4f46e5, #6366f1)',
  barBg: string = '#eef2ff'
): string {
  const entries = Object.entries(data).filter(([k]) => k !== 'Not specified' && k !== 'N/A' && k !== 'Unknown');
  const allEntries = entries.length > 0 ? entries : Object.entries(data);

  if (allEntries.length === 0) {
    return '<div class="empty-state">No breakdown data available for this metric</div>';
  }

  const maxVal = Math.max(...allEntries.map(([, v]) => v), 1);

  const rowsHtml = allEntries
    .map(([label, val], idx) => {
      const pctOfTotal = total > 0 ? ((val / total) * 100).toFixed(1) : '0.0';
      const pctOfMax = Math.max(Math.round((val / maxVal) * 100), 4);

      return `
        <div class="chart-row">
          <div class="chart-row-header">
            <span class="chart-label" title="${escapeHtml(label)}">
              <span class="rank-badge">${idx + 1}</span> ${escapeHtml(label)}
            </span>
            <span class="chart-value">
              <strong>${formatNum(val)}</strong> <span class="chart-pct">(${pctOfTotal}%)</span>
            </span>
          </div>
          <div class="chart-track" style="background-color: ${barBg};">
            <div 
              class="chart-fill" 
              style="width: ${pctOfMax}%; background: ${accentGradient};"
            ></div>
          </div>
        </div>
      `;
    })
    .join('');

  return `<div class="horizontal-bar-chart">${rowsHtml}</div>`;
}

function renderVerticalColumnChart(
  data: Record<string, number>,
  total: number
): string {
  const allEntries = Object.entries(data);
  if (allEntries.length === 0) {
    return '<div class="empty-state">No trend timeline data available</div>';
  }

  const maxVal = Math.max(...allEntries.map(([, v]) => v), 1);

  const columnsHtml = allEntries
    .map(([label, val]) => {
      const heightPct = Math.max(Math.round((val / maxVal) * 100), 8);
      const pctOfTotal = total > 0 ? ((val / total) * 100).toFixed(1) : '0';

      return `
        <div class="col-item">
          <span class="col-val-top">${formatNum(val)}</span>
          <div class="col-track">
            <div class="col-bar" style="height: ${heightPct}%;">
              <span class="col-tooltip">${pctOfTotal}%</span>
            </div>
          </div>
          <span class="col-label">${escapeHtml(label)}</span>
        </div>
      `;
    })
    .join('');

  return `
    <div class="vertical-column-chart-wrap">
      <div class="vertical-column-chart">
        ${columnsHtml}
      </div>
    </div>
  `;
}

export function generateApprovedAnalyticsReportHtml(payload: ReportDataPayload): string {
  const kpis = payload.kpis;
  const dq = payload.data_quality;
  const total = kpis?.total_approved || payload.total || 0;
  const breakdowns = payload.breakdowns || {
    by_name: payload.by_name || {},
    by_type: payload.by_type || {},
    by_issuer: payload.by_issuer || {},
    by_course: payload.by_course || {},
    by_year: payload.trends || {},
  };
  const certsPerPerson = payload.certs_per_person || {};
  const topRecipients = payload.recipients || [];
  const records = payload.certificates || [];
  const insights = payload.insights || [];

  const genDate = new Date(payload.generated_at || Date.now()).toLocaleString('en-US', {
    dateStyle: 'full',
    timeStyle: 'medium',
  });

  // Render filter items
  const activeFilters = Object.entries(payload.filters || {})
    .filter(([, v]) => v !== null && v !== undefined && v !== '')
    .map(([k, v]) => {
      const label = k.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
      return `<span class="filter-chip"><strong>${escapeHtml(label)}:</strong> ${escapeHtml(String(v))}</span>`;
    });

  const filterSummaryHtml =
    activeFilters.length > 0
      ? activeFilters.join('')
      : '<span class="filter-chip filter-all">All Approved Certificates (Unfiltered)</span>';

  // Quality percentages
  const dqTotal = dq?.total || total || 1;
  const dqItems = [
    { label: 'Recipient Name', count: dq?.recipient_identified ?? 0 },
    { label: 'Certificate Name', count: dq?.certificate_name_identified ?? 0 },
    { label: 'Completion Date', count: dq?.completion_date_identified ?? 0 },
    { label: 'Issuing Organization', count: dq?.institution_identified ?? 0 },
    { label: 'Certificate Number', count: dq?.certificate_number_identified ?? 0 },
    { label: 'Course / Program', count: dq?.course_identified ?? 0 },
  ];

  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>${escapeHtml(payload.title || 'Approved Certificate Analytics Report')} — DataFlow</title>
  <style>
    :root {
      --primary: #4f46e5;
      --primary-dark: #3730a3;
      --primary-light: #e0e7ff;
      --slate-900: #0f172a;
      --slate-800: #1e293b;
      --slate-700: #334155;
      --slate-600: #475569;
      --slate-500: #64748b;
      --slate-400: #94a3b8;
      --slate-200: #e2e8f0;
      --slate-100: #f1f5f9;
      --slate-50: #f8fafc;
      --emerald-600: #059669;
      --emerald-50: #ecfdf5;
      --blue-600: #2563eb;
      --blue-50: #eff6ff;
      --amber-600: #d97706;
      --amber-50: #fffbeb;
      --purple-600: #7c3aed;
      --purple-50: #f5f3ff;
      --radius: 10px;
      --font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    }

    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }

    body {
      font-family: var(--font-family);
      background-color: #f8fafc;
      color: var(--slate-800);
      line-height: 1.5;
      -webkit-font-smoothing: antialiased;
      padding-bottom: 60px;
    }

    /* Print Controls Bar */
    .action-bar {
      position: sticky;
      top: 0;
      z-index: 100;
      background: rgba(255, 255, 255, 0.95);
      backdrop-filter: blur(10px);
      border-bottom: 1px solid var(--slate-200);
      padding: 12px 24px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    }

    .action-left {
      display: flex;
      align-items: center;
      gap: 12px;
    }

    .brand-tag {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      font-weight: 700;
      font-size: 15px;
      color: var(--slate-900);
    }

    .brand-icon {
      background: var(--primary);
      color: white;
      width: 28px;
      height: 28px;
      border-radius: 6px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 14px;
      font-weight: 800;
    }

    .btn {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 8px 16px;
      border-radius: 6px;
      font-size: 13px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.15s ease;
      border: 1px solid transparent;
      text-decoration: none;
    }

    .btn-primary {
      background: var(--primary);
      color: white;
      box-shadow: 0 1px 2px rgba(79, 70, 229, 0.2);
    }

    .btn-primary:hover {
      background: var(--primary-dark);
    }

    .btn-outline {
      background: white;
      border-color: var(--slate-200);
      color: var(--slate-700);
    }

    .btn-outline:hover {
      background: var(--slate-50);
      border-color: var(--slate-400);
    }

    /* Container */
    .container {
      max-width: 1200px;
      margin: 0 auto;
      padding: 32px 24px;
    }

    /* Header Section */
    .report-header {
      background: white;
      border: 1px solid var(--slate-200);
      border-radius: var(--radius);
      padding: 32px;
      margin-bottom: 24px;
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02);
      position: relative;
      overflow: hidden;
    }

    .report-header::before {
      content: '';
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      height: 4px;
      background: linear-gradient(90deg, #4f46e5, #06b6d4, #10b981);
    }

    .header-top {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      flex-wrap: wrap;
      gap: 16px;
      margin-bottom: 20px;
    }

    .report-title-group h1 {
      font-size: 26px;
      font-weight: 800;
      color: var(--slate-900);
      letter-spacing: -0.02em;
    }

    .report-title-group p {
      font-size: 14px;
      color: var(--slate-500);
      margin-top: 4px;
    }

    .badge-approved {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      background: var(--emerald-50);
      color: var(--emerald-600);
      border: 1px solid #a7f3d0;
      padding: 6px 12px;
      border-radius: 9999px;
      font-size: 12px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }

    .meta-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 16px;
      border-top: 1px solid var(--slate-100);
      padding-top: 20px;
    }

    .meta-item {
      display: flex;
      flex-direction: column;
    }

    .meta-label {
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: var(--slate-400);
      font-weight: 600;
    }

    .meta-val {
      font-size: 14px;
      font-weight: 600;
      color: var(--slate-700);
      margin-top: 2px;
    }

    .filter-pills {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: 16px;
      padding-top: 16px;
      border-top: 1px dashed var(--slate-200);
      align-items: center;
    }

    .filter-pills-label {
      font-size: 12px;
      font-weight: 700;
      color: var(--slate-500);
    }

    .filter-chip {
      background: var(--slate-100);
      border: 1px solid var(--slate-200);
      padding: 3px 10px;
      border-radius: 6px;
      font-size: 12px;
      color: var(--slate-700);
    }

    .filter-all {
      background: var(--primary-light);
      color: var(--primary);
      border-color: #c7d2fe;
      font-weight: 600;
    }

    /* KPI Grid */
    .kpi-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 16px;
      margin-bottom: 28px;
    }

    .kpi-card {
      background: white;
      border: 1px solid var(--slate-200);
      border-radius: var(--radius);
      padding: 18px 20px;
      box-shadow: 0 1px 2px rgba(0, 0, 0, 0.02);
      transition: transform 0.15s ease;
    }

    .kpi-title {
      font-size: 12px;
      font-weight: 600;
      color: var(--slate-500);
      text-transform: uppercase;
      letter-spacing: 0.03em;
    }

    .kpi-number {
      font-size: 26px;
      font-weight: 800;
      color: var(--slate-900);
      margin-top: 6px;
      letter-spacing: -0.02em;
    }

    .kpi-sub {
      font-size: 11px;
      color: var(--slate-400);
      margin-top: 4px;
    }

    /* Section Containers */
    .report-section {
      background: white;
      border: 1px solid var(--slate-200);
      border-radius: var(--radius);
      margin-bottom: 24px;
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02);
      overflow: hidden;
      break-inside: avoid;
    }

    .section-header {
      padding: 20px 24px;
      border-bottom: 1px solid var(--slate-100);
      display: flex;
      justify-content: space-between;
      align-items: center;
      background: var(--slate-50);
    }

    .section-title {
      font-size: 17px;
      font-weight: 700;
      color: var(--slate-900);
      display: flex;
      align-items: center;
      gap: 10px;
    }

    .section-desc {
      font-size: 13px;
      color: var(--slate-500);
      padding: 12px 24px 0 24px;
    }

    .section-body {
      padding: 24px;
    }

    .grid-2 {
      display: grid;
      grid-template-columns: 1.3fr 1fr;
      gap: 24px;
      align-items: start;
    }

    @media (max-width: 900px) {
      .grid-2 {
        grid-template-columns: 1fr;
      }
    }

    /* Horizontal Bar Chart */
    .horizontal-bar-chart {
      display: flex;
      flex-direction: column;
      gap: 14px;
    }

    .chart-row {
      display: flex;
      flex-direction: column;
      gap: 5px;
    }

    .chart-row-header {
      display: flex;
      justify-content: space-between;
      align-items: baseline;
      font-size: 13px;
    }

    .chart-label {
      font-weight: 600;
      color: var(--slate-800);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      max-width: 75%;
      display: flex;
      align-items: center;
      gap: 6px;
    }

    .rank-badge {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 18px;
      height: 18px;
      background: var(--slate-100);
      color: var(--slate-600);
      border-radius: 4px;
      font-size: 10px;
      font-weight: 700;
    }

    .chart-value {
      font-size: 13px;
      color: var(--slate-700);
    }

    .chart-pct {
      font-size: 11px;
      color: var(--slate-400);
    }

    .chart-track {
      width: 100%;
      height: 14px;
      background: var(--slate-100);
      border-radius: 9999px;
      overflow: hidden;
      display: flex;
    }

    .chart-fill {
      height: 100%;
      border-radius: 9999px;
      transition: width 0.3s ease;
      min-width: 4px;
    }

    /* Vertical Column Chart */
    .vertical-column-chart-wrap {
      padding: 16px 0 8px 0;
    }

    .vertical-column-chart {
      display: flex;
      align-items: flex-end;
      justify-content: space-around;
      gap: 16px;
      height: 180px;
      border-bottom: 2px solid var(--slate-200);
      padding-bottom: 8px;
    }

    .col-item {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: flex-end;
      flex: 1;
      height: 100%;
      position: relative;
    }

    .col-val-top {
      font-size: 12px;
      font-weight: 700;
      color: var(--slate-700);
      margin-bottom: 6px;
    }

    .col-track {
      width: 100%;
      max-width: 48px;
      height: 130px;
      display: flex;
      align-items: flex-end;
      justify-content: center;
    }

    .col-bar {
      width: 100%;
      background: linear-gradient(180deg, #6366f1, #4f46e5);
      border-radius: 6px 6px 0 0;
      transition: height 0.3s ease;
      position: relative;
    }

    .col-tooltip {
      display: none;
    }

    .col-label {
      font-size: 12px;
      font-weight: 600;
      color: var(--slate-600);
      margin-top: 10px;
    }

    /* Breakdown Tables */
    .data-table {
      width: 100%;
      border-collapse: collapse;
      font-size: 12.5px;
    }

    .data-table th {
      text-align: left;
      padding: 8px 12px;
      background: var(--slate-50);
      color: var(--slate-500);
      font-weight: 600;
      border-bottom: 1px solid var(--slate-200);
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }

    .data-table td {
      padding: 8px 12px;
      border-bottom: 1px solid var(--slate-100);
      color: var(--slate-700);
    }

    .data-table tr:last-child td {
      border-bottom: none;
    }

    .data-table tr:hover td {
      background-color: var(--slate-50);
    }

    .text-right {
      text-align: right;
    }

    /* Quality meters */
    .dq-list {
      display: flex;
      flex-direction: column;
      gap: 12px;
    }

    .dq-item-header {
      display: flex;
      justify-content: space-between;
      font-size: 13px;
      font-weight: 600;
      margin-bottom: 4px;
    }

    .dq-bar {
      height: 10px;
      background: var(--slate-100);
      border-radius: 999px;
      overflow: hidden;
    }

    .dq-fill {
      height: 100%;
      border-radius: 999px;
      background: linear-gradient(90deg, #10b981, #059669);
    }

    /* Insights */
    .insight-card {
      padding: 14px 16px;
      border-radius: 8px;
      border-left: 4px solid var(--primary);
      background: var(--slate-50);
      margin-bottom: 12px;
    }

    .insight-card.success {
      border-left-color: var(--emerald-600);
      background: #f0fdf4;
    }

    .insight-card.warning {
      border-left-color: var(--amber-600);
      background: #fffbeb;
    }

    .insight-title {
      font-size: 13px;
      font-weight: 700;
      color: var(--slate-900);
    }

    .insight-text {
      font-size: 12px;
      color: var(--slate-600);
      margin-top: 3px;
    }

    .empty-state {
      text-align: center;
      padding: 30px;
      color: var(--slate-400);
      font-size: 13px;
    }

    /* Footer */
    .report-footer {
      border-top: 1px solid var(--slate-200);
      padding: 24px;
      text-align: center;
      font-size: 12px;
      color: var(--slate-400);
      margin-top: 40px;
    }

    /* Print Styles */
    @media print {
      body {
        background: white !important;
        color: #000 !important;
        padding-bottom: 0 !important;
      }
      .action-bar {
        display: none !important;
      }
      .container {
        max-width: 100% !important;
        padding: 0 !important;
      }
      .report-header, .report-section, .kpi-card {
        box-shadow: none !important;
        border: 1px solid #cbd5e1 !important;
        break-inside: avoid !important;
      }
      .chart-fill, .dq-fill, .col-bar {
        -webkit-print-color-adjust: exact !important;
        print-color-adjust: exact !important;
      }
      .badge-approved {
        -webkit-print-color-adjust: exact !important;
        print-color-adjust: exact !important;
      }
    }
  </style>
</head>
<body>

  <!-- Top Action Bar (hidden on print) -->
  <header class="action-bar">
    <div class="action-left">
      <div class="brand-tag">
        <div class="brand-icon">D</div>
        <span>DataFlow Intelligence</span>
      </div>
      <span style="color: var(--slate-300);">|</span>
      <span style="font-size: 13px; color: var(--slate-600); font-weight: 500;">Approved Certificates Audit</span>
    </div>
    <div style="display: flex; gap: 10px;">
      <button onclick="window.print()" class="btn btn-primary">
        🖨️ Print / Save as PDF
      </button>
    </div>
  </header>

  <main class="container">
    <!-- Header Block -->
    <div class="report-header">
      <div class="header-top">
        <div class="report-title-group">
          <h1>${escapeHtml(payload.title || 'Approved Certificate Analytics Report')}</h1>
          <p>Verified credential distribution, quality audit, and recipient analytics</p>
        </div>
        <div class="badge-approved">
          ✓ Verified Approved Scope
        </div>
      </div>

      <div class="meta-grid">
        <div class="meta-item">
          <span class="meta-label">Generated Timestamp</span>
          <span class="meta-val">${escapeHtml(genDate)}</span>
        </div>
        <div class="meta-item">
          <span class="meta-label">Total Verified Scope</span>
          <span class="meta-val">${formatNum(total)} Approved Certificates</span>
        </div>
        <div class="meta-item">
          <span class="meta-label">Unique Recipients</span>
          <span class="meta-val">${formatNum(kpis?.unique_recipients)} Individuals</span>
        </div>
        <div class="meta-item">
          <span class="meta-label">Issuing Bodies</span>
          <span class="meta-val">${formatNum(kpis?.issuing_organizations)} Organizations</span>
        </div>
      </div>

      <div class="filter-pills">
        <span class="filter-pills-label">Filters Applied:</span>
        ${filterSummaryHtml}
      </div>
    </div>

    <!-- Executive KPIs -->
    <div class="kpi-grid">
      <div class="kpi-card">
        <div class="kpi-title">Total Approved</div>
        <div class="kpi-number" style="color: var(--primary);">${formatNum(kpis?.total_approved)}</div>
        <div class="kpi-sub">100% verified credentials</div>
      </div>

      <div class="kpi-card">
        <div class="kpi-title">Unique Recipients</div>
        <div class="kpi-number" style="color: var(--emerald-600);">${formatNum(kpis?.unique_recipients)}</div>
        <div class="kpi-sub">Distinct certificate holders</div>
      </div>

      <div class="kpi-card">
        <div class="kpi-title">Certificate Types</div>
        <div class="kpi-number" style="color: var(--blue-600);">${formatNum(kpis?.certificate_types)}</div>
        <div class="kpi-sub">Distinct classifications</div>
      </div>

      <div class="kpi-card">
        <div class="kpi-title">Certificate Names</div>
        <div class="kpi-number" style="color: var(--purple-600);">${formatNum(kpis?.certificate_names)}</div>
        <div class="kpi-sub">Unique credential titles</div>
      </div>

      <div class="kpi-card">
        <div class="kpi-title">Avg Certs / Person</div>
        <div class="kpi-number" style="color: var(--amber-600);">${kpis?.avg_certs_per_person || '0'}</div>
        <div class="kpi-sub">Multi-certification depth</div>
      </div>

      <div class="kpi-card">
        <div class="kpi-title">Completed This Year</div>
        <div class="kpi-number" style="color: var(--slate-900);">${formatNum(kpis?.completed_this_year)}</div>
        <div class="kpi-sub">${formatNum(kpis?.completed_this_month)} completed this month</div>
      </div>
    </div>

    <!-- REPORT 1: Certificate Name Distribution -->
    <section class="report-section">
      <div class="section-header">
        <div class="section-title">
          <span>📜 Certificate Title Distribution</span>
        </div>
        <span style="font-size: 12px; color: var(--slate-500); font-weight: 600;">
          ${Object.keys(breakdowns.by_name || {}).length} Distinct Names
        </span>
      </div>
      <p class="section-desc">Volume and market frequency breakdown across all approved certificate designations.</p>
      <div class="section-body">
        <div class="grid-2">
          <div>
            ${renderHorizontalBarChart(breakdowns.by_name || {}, total, 'linear-gradient(90deg, #4f46e5, #6366f1)', '#eef2ff')}
          </div>
          <div>
            <table class="data-table">
              <thead>
                <tr>
                  <th>#</th>
                  <th>Certificate Name</th>
                  <th class="text-right">Count</th>
                  <th class="text-right">Share</th>
                </tr>
              </thead>
              <tbody>
                ${(Object.entries(breakdowns.by_name || {}) as [string, number][])
                  .slice(0, 15)
                  .map(([name, count], i) => {
                    const pct = total > 0 ? ((count / total) * 100).toFixed(1) : '0';
                    return `
                      <tr>
                        <td>${i + 1}</td>
                        <td style="font-weight: 600;">${escapeHtml(name)}</td>
                        <td class="text-right font-semibold">${formatNum(count)}</td>
                        <td class="text-right text-slate-500">${pct}%</td>
                      </tr>
                    `;
                  })
                  .join('')}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </section>

    <!-- REPORT 2: Certificate Type Breakdown -->
    <section class="report-section">
      <div class="section-header">
        <div class="section-title">
          <span>🏷️ Certificate Type Classification</span>
        </div>
        <span style="font-size: 12px; color: var(--slate-500); font-weight: 600;">
          ${Object.keys(breakdowns.by_type || {}).length} Categories
        </span>
      </div>
      <p class="section-desc">Distribution across professional licenses, technical credentials, and academic recognitions.</p>
      <div class="section-body">
        <div class="grid-2">
          <div>
            ${renderHorizontalBarChart(breakdowns.by_type || {}, total, 'linear-gradient(90deg, #059669, #10b981)', '#ecfdf5')}
          </div>
          <div>
            <table class="data-table">
              <thead>
                <tr>
                  <th>#</th>
                  <th>Type / Category</th>
                  <th class="text-right">Count</th>
                  <th class="text-right">Share</th>
                </tr>
              </thead>
              <tbody>
                ${(Object.entries(breakdowns.by_type || {}) as [string, number][])
                  .map(([type, count], i) => {
                    const pct = total > 0 ? ((count / total) * 100).toFixed(1) : '0';
                    return `
                      <tr>
                        <td>${i + 1}</td>
                        <td style="font-weight: 600;">${escapeHtml(type)}</td>
                        <td class="text-right font-semibold">${formatNum(count)}</td>
                        <td class="text-right text-slate-500">${pct}%</td>
                      </tr>
                    `;
                  })
                  .join('')}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </section>

    <!-- REPORT 3: Issuing Organizations -->
    <section class="report-section">
      <div class="section-header">
        <div class="section-title">
          <span>🏛️ Issuing Organizations & Accreditation Bodies</span>
        </div>
        <span style="font-size: 12px; color: var(--slate-500); font-weight: 600;">
          ${Object.keys(breakdowns.by_issuer || {}).length} Institutions
        </span>
      </div>
      <p class="section-desc">Institutions, universities, and enterprise vendors issuing verified credentials.</p>
      <div class="section-body">
        <div class="grid-2">
          <div>
            ${renderHorizontalBarChart(breakdowns.by_issuer || {}, total, 'linear-gradient(90deg, #2563eb, #3b82f6)', '#eff6ff')}
          </div>
          <div>
            <table class="data-table">
              <thead>
                <tr>
                  <th>#</th>
                  <th>Organization Name</th>
                  <th class="text-right">Issued</th>
                  <th class="text-right">Share</th>
                </tr>
              </thead>
              <tbody>
                ${(Object.entries(breakdowns.by_issuer || {}) as [string, number][])
                  .slice(0, 15)
                  .map(([issuer, count], i) => {
                    const pct = total > 0 ? ((count / total) * 100).toFixed(1) : '0';
                    return `
                      <tr>
                        <td>${i + 1}</td>
                        <td style="font-weight: 600;">${escapeHtml(issuer)}</td>
                        <td class="text-right font-semibold">${formatNum(count)}</td>
                        <td class="text-right text-slate-500">${pct}%</td>
                      </tr>
                    `;
                  })
                  .join('')}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </section>

    <!-- REPORT 4: Course & Curriculum Programs -->
    <section class="report-section">
      <div class="section-header">
        <div class="section-title">
          <span>📚 Course & Curriculum Specializations</span>
        </div>
        <span style="font-size: 12px; color: var(--slate-500); font-weight: 600;">
          ${Object.keys(breakdowns.by_course || {}).length} Specializations
        </span>
      </div>
      <p class="section-desc">Curriculum pathways and specific training tracks tied to approved certificates.</p>
      <div class="section-body">
        <div class="grid-2">
          <div>
            ${renderHorizontalBarChart(breakdowns.by_course || {}, total, 'linear-gradient(90deg, #7c3aed, #8b5cf6)', '#f5f3ff')}
          </div>
          <div>
            <table class="data-table">
              <thead>
                <tr>
                  <th>#</th>
                  <th>Course Title</th>
                  <th class="text-right">Completions</th>
                  <th class="text-right">Share</th>
                </tr>
              </thead>
              <tbody>
                ${(Object.entries(breakdowns.by_course || {}) as [string, number][])
                  .slice(0, 15)
                  .map(([course, count], i) => {
                    const pct = total > 0 ? ((count / total) * 100).toFixed(1) : '0';
                    return `
                      <tr>
                        <td>${i + 1}</td>
                        <td style="font-weight: 600;">${escapeHtml(course)}</td>
                        <td class="text-right font-semibold">${formatNum(count)}</td>
                        <td class="text-right text-slate-500">${pct}%</td>
                      </tr>
                    `;
                  })
                  .join('')}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </section>

    <!-- REPORT 5: Annual Trends & Timeline -->
    <section class="report-section">
      <div class="section-header">
        <div class="section-title">
          <span>📈 Completion Trajectory & Annual Trends</span>
        </div>
        <span style="font-size: 12px; color: var(--slate-500); font-weight: 600;">
          Historical Distribution
        </span>
      </div>
      <p class="section-desc">Multi-year completion velocity and certificate acquisition over time.</p>
      <div class="section-body">
        <div class="grid-2">
          <div>
            ${renderVerticalColumnChart(breakdowns.by_year || {}, total)}
          </div>
          <div>
            <table class="data-table">
              <thead>
                <tr>
                  <th>Period / Year</th>
                  <th class="text-right">Approved Certs</th>
                  <th class="text-right">Percentage</th>
                </tr>
              </thead>
              <tbody>
                ${(Object.entries(breakdowns.by_year || {}) as [string, number][])
                  .map(([yr, count]) => {
                    const pct = total > 0 ? ((count / total) * 100).toFixed(1) : '0';
                    return `
                      <tr>
                        <td style="font-weight: 600;">${escapeHtml(yr)}</td>
                        <td class="text-right font-semibold">${formatNum(count)}</td>
                        <td class="text-right text-slate-500">${pct}%</td>
                      </tr>
                    `;
                  })
                  .join('')}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </section>

    <!-- REPORT 6: Credential Depth & Top Recipients -->
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin-bottom: 24px;">
      <!-- Certificates Per Person -->
      <section class="report-section" style="margin-bottom: 0;">
        <div class="section-header">
          <div class="section-title">
            <span>👥 Multi-Certification Depth</span>
          </div>
        </div>
        <p class="section-desc">Distribution of how many credentials individual team members hold.</p>
        <div class="section-body">
          ${renderHorizontalBarChart(certsPerPerson, kpis?.unique_recipients || 1, 'linear-gradient(90deg, #d97706, #f59e0b)', '#fffbeb')}
        </div>
      </section>

      <!-- Top Recipients Leaderboard -->
      <section class="report-section" style="margin-bottom: 0;">
        <div class="section-header">
          <div class="section-title">
            <span>🏆 Top Credential Holders</span>
          </div>
        </div>
        <p class="section-desc">Individuals with the highest volume of approved credentials.</p>
        <div class="section-body">
          ${
            topRecipients.length > 0
              ? renderHorizontalBarChart(
                  Object.fromEntries(topRecipients.slice(0, 8).map((r) => [r.name, r.approved_certificates])),
                  total,
                  'linear-gradient(90deg, #4f46e5, #ec4899)',
                  '#fdf2f8'
                )
              : '<div class="empty-state">No recipient rankings recorded</div>'
          }
        </div>
      </section>
    </div>

    <!-- Data Quality Audit -->
    <section class="report-section">
      <div class="section-header">
        <div class="section-title">
          <span>🛡️ Data Integrity & Metadata Completeness Audit</span>
        </div>
        <span style="font-size: 12px; color: var(--emerald-600); font-weight: 700;">
          Verified Scope
        </span>
      </div>
      <p class="section-desc">Field extraction completeness and data confidence audit across all approved records.</p>
      <div class="section-body">
        <div class="dq-list">
          ${dqItems
            .map((item) => {
              const pct = dqTotal > 0 ? Math.min(Math.round((item.count / dqTotal) * 100), 100) : 0;
              return `
                <div class="dq-item">
                  <div class="dq-item-header">
                    <span>${escapeHtml(item.label)}</span>
                    <span>${item.count} of ${dqTotal} (${pct}%)</span>
                  </div>
                  <div class="dq-bar">
                    <div class="dq-fill" style="width: ${pct}%;"></div>
                  </div>
                </div>
              `;
            })
            .join('')}
        </div>
      </div>
    </section>

    <!-- Strategic Insights -->
    ${
      insights.length > 0
        ? `
      <section class="report-section">
        <div class="section-header">
          <div class="section-title">
            <span>💡 Automated Analytics Insights & Findings</span>
          </div>
        </div>
        <div class="section-body">
          ${insights
            .map((ins) => {
              const title = typeof ins === 'string' ? 'Observation' : (ins.title || ins.type || 'Observation');
              const text = typeof ins === 'string' ? ins : (ins.text || '');
              const severity = typeof ins === 'string' ? '' : (ins.severity || '');
              const cls = severity === 'warning' ? 'warning' : severity === 'success' ? 'success' : '';
              return `
                <div class="insight-card ${cls}">
                  <div class="insight-title">${escapeHtml(title)}</div>
                  <div class="insight-text">${escapeHtml(text)}</div>
                </div>
              `;
            })
            .join('')}
        </div>
      </section>
    `
        : ''
    }

    <!-- Detailed Certificate Registry -->
    <section class="report-section">
      <div class="section-header">
        <div class="section-title">
          <span>📋 Approved Certificate Registry</span>
        </div>
        <span style="font-size: 12px; color: var(--slate-500); font-weight: 600;">
          Showing ${Math.min(records.length, 500)} of ${records.length} Records
        </span>
      </div>
      <div class="section-body" style="padding: 0; overflow-x: auto;">
        <table class="data-table" style="font-size: 12px;">
          <thead>
            <tr>
              <th>#</th>
              <th>Recipient</th>
              <th>Certificate Title</th>
              <th>Type</th>
              <th>Issuing Organization</th>
              <th>Course</th>
              <th>Completion Date</th>
              <th>Certificate ID</th>
            </tr>
          </thead>
          <tbody>
            ${records
              .slice(0, 500)
              .map((r, i) => `
                <tr>
                  <td style="color: var(--slate-400);">${i + 1}</td>
                  <td style="font-weight: 600; color: var(--slate-900);">${escapeHtml(r.recipient)}</td>
                  <td>${escapeHtml(r.certificate_name)}</td>
                  <td><span class="filter-chip" style="font-size: 11px;">${escapeHtml(r.certificate_type)}</span></td>
                  <td>${escapeHtml(r.issuing_organization)}</td>
                  <td>${escapeHtml(r.course)}</td>
                  <td>${escapeHtml(r.completion_date)}</td>
                  <td style="font-family: monospace; font-size: 11px; color: var(--slate-500);">${escapeHtml(r.certificate_number)}</td>
                </tr>
              `)
              .join('')}
          </tbody>
        </table>
      </div>
    </section>

    <!-- Footer -->
    <footer class="report-footer">
      <p><strong>DataFlow Intelligence Analytics Engine</strong> · Confidential & Official Audit Report</p>
      <p style="margin-top: 4px;">Computed strictly from officially approved certificates. All rights reserved.</p>
    </footer>
  </main>

</body>
</html>`;
}
