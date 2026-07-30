import {
  Database, BarChart3, FileText, Upload, ScanLine,
  Users, Building2, Shield, Sparkles, FlaskConical,
  TrendingUp, CheckCircle2, Zap, Bot, CalendarClock,
  type LucideIcon,
} from 'lucide-react';
import { ROLES } from './permissions';

export interface HelpTopic {
  id: string;
  title: string;
  description: string;
  href?: string;
  icon: LucideIcon;
}

export interface HelpCategory {
  id: string;
  label: string;
  topics: HelpTopic[];
}

export interface HelpConfig {
  role: string;
  categories: HelpCategory[];
  searchPlaceholder: string;
}

const HELP_CONFIGS: Record<string, HelpConfig> = {
  [ROLES.SUPER_ADMIN]: {
    role: ROLES.SUPER_ADMIN,
    searchPlaceholder: 'Search platform help...',
    categories: [
      {
        id: 'platform',
        label: 'Platform Management',
        topics: [
          { id: 'manage-orgs', title: 'How to manage organizations', description: 'View, suspend, and activate organizations', icon: Building2, href: '/admin-portal' },
          { id: 'feature-flags', title: 'How to configure feature flags', description: 'Enable or disable platform features', icon: Zap, href: '/admin-portal/feature-flags' },
          { id: 'security', title: 'How to review security alerts', description: 'Monitor and respond to security events', icon: Shield, href: '/admin-portal/security' },
        ],
      },
      {
        id: 'system',
        label: 'System Operations',
        topics: [
          { id: 'monitoring', title: 'How to monitor platform health', description: 'View uptime, incidents, and system status', icon: TrendingUp, href: '/admin-portal/monitoring' },
          { id: 'audit', title: 'How to view audit logs', description: 'Review all platform activity', icon: Shield, href: '/audit' },
        ],
      },
    ],
  },

  [ROLES.ORG_OWNER]: {
    role: ROLES.ORG_OWNER,
    searchPlaceholder: 'Search organization help...',
    categories: [
      {
        id: 'org-setup',
        label: 'Organization Setup',
        topics: [
          { id: 'invite-users', title: 'How to invite users', description: 'Send invitations to team members', icon: Users, href: '/admin' },
          { id: 'create-depts', title: 'How to create departments', description: 'Organize your team into departments', icon: Building2, href: '/admin/departments' },
          { id: 'manage-roles', title: 'How to assign roles', description: 'Control what users can do', icon: Shield, href: '/admin' },
        ],
      },
      {
        id: 'data',
        label: 'Data Management',
        topics: [
          { id: 'upload-data', title: 'How to upload datasets', description: 'Import CSV, Excel, or JSON files', icon: Upload, href: '/datasets' },
          { id: 'create-dashboards', title: 'How to create dashboards', description: 'Visualize your data', icon: BarChart3, href: '/analytics' },
          { id: 'generate-reports', title: 'How to generate reports', description: 'Create professional reports', icon: FileText, href: '/reports' },
        ],
      },
    ],
  },

  [ROLES.ORG_ADMIN]: {
    role: ROLES.ORG_ADMIN,
    searchPlaceholder: 'Search organization help...',
    categories: [
      {
        id: 'org-setup',
        label: 'Organization Setup',
        topics: [
          { id: 'invite-users', title: 'How to invite users', description: 'Send invitations to team members', icon: Users, href: '/admin' },
          { id: 'create-depts', title: 'How to create departments', description: 'Organize your team into departments', icon: Building2, href: '/admin/departments' },
          { id: 'manage-roles', title: 'How to assign roles', description: 'Control what users can do', icon: Shield, href: '/admin' },
        ],
      },
      {
        id: 'data',
        label: 'Data Management',
        topics: [
          { id: 'upload-data', title: 'How to upload datasets', description: 'Import CSV, Excel, or JSON files', icon: Upload, href: '/datasets' },
          { id: 'create-dashboards', title: 'How to create dashboards', description: 'Visualize your data', icon: BarChart3, href: '/analytics' },
          { id: 'generate-reports', title: 'How to generate reports', description: 'Create professional reports', icon: FileText, href: '/reports' },
        ],
      },
    ],
  },

  [ROLES.DEPT_MANAGER]: {
    role: ROLES.DEPT_MANAGER,
    searchPlaceholder: 'Search department help...',
    categories: [
      {
        id: 'dept',
        label: 'Department Management',
        topics: [
          { id: 'view-team', title: 'How to view your team', description: 'See department members and their activity', icon: Users, href: '/admin' },
          { id: 'assign-work', title: 'How to assign work', description: 'Delegate tasks to team members', icon: CheckCircle2 },
        ],
      },
      {
        id: 'data',
        label: 'Data & Analytics',
        topics: [
          { id: 'upload-data', title: 'How to upload datasets', description: 'Import data for your department', icon: Upload, href: '/datasets' },
          { id: 'create-dashboards', title: 'How to create department dashboards', description: 'Track department KPIs', icon: BarChart3, href: '/analytics' },
          { id: 'generate-reports', title: 'How to generate reports', description: 'Create reports from department data', icon: FileText, href: '/reports' },
        ],
      },
    ],
  },

  [ROLES.DATA_ENGINEER]: {
    role: ROLES.DATA_ENGINEER,
    searchPlaceholder: 'Search engineering help...',
    categories: [
      {
        id: 'pipelines',
        label: 'Data Pipelines',
        topics: [
          { id: 'connect-db', title: 'How to connect a database', description: 'Link external databases and APIs', icon: Database, href: '/connectors' },
          { id: 'upload-data', title: 'How to upload datasets', description: 'Import data files', icon: Upload, href: '/datasets' },
          { id: 'schedule', title: 'How to schedule pipelines', description: 'Automate data processing', icon: CalendarClock, href: '/scheduler' },
        ],
      },
    ],
  },

  [ROLES.DATA_ANALYST]: {
    role: ROLES.DATA_ANALYST,
    searchPlaceholder: 'Search analytics help...',
    categories: [
      {
        id: 'data',
        label: 'Data Preparation',
        topics: [
          { id: 'upload-data', title: 'How to upload datasets', description: 'Import CSV, Excel, or JSON files', icon: Upload, href: '/datasets' },
          { id: 'clean-data', title: 'How to clean data', description: 'Fix missing values, duplicates, and formatting', icon: Sparkles, href: '/datasets/workflow' },
          { id: 'validate', title: 'How to run validation', description: 'Automated data quality checks', icon: CheckCircle2, href: '/datasets/workflow' },
        ],
      },
      {
        id: 'analysis',
        label: 'Analysis & Visualization',
        topics: [
          { id: 'create-dashboards', title: 'How to create dashboards', description: 'Build visual dashboards with charts and KPIs', icon: BarChart3, href: '/analytics' },
          { id: 'generate-reports', title: 'How to generate reports', description: 'Create professional reports from your data', icon: FileText, href: '/reports' },
          { id: 'ai-assistant', title: 'How to use the AI assistant', description: 'Ask questions about your data in natural language', icon: Bot, href: '/ai' },
        ],
      },
    ],
  },

  [ROLES.BUSINESS_ANALYST]: {
    role: ROLES.BUSINESS_ANALYST,
    searchPlaceholder: 'Search business analytics help...',
    categories: [
      {
        id: 'view',
        label: 'Dashboards & Reports',
        topics: [
          { id: 'view-dashboards', title: 'How to view dashboards', description: 'Explore dashboards built by your team', icon: BarChart3, href: '/analytics' },
          { id: 'view-reports', title: 'How to view reports', description: 'Browse and download reports', icon: FileText, href: '/reports' },
          { id: 'ai-assistant', title: 'How to use the AI assistant', description: 'Get AI-powered business insights', icon: Bot, href: '/ai' },
        ],
      },
    ],
  },

  [ROLES.EXECUTIVE]: {
    role: ROLES.EXECUTIVE,
    searchPlaceholder: 'Search executive help...',
    categories: [
      {
        id: 'overview',
        label: 'Executive View',
        topics: [
          { id: 'view-dashboards', title: 'How to view executive dashboards', description: 'See high-level KPIs and performance', icon: BarChart3, href: '/analytics' },
          { id: 'view-reports', title: 'How to view reports', description: 'Review reports from your team', icon: FileText, href: '/reports' },
        ],
      },
    ],
  },

  [ROLES.RESEARCHER]: {
    role: ROLES.RESEARCHER,
    searchPlaceholder: 'Search research help...',
    categories: [
      {
        id: 'research',
        label: 'Research Workflow',
        topics: [
          { id: 'import-survey', title: 'How to import survey data', description: 'Upload survey responses from CSV, Excel, or API', icon: Upload, href: '/datasets' },
          { id: 'stat-analysis', title: 'How to perform statistical analysis', description: 'Run descriptive and inferential statistics', icon: FlaskConical, href: '/studios/statistics' },
          { id: 'pub-report', title: 'How to generate publication reports', description: 'Create publication-ready reports', icon: FileText, href: '/reports' },
          { id: 'ai-assistant', title: 'How to use AI for interpretation', description: 'Get AI-powered interpretation of findings', icon: Bot, href: '/ai' },
        ],
      },
    ],
  },

  [ROLES.AUDITOR]: {
    role: ROLES.AUDITOR,
    searchPlaceholder: 'Search audit help...',
    categories: [
      {
        id: 'audit',
        label: 'Audit & Compliance',
        topics: [
          { id: 'view-audit', title: 'How to view audit logs', description: 'Review system activity and user actions', icon: Shield, href: '/audit' },
          { id: 'review-users', title: 'How to review user access', description: 'Check who has access to the organization', icon: Users, href: '/admin' },
        ],
      },
    ],
  },

  [ROLES.DEPT_OFFICER]: {
    role: ROLES.DEPT_OFFICER,
    searchPlaceholder: 'Search help...',
    categories: [
      {
        id: 'data',
        label: 'Data & Reports',
        topics: [
          { id: 'view-datasets', title: 'How to view datasets', description: 'See datasets available to your department', icon: Database, href: '/datasets' },
          { id: 'view-reports', title: 'How to view reports', description: 'Check available reports', icon: FileText, href: '/reports' },
        ],
      },
    ],
  },

  [ROLES.DATA_ENTRY_OFFICER]: {
    role: ROLES.DATA_ENTRY_OFFICER,
    searchPlaceholder: 'Search capture help...',
    categories: [
      {
        id: 'capture',
        label: 'Smart Data Capture',
        topics: [
          { id: 'capture-doc', title: 'How to capture paper forms', description: 'Upload documents and let OCR extract data', icon: ScanLine, href: '/capture' },
          { id: 'review-data', title: 'How to review extracted data', description: 'Check confidence scores and correct errors', icon: CheckCircle2, href: '/capture' },
          { id: 'submit-data', title: 'How to submit verified data', description: 'Save captured data as a dataset', icon: Upload, href: '/datasets' },
        ],
      },
    ],
  },

  [ROLES.VIEWER]: {
    role: ROLES.VIEWER,
    searchPlaceholder: 'Search help...',
    categories: [
      {
        id: 'view',
        label: 'Viewing Content',
        topics: [
          { id: 'view-dashboards', title: 'How to view dashboards', description: 'Explore dashboards shared with you', icon: BarChart3, href: '/analytics' },
          { id: 'view-reports', title: 'How to view and download reports', description: 'Browse and export reports', icon: FileText, href: '/reports' },
        ],
      },
    ],
  },
};

const DEFAULT_CONFIG: HelpConfig = {
  role: 'viewer',
  searchPlaceholder: 'Search help...',
  categories: [
    {
      id: 'general',
      label: 'Getting Started',
      topics: [
        { id: 'dashboards', title: 'How to view dashboards', description: 'Explore available dashboards', icon: BarChart3, href: '/analytics' },
        { id: 'reports', title: 'How to view reports', description: 'Browse available reports', icon: FileText, href: '/reports' },
      ],
    },
  ],
};

export function getHelpConfig(role: string): HelpConfig {
  return HELP_CONFIGS[role] || DEFAULT_CONFIG;
}

export function getHelpConfigForRoles(roles: string[]): HelpConfig {
  const { getPrimaryRole } = require('./navigation');
  const primaryRole = getPrimaryRole(roles);
  return getHelpConfig(primaryRole);
}

export { HELP_CONFIGS };
