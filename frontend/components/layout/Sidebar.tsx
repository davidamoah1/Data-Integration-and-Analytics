'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
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
  type LucideIcon,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useAuthStore } from '@/stores/authStore';

interface NavItem {
  label: string;
  href: string;
  icon: LucideIcon;
  permission?: string;
  role?: string;
}

interface NavGroup {
  label: string;
  items: NavItem[];
}

const navGroups: NavGroup[] = [
  {
    label: 'Overview',
    items: [
      { label: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
      { label: 'Studios', href: '/studios', icon: Sparkles },
      { label: 'Templates', href: '/templates', icon: LayoutTemplate },
    ],
  },
  {
    label: 'Data',
    items: [
      { label: 'Smart Capture', href: '/capture', icon: ScanLine },
      { label: 'Datasets', href: '/datasets', icon: Database, permission: 'datasets.view' },
      { label: 'Analytics', href: '/analytics', icon: BarChart3, permission: 'analytics.view' },
      { label: 'Reports', href: '/reports', icon: FileText, permission: 'reports.view' },
    ],
  },
  {
    label: 'Intelligence',
    items: [
      { label: 'Analytics Assistant', href: '/ai', icon: Bot, permission: 'ai.use' },
      { label: 'Scheduler', href: '/scheduler', icon: CalendarClock },
    ],
  },
  {
    label: 'Administration',
    items: [
      { label: 'Notifications', href: '/notifications', icon: Bell },
      { label: 'Members', href: '/admin', icon: Users, permission: 'users.read' },
      { label: 'Admin Portal', href: '/admin-portal', icon: Crown, role: 'super_admin' },
      { label: 'Audit Logs', href: '/audit', icon: ScrollText, permission: 'audit.view' },
    ],
  },
  {
    label: 'Platform',
    items: [
      { label: 'Billing', href: '/billing', icon: CreditCard },
      { label: 'Connectors', href: '/connectors', icon: Zap },
      { label: 'Marketplace', href: '/marketplace', icon: Package },
      { label: 'API Keys', href: '/api-keys', icon: Key },
      { label: 'Webhooks', href: '/webhooks', icon: Webhook },
      { label: 'Settings', href: '/settings', icon: Settings },
    ],
  },
];

export function Sidebar() {
  const pathname = usePathname();
  const { hasPermission, hasRole, user } = useAuthStore();

  const isVisible = (item: NavItem) => {
    if (item.permission && !hasPermission(item.permission)) return false;
    if (item.role && !hasRole(item.role)) return false;
    return true;
  };

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
                  {role.replace(/_/g, ' ')}
                </span>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Navigation */}
      <nav className="flex-1 space-y-4 overflow-y-auto scrollbar-thin px-3 py-4">
        {navGroups.map((group) => {
          const visibleItems = group.items.filter(isVisible);
          if (visibleItems.length === 0) return null;

          return (
            <div key={group.label}>
              <p className="px-3 pb-1.5 text-[11px] font-semibold uppercase tracking-wider text-sidebar-foreground/40">
                {group.label}
              </p>
              <div className="space-y-0.5">
                {visibleItems.map((item) => {
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
      </div>
    </aside>
  );
}
