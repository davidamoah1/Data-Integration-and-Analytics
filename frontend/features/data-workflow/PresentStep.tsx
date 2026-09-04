'use client';

import { useState, useMemo } from 'react';
import {
  Presentation,
  Download,
  CheckCircle2,
  RotateCcw,
  Loader2,
  Sparkles,
  Layout,
  Palette,
  Users,
  Layers,
  TrendingUp,
  BarChart3,
  PieChart,
  Table2,
  FileText,
  ShieldAlert,
  Milestone,
  Info,
  Eye,
  X,
  HelpCircle,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Input } from '@/components/ui/Input';
import { cleanMojibake } from '@/lib/utils';

interface Props {
  onGeneratePresentation: (template: string, title: string) => Promise<void>;
  onDownloadPresentation: () => void;
  onStartOver: () => void;
  isGenerating: boolean;
  presentationReady: boolean;
  datasetName: string;
  workflowId?: string;
  industry?: string;
}

interface SlideDefinition {
  num: number;
  title: string;
  categoryTag: string;
  type: 'Header' | 'Scorecard' | 'Native Chart' | 'Audit Table' | 'Insights' | 'Roadmap' | 'Closing';
  purpose: string;
  components: string;
  notes: string;
}

interface DeckArchitecture {
  id: string;
  name: string;
  badge: string;
  audience: string;
  tagline: string;
  desc: string;
  cadence: string;
  defaultTitleSuffix: string;
  palette: {
    name: string;
    hex: string;
    role: string;
    border: string;
  }[];
  slides: SlideDefinition[];
}

