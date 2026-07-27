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
  type LucideIcon,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useAuthStore } from '@/stores/authStore';

interface NavItem {
  label: string;
  href: string;
  icon: LucideIcon;
  permission?: string;
}

const navItems: NavItem[] = [
  { label: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { label: 'Datasets', href: '/datasets', icon: Database, permission: 'datasets.view' },
  { label: 'Analytics', href: '/analytics', icon: BarChart3, permission: 'analytics.view' },
  { label: 'AI Copilot', href: '/ai', icon: Bot, permission: 'ai.use' },
  { label: 'Reports', href: '/reports', icon: FileText, permission: 'reports.view' },
  { label: 'Scheduler', href: '/scheduler', icon: CalendarClock },
  { label: 'Notifications', href: '/notifications', icon: Bell },
  { label: 'Administration', href: '/admin', icon: Shield, permission: 'users.read' },
  { label: 'Settings', href: '/settings', icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();
  const hasPermission = useAuthStore((s) => s.hasPermission);

  return (
    <aside className="fixed inset-y-0 left-0 z-40 flex w-64 flex-col bg-sidebar text-sidebar-foreground">
      {/* Logo */}
      <div className="flex h-16 items-center gap-2 border-b border-sidebar-border px-6">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground font-bold">
          D
        </div>
        <span className="text-lg font-bold">DataFlow</span>
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1 overflow-y-auto scrollbar-thin px-3 py-4">
        {navItems.map((item) => {
          if (item.permission && !hasPermission(item.permission)) return null;

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
              <Icon className="h-4 w-4" />
              {item.label}
            </Link>
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
