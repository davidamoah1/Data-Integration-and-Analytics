import {
  Database, BarChart3, FileText, TrendingUp, Activity, Users,
  Building2, Shield, AlertTriangle, Server, CreditCard,
  Upload, CheckCircle2, Sparkles, ScanLine, FlaskConical,
  Bell, Clock, Heart, GraduationCap, type LucideIcon,
} from 'lucide-react';
import { ROLES } from './permissions';

export interface DashboardWidget {
  id: string;
  title: string;
  type: 'kpi' | 'list' | 'chart' | 'alert' | 'status' | 'actions';
  icon: LucideIcon;
  description?: string;
  permission?: string;
  dataSource?: string;
  limit?: number;
  columns?: string[];
}

export interface DashboardSection {
  id: string;
  title: string;
  widgets: DashboardWidget[];
  order?: number;
}

export interface QuickAction {
  id: string;
  label: string;
  icon: LucideIcon;
  href: string;
  permission?: string;
  color: string;
}

export interface DashboardConfig {
  role: string;
  purpose: string;
  greeting: string;
  sections: DashboardSection[];
  quickActions: QuickAction[];
  emptyStateActions: EmptyStateAction[];
}

export interface EmptyStateAction {
  id: string;
  label: string;
  icon: LucideIcon;
  href: string;
  description: string;
}

const DEFAULT_EMPTY_ACTIONS: EmptyStateAction[] = [
  { id: 'upload', label: 'Upload Dataset', icon: Upload, href: '/datasets', description: 'Upload a CSV or Excel file' },
  { id: 'connect', label: 'Connect Database', icon: Database, href: '/connectors', description: 'Link an external database' },
  { id: 'templates', label: 'Browse Templates', icon: Sparkles, href: '/templates', description: 'Start from a pre-built template' },
];