const SLIDE_ARCHITECTURES: Record<string, DeckArchitecture> = {
  executive: {
    id: 'executive',
    name: 'Executive Briefing',
    badge: 'C-Suite & Board',
    audience: 'Executive Committee, Board of Directors, Managing Partners',
    tagline: 'High-level strategic synthesis, core scorecard KPIs, and capital allocation',
    desc: 'Bottom-Line-Up-Front (BLUF) narrative tailored for fast executive decisions and risk visibility.',
    cadence: 'BLUF Strategic Summary → Executive Scorecard → Primary Metric Drivers → Segment Mix → Risk Flags → Action Plan',
    defaultTitleSuffix: 'Strategic Executive Briefing',
    palette: [
      { name: 'Navy Midnight', hex: '#0F172A', role: 'Dominant Deep Sapphire Canvas & Framing', border: 'border-slate-800' },
      { name: 'Slate Surface', hex: '#1E293B', role: 'KPI Metric Containers & Intelligence Cards', border: 'border-slate-700' },
      { name: 'Electric Sky', hex: '#38BDF8', role: 'Ultra-Crisp Executive Accent & Key Focus Headers', border: 'border-sky-400' },
      { name: 'Emerald Mint', hex: '#10B981', role: 'Target Milestones & Benchmark Conformance', border: 'border-emerald-500' },
    ],
    slides: [
      {
        num: 1,
        title: 'Title Slide',
        categoryTag: '00 // EXECUTIVE BRIEFING',
        type: 'Header',
        purpose: 'Executive context, sector scope, and presenter governance credentials',
        components: '16:9 Widescreen Title Banner • Sector Benchmark Tag • Presenter Metadata',
        notes: 'Welcome leadership team. This strategic briefing synthesizes macro performance indicators, primary operational drivers, and high-conviction recommendations.',
      },
      {
        num: 2,
        title: 'Executive Summary & Strategic Context',
        categoryTag: '01 // EXECUTIVE SUMMARY',
        type: 'Insights',
        purpose: 'Bottom-Line-Up-Front (BLUF) overview of dataset health and strategic positioning',
        components: '3 Core Strategic Takeaways • Operational Health Check • Scope Callouts',
        notes: 'Deliver the strategic bottom-line upfront: outline dataset breadth, top operational findings, and immediate growth vectors.',
      },
      {
        num: 3,
        title: 'Executive Scorecard & Strategic KPIs',
        categoryTag: '02 // STRATEGIC SCORECARD',
        type: 'Scorecard',
        purpose: 'Commercial benchmarks, core measure means, and variance targets',
        components: '6 Rounded Metric Cards • Target Benchmark Deltas • Visual Accent Borders',
        notes: 'Review executive scorecard KPIs. Pay specific attention to comparison benchmarks and variance against targets.',
      },
      {
        num: 4,
        title: 'Primary Performance Drivers',
        categoryTag: '03 // MACRO PERFORMANCE',
        type: 'Native Chart',
        purpose: 'High-yield dimensional breakdown and volume concentration analysis',
        components: 'Native Clustered Bar Chart • Bottom Analytical Insight Callout Box',
        notes: 'Deep-dive into primary performance drivers. Identify top contributing dimensions and growth vectors.',
      },
      {
        num: 5,
        title: 'Strategic Segment Allocation',
        categoryTag: '04 // PORTFOLIO ALLOCATION',
        type: 'Native Chart',
        purpose: 'Category distribution, portfolio composition, and relative share',
        components: 'Native Donut Chart • Proportional Concentration Markers',
        notes: 'Examine segment allocation and concentration across categories. Highlight overweight and underweight segments.',
      },
      {
        num: 6,
        title: 'Critical Business Findings & Risk Flags',
        categoryTag: '05 // STRATEGIC INSIGHTS',
        type: 'Insights',
        purpose: 'High-priority observations, outlier anomalies, and operational tailwinds',
        components: 'Prioritized Risk Observation Cards • Severity Indicators',
        notes: 'Walk through critical risk alerts and operational findings. Highlight observations with direct revenue or compliance impact.',
      },
      {
        num: 7,
        title: 'Executive Action Plan & Capital Allocation',
        categoryTag: '06 // ACTION ROADMAP',
        type: 'Roadmap',
        purpose: 'Prioritized initiatives, resource allocation, and milestone roadmap',
        components: 'Action Checklist Cards • Milestone Horizons • Resource Allocation Flags',
        notes: 'Present actionable recommendations. Seek leadership consensus on timeline, owners, and capital deployment.',
      },
      {
        num: 8,
        title: 'Strategic Sign-off & Next Steps',
        categoryTag: '07 // GOVERNANCE & APPROVALS',
        type: 'Closing',
        purpose: 'Open leadership discussion, formal approval, and archival sign-off',
        components: 'Executive Closing Header • Discussion Agenda • Formal Approval Block',
        notes: 'Open the floor for leadership Q&A and confirm milestone sign-off.',
      },
    ],
  },
  analytical: {
    id: 'analytical',
    name: 'Analytical Deep-Dive',
    badge: 'Data Science & Quants',
    audience: 'Data Scientists, Quantitative Analysts, Technical PMs, BI Architects',
    tagline: 'Distribution profiling, cross-sectional breakdown, and outlier tests',
    desc: 'Empirical rigor examining variance, continuous histograms, binned frequencies, and Tukey IQR fence anomalies.',
    cadence: 'Statistical Baseline → Binned Distributions → Cross-Sectional Breakdown → Segment Density → Outlier Audit → Modeling Inferences',
    defaultTitleSuffix: 'Quantitative Analysis & Distribution Profiling',
    palette: [
      { name: 'Deep Cobalt', hex: '#082F49', role: 'Mathematical Dark Theme & Contrast Backdrop', border: 'border-cyan-900' },
      { name: 'Dark Slate', hex: '#0F172A', role: 'Diagnostic Card Surfaces & Data Fills', border: 'border-slate-800' },
      { name: 'Electric Cyan', hex: '#06B6D4', role: 'Continuous Histogram Bins & Skewness Accents', border: 'border-cyan-500' },
      { name: 'Matrix Teal', hex: '#0D9488', role: 'Comparative Horizontal Bars & Density Indicators', border: 'border-teal-500' },
    ],
    slides: [
      {
        num: 1,
        title: 'Quantitative Scope & Modeling Foundations',
        categoryTag: '00 // ANALYTICAL DEEP-DIVE',
        type: 'Header',
        purpose: 'Quantitative problem statement, sample dimensions, and analytical scope',
        components: '16:9 Analytical Header • Parameter Scope • Mathematical Rigor Tag',
        notes: 'Welcome analytics team. Today we explore the full statistical distribution, variance characteristics, and correlation dynamics of the dataset.',
      },
      {
        num: 2,
        title: 'Statistical Summary & Baseline Aggregates',
        categoryTag: '01 // STATISTICAL BASELINE',
        type: 'Scorecard',
        purpose: 'Central tendencies, observation volume, and parametric benchmarks',
        components: '6 Metric Cards • N Observations • Mean • Variance • Spread Indicators',
        notes: 'Examine the primary dataset statistics: central tendencies, total observations, and baseline measure means.',
      },
      {
        num: 3,
        title: 'Metric Distribution & Spread',
        categoryTag: '02 // BINNED DISTRIBUTION',
        type: 'Native Chart',
        purpose: 'Continuous binned frequency distribution with skewness and Kurtosis evaluation',
        components: 'Native Histogram Chart • Parametric Spread & Skew Callout Box',
        notes: 'Analyze the continuous binned frequency distribution. Evaluate skewness, kurtosis, and modal peaks.',
      },
      {
        num: 4,
        title: 'Cross-Sectional Breakdown',
        categoryTag: '03 // MULTI-FACTOR COMPARISON',
        type: 'Native Chart',
        purpose: 'Comparative ranking across dimensional categories with delta variance',
        components: 'Native Horizontal Bar Chart • Ranking Order • Category Delta Metrics',
        notes: 'Discuss comparative ranking across dimensional categories. Analyze factor spread and variance.',
      },
      {
        num: 5,
        title: 'Categorical Density & Segment Share',
        categoryTag: '04 // SEGMENT DENSITY',
        type: 'Native Chart',
        purpose: 'Proportional concentration shares and category density mapping',
        components: 'Native Donut Chart • Proportional Share Indicators • Concentration Index',
        notes: 'Examine relative proportion shares and concentration across categorical dimensions.',
      },
      {
        num: 6,
        title: 'Dimensional Interactions & Trends',
        categoryTag: '05 // MULTIVARIATE PATTERNS',
        type: 'Native Chart',
        purpose: 'Secondary dimensional patterns and multivariate interactions',
        components: 'Native Line/Clustered Chart • Correlation Dynamics • Trend Gradient',
        notes: 'Inspect secondary dimensional patterns, correlation dynamics, and multi-factor trends.',
      },
      {
        num: 7,
        title: 'Statistical Anomalies & Outliers',
        categoryTag: '06 // OUTLIER & VARIANCE AUDIT',
        type: 'Insights',
        purpose: 'Tukey IQR fence breaches, extreme deviations, and irregular distributions',
        components: 'Outlier Diagnostic Cards • Tukey IQR Boundaries • Anomaly Flag Severity',
        notes: 'Review outlier points and dispersion boundaries. Validate whether anomalies represent systemic shifts or data artifacts.',
      },
      {
        num: 8,
        title: 'Analytical Inferences & Model Readiness',
        categoryTag: '07 // INFERENCES & MODELING',
        type: 'Roadmap',
        purpose: 'Downstream ML feature engineering guidance and statistical inferences',
        components: 'Feature Scaling Notes • Missing Imputation Impact • Production Model Guidance',
        notes: 'Summarize quantitative inferences, feature scaling recommendations, and downstream ML readiness.',
      },
      {
        num: 9,
        title: 'Technical Q&A & Methodological Discussion',
        categoryTag: '08 // METHODOLOGICAL REVIEW',
        type: 'Closing',
        purpose: 'Open discussion on statistical assumptions, boundaries, and scope',
        components: 'Review Header • Hypothesis Validation Checkpoints • Technical Q&A Block',
        notes: 'Open the floor for questions on statistical methodologies and data boundaries.',
      },
    ],
  },
  research: {
    id: 'research',
    name: 'Technical / Research',
    badge: 'Auditors & Governance',
    audience: 'Data Governance Committees, Compliance Auditors, System Architects',
    tagline: 'Structured methodology, data quality audit tables, and statistical inference',
    desc: 'Formal data hygiene scorecard, completeness verification %, and pipeline engineering roadmap.',
    cadence: 'Data Provenance & Hygiene Audit → Empirical Parametric Distributions → Factor Variance → Boundary Exceptions → Engineering Roadmap',
    defaultTitleSuffix: 'Technical Research & Data Audit',
    palette: [
      { name: 'Obsidian Tech', hex: '#18181B', role: 'Structural Canvas & Technical Surface', border: 'border-zinc-800' },
      { name: 'Zinc Surface', hex: '#27272A', role: 'Schema Audit Tables & Boundary Panels', border: 'border-zinc-700' },
      { name: 'Audit Emerald', hex: '#059669', role: 'Data Completeness % & Hygiene Badges', border: 'border-emerald-600' },
      { name: 'Blueprint Blue', hex: '#2563EB', role: 'Parametric Charts & Implementation Roadmap', border: 'border-blue-600' },
    ],
    slides: [
      {
        num: 1,
        title: 'Title Slide',
        categoryTag: '00 // TECHNICAL RESEARCH',
        type: 'Header',
        purpose: 'Empirical data audit scope, schema provenance, and compliance context',
        components: '16:9 Research Cover • Audit Protocol Tag • Version & Schema Metadata',
        notes: 'Presenting the empirical data audit and technical research findings for formal review and compliance sign-off.',
      },
      {
        num: 2,
        title: 'Data Hygiene & Schema Quality Scorecard',
        categoryTag: '01 // SCHEMA AUDIT',
        type: 'Audit Table',
        purpose: 'Completeness %, null/missing checks, type sanity, and record volume verification',
        components: 'ETL Conformance Grid • Missing Value Rates • Normalization Status',
        notes: 'Detail data hygiene verification, missing value patterns, and ETL boundary integrity.',
      },
      {
        num: 3,
        title: 'Empirical Parametric Distributions',
        categoryTag: '02 // PARAMETRIC EVALUATION',
        type: 'Native Chart',
        purpose: 'Continuous parametric verification and normality distribution testing',
        components: 'Native Histogram Chart • Normality & Kurtosis Verification Box',
        notes: 'Evaluate empirical distribution bins. Assess normal vs skewed properties across observation records.',
      },
      {
        num: 4,
        title: 'Factor Variance Breakdown',
        categoryTag: '03 // FACTOR VARIANCE',
        type: 'Native Chart',
        purpose: 'Variance decomposition across primary categorical factors',
        components: 'Native Clustered Bar Chart • ANOVA Factor Variance Indicators',
        notes: 'Analyze factor variance across categorical dimensions. Confirm between-group vs within-group dispersion.',
      },
      {
        num: 5,
        title: 'Discrete Categorical Classifications',
        categoryTag: '04 // DISCRETE MAPPING',
        type: 'Native Chart',
        purpose: 'Discrete categorical frequency mappings and cardinality audit',
        components: 'Native Donut Chart • Cardinality Index • Classification Density',
        notes: 'Review discrete categorical frequency mappings and verify low-sample category boundaries.',
      },
      {
        num: 6,
        title: 'Audit Exceptions & Boundary Violations',
        categoryTag: '05 // AUDIT EXCEPTIONS',
        type: 'Insights',
        purpose: 'Anomalous observations, extreme variance, and data quality alerts',
        components: 'Audit Exception Cards • Boundary Violation Badges • Critical Alert Flags',
        notes: 'Examine anomalous observations and boundary exceptions identified during the audit.',
      },
      {
        num: 7,
        title: 'Methodological Scope & Technical Limitations',
        categoryTag: '06 // TECHNICAL BOUNDARIES',
        type: 'Audit Table',
        purpose: 'Boundary assumptions, confidence intervals, and reproducibility criteria',
        components: 'Confidence Interval Table • Sample Constraints • Stationarity Boundaries',
        notes: 'Document methodological constraints, sample boundaries, and reproducibility criteria.',
      },
      {
        num: 8,
        title: 'Production Engineering & Implementation Roadmap',
        categoryTag: '07 // ENGINEERING ROADMAP',
        type: 'Roadmap',
        purpose: 'Systemic architecture adjustments, validation checks, and data pipeline steps',
        components: 'Phased Technical Roadmap • Data Pipeline Gates • Architecture Milestones',
        notes: 'Detail concrete technical implementation steps for data engineering and production deployment.',
      },
      {
        num: 9,
        title: 'Technical Appendix & Audit Sign-off',
        categoryTag: '08 // FORMAL SIGN-OFF',
        type: 'Closing',
        purpose: 'Formal committee review completion, audit certification, and archival',
        components: 'Audit Archival Summary • Governance Certification • Committee Sign-off',
        notes: 'Conclude technical review and open for committee validation sign-off.',
      },
    ],
  },
  pitch: {
    id: 'pitch',
    name: 'Investor / Pitch',
    badge: 'Investors & Growth',
    audience: 'Venture Capitalists, Angel Syndicates, Growth Partners',
    tagline: 'Fast-paced narrative with punchy headline metrics and strategic growth steps',
    desc: 'Compelling market whitespace, traction acceleration, unit economics, and 12-month runway.',
    cadence: 'The Friction Hook → Hero Traction Numbers → Outperformance Velocity → Category Share → Moats → Growth Runway',
    defaultTitleSuffix: 'Investor Pitch & Growth Strategy',
    palette: [
      { name: 'Pitch Dark', hex: '#09090B', role: 'High-Impact Dark Mode Slide Stage', border: 'border-zinc-800' },
      { name: 'Deep Violet', hex: '#1E1B4B', role: 'Hero Card Backdrops & Elevated Containers', border: 'border-violet-900' },
      { name: 'Electric Violet', hex: '#7C3AED', role: 'Growth Velocity Charts & Key Catalysts', border: 'border-violet-500' },
      { name: 'Growth Rose', hex: '#F43F5E', role: 'Big-Number KPI Badges & Market Traction', border: 'border-rose-500' },
    ],
    slides: [
      {
        num: 1,
        title: 'Title Slide',
        categoryTag: '00 // INVESTOR PITCH',
        type: 'Header',
        purpose: 'Vision hook, sector disruption narrative, and investment thesis',
        components: '16:9 Hero Pitch Header • Category Disruption Tag • Founder Metadata',
        notes: 'Welcome partners and investors. Today we showcase empirical traction, high-velocity growth drivers, and strategic market capture.',
      },
      {
        num: 2,
        title: 'The Market Inefficiency & Strategic Opportunity',
        categoryTag: '01 // OPPORTUNITY & HOOK',
        type: 'Insights',
        purpose: 'Empirical proof of market friction and the value-capture unlock',
        components: '3 Problem & Value Unlock Cards • Market Friction Quantification',
        notes: 'Set the hook: explain the core friction demonstrated by the data and how our strategic focus captures value.',
      },
      {
        num: 3,
        title: 'Headline Traction & Performance Scorecard',
        categoryTag: '02 // HERO TRACTION',
        type: 'Scorecard',
        purpose: 'Core proof points demonstrating momentum, scale, and operating yield',
        components: '4 Big-Number Hero Metric Cards • Growth Proof Points • Outperformance Flags',
        notes: 'Present hero metric traction. Highlight outperformance benchmarks and growth trajectories.',
      },
      {
        num: 4,
        title: 'Growth Velocity & Outperformance Trends',
        categoryTag: '03 // GROWTH VELOCITY',
        type: 'Native Chart',
        purpose: 'Primary growth drivers, volume compounding, and velocity trajectory',
        components: 'Native Trend Bar/Line Chart • Compounding Velocity Insight Box',
        notes: 'Demonstrate operational compounding and volume acceleration in core categories.',
      },
      {
        num: 5,
        title: 'Market Share & Category Dominance',
        categoryTag: '04 // MARKET SHARE',
        type: 'Native Chart',
        purpose: 'Volume capture, category dominance, and relative concentration',
        components: 'Native Donut Chart • Segment Dominance Share • Whitespace Index',
        notes: 'Highlight addressable category dominance and addressable whitespace capture.',
      },
      {
        num: 6,
        title: 'Competitive Moats & Market Tailwinds',
        categoryTag: '05 // DEFENSIBLE MOATS',
        type: 'Insights',
        purpose: 'Structural advantages, proprietary efficiencies, and defensibility',
        components: 'Defensible Moat Cards • Network Effect Markers • Margin Catalysts',
        notes: 'Detail our structural defensibility, unit economics advantage, and scalable moats.',
      },
      {
        num: 7,
        title: '12-Month Execution Milestones & Runway',
        categoryTag: '06 // GROWTH RUNWAY',
        type: 'Roadmap',
        purpose: 'Phased scale targets, capital allocation runway, and expansion goals',
        components: 'Quarterly Milestones • Resource Allocation Runway • Expansion Targets',
        notes: 'Review the 12-month execution roadmap and milestone gates for capital deployment.',
      },
      {
        num: 8,
        title: 'Investment Thesis & Vision Sign-off',
        categoryTag: '07 // INVESTMENT THESIS',
        type: 'Closing',
        purpose: 'Conviction closing statement, partner discussion, and terms Q&A',
        components: 'Investment Thesis Summary • Target Return Vectors • Partner Q&A',
        notes: 'Summarize the investment thesis and open the floor for syndicate discussion.',
      },
    ],
  },
};

