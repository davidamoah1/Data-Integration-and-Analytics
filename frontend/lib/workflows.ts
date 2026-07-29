import {
  Heart, GraduationCap, Building2, Landmark, FlaskConical,
  Database, BarChart3, FileText, Upload, CheckCircle2,
  ArrowRight, Sparkles, Users, TrendingUp, Map, Presentation,
  type LucideIcon,
} from 'lucide-react';

export interface WorkflowStep {
  label: string;
  description: string;
  href?: string;
  icon: LucideIcon;
}

export interface Workflow {
  id: string;
  title: string;
  description: string;
  icon: LucideIcon;
  color: string;
  category: 'healthcare' | 'research' | 'business' | 'education' | 'government' | 'general';
  steps: WorkflowStep[];
}

export const WORKFLOWS: Workflow[] = [
  {
    id: 'healthcare',
    title: 'Healthcare Analytics',
    description: 'Connect hospital data, validate, generate KPIs and Ministry reports',
    icon: Heart,
    color: 'bg-red-500',
    category: 'healthcare',
    steps: [
      { label: 'Connect Hospital Database', description: 'Link your hospital database or import patient data', href: '/connectors', icon: Database },
      { label: 'Import Patient Data', description: 'Upload or connect patient records', href: '/datasets', icon: Upload },
      { label: 'Validate Data', description: 'Run automated data quality checks', href: '/datasets/workflow', icon: CheckCircle2 },
      { label: 'Generate KPIs', description: 'Create healthcare KPIs automatically', href: '/analytics', icon: TrendingUp },
      { label: 'Build Dashboards', description: 'Visualize patient outcomes and trends', href: '/analytics', icon: BarChart3 },
      { label: 'Generate Ministry Reports', description: 'Create compliance reports for Ministry of Health', href: '/reports', icon: FileText },
      { label: 'Export PDF', description: 'Export reports as professional PDF', href: '/reports', icon: FileText },
      { label: 'Export PowerPoint', description: 'Create presentation-ready slides', href: '/reports', icon: Presentation },
      { label: 'Schedule Monthly Report', description: 'Automate recurring report generation', href: '/scheduler', icon: Sparkles },
    ],
  },
  {
    id: 'research',
    title: 'Research Analysis',
    description: 'Import surveys, clean, analyze, and produce publication-ready reports',
    icon: FlaskConical,
    color: 'bg-purple-500',
    category: 'research',
    steps: [
      { label: 'Import Survey', description: 'Upload survey data (CSV, Excel, or connect API)', href: '/datasets', icon: Upload },
      { label: 'Clean Responses', description: 'Remove duplicates, fix formatting', href: '/datasets/workflow', icon: CheckCircle2 },
      { label: 'Detect Missing Values', description: 'Identify and handle missing data', href: '/studios/cleaning', icon: Sparkles },
      { label: 'Statistical Analysis', description: 'Run descriptive and inferential statistics', href: '/studios/statistics', icon: BarChart3 },
      { label: 'Generate Charts', description: 'Create publication-ready visualizations', href: '/studios/visualizations', icon: BarChart3 },
      { label: 'Interpret Results', description: 'AI-powered interpretation of findings', href: '/ai', icon: Sparkles },
      { label: 'Publication-Ready Tables', description: 'Format tables for journals and dissertations', href: '/reports', icon: FileText },
      { label: 'Generate Dissertation Report', description: 'Compile full research report', href: '/reports', icon: FileText },
      { label: 'Export', description: 'Export to PDF, Word, or Excel', href: '/reports', icon: FileText },
    ],
  },
  {
    id: 'business',
    title: 'Business Intelligence',
    description: 'Connect sales data, analyze, forecast, and create board reports',
    icon: Building2,
    color: 'bg-blue-500',
    category: 'business',
    steps: [
      { label: 'Connect Sales Data', description: 'Import from CRM, ERP, or spreadsheet', href: '/connectors', icon: Database },
      { label: 'Clean Data', description: 'Standardize and validate records', href: '/datasets/workflow', icon: CheckCircle2 },
      { label: 'Analyze', description: 'Run sales performance analysis', href: '/analytics', icon: BarChart3 },
      { label: 'Executive Dashboard', description: 'Build real-time executive dashboard', href: '/analytics', icon: BarChart3 },
      { label: 'Forecast', description: 'Generate sales forecasts and projections', href: '/studios/ml-lab', icon: TrendingUp },
      { label: 'Recommendations', description: 'AI-driven business recommendations', href: '/ai', icon: Sparkles },
      { label: 'Board Report', description: 'Create professional board report', href: '/reports', icon: FileText },
      { label: 'Presentation', description: 'Export as PowerPoint presentation', href: '/reports', icon: Presentation },
    ],
  },
  {
    id: 'education',
    title: 'Education Analytics',
    description: 'Import student records, analyze performance, and generate academic reports',
    icon: GraduationCap,
    color: 'bg-indigo-500',
    category: 'education',
    steps: [
      { label: 'Import Student Records', description: 'Upload student data from SIS or spreadsheet', href: '/datasets', icon: Upload },
      { label: 'Attendance Analysis', description: 'Analyze attendance patterns', href: '/analytics', icon: BarChart3 },
      { label: 'Performance Analysis', description: 'Evaluate academic performance', href: '/studios/statistics', icon: TrendingUp },
      { label: 'Subject Trends', description: 'Identify trends across subjects', href: '/analytics', icon: TrendingUp },
      { label: 'Institution Dashboard', description: 'Build school-wide dashboard', href: '/analytics', icon: BarChart3 },
      { label: 'Academic Reports', description: 'Generate report cards and summaries', href: '/reports', icon: FileText },
      { label: 'Presentation', description: 'Export for board or parent meetings', href: '/reports', icon: Presentation },
    ],
  },
  {
    id: 'government',
    title: 'Government Analytics',
    description: 'Import census data, analyze regions, and produce policy reports',
    icon: Landmark,
    color: 'bg-emerald-500',
    category: 'government',
    steps: [
      { label: 'Import Census', description: 'Upload census or population data', href: '/datasets', icon: Upload },
      { label: 'Validate', description: 'Run data quality checks', href: '/datasets/workflow', icon: CheckCircle2 },
      { label: 'Regional Analysis', description: 'Analyze data by region and district', href: '/analytics', icon: BarChart3 },
      { label: 'Maps', description: 'Create geographic visualizations', href: '/studios/visualizations', icon: Map },
      { label: 'Population Insights', description: 'Derive demographic insights', href: '/ai', icon: Sparkles },
      { label: 'Policy Reports', description: 'Generate evidence-based policy reports', href: '/reports', icon: FileText },
      { label: 'Presentation', description: 'Export for government briefings', href: '/reports', icon: Presentation },
    ],
  },
];

