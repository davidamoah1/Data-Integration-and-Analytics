import {
  LayoutDashboard,
  Database,
  BarChart3,
  Bot,
  FileText,
  CalendarClock,
  Bell,
  Shield,
  Settings,
  Zap,
  Package,
  Key,
  Webhook,
  CreditCard,
  Crown,
  Sparkles,
  ScanLine,
  LayoutTemplate,
  Users,
  Building2,
  ScrollText,
  FlaskConical,
  TrendingUp,
  Activity,
  Server,
  AlertTriangle,
  Stethoscope,
  GraduationCap,
  ClipboardList,
  CheckSquare,
  BookOpen,
  Newspaper,
  Globe2,
  ListChecks,
  HardDrive,
  Rocket,
  Award,
  type LucideIcon,
} from 'lucide-react';
import { ROLES } from './permissions';

export interface NavItem {
  label: string;
  href: string;
  icon: LucideIcon;
  permission?: string;
  role?: string;
  roles?: string[];
  excludeRoles?: string[];
  badge?: string;
  order?: number;
}

export interface NavGroup {
  label: string;
  items: NavItem[];
  order?: number;
  roles?: string[];
  excludeRoles?: string[];
}

type RoleKey = string;

interface RoleProfile {
  purpose: string;
  groups: NavGroup[];
}

