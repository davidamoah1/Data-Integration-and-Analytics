'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/stores/authStore';

interface RouteGuardProps {
  children: React.ReactNode;
  permission?: string;
  role?: string;
  permissions?: string[];
  roles?: string[];
  excludeRoles?: string[];
  requireAll?: boolean;
}

export function RouteGuard({
  children,
  permission,
  role,
  permissions,
  roles,
  excludeRoles,
  requireAll = false,
}: RouteGuardProps) {
  const router = useRouter();
  const { user, hasPermission, hasRole, isAuthenticated } = useAuthStore();

  useEffect(() => {
    if (!isAuthenticated || !user) {
      router.push('/login');
      return;
    }

    const checkPermission = (perm: string) => hasPermission(perm);
    const checkRole = (r: string) => hasRole(r);

    let allowed = true;

    if (permission) {
      allowed = checkPermission(permission);
    } else if (permissions && permissions.length > 0) {
      allowed = requireAll
        ? permissions.every(checkPermission)
        : permissions.some(checkPermission);
    }

    if (allowed && role) {
      allowed = checkRole(role);
    } else if (allowed && roles && roles.length > 0) {
      allowed = requireAll ? roles.every(checkRole) : roles.some(checkRole);
    }

    if (allowed && excludeRoles && excludeRoles.length > 0) {
      allowed = !excludeRoles.some((r) => hasRole(r));
    }

    if (!allowed) {
      router.push('/forbidden');
    }
  }, [router, user, isAuthenticated, hasPermission, hasRole, permission, role, permissions, roles, excludeRoles, requireAll]);

  if (!isAuthenticated || !user) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="animate-pulse text-muted-foreground">Loading...</div>
      </div>
    );
  }

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

  if (allowed && excludeRoles && excludeRoles.length > 0) {
    allowed = !excludeRoles.some((r) => hasRole(r));
  }

  if (!allowed) {
    return null;
  }

  return <>{children}</>;
}