export interface GuidedTask {
  id: string;
  title: string;
  description: string;
  icon: LucideIcon;
  color: string;
  workflowId?: string;
  href: string;
}

export const GUIDED_TASKS: GuidedTask[] = [
  { id: 'analyze-sales', title: 'Analyze Sales', description: 'Connect and analyze your sales data', icon: TrendingUp, color: 'bg-blue-500', workflowId: 'business', href: '/workflows/business' },
  { id: 'analyze-patients', title: 'Analyze Patients', description: 'Import and analyze patient data', icon: Heart, color: 'bg-red-500', workflowId: 'healthcare', href: '/workflows/healthcare' },
  { id: 'analyze-students', title: 'Analyze Students', description: 'Import and analyze student records', icon: GraduationCap, color: 'bg-indigo-500', workflowId: 'education', href: '/workflows/education' },
  { id: 'research-report', title: 'Create Research Report', description: 'Clean survey data and produce publication-ready report', icon: FlaskConical, color: 'bg-purple-500', workflowId: 'research', href: '/workflows/research' },
  { id: 'board-report', title: 'Prepare Board Report', description: 'Build executive dashboard and board presentation', icon: FileText, color: 'bg-slate-600', workflowId: 'business', href: '/workflows/business' },
  { id: 'clean-dataset', title: 'Clean Dataset', description: 'Fix missing values, duplicates, and formatting', icon: Sparkles, color: 'bg-green-500', href: '/datasets/workflow' },
  { id: 'connect-database', title: 'Connect Database', description: 'Link external databases and APIs', icon: Database, color: 'bg-cyan-500', href: '/connectors' },
  { id: 'capture-records', title: 'Capture Paper Records', description: 'Scan and extract data from paper documents', icon: Upload, color: 'bg-amber-500', href: '/capture' },
  { id: 'monthly-report', title: 'Generate Monthly Report', description: 'Create and schedule recurring reports', icon: FileText, color: 'bg-orange-500', href: '/reports' },
];

