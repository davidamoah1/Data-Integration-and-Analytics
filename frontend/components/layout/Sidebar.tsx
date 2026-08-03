'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
import { useAuthStore } from '@/stores/authStore';
import { buildNavigation, getNavigationPurpose, getPrimaryRole } from '@/lib/navigation';
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

  const purpose = user ? getNavigationPurpose(user.roles) : '';
  const primaryRole = user ? getPrimaryRole(user.roles) : '';

  return (
    <aside className="flex h-full w-64 flex-col bg-sidebar text-sidebar-foreground">
      {/* Logo */}
      <div className="flex h-16 items-center gap-2 border-b border-sidebar-border px-6">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground font-bold">
          D
        </div>
        <span className="text-lg font-bold">DataFlow</span>
      </div>

      {/* User info */}
      {user && (
        <div className="border-b border-sidebar-border px-4 py-3">
          <p className="truncate text-sm font-medium">{user.full_name}</p>
          <p className="truncate text-xs text-sidebar-foreground/50">{user.email}</p>
          {user.roles.length > 0 && (
            <div className="mt-1.5 flex flex-wrap gap-1">
              {user.roles.slice(0, 2).map((role) => (
                <span
                  key={role}
                  className="rounded bg-sidebar-accent/30 px-1.5 py-0.5 text-[10px] font-medium text-sidebar-foreground/70"
                >
                  {ROLE_LABELS[role] || role.replace(/_/g, ' ')}
                </span>
              ))}
            </div>
          )}
          {purpose && (
            <p className="mt-1.5 text-[10px] italic text-sidebar-foreground/40">{purpose}</p>
          )}
        </div>
      )}

      {/* Navigation */}
      <nav className="flex-1 space-y-4 overflow-y-auto scrollbar-thin px-3 py-4">
        {navGroups.map((group) => {
          return (
            <div key={group.label}>
              <p className="px-3 pb-1.5 text-[11px] font-semibold uppercase tracking-wider text-sidebar-foreground/40">
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
                        'flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors',
                        isActive
                          ? 'bg-sidebar-accent text-white'
                          : 'text-sidebar-foreground/70 hover:bg-sidebar-accent/50 hover:text-white',
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
      <div className="border-t border-sidebar-border px-6 py-3 text-xs text-sidebar-foreground/50">
        DataFlow v2.0.0
        {primaryRole && (
          <span className="ml-1 text-sidebar-foreground/30">· {ROLE_LABELS[primaryRole]}</span>
        )}
      </div>
    </aside>
  );
}
