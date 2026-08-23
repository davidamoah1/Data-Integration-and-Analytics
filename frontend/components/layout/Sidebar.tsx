'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
import { useAuthStore } from '@/stores/authStore';
import { buildNavigation, getPrimaryRole } from '@/lib/navigation';
import { ROLE_LABELS } from '@/lib/permissions';

export function Sidebar() {
  const pathname = usePathname();
  const { user } = useAuthStore();

  const navGroups = user
    ? buildNavigation({
        roles: user.roles,
        permissions: user.permissions,
        organizationType: user.organization_type || user.organization_name,
        industry: user.industry,
        departmentId: user.department_id,
        workspaceType: user.organization_id ? 'organization' : 'personal',
      })
    : [];

  const primaryRole = user ? getPrimaryRole(user.roles) : '';

  return (
    <aside className="flex h-full w-64 flex-col bg-sidebar text-sidebar-foreground">
      {/* Logo */}
      <div className="flex h-14 items-center gap-2.5 border-b border-sidebar-border px-5">
        <div className="flex h-7 w-7 items-center justify-center rounded-md bg-primary text-sm font-bold text-primary-foreground">
          D
        </div>
        <span className="text-base font-semibold">DataFlow</span>
      </div>

      {/* User info */}
      {user && (
        <div className="border-b border-sidebar-border px-4 py-3">
          <p className="truncate text-sm font-medium">{user.full_name}</p>
          <p className="truncate text-xs text-sidebar-foreground/50">{user.email}</p>
          {user.roles.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1">
              {user.roles.slice(0, 2).map((role) => (
                <span
                  key={role}
                  className="rounded bg-sidebar-accent/40 px-1.5 py-0.5 text-[10px] font-medium text-sidebar-foreground/60"
                >
                  {ROLE_LABELS[role] || role.replace(/_/g, ' ')}
                </span>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Navigation */}
      <nav className="flex-1 space-y-3 overflow-y-auto scrollbar-thin px-3 py-3">
        {navGroups.map((group) => {
          return (
            <div key={group.label}>
              <p className="px-3 pb-1 text-[11px] font-medium uppercase tracking-wider text-sidebar-foreground/40">
                {group.label}
              </p>
              <div className="space-y-0.5">
                {group.items.map((item) => {
                  const isActive = pathname === item.href || pathname.startsWith(`${item.href}/`);
                  const Icon = item.icon;

                  return (
                    <Link
                      key={item.href}
                      href={item.href}
                      className={cn(
                        'flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors',
                        isActive
                          ? 'bg-sidebar-accent font-medium text-sidebar-foreground'
                          : 'text-sidebar-foreground/60 hover:bg-sidebar-accent/50 hover:text-sidebar-foreground',
                      )}
                    >
                      <Icon className="h-4 w-4 shrink-0" />
                      <span className="truncate">{item.label}</span>
                    </Link>
                  );
                })}
              </div>
            </div>
          );
        })}
      </nav>

      {/* Version */}
      <div className="border-t border-sidebar-border px-5 py-3 text-xs text-sidebar-foreground/40">
        DataFlow v2.0.0
        {primaryRole && (
          <span className="ml-1 text-sidebar-foreground/30">· {ROLE_LABELS[primaryRole]}</span>
        )}
      </div>
    </aside>
  );
}