export interface SmartRecommendation {
  trigger: string;
  title: string;
  description: string;
  actionLabel: string;
  href: string;
  icon: LucideIcon;
}

export const RECOMMENDATIONS: Record<string, SmartRecommendation[]> = {
  'dataset.imported': [
    { trigger: 'dataset.imported', title: 'Validate your data', description: 'Run automated quality checks to find missing values and errors', actionLabel: 'Validate Data', href: '/datasets/workflow', icon: CheckCircle2 },
    { trigger: 'dataset.imported', title: 'Create a dashboard', description: 'Visualize your data with charts and KPIs', actionLabel: 'Build Dashboard', href: '/analytics', icon: BarChart3 },
  ],
  'dataset.validated': [
    { trigger: 'dataset.validated', title: 'Generate dashboard', description: 'Turn your clean data into visual insights', actionLabel: 'Create Dashboard', href: '/analytics', icon: BarChart3 },
    { trigger: 'dataset.validated', title: 'Run statistical analysis', description: 'Get descriptive stats and trends', actionLabel: 'Analyze', href: '/studios/statistics', icon: TrendingUp },
  ],
  'dashboard.created': [
    { trigger: 'dashboard.created', title: 'Create executive report', description: 'Compile your dashboard into a professional report', actionLabel: 'Generate Report', href: '/reports', icon: FileText },
    { trigger: 'dashboard.created', title: 'Share with team', description: 'Invite colleagues to collaborate', actionLabel: 'Share', href: '/studios/collaboration', icon: Users },
  ],
  'report.generated': [
    { trigger: 'report.generated', title: 'Export as PowerPoint', description: 'Create a presentation-ready version', actionLabel: 'Export', href: '/reports', icon: Presentation },
    { trigger: 'report.generated', title: 'Schedule recurring report', description: 'Automate monthly or weekly generation', actionLabel: 'Schedule', href: '/scheduler', icon: Sparkles },
  ],
};

export interface TemplateDefinition {
  id: string;
  name: string;
  description: string;
  industry: string;
  icon: LucideIcon;
  color: string;
  kpis: string[];
  charts: string[];
  filters: string[];
}