export function PresentStep({
  onGeneratePresentation,
  onDownloadPresentation,
  onStartOver,
  isGenerating,
  presentationReady,
  datasetName,
  workflowId,
  industry = 'general',
}: Props) {
  const [selectedTemplate, setSelectedTemplate] = useState('executive');
  const cleanName = useMemo(() => cleanMojibake(datasetName || 'Dataset'), [datasetName]);

  // Track if user has customized title manually
  const [hasCustomTitle, setHasCustomTitle] = useState(false);
  const [title, setTitle] = useState(`${cleanName} — Strategic Executive Briefing`);

  // Active architecture
  const activeDeck = useMemo(
    () => SLIDE_ARCHITECTURES[selectedTemplate] || SLIDE_ARCHITECTURES.executive,
    [selectedTemplate],
  );

  // Selected slide modal for deep inspection
  const [inspectedSlide, setInspectedSlide] = useState<SlideDefinition | null>(null);

  // Switch template and optionally update title if not customized
  const handleSelectTemplate = (templateId: string) => {
    setSelectedTemplate(templateId);
    const targetDeck = SLIDE_ARCHITECTURES[templateId];
    if (targetDeck && !hasCustomTitle) {
      setTitle(`${cleanName} — ${targetDeck.defaultTitleSuffix}`);
    }
  };

  const handleResetTitle = () => {
    setTitle(`${cleanName} — ${activeDeck.defaultTitleSuffix}`);
    setHasCustomTitle(false);
  };

  const handleGenerate = () => {
    onGeneratePresentation(selectedTemplate, title);
  };

  // Helper for type color badges
  const getTypeBadgeStyle = (type: SlideDefinition['type']) => {
    switch (type) {
      case 'Header':
        return 'bg-blue-500/10 text-blue-600 dark:text-blue-400 border-blue-500/20';
      case 'Scorecard':
        return 'bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/20';
      case 'Native Chart':
        return 'bg-sky-500/10 text-sky-600 dark:text-sky-400 border-sky-500/20';
      case 'Audit Table':
        return 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20';
      case 'Insights':
        return 'bg-purple-500/10 text-purple-600 dark:text-purple-400 border-purple-500/20';
      case 'Roadmap':
        return 'bg-orange-500/10 text-orange-600 dark:text-orange-400 border-orange-500/20';
      case 'Closing':
        return 'bg-slate-500/10 text-slate-600 dark:text-slate-400 border-slate-500/20';
      default:
        return 'bg-muted text-muted-foreground border-border';
    }
  };

  return (
    <div className="space-y-6">
      {/* ── 1. Configuration & Narrative Theme Selection Card ── */}
      <Card className="shadow-xs border-border/80">
        <CardHeader>
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <CardTitle className="text-base flex items-center gap-2">
                <Presentation className="h-5 w-5 text-primary" />
                PowerPoint Presentation Designer (.pptx)
              </CardTitle>
              <CardDescription>
                Generates a native 16:9 widescreen presentation with embedded native charts and speaker notes
              </CardDescription>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="text-xs font-mono">
                16:9 Widescreen
              </Badge>
              <Badge className="bg-primary/10 text-primary border-primary/20 text-xs">
                Native PPTX
              </Badge>
            </div>
          </div>
        </CardHeader>

        <CardContent className="space-y-5">
          {/* Title Input */}
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground block">
                Presentation Title
              </label>
              {hasCustomTitle && (
                <button
                  type="button"
                  onClick={handleResetTitle}
                  className="text-[11px] text-primary hover:underline flex items-center gap-1 font-medium"
                >
                  <RotateCcw className="h-3 w-3" /> Reset to theme default
                </button>
              )}
            </div>
            <Input
              value={title}
              onChange={(e) => {
                setTitle(e.target.value);
                setHasCustomTitle(true);
              }}
              placeholder="Enter presentation title..."
              className="h-10 text-sm font-medium"
            />
          </div>

          {/* Theme & Narrative Selection Grid */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground block">
                Presentation Theme & Narrative Style
              </label>
              <span className="text-[11px] text-muted-foreground">
                Selects slide deck sequence, color palette, and analytical focus
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {Object.values(SLIDE_ARCHITECTURES).map((deck) => {
                const isSelected = selectedTemplate === deck.id;
                return (
                  <button
                    key={deck.id}
                    type="button"
                    onClick={() => handleSelectTemplate(deck.id)}
                    className={`p-4 rounded-xl border text-left transition-all duration-200 relative group ${
                      isSelected
                        ? 'border-primary bg-primary/[0.04] ring-2 ring-primary/30 shadow-sm'
                        : 'border-border/80 hover:border-primary/40 hover:bg-muted/30'
                    }`}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-bold text-foreground group-hover:text-primary transition-colors">
                            {deck.name}
                          </span>
                          <Badge variant="outline" className="text-[10px] py-0 px-1.5 font-normal">
                            {deck.badge}
                          </Badge>
                        </div>
                        <p className="text-xs text-muted-foreground mt-1 leading-snug">
                          {deck.desc}
                        </p>
                      </div>

                      {isSelected ? (
                        <Badge className="text-[10px] bg-primary text-primary-foreground shrink-0">
                          Selected
                        </Badge>
                      ) : (
                        <span className="text-[10px] text-muted-foreground/60 shrink-0 font-mono">
                          {deck.slides.length} slides
                        </span>
                      )}
                    </div>

                    {/* Palette Swatches Preview */}
                    <div className="mt-3 pt-3 border-t border-border/50 flex items-center justify-between">
                      <div className="flex items-center gap-1.5">
                        <span className="text-[10px] text-muted-foreground font-mono mr-1">Palette:</span>
                        {deck.palette.map((swatch, idx) => (
                          <div
                            key={idx}
                            className="h-3.5 w-3.5 rounded-full border border-black/10 shadow-xs"
                            style={{ backgroundColor: swatch.hex }}
                            title={`${swatch.name} (${swatch.hex}): ${swatch.role}`}
                          />
                        ))}
                      </div>
                      <span className="text-[10px] text-primary/80 font-medium">
                        {deck.slides.length} Slides
                      </span>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* ── 2. Dynamic Slide Deck Architecture Section ── */}
      <Card className="border-2 border-primary/20 bg-card shadow-sm">
        <CardHeader className="pb-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="space-y-1">
              <div className="flex flex-wrap items-center gap-2">
                <Layout className="h-5 w-5 text-primary" />
                <CardTitle className="text-base font-bold">Slide Deck Architecture</CardTitle>
                <Badge variant="outline" className="text-xs font-semibold text-primary border-primary/30">
                  {activeDeck.name}
                </Badge>
                <Badge className="bg-primary text-primary-foreground text-xs font-mono">
                  {activeDeck.slides.length} Slides
                </Badge>
                {presentationReady && (
                  <Badge className="bg-emerald-600 text-white text-xs flex items-center gap-1">
                    <CheckCircle2 className="h-3.5 w-3.5" /> Ready
                  </Badge>
                )}
              </div>
              <CardDescription className="text-xs text-muted-foreground">
                Synthesizes Executive Summary, Metrics, Visualizations, and Recommendations into editable slides.
              </CardDescription>
            </div>

            {/* Action Buttons */}
            <div className="flex items-center gap-3 shrink-0">
              {!presentationReady ? (
                <Button
                  size="default"
                  onClick={handleGenerate}
                  disabled={isGenerating}
                  className="px-6 font-semibold shadow-xs"
                >
                  {isGenerating ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Rendering {activeDeck.name}...
                    </>
                  ) : (
                    <>
                      <Presentation className="mr-2 h-4 w-4" />
                      Create & Download PPTX ({activeDeck.slides.length} Slides)
                    </>
                  )}
                </Button>
              ) : (
                <div className="flex items-center gap-2">
                  <Button
                    size="default"
                    onClick={onDownloadPresentation}
                    disabled={isGenerating}
                    className="px-6 font-semibold shadow-xs"
                  >
                    {isGenerating ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Downloading...
                      </>
                    ) : (
                      <>
                        <Download className="mr-2 h-4 w-4" />
                        Download PPTX Again
                      </>
                    )}
                  </Button>
                </div>
              )}
            </div>
          </div>

          {/* Strategic Context Bar: Audience, Narrative Cadence & Palette */}
          <div className="mt-4 p-3.5 rounded-lg bg-muted/40 border border-border/80 space-y-2.5">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
              <div className="flex items-start gap-2">
                <Users className="h-4 w-4 text-primary shrink-0 mt-0.5" />
                <div>
                  <span className="font-semibold text-foreground">Target Audience: </span>
                  <span className="text-muted-foreground">{activeDeck.audience}</span>
                </div>
              </div>
              <div className="flex items-start gap-2">
                <Layers className="h-4 w-4 text-primary shrink-0 mt-0.5" />
                <div>
                  <span className="font-semibold text-foreground">Narrative Cadence: </span>
                  <span className="text-muted-foreground leading-snug">{activeDeck.cadence}</span>
                </div>
              </div>
            </div>

            {/* Theme Color Palette Bar */}
            <div className="pt-2 border-t border-border/60 flex flex-wrap items-center gap-4 text-xs">
              <div className="flex items-center gap-1.5 text-muted-foreground font-medium">
                <Palette className="h-3.5 w-3.5 text-primary" />
                <span>Native Theme Color DNA:</span>
              </div>
              <div className="flex flex-wrap items-center gap-3">
                {activeDeck.palette.map((swatch, idx) => (
                  <div key={idx} className="flex items-center gap-1.5">
                    <div
                      className="h-3 w-3 rounded-full border border-black/15 shadow-xs"
                      style={{ backgroundColor: swatch.hex }}
                    />
                    <span className="text-[11px] font-medium text-foreground">{swatch.name}</span>
                    <span className="text-[10px] text-muted-foreground font-mono">({swatch.hex})</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </CardHeader>

        <CardContent className="pt-2">
          {/* Slide Outline Grid */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Generated Slide Outline ({activeDeck.slides.length} Slides • Widescreen 16:9)
              </p>
              <span className="text-[11px] text-muted-foreground">
                Click any slide to view presenter notes and technical structure
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
              {activeDeck.slides.map((slide) => (
                <div
                  key={slide.num}
                  onClick={() => setInspectedSlide(slide)}
                  className="rounded-lg border border-border/80 p-3 bg-card hover:bg-muted/30 hover:border-primary/50 transition-all duration-200 cursor-pointer flex flex-col justify-between group shadow-2xs"
                >
                  <div>
                    {/* Top Row: Slide Number + Type Badge */}
                    <div className="flex items-center justify-between gap-1 mb-2">
                      <span className="text-[10px] font-mono font-bold text-muted-foreground">
                        SLIDE {slide.num.toString().padStart(2, '0')}
                      </span>
                      <Badge
                        variant="outline"
                        className={`text-[10px] font-medium py-0 px-2 ${getTypeBadgeStyle(slide.type)}`}
                      >
                        {slide.type}
                      </Badge>
                    </div>

                    {/* Category Tag */}
                    <p className="text-[9px] font-mono font-semibold text-primary/80 uppercase tracking-wider mb-1 truncate">
                      {slide.categoryTag}
                    </p>

                    {/* Title */}
                    <p className="font-bold text-xs text-foreground group-hover:text-primary transition-colors leading-tight line-clamp-2">
                      {slide.title}
                    </p>

                    {/* Purpose */}
                    <p className="text-[11px] text-muted-foreground mt-1.5 line-clamp-2 leading-snug">
                      {slide.purpose}
                    </p>
                  </div>

                  {/* Bottom Elements Preview */}
                  <div className="mt-3 pt-2 border-t border-border/60 flex items-center justify-between text-[10px]">
                    <span className="text-muted-foreground/80 truncate font-mono">
                      {slide.components.split('•')[0].trim()}
                    </span>
                    <span className="text-primary/70 group-hover:text-primary font-medium flex items-center gap-0.5 shrink-0 ml-1">
                      Inspect <Eye className="h-3 w-3" />
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* ── 3. Slide Deep Inspection Modal ── */}
      {inspectedSlide && (
        <div
          className="fixed inset-0 z-50 bg-black/60 backdrop-blur-xs flex items-center justify-center p-4 animate-in fade-in duration-150"
          onClick={() => setInspectedSlide(null)}
        >
          <div
            className="bg-card border border-border rounded-xl max-w-lg w-full p-6 shadow-xl space-y-4 animate-in zoom-in-95 duration-150"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div className="flex items-start justify-between gap-3">
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-xs font-mono font-bold text-primary">
                    SLIDE {inspectedSlide.num.toString().padStart(2, '0')} OF {activeDeck.slides.length.toString().padStart(2, '0')}
                  </span>
                  <Badge variant="outline" className={`text-xs ${getTypeBadgeStyle(inspectedSlide.type)}`}>
                    {inspectedSlide.type}
                  </Badge>
                </div>
                <h3 className="text-base font-bold text-foreground mt-1">
                  {inspectedSlide.title}
                </h3>
                <p className="text-xs text-muted-foreground font-mono">
                  {inspectedSlide.categoryTag}
                </p>
              </div>

              <button
                type="button"
                onClick={() => setInspectedSlide(null)}
                className="p-1 rounded-md hover:bg-muted text-muted-foreground hover:text-foreground transition-colors"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Content Details */}
            <div className="space-y-3 pt-2 text-xs">
              <div className="p-3 rounded-lg bg-muted/40 border border-border/80">
                <span className="font-semibold text-foreground block mb-1">
                  Presentation Objective:
                </span>
                <p className="text-muted-foreground leading-relaxed">
                  {inspectedSlide.purpose}
                </p>
              </div>

              <div className="p-3 rounded-lg bg-muted/40 border border-border/80">
                <span className="font-semibold text-foreground block mb-1">
                  Layout & Native Elements:
                </span>
                <p className="text-muted-foreground leading-relaxed">
                  {inspectedSlide.components}
                </p>
              </div>

              <div className="p-3 rounded-lg bg-primary/5 border border-primary/20">
                <span className="font-semibold text-primary block mb-1 flex items-center gap-1.5">
                  <FileText className="h-3.5 w-3.5" /> Embedded Presenter Speaker Notes:
                </span>
                <p className="text-foreground/90 italic leading-relaxed">
                  &ldquo;{inspectedSlide.notes}&rdquo;
                </p>
              </div>
            </div>

            {/* Modal Footer */}
            <div className="pt-2 flex justify-end">
              <Button size="sm" variant="outline" onClick={() => setInspectedSlide(null)}>
                Close Preview
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* ── 4. Workflow Complete Banner ── */}
      {presentationReady && (
        <Card className="bg-emerald-50/80 dark:bg-emerald-950/20 border-emerald-200 dark:border-emerald-900">
          <CardContent className="pt-6 text-center">
            <CheckCircle2 className="h-10 w-10 text-emerald-600 dark:text-emerald-400 mx-auto mb-3" />
            <p className="text-lg font-bold text-foreground">Data-to-Decision Pipeline Completed</p>
            <p className="text-xs text-muted-foreground mt-1 max-w-md mx-auto leading-relaxed">
              Your raw data has successfully traveled through understanding, cleaning, advanced analysis, visual dashboarding,
              formal reporting, and native PowerPoint slide generation.
            </p>
            <div className="flex flex-wrap justify-center gap-1.5 mt-4">
              <Badge variant="outline" className="text-xs">1. Upload</Badge>
              <Badge variant="outline" className="text-xs">2. Understand</Badge>
              <Badge variant="outline" className="text-xs">3. Clean</Badge>
              <Badge variant="outline" className="text-xs">4. Analyze</Badge>
              <Badge variant="outline" className="text-xs">5. Visualize</Badge>
              <Badge variant="outline" className="text-xs">6. Report</Badge>
              <Badge className="bg-emerald-600 text-white text-xs">7. Present ({activeDeck.name})</Badge>
            </div>
            <div className="mt-6 flex justify-center gap-3">
              <Button size="sm" onClick={onDownloadPresentation} className="shadow-xs">
                <Download className="mr-2 h-3.5 w-3.5" />
                Download {activeDeck.name} (.pptx)
              </Button>
              <Button variant="outline" size="sm" onClick={onStartOver}>
                <RotateCcw className="mr-2 h-3.5 w-3.5" />
                Analyze Another Dataset
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
