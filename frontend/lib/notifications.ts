import { ROLES } from './permissions';

export interface NotificationType {
  id: string;
  label: string;
  description: string;
  roles: string[];
  defaultEnabled: boolean;
}

export interface NotificationConfig {
  role: string;
  types: NotificationType[];
}

const ALL_NOTIFICATION_TYPES: NotificationType[] = [
  {
    id: 'org.activity',
    label: 'Organization Activity',
    description: 'Member joined, left, or role changed',
    roles: [ROLES.SUPER_ADMIN, ROLES.ORG_OWNER, ROLES.ORG_ADMIN],
    defaultEnabled: true,
  },
  {
    id: 'dept.activity',
    label: 'Department Activity',
    description: 'Activity within your department',
    roles: [ROLES.DEPT_MANAGER, ROLES.DEPT_OFFICER],
    defaultEnabled: true,
  },
  {
    id: 'dataset.uploaded',
    label: 'Dataset Uploaded',
    description: 'New dataset uploaded in your scope',
    roles: [ROLES.SUPER_ADMIN, ROLES.ORG_OWNER, ROLES.ORG_ADMIN, ROLES.DEPT_MANAGER, ROLES.DATA_ENGINEER, ROLES.DATA_ANALYST, ROLES.RESEARCHER],
    defaultEnabled: true,
  },
  {
    id: 'dataset.processed',
    label: 'Dataset Processing Complete',
    description: 'Dataset finished processing',
    roles: [ROLES.DATA_ENGINEER, ROLES.DATA_ANALYST, ROLES.RESEARCHER, ROLES.DEPT_OFFICER],
    defaultEnabled: true,
  },
  {
    id: 'report.generated',
    label: 'Report Generated',
    description: 'A report was generated in your scope',
    roles: [ROLES.SUPER_ADMIN, ROLES.ORG_OWNER, ROLES.ORG_ADMIN, ROLES.DEPT_MANAGER, ROLES.DATA_ANALYST, ROLES.BUSINESS_ANALYST, ROLES.EXECUTIVE, ROLES.RESEARCHER, ROLES.VIEWER],
    defaultEnabled: true,
  },
  {
    id: 'report.scheduled',
    label: 'Scheduled Report Ready',
    description: 'A scheduled report has been generated',
    roles: [ROLES.ORG_OWNER, ROLES.ORG_ADMIN, ROLES.DEPT_MANAGER, ROLES.DATA_ANALYST, ROLES.RESEARCHER],
    defaultEnabled: true,
  },
  {
    id: 'dashboard.shared',
    label: 'Dashboard Shared',
    description: 'A dashboard was shared with you',
    roles: [ROLES.DATA_ANALYST, ROLES.BUSINESS_ANALYST, ROLES.EXECUTIVE, ROLES.VIEWER, ROLES.DEPT_OFFICER],
    defaultEnabled: true,
  },
  {
    id: 'invitation.accepted',
    label: 'Invitation Accepted',
    description: 'A user accepted your invitation',
    roles: [ROLES.SUPER_ADMIN, ROLES.ORG_OWNER, ROLES.ORG_ADMIN],
    defaultEnabled: true,
  },
  {
    id: 'invitation.expiring',
    label: 'Invitation Expiring',
    description: 'A pending invitation is about to expire',
    roles: [ROLES.SUPER_ADMIN, ROLES.ORG_OWNER, ROLES.ORG_ADMIN],
    defaultEnabled: true,
  },
  {
    id: 'capture.assigned',
    label: 'Capture Assignment',
    description: 'You have been assigned a document to capture',
    roles: [ROLES.DATA_ENTRY_OFFICER],
    defaultEnabled: true,
  },
  {
    id: 'capture.review',
    label: 'Capture Review Needed',
    description: 'A captured document needs your review',
    roles: [ROLES.DATA_ENTRY_OFFICER, ROLES.DEPT_MANAGER],
    defaultEnabled: true,
  },
  {
    id: 'security.alert',
    label: 'Security Alerts',
    description: 'Security events and suspicious activity',
    roles: [ROLES.SUPER_ADMIN, ROLES.ORG_OWNER, ROLES.ORG_ADMIN, ROLES.AUDITOR],
    defaultEnabled: true,
  },
  {
    id: 'platform.incident',
    label: 'Platform Incidents',
    description: 'System-wide incidents and outages',
    roles: [ROLES.SUPER_ADMIN],
    defaultEnabled: true,
  },
  {
    id: 'audit.export',
    label: 'Audit Log Export',
    description: 'Audit logs were exported',
    roles: [ROLES.SUPER_ADMIN, ROLES.AUDITOR],
    defaultEnabled: false,
  },
  {
    id: 'pipeline.failed',
    label: 'Pipeline Failure',
    description: 'A data pipeline failed during execution',
    roles: [ROLES.DATA_ENGINEER, ROLES.DEPT_MANAGER, ROLES.ORG_ADMIN],
    defaultEnabled: true,
  },
  {
    id: 'pipeline.completed',
    label: 'Pipeline Completed',
    description: 'A data pipeline completed successfully',
    roles: [ROLES.DATA_ENGINEER, ROLES.DEPT_MANAGER],
    defaultEnabled: true,
  },
  {
    id: 'system.maintenance',
    label: 'System Maintenance',
    description: 'Scheduled maintenance windows',
    roles: [ROLES.SUPER_ADMIN, ROLES.ORG_OWNER, ROLES.ORG_ADMIN],
    defaultEnabled: true,
  },
];

export function getNotificationTypesForRole(role: string): NotificationType[] {
  return ALL_NOTIFICATION_TYPES.filter((t) => t.roles.includes(role));
}

export function getNotificationTypesForRoles(roles: string[]): NotificationType[] {
  const types = ALL_NOTIFICATION_TYPES.filter((t) =>
    roles.some((r) => t.roles.includes(r))
  );
  const seen = new Set<string>();
  return types.filter((t) => {
    if (seen.has(t.id)) return false;
    seen.add(t.id);
    return true;
  });
}

export { ALL_NOTIFICATION_TYPES };