const ALL_NAV_ITEMS: Record<string, NavItem> = {
  dashboard: { label: 'Dashboard', href: '/dashboard', icon: LayoutDashboard, order: 0 },
  dataToDecision: { label: 'Data to Decision', href: '/data-to-decision', icon: Rocket, order: 0.5 },
  studios: { label: 'Studios', href: '/studios', icon: Sparkles, order: 1 },
  templates: { label: 'Templates', href: '/templates', icon: LayoutTemplate, order: 2 },

  smartCapture: { label: 'Smart Data Capture', href: '/capture', icon: ScanLine, order: 0 },
  certificates: { label: 'Certificate Intelligence', href: '/certificates', icon: Award, order: 0.5 },
  captureQueue: { label: 'Capture Queue', href: '/capture/queue', icon: ClipboardList, order: 1 },
  assignedTasks: { label: 'Assigned Tasks', href: '/capture/tasks', icon: CheckSquare, order: 2 },
  validation: { label: 'Validation', href: '/capture/review', icon: CheckSquare, order: 3 },
  datasets: { label: 'Datasets', href: '/datasets', icon: Database, permission: 'datasets.view', order: 4 },
  analytics: { label: 'Analytics', href: '/analytics', icon: BarChart3, permission: 'analytics.view', order: 5 },
  reports: { label: 'Reports', href: '/reports', icon: FileText, permission: 'reports.view', order: 6 },
  reportBuilder: { label: 'Report Builder', href: '/reports/builder', icon: LayoutTemplate, permission: 'reports.view', order: 6.5 },
  dashboards: { label: 'Dashboards', href: '/dashboard', icon: LayoutDashboard, permission: 'dashboard.view', order: 7 },
  dashboardBuilder: { label: 'Dashboard Builder', href: '/dashboard/builder', icon: LayoutTemplate, permission: 'dashboard.manage', order: 8 },

  aiAssistant: { label: 'Analytics Assistant', href: '/ai', icon: Bot, permission: 'ai.use', order: 0 },
  scheduler: { label: 'Scheduler', href: '/scheduler', icon: CalendarClock, order: 1 },
  backgroundJobs: { label: 'Background Jobs', href: '/jobs', icon: ListChecks, order: 1.5 },
  fileStorage: { label: 'File Storage', href: '/storage', icon: HardDrive, order: 1.6 },

  notifications: { label: 'Notifications', href: '/notifications', icon: Bell, order: 0 },
  members: { label: 'Members', href: '/admin', icon: Users, permission: 'users.read', order: 1 },
  adminPortal: { label: 'Admin Portal', href: '/admin-portal', icon: Crown, role: 'super_admin', order: 2 },
  auditLogs: { label: 'Audit Logs', href: '/audit', icon: ScrollText, permission: 'audit.view', order: 3 },
  departments: { label: 'Departments', href: '/admin/departments', icon: Building2, permission: 'departments.manage', order: 4 },
  orgSettings: { label: 'Organization Settings', href: '/settings', icon: Settings, permission: 'settings.manage', order: 5 },

  billing: { label: 'Billing', href: '/billing', icon: CreditCard, order: 0 },
  subscriptions: { label: 'Subscriptions', href: '/admin-portal/subscriptions', icon: CreditCard, role: 'super_admin', order: 1 },
  organizations: { label: 'Organizations', href: '/admin-portal/organizations', icon: Building2, role: 'super_admin', order: 2 },
  connectors: { label: 'Connectors', href: '/connectors', icon: Zap, order: 3 },
  marketplace: { label: 'Marketplace', href: '/marketplace', icon: Package, order: 4 },
  apiKeys: { label: 'API Keys', href: '/api-keys', icon: Key, order: 5 },
  webhooks: { label: 'Webhooks', href: '/webhooks', icon: Webhook, order: 6 },
  settings: { label: 'Settings', href: '/settings', icon: Settings, order: 7 },

  platformAnalytics: { label: 'Platform Analytics', href: '/admin-portal/analytics', icon: TrendingUp, role: 'super_admin', order: 0 },
  platformMonitoring: { label: 'Monitoring', href: '/admin-portal/monitoring', icon: Activity, role: 'super_admin', order: 1 },
  platformSecurity: { label: 'Security', href: '/admin-portal/security', icon: Shield, role: 'super_admin', order: 2 },
  platformSettings: { label: 'Platform Settings', href: '/admin-portal/settings', icon: Server, role: 'super_admin', order: 3 },
  featureFlags: { label: 'Feature Flags', href: '/admin-portal/feature-flags', icon: Zap, role: 'super_admin', order: 4 },

  researchStudio: { label: 'Research Studio', href: '/studios/research', icon: FlaskConical, order: 0 },
  statistics: { label: 'Statistics', href: '/studios/statistics', icon: BarChart3, order: 1 },
  publications: { label: 'Publications', href: '/studios/publications', icon: Newspaper, order: 2 },

  healthcareStudio: { label: 'Healthcare Studio', href: '/studios/healthcare', icon: Stethoscope, order: 0 },
  educationStudio: { label: 'Education Studio', href: '/studios/education', icon: GraduationCap, order: 0 },

  profile: { label: 'Profile', href: '/settings', icon: Settings, order: 99 },
};

function group(label: string, items: NavItem[], order = 0, opts?: Partial<NavGroup>): NavGroup {
  return { label, items, order, ...opts };
}

