'use client';

import { useAuthStore } from '@/stores/authStore';

interface CanProps {
  children: React.ReactNode;
  permission?: string;
  permissions?: string[];
  role?: string;
  roles?: string[];
  requireAll?: boolean;
  fallback?: React.ReactNode;
}

export function Can({
  children,
  permission,
  permissions,
  role,
  roles,
  requireAll = false,
  fallback = null,
}: CanProps) {
  const { hasPermission, hasRole } = useAuthStore();

  let allowed = true;

  if (permission) {
    allowed = hasPermission(permission);
  } else if (permissions && permissions.length > 0) {
    allowed = requireAll
      ? permissions.every((p) => hasPermission(p))
      : permissions.some((p) => hasPermission(p));
  }

  if (allowed && role) {
    allowed = hasRole(role);
  } else if (allowed && roles && roles.length > 0) {
    allowed = requireAll ? roles.every((r) => hasRole(r)) : roles.some((r) => hasRole(r));
  }

  if (!allowed) return <>{fallback}</>;
  return <>{children}</>;
}