export const TEMPLATES: TemplateDefinition[] = [
  {
    id: 'executive-dashboard',
    name: 'Executive Dashboard',
    description: 'High-level KPIs and metrics for leadership teams',
    industry: 'Business',
    icon: Building2,
    color: 'bg-blue-500',
    kpis: ['Revenue', 'Growth Rate', 'Customer Acquisition', 'Churn Rate', 'Profit Margin'],
    charts: ['Revenue Trend', 'Growth by Quarter', 'Customer Funnel', 'Geographic Distribution'],
    filters: ['Date Range', 'Region', 'Product Line'],
  },
  {
    id: 'research-dashboard',
    name: 'Research Dashboard',
    description: 'Survey response analysis and statistical summaries',
    industry: 'Research',
    icon: FlaskConical,
    color: 'bg-purple-500',
    kpis: ['Response Rate', 'Completion Rate', 'Mean Score', 'Standard Deviation', 'Sample Size'],
    charts: ['Response Distribution', 'Cross-tabulation', 'Trend Analysis', 'Correlation Matrix'],
    filters: ['Survey Wave', 'Demographic', 'Question Category'],
  },
  {
    id: 'hospital-dashboard',
    name: 'Hospital Dashboard',
    description: 'Patient outcomes, capacity, and quality metrics',
    industry: 'Healthcare',
    icon: Heart,
    color: 'bg-red-500',
    kpis: ['Patient Satisfaction', 'Average Length of Stay', 'Readmission Rate', 'Bed Occupancy', 'Mortality Rate'],
    charts: ['Patient Flow', 'Outcome Trends', 'Department Performance', 'Capacity Utilization'],
    filters: ['Department', 'Time Period', 'Patient Type'],
  },
  {
    id: 'university-dashboard',
    name: 'University Dashboard',
    description: 'Student performance, enrollment, and academic metrics',
    industry: 'Education',
    icon: GraduationCap,
    color: 'bg-indigo-500',
    kpis: ['Graduation Rate', 'Enrollment', 'GPA Average', 'Retention Rate', 'Course Completion'],
    charts: ['Enrollment Trends', 'Performance by Faculty', 'Attendance Patterns', 'Graduation Pipeline'],
    filters: ['Faculty', 'Academic Year', 'Program'],
  },
  {
    id: 'financial-dashboard',
    name: 'Financial Dashboard',
    description: 'Revenue, expenses, and financial health metrics',
    industry: 'Finance',
    icon: TrendingUp,
    color: 'bg-green-500',
    kpis: ['Total Revenue', 'Operating Expenses', 'Net Profit', 'Cash Flow', 'ROI'],
    charts: ['Revenue vs Expenses', 'Profit Trend', 'Cash Flow Statement', 'Budget Variance'],
    filters: ['Fiscal Period', 'Department', 'Currency'],
  },
  {
    id: 'sales-dashboard',
    name: 'Sales Dashboard',
    description: 'Pipeline, conversion, and revenue performance',
    industry: 'Business',
    icon: BarChart3,
    color: 'bg-cyan-500',
    kpis: ['Total Sales', 'Conversion Rate', 'Average Deal Size', 'Sales Cycle', 'Pipeline Value'],
    charts: ['Sales Pipeline', 'Revenue by Region', 'Top Performers', 'Monthly Trend'],
    filters: ['Sales Rep', 'Region', 'Product Category'],
  },
  {
    id: 'population-dashboard',
    name: 'Population Dashboard',
    description: 'Census data and demographic insights',
    industry: 'Government',
    icon: Landmark,
    color: 'bg-emerald-500',
    kpis: ['Total Population', 'Growth Rate', 'Median Age', 'Urban vs Rural', 'Literacy Rate'],
    charts: ['Population Pyramid', 'Regional Distribution', 'Growth Trend', 'Demographic Breakdown'],
    filters: ['Region', 'Age Group', 'Gender'],
  },
  {
    id: 'survey-dashboard',
    name: 'Survey Dashboard',
    description: 'Real-time survey response tracking and analysis',
    industry: 'Research',
    icon: Users,
    color: 'bg-pink-500',
    kpis: ['Responses', 'Completion Rate', 'Average Score', 'NPS Score', 'Response Time'],
    charts: ['Response Timeline', 'Score Distribution', 'NPS Breakdown', 'Demographic Split'],
    filters: ['Survey Type', 'Date Range', 'Channel'],
  },
  {
    id: 'inventory-dashboard',
    name: 'Inventory Dashboard',
    description: 'Stock levels, turnover, and supply chain metrics',
    industry: 'Retail',
    icon: Building2,
    color: 'bg-orange-500',
    kpis: ['Stock Level', 'Turnover Rate', 'Out of Stock', 'Reorder Points', 'Inventory Value'],
    charts: ['Stock by Category', 'Turnover Trend', 'Reorder Alerts', 'Supplier Performance'],
    filters: ['Warehouse', 'Category', 'Supplier'],
  },
  {
    id: 'laboratory-dashboard',
    name: 'Laboratory Dashboard',
    description: 'Test volumes, turnaround times, and quality metrics',
    industry: 'Healthcare',
    icon: FlaskConical,
    color: 'bg-teal-500',
    kpis: ['Test Volume', 'Turnaround Time', 'Accuracy Rate', 'Equipment Utilization', 'Rejection Rate'],
    charts: ['Test Volume Trend', 'Turnaround by Test Type', 'Quality Control', 'Equipment Status'],
    filters: ['Lab Section', 'Test Type', 'Date Range'],
  },
];
