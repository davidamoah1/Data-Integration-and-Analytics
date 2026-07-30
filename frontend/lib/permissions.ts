export const PERMISSIONS = {
  // User management
  USERS_CREATE: 'users.create',
  USERS_READ: 'users.read',
  USERS_EDIT: 'users.edit',
  USERS_DELETE: 'users.delete',
  USERS_MANAGE: 'users.manage',

  // Role management
  ROLES_CREATE: 'roles.create',
  ROLES_READ: 'roles.read',
  ROLES_MANAGE: 'roles.manage',

  // Pipelines
  PIPELINES_CREATE: 'pipelines.create',
  PIPELINES_EXECUTE: 'pipelines.execute',
  PIPELINES_VIEW: 'pipelines.view',

  // ETL
  ETL_IMPORT: 'etl.import',
  ETL_EXPORT: 'etl.export',

  // Dashboards
  DASHBOARD_VIEW: 'dashboard.view',
  DASHBOARD_MANAGE: 'dashboard.manage',

  // Reports
  REPORTS_GENERATE: 'reports.generate',
  REPORTS_EXPORT: 'reports.export',
  REPORTS_VIEW: 'reports.view',

  // Datasets
  DATASETS_UPLOAD: 'datasets.upload',
  DATASETS_DELETE: 'datasets.delete',
  DATASETS_VIEW: 'datasets.view',

  // Analytics
  ANALYTICS_VIEW: 'analytics.view',
  ANALYTICS_MANAGE: 'analytics.manage',
  ANALYTICS_EXPORT: 'analytics.export',

  // AI
  AI_USE: 'ai.use',

  // Settings
  SETTINGS_MANAGE: 'settings.manage',

  // Audit
  AUDIT_VIEW: 'audit.view',

  // Notifications
  NOTIFICATIONS_MANAGE: 'notifications.manage',

  // Organization
  ORGANIZATIONS_MANAGE: 'organizations.manage',
  DEPARTMENTS_MANAGE: 'departments.manage',

  // Sessions
  SESSIONS_MANAGE: 'sessions.manage',

  // Profile
  PROFILE_UPDATE: 'profile.update',

  // ML
  ML_READ: 'ml.read',
  ML_WRITE: 'ml.write',
  ML_EXECUTE: 'ml.execute',
  ML_DELETE: 'ml.delete',
} as const;

export const ROLES = {
  SUPER_ADMIN: 'super_admin',
  ORG_OWNER: 'org_owner',
  ORG_ADMIN: 'org_admin',
  DEPT_MANAGER: 'dept_manager',
  DATA_ENGINEER: 'data_engineer',
  DATA_ANALYST: 'data_analyst',
  BUSINESS_ANALYST: 'business_analyst',
  EXECUTIVE: 'executive',
  DEPT_OFFICER: 'dept_officer',
  AUDITOR: 'auditor',
  VIEWER: 'viewer',
  RESEARCHER: 'researcher',
  DATA_ENTRY_OFFICER: 'data_entry_officer',
} as const;

export const ROLE_LABELS: Record<string, string> = {
  super_admin: 'Super Administrator',
  org_owner: 'Organization Owner',
  org_admin: 'Organization Administrator',
  dept_manager: 'Department Manager',
  data_engineer: 'Data Engineer',
  data_analyst: 'Data Analyst',
  business_analyst: 'Business Analyst',
  executive: 'Executive',
  dept_officer: 'Department Officer',
  auditor: 'Auditor',
  viewer: 'Viewer',
  researcher: 'Researcher',
  data_entry_officer: 'Data Entry Officer',
};

export const ROLE_DESCRIPTIONS: Record<string, string> = {
  super_admin: 'Full system access with all permissions',
  org_owner: 'Owner of an organization with full org access',
  org_admin: 'Manage users and data within organization',
  dept_manager: 'Manage department operations',
  data_engineer: 'Build and run ETL pipelines',
  data_analyst: 'Analyze data and create reports',
  business_analyst: 'View dashboards and reports',
  executive: 'View high-level analytics and reports',
  dept_officer: 'Department-level operations',
  auditor: 'View audit logs and security events',
  viewer: 'Read-only access to dashboards',
  researcher: 'Upload research datasets and perform statistical analysis',
  data_entry_officer: 'Upload documents and use Smart Data Capture',
};