const ROLE_PROFILES: Record<RoleKey, RoleProfile> = {
  [ROLES.SUPER_ADMIN]: {
    purpose: 'Operate the platform',
    groups: [
      group('Platform', [
        ALL_NAV_ITEMS.dashboard,
        ALL_NAV_ITEMS.organizations,
        ALL_NAV_ITEMS.platformAnalytics,
        ALL_NAV_ITEMS.platformMonitoring,
        ALL_NAV_ITEMS.platformSecurity,
      ], 0),
      group('Administration', [
        ALL_NAV_ITEMS.adminPortal,
        ALL_NAV_ITEMS.members,
        ALL_NAV_ITEMS.auditLogs,
        ALL_NAV_ITEMS.featureFlags,
        ALL_NAV_ITEMS.platformSettings,
      ], 1),
      group('Platform Tools', [
        ALL_NAV_ITEMS.studios,
        ALL_NAV_ITEMS.templates,
        ALL_NAV_ITEMS.connectors,
        ALL_NAV_ITEMS.marketplace,
        ALL_NAV_ITEMS.apiKeys,
        ALL_NAV_ITEMS.webhooks,
        ALL_NAV_ITEMS.subscriptions,
        ALL_NAV_ITEMS.billing,
      ], 2),
      group('System', [
        ALL_NAV_ITEMS.notifications,
        ALL_NAV_ITEMS.settings,
      ], 3),
    ],
  },

  [ROLES.ORG_OWNER]: {
    purpose: 'Own and operate their organization',
    groups: [
      group('Overview', [
        ALL_NAV_ITEMS.dashboard,
        ALL_NAV_ITEMS.dataToDecision,
        ALL_NAV_ITEMS.dashboards,
        ALL_NAV_ITEMS.dashboardBuilder,
        ALL_NAV_ITEMS.studios,
        ALL_NAV_ITEMS.templates,
      ], 0),
      group('Data', [
        ALL_NAV_ITEMS.smartCapture,
        ALL_NAV_ITEMS.certificates,
        ALL_NAV_ITEMS.datasets,
        ALL_NAV_ITEMS.analytics,
        ALL_NAV_ITEMS.reports,
        ALL_NAV_ITEMS.reportBuilder,
      ], 1),
      group('Intelligence', [
        ALL_NAV_ITEMS.aiAssistant,
        ALL_NAV_ITEMS.scheduler,
        ALL_NAV_ITEMS.backgroundJobs,
        ALL_NAV_ITEMS.fileStorage,
      ], 2),
      group('Administration', [
        ALL_NAV_ITEMS.notifications,
        ALL_NAV_ITEMS.members,
        ALL_NAV_ITEMS.departments,
        ALL_NAV_ITEMS.auditLogs,
        ALL_NAV_ITEMS.orgSettings,
      ], 3),
      group('Platform', [
        ALL_NAV_ITEMS.connectors,
      ], 4),
    ],
  },

  [ROLES.ORG_ADMIN]: {
    purpose: 'Operate their organization',
    groups: [
      group('Overview', [
        ALL_NAV_ITEMS.dashboard,
        ALL_NAV_ITEMS.dataToDecision,
        ALL_NAV_ITEMS.dashboards,
        ALL_NAV_ITEMS.dashboardBuilder,
        ALL_NAV_ITEMS.studios,
        ALL_NAV_ITEMS.templates,
      ], 0),
      group('Data', [
        ALL_NAV_ITEMS.smartCapture,
        ALL_NAV_ITEMS.certificates,
        ALL_NAV_ITEMS.datasets,
        ALL_NAV_ITEMS.analytics,
        ALL_NAV_ITEMS.reports,
        ALL_NAV_ITEMS.reportBuilder,
      ], 1),
      group('Intelligence', [
        ALL_NAV_ITEMS.aiAssistant,
        ALL_NAV_ITEMS.scheduler,
        ALL_NAV_ITEMS.backgroundJobs,
        ALL_NAV_ITEMS.fileStorage,
      ], 2),
      group('Administration', [
        ALL_NAV_ITEMS.notifications,
        ALL_NAV_ITEMS.members,
        ALL_NAV_ITEMS.departments,
        ALL_NAV_ITEMS.auditLogs,
        ALL_NAV_ITEMS.orgSettings,
      ], 3),
      group('Platform', [
        ALL_NAV_ITEMS.connectors,
      ], 4),
    ],
  },

  [ROLES.DEPT_MANAGER]: {
    purpose: 'Manage a department',
    groups: [
      group('Overview', [
        ALL_NAV_ITEMS.dashboard,
      ], 0),
      group('Department', [
        ALL_NAV_ITEMS.members,
        ALL_NAV_ITEMS.datasets,
        ALL_NAV_ITEMS.reports,
        ALL_NAV_ITEMS.reportBuilder,
      ], 1),
      group('Intelligence', [
        ALL_NAV_ITEMS.analytics,
        ALL_NAV_ITEMS.aiAssistant,
      ], 2),
      group('Personal', [
        ALL_NAV_ITEMS.notifications,
        ALL_NAV_ITEMS.profile,
      ], 3),
    ],
  },

  [ROLES.DATA_ENGINEER]: {
    purpose: 'Build and run ETL pipelines',
    groups: [
      group('Overview', [
        ALL_NAV_ITEMS.dashboard,
      ], 0),
      group('Data', [
        ALL_NAV_ITEMS.datasets,
        ALL_NAV_ITEMS.connectors,
        ALL_NAV_ITEMS.scheduler,
        ALL_NAV_ITEMS.backgroundJobs,
        ALL_NAV_ITEMS.fileStorage,
      ], 1),
      group('Intelligence', [
        ALL_NAV_ITEMS.analytics,
        ALL_NAV_ITEMS.aiAssistant,
      ], 2),
      group('Personal', [
        ALL_NAV_ITEMS.notifications,
        ALL_NAV_ITEMS.profile,
      ], 3),
    ],
  },

  [ROLES.DATA_ANALYST]: {
    purpose: 'Prepare and analyze data',
    groups: [
      group('Overview', [
        ALL_NAV_ITEMS.dashboard,
        ALL_NAV_ITEMS.dataToDecision,
        ALL_NAV_ITEMS.dashboards,
        ALL_NAV_ITEMS.dashboardBuilder,
        ALL_NAV_ITEMS.templates,
      ], 0),
      group('Analytics Studio', [
        ALL_NAV_ITEMS.datasets,
        ALL_NAV_ITEMS.analytics,
        ALL_NAV_ITEMS.reports,
        ALL_NAV_ITEMS.reportBuilder,
      ], 1),
      group('Intelligence', [
        ALL_NAV_ITEMS.aiAssistant,
        ALL_NAV_ITEMS.scheduler,
        ALL_NAV_ITEMS.backgroundJobs,
        ALL_NAV_ITEMS.fileStorage,
      ], 2),
      group('Personal', [
        ALL_NAV_ITEMS.notifications,
        ALL_NAV_ITEMS.profile,
      ], 3),
    ],
  },

  [ROLES.BUSINESS_ANALYST]: {
    purpose: 'Interpret data for business insights',
    groups: [
      group('Overview', [
        ALL_NAV_ITEMS.dashboard,
        ALL_NAV_ITEMS.dataToDecision,
      ], 0),
      group('Analytics', [
        ALL_NAV_ITEMS.analytics,
        ALL_NAV_ITEMS.reports,
        ALL_NAV_ITEMS.reportBuilder,
        ALL_NAV_ITEMS.datasets,
      ], 1),
      group('Intelligence', [
        ALL_NAV_ITEMS.aiAssistant,
      ], 2),
      group('Personal', [
        ALL_NAV_ITEMS.notifications,
        ALL_NAV_ITEMS.profile,
      ], 3),
    ],
  },

  [ROLES.EXECUTIVE]: {
    purpose: 'High-level oversight',
    groups: [
      group('Overview', [
        ALL_NAV_ITEMS.dashboard,
        ALL_NAV_ITEMS.dataToDecision,
      ], 0),
      group('Insights', [
        ALL_NAV_ITEMS.analytics,
        ALL_NAV_ITEMS.reports,
        ALL_NAV_ITEMS.reportBuilder,
        ALL_NAV_ITEMS.datasets,
      ], 1),
      group('Personal', [
        ALL_NAV_ITEMS.notifications,
        ALL_NAV_ITEMS.profile,
      ], 2),
    ],
  },

  [ROLES.RESEARCHER]: {
    purpose: 'Research and statistical analysis',
    groups: [
      group('Overview', [
        ALL_NAV_ITEMS.dashboard,
        ALL_NAV_ITEMS.dataToDecision,
        ALL_NAV_ITEMS.templates,
      ], 0),
      group('Research', [
        ALL_NAV_ITEMS.researchStudio,
        ALL_NAV_ITEMS.statistics,
        ALL_NAV_ITEMS.publications,
        ALL_NAV_ITEMS.reports,
        ALL_NAV_ITEMS.reportBuilder,
        ALL_NAV_ITEMS.datasets,
      ], 1),
      group('Intelligence', [
        ALL_NAV_ITEMS.aiAssistant,
        ALL_NAV_ITEMS.scheduler,
        ALL_NAV_ITEMS.backgroundJobs,
        ALL_NAV_ITEMS.fileStorage,
      ], 2),
      group('Personal', [
        ALL_NAV_ITEMS.notifications,
        ALL_NAV_ITEMS.profile,
      ], 3),
    ],
  },

  [ROLES.AUDITOR]: {
    purpose: 'Audit and compliance review',
    groups: [
      group('Overview', [
        ALL_NAV_ITEMS.dashboard,
      ], 0),
      group('Audit', [
        ALL_NAV_ITEMS.auditLogs,
        ALL_NAV_ITEMS.members,
      ], 1),
      group('Data', [
        ALL_NAV_ITEMS.datasets,
        ALL_NAV_ITEMS.reports,
        ALL_NAV_ITEMS.reportBuilder,
      ], 2),
      group('Personal', [
        ALL_NAV_ITEMS.notifications,
        ALL_NAV_ITEMS.profile,
      ], 3),
    ],
  },

  [ROLES.DEPT_OFFICER]: {
    purpose: 'Department-level operations',
    groups: [
      group('Overview', [
        ALL_NAV_ITEMS.dashboard,
      ], 0),
      group('Data', [
        ALL_NAV_ITEMS.datasets,
        ALL_NAV_ITEMS.reports,
        ALL_NAV_ITEMS.reportBuilder,
      ], 1),
      group('Personal', [
        ALL_NAV_ITEMS.notifications,
        ALL_NAV_ITEMS.profile,
      ], 2),
    ],
  },

  [ROLES.DATA_ENTRY_OFFICER]: {
    purpose: 'Capture and validate data',
    groups: [
      group('Capture', [
        ALL_NAV_ITEMS.smartCapture,
        ALL_NAV_ITEMS.certificates,
        ALL_NAV_ITEMS.captureQueue,
        ALL_NAV_ITEMS.assignedTasks,
        ALL_NAV_ITEMS.validation,
      ], 0),
      group('Personal', [
        ALL_NAV_ITEMS.notifications,
        ALL_NAV_ITEMS.profile,
      ], 1),
    ],
  },

  [ROLES.VIEWER]: {
    purpose: 'Consume information',
    groups: [
      group('View', [
        ALL_NAV_ITEMS.dashboards,
        ALL_NAV_ITEMS.reports,
        ALL_NAV_ITEMS.reportBuilder,
      ], 0),
      group('Personal', [
        ALL_NAV_ITEMS.notifications,
        ALL_NAV_ITEMS.profile,
      ], 1),
    ],
  },
};

