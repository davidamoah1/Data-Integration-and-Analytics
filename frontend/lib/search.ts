import { ROLES } from './permissions';

export interface SearchScope {
  id: string;
  label: string;
  entity: string;
  permission?: string;
  role?: string;
  excludeRoles?: string[];
  icon: string;
}

export interface SearchConfig {
  role: string;
  scopes: SearchScope[];
  placeholder: string;
}

const SEARCH_CONFIGS: Record<string, SearchConfig> = {
  [ROLES.SUPER_ADMIN]: {
    role: ROLES.SUPER_ADMIN,
    placeholder: 'Search across the platform...',
    scopes: [
      { id: 'organizations', label: 'Organizations', entity: 'organization', icon: 'Building2' },
      { id: 'users', label: 'Users', entity: 'user', icon: 'Users' },
      { id: 'datasets', label: 'Datasets', entity: 'dataset', icon: 'Database' },
      { id: 'dashboards', label: 'Dashboards', entity: 'dashboard', icon: 'BarChart3' },
      { id: 'reports', label: 'Reports', entity: 'report', icon: 'FileText' },
      { id: 'audit', label: 'Audit Logs', entity: 'audit_log', icon: 'Shield' },
    ],
  },

  [ROLES.ORG_OWNER]: {
    role: ROLES.ORG_OWNER,
    placeholder: 'Search your organization...',
    scopes: [
      { id: 'users', label: 'Members', entity: 'user', permission: 'users.read', icon: 'Users' },
      { id: 'datasets', label: 'Datasets', entity: 'dataset', icon: 'Database' },
      { id: 'dashboards', label: 'Dashboards', entity: 'dashboard', icon: 'BarChart3' },
      { id: 'reports', label: 'Reports', entity: 'report', icon: 'FileText' },
      { id: 'departments', label: 'Departments', entity: 'department', icon: 'Building2' },
    ],
  },

  [ROLES.ORG_ADMIN]: {
    role: ROLES.ORG_ADMIN,
    placeholder: 'Search your organization...',
    scopes: [
      { id: 'users', label: 'Members', entity: 'user', permission: 'users.read', icon: 'Users' },
      { id: 'datasets', label: 'Datasets', entity: 'dataset', icon: 'Database' },
      { id: 'dashboards', label: 'Dashboards', entity: 'dashboard', icon: 'BarChart3' },
      { id: 'reports', label: 'Reports', entity: 'report', icon: 'FileText' },
      { id: 'departments', label: 'Departments', entity: 'department', icon: 'Building2' },
    ],
  },

  [ROLES.DEPT_MANAGER]: {
    role: ROLES.DEPT_MANAGER,
    placeholder: 'Search your department...',
    scopes: [
      { id: 'datasets', label: 'Datasets', entity: 'dataset', icon: 'Database' },
      { id: 'dashboards', label: 'Dashboards', entity: 'dashboard', icon: 'BarChart3' },
      { id: 'reports', label: 'Reports', entity: 'report', icon: 'FileText' },
    ],
  },

  [ROLES.DATA_ENGINEER]: {
    role: ROLES.DATA_ENGINEER,
    placeholder: 'Search datasets and pipelines...',
    scopes: [
      { id: 'datasets', label: 'Datasets', entity: 'dataset', icon: 'Database' },
      { id: 'connectors', label: 'Connectors', entity: 'connector', icon: 'Zap' },
    ],
  },

  [ROLES.DATA_ANALYST]: {
    role: ROLES.DATA_ANALYST,
    placeholder: 'Search datasets, dashboards, reports...',
    scopes: [
      { id: 'datasets', label: 'Datasets', entity: 'dataset', icon: 'Database' },
      { id: 'dashboards', label: 'Dashboards', entity: 'dashboard', icon: 'BarChart3' },
      { id: 'reports', label: 'Reports', entity: 'report', icon: 'FileText' },
      { id: 'templates', label: 'Templates', entity: 'template', icon: 'Sparkles' },
    ],
  },

  [ROLES.BUSINESS_ANALYST]: {
    role: ROLES.BUSINESS_ANALYST,
    placeholder: 'Search dashboards and reports...',
    scopes: [
      { id: 'dashboards', label: 'Dashboards', entity: 'dashboard', icon: 'BarChart3' },
      { id: 'reports', label: 'Reports', entity: 'report', icon: 'FileText' },
      { id: 'datasets', label: 'Datasets', entity: 'dataset', icon: 'Database' },
    ],
  },

  [ROLES.EXECUTIVE]: {
    role: ROLES.EXECUTIVE,
    placeholder: 'Search dashboards and reports...',
    scopes: [
      { id: 'dashboards', label: 'Dashboards', entity: 'dashboard', icon: 'BarChart3' },
      { id: 'reports', label: 'Reports', entity: 'report', icon: 'FileText' },
    ],
  },

  [ROLES.RESEARCHER]: {
    role: ROLES.RESEARCHER,
    placeholder: 'Search research data and reports...',
    scopes: [
      { id: 'datasets', label: 'Datasets', entity: 'dataset', icon: 'Database' },
      { id: 'reports', label: 'Reports', entity: 'report', icon: 'FileText' },
    ],
  },

  [ROLES.AUDITOR]: {
    role: ROLES.AUDITOR,
    placeholder: 'Search audit logs and users...',
    scopes: [
      { id: 'audit', label: 'Audit Logs', entity: 'audit_log', permission: 'audit.view', icon: 'Shield' },
      { id: 'users', label: 'Users', entity: 'user', permission: 'users.read', icon: 'Users' },
    ],
  },

  [ROLES.DEPT_OFFICER]: {
    role: ROLES.DEPT_OFFICER,
    placeholder: 'Search datasets and reports...',
    scopes: [
      { id: 'datasets', label: 'Datasets', entity: 'dataset', icon: 'Database' },
      { id: 'reports', label: 'Reports', entity: 'report', icon: 'FileText' },
    ],
  },

  [ROLES.DATA_ENTRY_OFFICER]: {
    role: ROLES.DATA_ENTRY_OFFICER,
    placeholder: 'Search datasets...',
    scopes: [
      { id: 'datasets', label: 'Datasets', entity: 'dataset', icon: 'Database' },
    ],
  },

  [ROLES.VIEWER]: {
    role: ROLES.VIEWER,
    placeholder: 'Search dashboards and reports...',
    scopes: [
      { id: 'dashboards', label: 'Dashboards', entity: 'dashboard', icon: 'BarChart3' },
      { id: 'reports', label: 'Reports', entity: 'report', icon: 'FileText' },
    ],
  },
};

const DEFAULT_CONFIG: SearchConfig = {
  role: 'viewer',
  placeholder: 'Search...',
  scopes: [
    { id: 'dashboards', label: 'Dashboards', entity: 'dashboard', icon: 'BarChart3' },
    { id: 'reports', label: 'Reports', entity: 'report', icon: 'FileText' },
  ],
};

export function getSearchConfig(role: string): SearchConfig {
  return SEARCH_CONFIGS[role] || DEFAULT_CONFIG;
}

export function getSearchConfigForRoles(roles: string[], permissions: string[]): SearchConfig {
  const { getPrimaryRole } = require('./navigation');
  const primaryRole = getPrimaryRole(roles);
  const config = getSearchConfig(primaryRole);

  const hasPermission = (perm?: string) => {
    if (!perm) return true;
    if (roles.includes(ROLES.SUPER_ADMIN)) return true;
    return permissions.includes(perm);
  };

  return {
    ...config,
    scopes: config.scopes.filter((s) => hasPermission(s.permission)),
  };
}

export { SEARCH_CONFIGS };
