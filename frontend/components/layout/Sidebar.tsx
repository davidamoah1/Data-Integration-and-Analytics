'use client';

import { useState, useEffect, useMemo, useCallback } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  LayoutGrid,
  Database,
  Sparkles,
  Shield,
  Layers,
  ChevronDown,
  Folder,
  type LucideIcon,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useAuthStore } from '@/stores/authStore';
import { buildNavigation, getPrimaryRole } from '@/lib/navigation';
import { ROLE_LABELS } from '@/lib/permissions';

const GROUP_ICONS: Record<string, LucideIcon> = {
  Overview: LayoutGrid,
  Data: Database,
  Intelligence: Sparkles,
  Administration: Shield,
  Platform: Layers,
  'Platform Tools': Layers,
  System: Layers,
  Research: Sparkles,
  Clinical: Sparkles,
};

export function Sidebar() {
  const pathname = usePathname();
  const user = useAuthStore((state) => state.user);

  const navGroups = useMemo(() => {
    if (!user) return [];
    return buildNavigation({
      roles: user.roles,
      permissions: user.permissions,
      organizationType: user.organization_type || user.organization_name,
      industry: user.industry,
      departmentId: user.department_id,
      workspaceType: user.organization_id ? 'organization' : 'personal',
    });
  }, [user]);

  const primaryRole = user ? getPrimaryRole(user.roles) : '';

  // Collect all unique item hrefs across all nav groups
  const allHrefs = useMemo(() => {
    return navGroups.flatMap((group) => group.items.map((item) => item.href));
  }, [navGroups]);

  // Determine if a nav item is the closest active match for the current pathname
  const isItemActive = useCallback(
    (href: string) => {
      if (pathname === href) return true;
      if (href === '/') return false;
      if (!pathname.startsWith(`${href}/`)) return false;

      // If another nav item is a longer (more specific) match for the current route, this one is not active
      return !allHrefs.some(
        (otherHref) =>
          otherHref !== href &&
          otherHref.length > href.length &&
          (pathname === otherHref || pathname.startsWith(`${otherHref}/`)),
      );
    },
    [pathname, allHrefs],
  );

  // Collapsible submenus state
  const [openSections, setOpenSections] = useState<Record<string, boolean>>({});

  // Auto-expand the section containing the active pathname, or default to first group
  useEffect(() => {
    if (!navGroups || navGroups.length === 0) return;

    const activeGroup = navGroups.find((group) =>
      group.items.some((item) => isItemActive(item.href)),
    );

    setOpenSections((prev) => {
      // 1. If an active item belongs to a group, ensure that group is open
      if (activeGroup) {
        if (prev[activeGroup.label]) return prev;
        return { ...prev, [activeGroup.label]: true };
      }

      // 2. If no group is open at all, open the first group by default
      const hasAnyOpen = Object.values(prev).some(Boolean);
      if (!hasAnyOpen && navGroups[0]) {
        if (prev[navGroups[0].label]) return prev;
        return { ...prev, [navGroups[0].label]: true };
      }

      return prev;
    });
  }, [pathname, navGroups, isItemActive]);

  const toggleSection = (label: string) => {
    setOpenSections((prev) => ({
      ...prev,
      [label]: !prev[label],
    }));
  };

  return (
    <aside className="relative flex h-full w-64 flex-col border-r border-sidebar-border bg-white text-sidebar-foreground overflow-hidden">
      {/* Dotted mesh background */}
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-0 bg-dot-mesh z-0"
      />

      {/* Logo */}
      <div className="relative z-10 flex h-16 items-center gap-2.5 border-b border-sidebar-border bg-white/80 backdrop-blur-xs px-5">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-600 text-sm font-bold text-white shadow-sm">
          D
        </div>
        <span className="text-base font-bold tracking-tight text-slate-900">DataFlow</span>
      </div>

      {/* User info */}
      {user && (
        <div className="relative z-10 border-b border-sidebar-border px-4 py-3 bg-white/70 backdrop-blur-xs">
          <p className="truncate text-sm font-semibold text-slate-800">{user.full_name}</p>
          <p className="truncate text-xs text-slate-500">{user.email}</p>
          {user.roles.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1">
              {user.roles.slice(0, 2).map((role) => (
                <span
                  key={role}
                  className="rounded-md bg-white px-2 py-0.5 text-[10px] font-medium text-slate-600 border border-slate-200 shadow-xs"
                >
                  {ROLE_LABELS[role] || role.replace(/_/g, ' ')}
                </span>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Navigation with submenus */}
      <nav className="relative z-10 flex-1 space-y-1.5 overflow-y-auto scrollbar-thin px-3 py-3">
        {navGroups.map((group) => {
          const GroupIcon = GROUP_ICONS[group.label] || Folder;
          const isOpen = openSections[group.label] ?? false;
          const hasActiveItem = group.items.some((item) => isItemActive(item.href));

          return (
            <div key={group.label} className="rounded-lg transition-colors">
              {/* Submenu Header / Trigger */}
              <button
                type="button"
                onClick={() => toggleSection(group.label)}
                className={cn(
                  'group flex w-full items-center justify-between rounded-lg px-2.5 py-2 text-xs font-semibold tracking-wide transition-all select-none',
                  hasActiveItem
                    ? 'bg-indigo-50/90 text-indigo-900 font-bold shadow-xs border border-indigo-100/50 backdrop-blur-xs'
                    : 'text-slate-600 hover:bg-white/80 hover:text-slate-900',
                )}
              >
                <div className="flex items-center gap-2.5 min-w-0">
                  <GroupIcon
                    className={cn(
                      'h-4 w-4 shrink-0 transition-colors',
                      hasActiveItem ? 'text-indigo-600' : 'text-slate-400 group-hover:text-slate-600',
                    )}
                  />
                  <span className="truncate">{group.label}</span>
                </div>

                <div className="flex items-center gap-1.5 shrink-0">
                  {hasActiveItem && !isOpen && (
                    <span className="h-1.5 w-1.5 rounded-full bg-indigo-600 ring-2 ring-indigo-100" />
                  )}
                  <span className="rounded bg-slate-100/90 px-1.5 py-0.5 text-[10px] font-medium text-slate-500">
                    {group.items.length}
                  </span>
                  <ChevronDown
                    size={14}
                    className={cn(
                      'text-slate-400 transition-transform duration-200',
                      isOpen ? 'rotate-0' : '-rotate-90',
                    )}
                  />
                </div>
              </button>

              {/* Submenu Child Items */}
              {isOpen && (
                <div className="relative ml-3.5 mt-1 space-y-0.5 border-l border-slate-200 pl-2">
                  {group.items.map((item) => {
                    const isActive = isItemActive(item.href);
                    const Icon = item.icon;

                    return (
                      <Link
                        key={item.href}
                        href={item.href}
                        className={cn(
                          'group flex items-center gap-2.5 rounded-lg px-2.5 py-1.5 text-xs sm:text-sm font-medium transition-all',
                          isActive
                            ? 'bg-indigo-50/95 text-indigo-700 font-semibold shadow-xs border border-indigo-100/60 backdrop-blur-xs'
                            : 'text-slate-600 hover:bg-white/80 hover:text-slate-900',
                        )}
                      >
                        <Icon
                          className={cn(
                            'h-4 w-4 shrink-0 transition-colors',
                            isActive ? 'text-indigo-600' : 'text-slate-400 group-hover:text-slate-600',
                          )}
                        />
                        <span className="truncate">{item.label}</span>
                      </Link>
                    );
                  })}
                </div>
              )}
            </div>
          );
        })}
      </nav>

      {/* Version */}
      <div className="relative z-10 border-t border-sidebar-border bg-white/80 backdrop-blur-xs px-5 py-3 text-xs text-slate-500">
        <div className="flex items-center justify-between gap-1">
          <span className="shrink-0 text-slate-400">DataFlow v2.0.0</span>
          {primaryRole && (
            <span
              className="truncate text-[11px] font-medium text-slate-600"
              title={ROLE_LABELS[primaryRole] || primaryRole}
            >
              {ROLE_LABELS[primaryRole] || primaryRole}
            </span>
          )}
        </div>
      </div>
    </aside>
  );
}