const DEFAULT_PROFILE: RoleProfile = {
  purpose: 'Access the platform',
  groups: [
    group('Overview', [
      ALL_NAV_ITEMS.dashboard,
    ], 0),
    group('Personal', [
      ALL_NAV_ITEMS.notifications,
      ALL_NAV_ITEMS.profile,
    ], 1),
  ],
};

export interface NavContext {
  roles: string[];
  permissions: string[];
  organizationType?: string;
  industry?: string;
  departmentId?: number;
  workspaceType?: 'organization' | 'personal';
  featureFlags?: Record<string, boolean>;
}

export function getRoleProfile(role: string): RoleProfile {
  return ROLE_PROFILES[role] || DEFAULT_PROFILE;
}

export function getPrimaryRole(roles: string[]): string {
  const priority = [
    ROLES.SUPER_ADMIN,
    ROLES.ORG_OWNER,
    ROLES.ORG_ADMIN,
    ROLES.DEPT_MANAGER,
    ROLES.AUDITOR,
    ROLES.DATA_ENGINEER,
    ROLES.DATA_ANALYST,
    ROLES.RESEARCHER,
    ROLES.BUSINESS_ANALYST,
    ROLES.EXECUTIVE,
    ROLES.DEPT_OFFICER,
    ROLES.DATA_ENTRY_OFFICER,
    ROLES.VIEWER,
  ];
  for (const role of priority) {
    if (roles.includes(role)) return role;
  }
  return roles[0] || ROLES.VIEWER;
}