export const PERMISSION_GROUPS = [
  {
    module: 'users',
    label: 'User Management',
    permissions: [
      { name: 'users.create', label: 'Create Users' },
      { name: 'users.read', label: 'View Users' },
      { name: 'users.edit', label: 'Edit Users' },
      { name: 'users.delete', label: 'Delete Users' },
      { name: 'users.manage', label: 'Full User Management' },
    ],
  },
  {
    module: 'roles',
    label: 'Role Management',
    permissions: [
      { name: 'roles.create', label: 'Create Roles' },
      { name: 'roles.read', label: 'View Roles' },
      { name: 'roles.manage', label: 'Manage Roles' },
    ],
  },
  {
    module: 'datasets',
    label: 'Datasets',
    permissions: [
      { name: 'datasets.upload', label: 'Upload Datasets' },
      { name: 'datasets.view', label: 'View Datasets' },
      { name: 'datasets.delete', label: 'Delete Datasets' },
    ],
  },
  {
    module: 'dashboard',
    label: 'Dashboards',
    permissions: [
      { name: 'dashboard.view', label: 'View Dashboards' },
      { name: 'dashboard.manage', label: 'Manage Dashboards' },
    ],
  },
  {
    module: 'reports',
    label: 'Reports',
    permissions: [
      { name: 'reports.generate', label: 'Generate Reports' },
      { name: 'reports.view', label: 'View Reports' },
      { name: 'reports.export', label: 'Export Reports' },
    ],
  },
  {
    module: 'analytics',
    label: 'Analytics',
    permissions: [
      { name: 'analytics.view', label: 'View Analytics' },
      { name: 'analytics.manage', label: 'Manage Analytics' },
      { name: 'analytics.export', label: 'Export Analytics' },
    ],
  },
  {
    module: 'pipelines',
    label: 'Pipelines',
    permissions: [
      { name: 'pipelines.create', label: 'Create Pipelines' },
      { name: 'pipelines.execute', label: 'Execute Pipelines' },
      { name: 'pipelines.view', label: 'View Pipelines' },
    ],
  },
  {
    module: 'etl',
    label: 'ETL',
    permissions: [
      { name: 'etl.import', label: 'Import Data' },
      { name: 'etl.export', label: 'Export Data' },
    ],
  },
  {
    module: 'ai',
    label: 'AI Features',
    permissions: [
      { name: 'ai.use', label: 'Use AI Features' },
    ],
  },
  {
    module: 'ml',
    label: 'Machine Learning',
    permissions: [
      { name: 'ml.read', label: 'View ML Models' },
      { name: 'ml.write', label: 'Create ML Models' },
      { name: 'ml.execute', label: 'Execute ML Training' },
      { name: 'ml.delete', label: 'Delete ML Models' },
    ],
  },
  {
    module: 'settings',
    label: 'Settings',
    permissions: [
      { name: 'settings.manage', label: 'Manage Settings' },
    ],
  },
  {
    module: 'audit',
    label: 'Audit',
    permissions: [
      { name: 'audit.view', label: 'View Audit Logs' },
    ],
  },
  {
    module: 'organizations',
    label: 'Organization',
    permissions: [
      { name: 'organizations.manage', label: 'Manage Organizations' },
      { name: 'departments.manage', label: 'Manage Departments' },
    ],
  },
  {
    module: 'sessions',
    label: 'Sessions',
    permissions: [
      { name: 'sessions.manage', label: 'Manage Sessions' },
    ],
  },
  {
    module: 'profile',
    label: 'Profile',
    permissions: [
      { name: 'profile.update', label: 'Update Profile' },
    ],
  },
] as const;