const DASHBOARD_CONFIGS: Record<string, DashboardConfig> = {
  [ROLES.SUPER_ADMIN]: {
    role: ROLES.SUPER_ADMIN,
    purpose: 'Operate the platform',
    greeting: 'Platform Overview',
    sections: [
      {
        id: 'platform-health',
        title: 'Platform Health',
        order: 0,
        widgets: [
          { id: 'org-count', title: 'Organizations', type: 'kpi', icon: Building2, dataSource: 'platform.orgs' },
          { id: 'user-count', title: 'Total Users', type: 'kpi', icon: Users, dataSource: 'platform.users' },
          { id: 'revenue', title: 'Revenue (MRR)', type: 'kpi', icon: CreditCard, dataSource: 'platform.revenue' },
          { id: 'usage', title: 'Platform Usage', type: 'kpi', icon: Activity, dataSource: 'platform.usage' },
        ],
      },
      {
        id: 'system-status',
        title: 'System Status',
        order: 1,
        widgets: [
          { id: 'uptime', title: 'System Uptime', type: 'status', icon: Server, dataSource: 'platform.uptime' },
          { id: 'incidents', title: 'Recent Incidents', type: 'alert', icon: AlertTriangle, dataSource: 'platform.incidents', limit: 5 },
          { id: 'security', title: 'Security Alerts', type: 'alert', icon: Shield, dataSource: 'platform.security', limit: 5 },
        ],
      },
      {
        id: 'global-analytics',
        title: 'Global Analytics',
        order: 2,
        widgets: [
          { id: 'global-dashboards', title: 'Dashboards Across Platform', type: 'chart', icon: BarChart3, dataSource: 'platform.dashboards' },
          { id: 'global-datasets', title: 'Datasets Across Platform', type: 'chart', icon: Database, dataSource: 'platform.datasets' },
        ],
      },
    ],
    quickActions: [
      { id: 'view-orgs', label: 'View Organizations', icon: Building2, href: '/admin-portal', color: 'bg-blue-500' },
      { id: 'audit', label: 'Audit Center', icon: Shield, href: '/audit', color: 'bg-red-500' },
      { id: 'feature-flags', label: 'Feature Flags', icon: Sparkles, href: '/admin-portal/feature-flags', color: 'bg-purple-500' },
    ],
    emptyStateActions: DEFAULT_EMPTY_ACTIONS,
  },

  [ROLES.ORG_OWNER]: {
    role: ROLES.ORG_OWNER,
    purpose: 'Own and operate their organization',
    greeting: 'Organization Overview',
    sections: [
      {
        id: 'org-overview',
        title: 'Organization Overview',
        order: 0,
        widgets: [
          { id: 'members', title: 'Members', type: 'kpi', icon: Users, dataSource: 'org.members' },
          { id: 'departments', title: 'Departments', type: 'kpi', icon: Building2, dataSource: 'org.departments' },
          { id: 'datasets', title: 'Datasets', type: 'kpi', icon: Database, dataSource: 'org.datasets' },
          { id: 'storage', title: 'Storage Usage', type: 'kpi', icon: Server, dataSource: 'org.storage' },
        ],
      },
      {
        id: 'activity',
        title: 'Member Activity',
        order: 1,
        widgets: [
          { id: 'recent-activity', title: 'Recent Activity', type: 'list', icon: Activity, dataSource: 'org.activity', limit: 10 },
          { id: 'pending-invites', title: 'Pending Invitations', type: 'list', icon: Users, dataSource: 'org.invitations', limit: 5 },
        ],
      },
      {
        id: 'data-status',
        title: 'Data & Reports',
        order: 2,
        widgets: [
          { id: 'recent-reports', title: 'Recent Reports', type: 'list', icon: FileText, dataSource: 'org.reports', limit: 5 },
          { id: 'dataset-status', title: 'Dataset Status', type: 'status', icon: Database, dataSource: 'org.datasetStatus' },
        ],
      },
    ],
    quickActions: [
      { id: 'invite', label: 'Invite Member', icon: Users, href: '/admin', permission: 'users.create', color: 'bg-blue-500' },
      { id: 'create-dept', label: 'Create Department', icon: Building2, href: '/admin/departments', permission: 'departments.manage', color: 'bg-indigo-500' },
      { id: 'upload', label: 'Upload Dataset', icon: Upload, href: '/datasets', permission: 'datasets.upload', color: 'bg-green-500' },
      { id: 'create-dashboard', label: 'Create Dashboard', icon: BarChart3, href: '/analytics', permission: 'analytics.manage', color: 'bg-purple-500' },
      { id: 'generate-report', label: 'Generate Report', icon: FileText, href: '/reports', permission: 'reports.generate', color: 'bg-orange-500' },
    ],
    emptyStateActions: DEFAULT_EMPTY_ACTIONS,
  },

  [ROLES.ORG_ADMIN]: {
    role: ROLES.ORG_ADMIN,
    purpose: 'Operate their organization',
    greeting: 'Organization Overview',
    sections: [
      {
        id: 'org-overview',
        title: 'Organization Overview',
        order: 0,
        widgets: [
          { id: 'members', title: 'Members', type: 'kpi', icon: Users, dataSource: 'org.members' },
          { id: 'departments', title: 'Departments', type: 'kpi', icon: Building2, dataSource: 'org.departments' },
          { id: 'datasets', title: 'Datasets', type: 'kpi', icon: Database, dataSource: 'org.datasets' },
          { id: 'storage', title: 'Storage Usage', type: 'kpi', icon: Server, dataSource: 'org.storage' },
        ],
      },
      {
        id: 'activity',
        title: 'Member Activity',
        order: 1,
        widgets: [
          { id: 'recent-activity', title: 'Recent Activity', type: 'list', icon: Activity, dataSource: 'org.activity', limit: 10 },
          { id: 'pending-invites', title: 'Pending Invitations', type: 'list', icon: Users, dataSource: 'org.invitations', limit: 5 },
        ],
      },
      {
        id: 'data-status',
        title: 'Data & Reports',
        order: 2,
        widgets: [
          { id: 'recent-reports', title: 'Recent Reports', type: 'list', icon: FileText, dataSource: 'org.reports', limit: 5 },
          { id: 'dataset-status', title: 'Dataset Status', type: 'status', icon: Database, dataSource: 'org.datasetStatus' },
        ],
      },
    ],
    quickActions: [
      { id: 'invite', label: 'Invite Member', icon: Users, href: '/admin', permission: 'users.create', color: 'bg-blue-500' },
      { id: 'create-dept', label: 'Create Department', icon: Building2, href: '/admin/departments', permission: 'departments.manage', color: 'bg-indigo-500' },
      { id: 'upload', label: 'Upload Dataset', icon: Upload, href: '/datasets', permission: 'datasets.upload', color: 'bg-green-500' },
      { id: 'create-dashboard', label: 'Create Dashboard', icon: BarChart3, href: '/analytics', permission: 'analytics.manage', color: 'bg-purple-500' },
      { id: 'generate-report', label: 'Generate Report', icon: FileText, href: '/reports', permission: 'reports.generate', color: 'bg-orange-500' },
    ],
    emptyStateActions: DEFAULT_EMPTY_ACTIONS,
  },

  [ROLES.DEPT_MANAGER]: {
    role: ROLES.DEPT_MANAGER,
    purpose: 'Manage a department',
    greeting: 'Department Dashboard',
    sections: [
      {
        id: 'dept-kpis',
        title: 'Department KPIs',
        order: 0,
        widgets: [
          { id: 'team-size', title: 'Team Members', type: 'kpi', icon: Users, dataSource: 'dept.members' },
          { id: 'datasets', title: 'Assigned Datasets', type: 'kpi', icon: Database, dataSource: 'dept.datasets' },
          { id: 'reports', title: 'Recent Reports', type: 'kpi', icon: FileText, dataSource: 'dept.reports' },
          { id: 'pending', title: 'Pending Reviews', type: 'kpi', icon: Clock, dataSource: 'dept.pending' },
        ],
      },
      {
        id: 'team-activity',
        title: 'Team Activity',
        order: 1,
        widgets: [
          { id: 'activity', title: 'Recent Activity', type: 'list', icon: Activity, dataSource: 'dept.activity', limit: 10 },
          { id: 'assigned', title: 'Assigned Work', type: 'list', icon: CheckCircle2, dataSource: 'dept.assigned', limit: 5 },
        ],
      },
    ],
    quickActions: [
      { id: 'upload', label: 'Upload Dataset', icon: Upload, href: '/datasets', permission: 'datasets.upload', color: 'bg-green-500' },
      { id: 'create-dashboard', label: 'Create Dashboard', icon: BarChart3, href: '/analytics', permission: 'analytics.manage', color: 'bg-purple-500' },
      { id: 'generate-report', label: 'Generate Report', icon: FileText, href: '/reports', permission: 'reports.generate', color: 'bg-orange-500' },
    ],
    emptyStateActions: DEFAULT_EMPTY_ACTIONS,
  },

  [ROLES.DATA_ENGINEER]: {
    role: ROLES.DATA_ENGINEER,
    purpose: 'Build and run ETL pipelines',
    greeting: 'Engineering Dashboard',
    sections: [
      {
        id: 'pipeline-status',
        title: 'Pipeline Status',
        order: 0,
        widgets: [
          { id: 'active-pipelines', title: 'Active Pipelines', type: 'kpi', icon: Activity, dataSource: 'pipelines.active' },
          { id: 'datasets', title: 'Datasets', type: 'kpi', icon: Database, dataSource: 'datasets.count' },
          { id: 'jobs', title: 'Processing Jobs', type: 'kpi', icon: Clock, dataSource: 'pipelines.jobs' },
          { id: 'connectors', title: 'Connectors', type: 'kpi', icon: Database, dataSource: 'connectors.count' },
        ],
      },
      {
        id: 'recent',
        title: 'Recent Jobs',
        order: 1,
        widgets: [
          { id: 'job-history', title: 'Job History', type: 'list', icon: Activity, dataSource: 'pipelines.history', limit: 10 },
        ],
      },
    ],
    quickActions: [
      { id: 'upload', label: 'Upload Dataset', icon: Upload, href: '/datasets', permission: 'datasets.upload', color: 'bg-green-500' },
      { id: 'connect', label: 'Connect Database', icon: Database, href: '/connectors', color: 'bg-cyan-500' },
      { id: 'schedule', label: 'Schedule Pipeline', icon: Clock, href: '/scheduler', color: 'bg-blue-500' },
    ],
    emptyStateActions: DEFAULT_EMPTY_ACTIONS,
  },

  [ROLES.DATA_ANALYST]: {
    role: ROLES.DATA_ANALYST,
    purpose: 'Prepare and analyze data',
    greeting: 'Analytics Dashboard',
    sections: [
      {
        id: 'data-overview',
        title: 'Data Overview',
        order: 0,
        widgets: [
          { id: 'datasets', title: 'Recent Datasets', type: 'kpi', icon: Database, dataSource: 'datasets.recent' },
          { id: 'processing', title: 'Processing Jobs', type: 'kpi', icon: Activity, dataSource: 'datasets.processing' },
          { id: 'dashboards', title: 'Saved Dashboards', type: 'kpi', icon: BarChart3, dataSource: 'dashboards.count' },
          { id: 'reports', title: 'Recent Reports', type: 'kpi', icon: FileText, dataSource: 'reports.recent' },
        ],
      },
      {
        id: 'suggestions',
        title: 'Suggested Analyses',
        order: 1,
        widgets: [
          { id: 'suggested', title: 'Recommended for You', type: 'list', icon: Sparkles, dataSource: 'ai.suggestions', limit: 5 },
        ],
      },
    ],
    quickActions: [
      { id: 'upload', label: 'Upload Dataset', icon: Upload, href: '/datasets', permission: 'datasets.upload', color: 'bg-green-500' },
      { id: 'validate', label: 'Run Validation', icon: CheckCircle2, href: '/datasets/workflow', color: 'bg-blue-500' },
      { id: 'create-dashboard', label: 'Create Dashboard', icon: BarChart3, href: '/analytics', permission: 'analytics.manage', color: 'bg-purple-500' },
      { id: 'generate-report', label: 'Generate Report', icon: FileText, href: '/reports', permission: 'reports.generate', color: 'bg-orange-500' },
    ],
    emptyStateActions: DEFAULT_EMPTY_ACTIONS,
  },

  [ROLES.BUSINESS_ANALYST]: {
    role: ROLES.BUSINESS_ANALYST,
    purpose: 'Interpret data for business insights',
    greeting: 'Business Analytics',
    sections: [
      {
        id: 'overview',
        title: 'Overview',
        order: 0,
        widgets: [
          { id: 'dashboards', title: 'Dashboards', type: 'kpi', icon: BarChart3, dataSource: 'dashboards.count' },
          { id: 'reports', title: 'Reports', type: 'kpi', icon: FileText, dataSource: 'reports.count' },
          { id: 'datasets', title: 'Datasets', type: 'kpi', icon: Database, dataSource: 'datasets.count' },
        ],
      },
      {
        id: 'insights',
        title: 'Recent Insights',
        order: 1,
        widgets: [
          { id: 'recent-reports', title: 'Recent Reports', type: 'list', icon: FileText, dataSource: 'reports.recent', limit: 5 },
        ],
      },
    ],
    quickActions: [
      { id: 'view-dashboards', label: 'View Dashboards', icon: BarChart3, href: '/analytics', color: 'bg-purple-500' },
      { id: 'generate-report', label: 'Generate Report', icon: FileText, href: '/reports', permission: 'reports.generate', color: 'bg-orange-500' },
    ],
    emptyStateActions: [
      { id: 'browse-dashboards', label: 'Browse Dashboards', icon: BarChart3, href: '/analytics', description: 'Explore existing dashboards' },
      { id: 'view-reports', label: 'View Reports', icon: FileText, href: '/reports', description: 'See available reports' },
    ],
  },

  [ROLES.EXECUTIVE]: {
    role: ROLES.EXECUTIVE,
    purpose: 'High-level oversight',
    greeting: 'Executive Overview',
    sections: [
      {
        id: 'exec-overview',
        title: 'Organization Performance',
        order: 0,
        widgets: [
          { id: 'dashboards', title: 'Dashboards', type: 'kpi', icon: BarChart3, dataSource: 'dashboards.count' },
          { id: 'reports', title: 'Reports', type: 'kpi', icon: FileText, dataSource: 'reports.count' },
        ],
      },
      {
        id: 'exec-reports',
        title: 'Recent Reports',
        order: 1,
        widgets: [
          { id: 'reports-list', title: 'Latest Reports', type: 'list', icon: FileText, dataSource: 'reports.recent', limit: 5 },
        ],
      },
    ],
    quickActions: [
      { id: 'view-dashboards', label: 'View Dashboards', icon: BarChart3, href: '/analytics', color: 'bg-purple-500' },
      { id: 'view-reports', label: 'View Reports', icon: FileText, href: '/reports', color: 'bg-orange-500' },
    ],
    emptyStateActions: [
      { id: 'browse-dashboards', label: 'Browse Dashboards', icon: BarChart3, href: '/analytics', description: 'Explore executive dashboards' },
    ],
  },

  [ROLES.RESEARCHER]: {
    role: ROLES.RESEARCHER,
    purpose: 'Research and statistical analysis',
    greeting: 'Research Dashboard',
    sections: [
      {
        id: 'research-overview',
        title: 'Research Projects',
        order: 0,
        widgets: [
          { id: 'projects', title: 'Research Projects', type: 'kpi', icon: FlaskConical, dataSource: 'research.projects' },
          { id: 'surveys', title: 'Imported Surveys', type: 'kpi', icon: Database, dataSource: 'research.surveys' },
          { id: 'queue', title: 'Analysis Queue', type: 'kpi', icon: Clock, dataSource: 'research.queue' },
          { id: 'pubs', title: 'Publication Reports', type: 'kpi', icon: FileText, dataSource: 'research.publications' },
        ],
      },
    ],
    quickActions: [
      { id: 'import-survey', label: 'Import Survey', icon: Upload, href: '/datasets', permission: 'datasets.upload', color: 'bg-green-500' },
      { id: 'run-analysis', label: 'Run Analysis', icon: BarChart3, href: '/studios/statistics', color: 'bg-purple-500' },
      { id: 'pub-report', label: 'Publication Report', icon: FileText, href: '/reports', permission: 'reports.generate', color: 'bg-orange-500' },
    ],
    emptyStateActions: [
      { id: 'import', label: 'Import Survey Data', icon: Upload, href: '/datasets', description: 'Upload survey responses' },
      { id: 'templates', label: 'Browse Templates', icon: Sparkles, href: '/templates', description: 'Start from a research template' },
    ],
  },

  [ROLES.AUDITOR]: {
    role: ROLES.AUDITOR,
    purpose: 'Audit and compliance review',
    greeting: 'Audit Dashboard',
    sections: [
      {
        id: 'audit-overview',
        title: 'Audit Overview',
        order: 0,
        widgets: [
          { id: 'logs', title: 'Audit Logs', type: 'kpi', icon: Shield, dataSource: 'audit.count' },
          { id: 'security', title: 'Security Events', type: 'kpi', icon: AlertTriangle, dataSource: 'audit.security' },
          { id: 'users', title: 'Active Users', type: 'kpi', icon: Users, dataSource: 'org.users' },
        ],
      },
      {
        id: 'recent-audit',
        title: 'Recent Audit Events',
        order: 1,
        widgets: [
          { id: 'recent-logs', title: 'Recent Audit Logs', type: 'list', icon: Shield, dataSource: 'audit.recent', limit: 10 },
        ],
      },
    ],
    quickActions: [
      { id: 'view-audit', label: 'View Audit Logs', icon: Shield, href: '/audit', permission: 'audit.view', color: 'bg-red-500' },
      { id: 'view-members', label: 'View Members', icon: Users, href: '/admin', color: 'bg-blue-500' },
    ],
    emptyStateActions: [
      { id: 'audit', label: 'View Audit Logs', icon: Shield, href: '/audit', description: 'Review system activity' },
    ],
  },

  [ROLES.DEPT_OFFICER]: {
    role: ROLES.DEPT_OFFICER,
    purpose: 'Department-level operations',
    greeting: 'Department Dashboard',
    sections: [
      {
        id: 'dept-overview',
        title: 'Overview',
        order: 0,
        widgets: [
          { id: 'datasets', title: 'Datasets', type: 'kpi', icon: Database, dataSource: 'dept.datasets' },
          { id: 'reports', title: 'Reports', type: 'kpi', icon: FileText, dataSource: 'dept.reports' },
        ],
      },
    ],
    quickActions: [
      { id: 'upload', label: 'Upload Dataset', icon: Upload, href: '/datasets', permission: 'datasets.upload', color: 'bg-green-500' },
      { id: 'view-reports', label: 'View Reports', icon: FileText, href: '/reports', color: 'bg-orange-500' },
    ],
    emptyStateActions: DEFAULT_EMPTY_ACTIONS,
  },

  [ROLES.DATA_ENTRY_OFFICER]: {
    role: ROLES.DATA_ENTRY_OFFICER,
    purpose: 'Capture and validate data',
    greeting: 'Capture Dashboard',
    sections: [
      {
        id: 'capture-overview',
        title: 'Today\'s Assignments',
        order: 0,
        widgets: [
          { id: 'assignments', title: 'Today\'s Assignments', type: 'kpi', icon: CheckCircle2, dataSource: 'capture.assignments' },
          { id: 'pending', title: 'Pending Reviews', type: 'kpi', icon: Clock, dataSource: 'capture.pending' },
          { id: 'queue', title: 'Capture Queue', type: 'kpi', icon: ScanLine, dataSource: 'capture.queue' },
          { id: 'validated', title: 'Validation Status', type: 'kpi', icon: CheckCircle2, dataSource: 'capture.validated' },
        ],
      },
    ],
    quickActions: [
      { id: 'capture', label: 'Capture Document', icon: ScanLine, href: '/capture', color: 'bg-amber-500' },
      { id: 'review', label: 'Review Records', icon: CheckCircle2, href: '/datasets', color: 'bg-blue-500' },
      { id: 'submit', label: 'Submit Data', icon: Upload, href: '/datasets', color: 'bg-green-500' },
    ],
    emptyStateActions: [
      { id: 'capture', label: 'Capture Document', icon: ScanLine, href: '/capture', description: 'Scan and extract data from paper documents' },
    ],
  },

  [ROLES.VIEWER]: {
    role: ROLES.VIEWER,
    purpose: 'Consume information',
    greeting: 'Your Dashboards',
    sections: [
      {
        id: 'view-overview',
        title: 'Overview',
        order: 0,
        widgets: [
          { id: 'fav-dashboards', title: 'Favorite Dashboards', type: 'list', icon: BarChart3, dataSource: 'dashboards.favorites', limit: 5 },
          { id: 'recent-reports', title: 'Recent Reports', type: 'list', icon: FileText, dataSource: 'reports.recent', limit: 5 },
        ],
      },
    ],
    quickActions: [
      { id: 'view-dashboards', label: 'View Dashboards', icon: BarChart3, href: '/dashboard', color: 'bg-purple-500' },
      { id: 'view-reports', label: 'View Reports', icon: FileText, href: '/reports', color: 'bg-orange-500' },
    ],
    emptyStateActions: [
      { id: 'browse-dashboards', label: 'Browse Dashboards', icon: BarChart3, href: '/dashboard', description: 'Explore available dashboards' },
      { id: 'view-reports', label: 'View Reports', icon: FileText, href: '/reports', description: 'See available reports' },
    ],
  },
};

const DEFAULT_CONFIG: DashboardConfig = {
  role: 'viewer',
  purpose: 'Access the platform',
  greeting: 'Dashboard',
  sections: [
    {
      id: 'overview',
      title: 'Overview',
      order: 0,
      widgets: [
        { id: 'dashboards', title: 'Dashboards', type: 'kpi', icon: BarChart3, dataSource: 'dashboards.count' },
        { id: 'datasets', title: 'Datasets', type: 'kpi', icon: Database, dataSource: 'datasets.count' },
      ],
    },
  ],
  quickActions: [],
  emptyStateActions: DEFAULT_EMPTY_ACTIONS,
};

export function getDashboardConfig(role: string): DashboardConfig {
  return DASHBOARD_CONFIGS[role] || DEFAULT_CONFIG;
}

export function getDashboardConfigsForRoles(roles: string[]): DashboardConfig {
  const { getPrimaryRole } = require('./navigation');
  const primaryRole = getPrimaryRole(roles);
  return getDashboardConfig(primaryRole);
}

export { DASHBOARD_CONFIGS };