export function buildNavigation(ctx: NavContext): NavGroup[] {
  const primaryRole = getPrimaryRole(ctx.roles);
  const profile = getRoleProfile(primaryRole);

  const hasPermission = (perm?: string): boolean => {
    if (!perm) return true;
    if (ctx.roles.includes(ROLES.SUPER_ADMIN)) return true;
    return ctx.permissions.includes(perm);
  };

  const hasRole = (role?: string): boolean => {
    if (!role) return true;
    return ctx.roles.includes(role);
  };

  const passesRoleFilter = (item: NavItem): boolean => {
    if (item.role && !hasRole(item.role)) return false;
    if (item.roles && !item.roles.some((r) => ctx.roles.includes(r))) return false;
    if (item.excludeRoles && item.excludeRoles.some((r) => ctx.roles.includes(r))) return false;
    return true;
  };

  const passesGroupFilter = (grp: NavGroup): boolean => {
    if (grp.roles && !grp.roles.some((r) => ctx.roles.includes(r))) return false;
    if (grp.excludeRoles && grp.excludeRoles.some((r) => ctx.roles.includes(r))) return false;
    return true;
  };

  const passesFeatureFlag = (item: NavItem): boolean => {
    if (!ctx.featureFlags) return true;
    const flagMap: Record<string, string> = {
      '/api-keys': 'api_keys',
      '/webhooks': 'webhooks',
      '/marketplace': 'marketplace',
      '/billing': 'billing',
      '/connectors': 'connectors',
    };
    const flag = flagMap[item.href];
    if (flag && ctx.featureFlags[flag] === false) return false;
    return true;
  };

  const INDUSTRY_STUDIOS: Record<string, NavItem> = {
    healthcare: ALL_NAV_ITEMS.healthcareStudio,
    education: ALL_NAV_ITEMS.educationStudio,
  };

  let groups = profile.groups;

  if (ctx.industry && INDUSTRY_STUDIOS[ctx.industry]) {
    const industryItem = INDUSTRY_STUDIOS[ctx.industry];
    groups = groups.map((grp) => {
      if (grp.label === 'Overview' || grp.label === 'Platform Tools') {
        const hasItem = grp.items.some((i) => i.href === industryItem.href);
        if (!hasItem) {
          return { ...grp, items: [...grp.items, industryItem] };
        }
      }
      return grp;
    });
  }

  const filteredGroups = groups
    .filter(passesGroupFilter)
    .map((grp) => ({
      ...grp,
      items: grp.items
        .filter((item) => hasPermission(item.permission))
        .filter(passesRoleFilter)
        .filter(passesFeatureFlag)
        .sort((a, b) => (a.order ?? 99) - (b.order ?? 99)),
    }))
    .filter((grp) => grp.items.length > 0)
    .sort((a, b) => (a.order ?? 99) - (b.order ?? 99));

  if (ctx.workspaceType === 'personal') {
    return filteredGroups
      .filter((g) => !['Administration', 'Platform', 'Platform Tools'].includes(g.label))
      .map((g) => ({
        ...g,
        items: g.items.filter((i) => !i.role && i.role !== 'super_admin'),
      }))
      .filter((g) => g.items.length > 0);
  }

  return filteredGroups;
}

export function getNavigationPurpose(roles: string[]): string {
  const primaryRole = getPrimaryRole(roles);
  return getRoleProfile(primaryRole).purpose;
}

export { ALL_NAV_ITEMS };
