import {
  Sparkles, Upload, BarChart3, FileText, ScanLine,
  Building2, Shield, Users, Database, CheckCircle2,
  FlaskConical, ArrowRight, type LucideIcon,
} from 'lucide-react';
import { ROLES } from './permissions';

export interface OnboardingStep {
  id: string;
  title: string;
  description: string;
  icon: LucideIcon;
  href?: string;
  optional?: boolean;
}

export interface OnboardingFlow {
  role: string;
  title: string;
  description: string;
  steps: OnboardingStep[];
}

const FLOWS: Record<string, OnboardingFlow> = {
  [ROLES.SUPER_ADMIN]: {
    role: ROLES.SUPER_ADMIN,
    title: 'Platform Configuration',
    description: 'Set up the platform for all organizations',
    steps: [
      { id: 'welcome', title: 'Welcome to DataFlow Platform', description: 'You have full platform access. Let\'s configure the system.', icon: Sparkles },
      { id: 'review-orgs', title: 'Review Organizations', description: 'View and manage all organizations on the platform', icon: Building2, href: '/admin-portal' },
      { id: 'feature-flags', title: 'Configure Feature Flags', description: 'Enable or disable platform features', icon: Shield, href: '/admin-portal/feature-flags' },
      { id: 'security', title: 'Review Security Settings', description: 'Check security policies and alerts', icon: Shield, href: '/admin-portal/security' },
      { id: 'done', title: 'Platform Ready', description: 'The platform is configured and ready for organizations', icon: CheckCircle2 },
    ],
  },

  [ROLES.ORG_OWNER]: {
    role: ROLES.ORG_OWNER,
    title: 'Organization Setup',
    description: 'Set up your organization for success',
    steps: [
      { id: 'welcome', title: 'Welcome to Your Organization', description: 'Let\'s get your organization set up in a few steps.', icon: Sparkles },
      { id: 'invite', title: 'Invite Team Members', description: 'Bring your team on board by sending invitations', icon: Users, href: '/admin' },
      { id: 'departments', title: 'Create Departments', description: 'Organize your team into departments', icon: Building2, href: '/admin/departments' },
      { id: 'upload', title: 'Upload First Dataset', description: 'Import your first data file to get started', icon: Upload, href: '/datasets' },
      { id: 'dashboard', title: 'Create Dashboard', description: 'Build your first dashboard to visualize data', icon: BarChart3, href: '/analytics' },
      { id: 'done', title: 'Organization Ready', description: 'Your organization is set up and ready to go', icon: CheckCircle2 },
    ],
  },

  [ROLES.ORG_ADMIN]: {
    role: ROLES.ORG_ADMIN,
    title: 'Organization Setup',
    description: 'Set up your organization for success',
    steps: [
      { id: 'welcome', title: 'Welcome to Your Organization', description: 'Let\'s get your organization set up in a few steps.', icon: Sparkles },
      { id: 'invite', title: 'Invite Team Members', description: 'Bring your team on board by sending invitations', icon: Users, href: '/admin' },
      { id: 'departments', title: 'Create Departments', description: 'Organize your team into departments', icon: Building2, href: '/admin/departments' },
      { id: 'upload', title: 'Upload First Dataset', description: 'Import your first data file to get started', icon: Upload, href: '/datasets' },
      { id: 'dashboard', title: 'Create Dashboard', description: 'Build your first dashboard to visualize data', icon: BarChart3, href: '/analytics' },
      { id: 'done', title: 'Organization Ready', description: 'Your organization is set up and ready to go', icon: CheckCircle2 },
    ],
  },

  [ROLES.DEPT_MANAGER]: {
    role: ROLES.DEPT_MANAGER,
    title: 'Department Setup',
    description: 'Get your department up and running',
    steps: [
      { id: 'welcome', title: 'Welcome to Your Department', description: 'Let\'s set up your department workspace.', icon: Sparkles },
      { id: 'review-team', title: 'Review Team Members', description: 'See who\'s in your department', icon: Users, href: '/admin' },
      { id: 'upload', title: 'Upload Department Data', description: 'Import data for your department', icon: Upload, href: '/datasets' },
      { id: 'dashboard', title: 'Create Department Dashboard', description: 'Build a dashboard for department KPIs', icon: BarChart3, href: '/analytics' },
      { id: 'done', title: 'Department Ready', description: 'Your department workspace is ready', icon: CheckCircle2 },
    ],
  },

  [ROLES.DATA_ENGINEER]: {
    role: ROLES.DATA_ENGINEER,
    title: 'Engineering Setup',
    description: 'Start building data pipelines',
    steps: [
      { id: 'welcome', title: 'Welcome, Engineer', description: 'Let\'s get you started with data engineering.', icon: Sparkles },
      { id: 'connect', title: 'Connect a Database', description: 'Link an external database or API', icon: Database, href: '/connectors' },
      { id: 'upload', title: 'Upload a Dataset', description: 'Or upload a file directly', icon: Upload, href: '/datasets' },
      { id: 'schedule', title: 'Schedule a Pipeline', description: 'Set up automated data processing', icon: CheckCircle2, href: '/scheduler' },
      { id: 'done', title: 'Engineering Ready', description: 'Your engineering workspace is ready', icon: CheckCircle2 },
    ],
  },

  [ROLES.DATA_ANALYST]: {
    role: ROLES.DATA_ANALYST,
    title: 'Analyst Onboarding',
    description: 'Start analyzing data',
    steps: [
      { id: 'welcome', title: 'Welcome, Analyst', description: 'Let\'s get you analyzing data in no time.', icon: Sparkles },
      { id: 'upload', title: 'Upload Your First Dataset', description: 'Import a CSV, Excel, or JSON file', icon: Upload, href: '/datasets' },
      { id: 'validate', title: 'Run Data Validation', description: 'Check data quality automatically', icon: CheckCircle2, href: '/datasets/workflow' },
      { id: 'dashboard', title: 'Create a Dashboard', description: 'Visualize your data with charts and KPIs', icon: BarChart3, href: '/analytics' },
      { id: 'report', title: 'Generate a Report', description: 'Create a professional report from your data', icon: FileText, href: '/reports' },
      { id: 'done', title: 'Analyst Ready', description: 'You\'re all set to start analyzing!', icon: CheckCircle2 },
    ],
  },

  [ROLES.BUSINESS_ANALYST]: {
    role: ROLES.BUSINESS_ANALYST,
    title: 'Business Analytics Onboarding',
    description: 'Start exploring business insights',
    steps: [
      { id: 'welcome', title: 'Welcome, Business Analyst', description: 'Let\'s explore your business data.', icon: Sparkles },
      { id: 'dashboards', title: 'Explore Dashboards', description: 'View existing dashboards built by your team', icon: BarChart3, href: '/analytics' },
      { id: 'reports', title: 'View Reports', description: 'Check out available reports', icon: FileText, href: '/reports' },
      { id: 'ai', title: 'Try AI Assistant', description: 'Ask questions about your data in natural language', icon: Sparkles, href: '/ai', optional: true },
      { id: 'done', title: 'Ready to Analyze', description: 'You\'re all set to explore business insights!', icon: CheckCircle2 },
    ],
  },

  [ROLES.EXECUTIVE]: {
    role: ROLES.EXECUTIVE,
    title: 'Executive Onboarding',
    description: 'Get a high-level view of your organization',
    steps: [
      { id: 'welcome', title: 'Welcome', description: 'Let\'s show you the key metrics for your organization.', icon: Sparkles },
      { id: 'dashboards', title: 'View Executive Dashboards', description: 'See high-level KPIs and performance metrics', icon: BarChart3, href: '/analytics' },
      { id: 'reports', title: 'Browse Reports', description: 'Review recent reports from your team', icon: FileText, href: '/reports' },
      { id: 'done', title: 'Ready', description: 'You\'re all set to monitor your organization!', icon: CheckCircle2 },
    ],
  },

  [ROLES.RESEARCHER]: {
    role: ROLES.RESEARCHER,
    title: 'Researcher Onboarding',
    description: 'Start your research journey',
    steps: [
      { id: 'welcome', title: 'Welcome, Researcher', description: 'Let\'s get you started with research analysis.', icon: Sparkles },
      { id: 'import', title: 'Import Your First Survey', description: 'Upload survey data (CSV, Excel, or JSON)', icon: Upload, href: '/datasets' },
      { id: 'statistics', title: 'Run Statistical Analysis', description: 'Perform descriptive and inferential statistics', icon: FlaskConical, href: '/studios/statistics' },
      { id: 'report', title: 'Generate Publication Report', description: 'Create a publication-ready report', icon: FileText, href: '/reports' },
      { id: 'done', title: 'Research Ready', description: 'Your research workspace is ready!', icon: CheckCircle2 },
    ],
  },

  [ROLES.AUDITOR]: {
    role: ROLES.AUDITOR,
    title: 'Auditor Onboarding',
    description: 'Review system activity and compliance',
    steps: [
      { id: 'welcome', title: 'Welcome, Auditor', description: 'Let\'s review the audit capabilities.', icon: Sparkles },
      { id: 'audit', title: 'View Audit Logs', description: 'Review system activity and user actions', icon: Shield, href: '/audit' },
      { id: 'members', title: 'Review Members', description: 'See who has access to the organization', icon: Users, href: '/admin' },
      { id: 'done', title: 'Audit Ready', description: 'You\'re all set to review compliance!', icon: CheckCircle2 },
    ],
  },

  [ROLES.DEPT_OFFICER]: {
    role: ROLES.DEPT_OFFICER,
    title: 'Department Officer Onboarding',
    description: 'Get started with department operations',
    steps: [
      { id: 'welcome', title: 'Welcome', description: 'Let\'s get you started with department operations.', icon: Sparkles },
      { id: 'datasets', title: 'View Datasets', description: 'See datasets available to your department', icon: Database, href: '/datasets' },
      { id: 'reports', title: 'View Reports', description: 'Check available reports', icon: FileText, href: '/reports' },
      { id: 'done', title: 'Ready', description: 'You\'re all set!', icon: CheckCircle2 },
    ],
  },

  [ROLES.DATA_ENTRY_OFFICER]: {
    role: ROLES.DATA_ENTRY_OFFICER,
    title: 'Data Capture Onboarding',
    description: 'Start capturing data from documents',
    steps: [
      { id: 'welcome', title: 'Welcome, Data Entry Officer', description: 'Let\'s get you started with Smart Data Capture.', icon: Sparkles },
      { id: 'capture', title: 'Capture Your First Document', description: 'Upload a paper document and let OCR extract the data', icon: ScanLine, href: '/capture' },
      { id: 'review', title: 'Review Extracted Data', description: 'Check confidence scores and correct any errors', icon: CheckCircle2, href: '/capture' },
      { id: 'submit', title: 'Submit Verified Data', description: 'Save the captured data as a dataset', icon: Upload, href: '/datasets' },
      { id: 'done', title: 'Capture Ready', description: 'You\'re all set to capture documents!', icon: CheckCircle2 },
    ],
  },

  [ROLES.VIEWER]: {
    role: ROLES.VIEWER,
    title: 'Viewer Onboarding',
    description: 'Explore dashboards and reports',
    steps: [
      { id: 'welcome', title: 'Welcome', description: 'Let\'s show you around the platform.', icon: Sparkles },
      { id: 'dashboards', title: 'Explore Dashboards', description: 'View dashboards shared with you', icon: BarChart3, href: '/analytics' },
      { id: 'reports', title: 'Browse Reports', description: 'Check out available reports', icon: FileText, href: '/reports' },
      { id: 'done', title: 'Ready to Explore', description: 'You\'re all set to view insights!', icon: CheckCircle2 },
    ],
  },
};

const DEFAULT_FLOW: OnboardingFlow = {
  role: 'viewer',
  title: 'Welcome to DataFlow',
  description: 'Let\'s get you started',
  steps: [
    { id: 'welcome', title: 'Welcome', description: 'Let\'s get you started with DataFlow.', icon: Sparkles },
    { id: 'explore', title: 'Explore Dashboards', description: 'View available dashboards', icon: BarChart3, href: '/analytics' },
    { id: 'done', title: 'Ready', description: 'You\'re all set!', icon: CheckCircle2 },
  ],
};

export function getOnboardingFlow(role: string): OnboardingFlow {
  return FLOWS[role] || DEFAULT_FLOW;
}

export function getOnboardingFlowForRoles(roles: string[]): OnboardingFlow {
  const { getPrimaryRole } = require('./navigation');
  const primaryRole = getPrimaryRole(roles);
  return getOnboardingFlow(primaryRole);
}

export { FLOWS };
