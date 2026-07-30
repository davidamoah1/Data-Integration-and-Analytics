'use client';

import Link from 'next/link';
import { useAuthStore } from '@/stores/authStore';
import { getDashboardConfigsForRoles, type QuickAction } from '@/lib/dashboards';
import { cn } from '@/lib/utils';

interface QuickActionsProps {
  className?: string;
  maxItems?: number;
}

export function QuickActions({ className, maxItems = 6 }: QuickActionsProps) {
  const { user, hasPermission } = useAuthStore();
  if (!user) return null;

  const config = getDashboardConfigsForRoles(user.roles);
  const actions = config.quickActions
    .filter((a) => !a.permission || hasPermission(a.permission))
    .slice(0, maxItems);

  if (actions.length === 0) return null;

  return (
    <div className={cn('grid gap-3 sm:grid-cols-2 lg:grid-cols-3', className)}>
      {actions.map((action) => {
        const Icon = action.icon;
        return (
          <Link
            key={action.id}
            href={action.href}
            className="group flex items-center gap-3 rounded-xl border bg-card p-4 transition-all hover:border-primary/50 hover:shadow-md"
          >
            <div className={cn('flex h-10 w-10 shrink-0 items-center justify-center rounded-lg text-white', action.color)}>
              <Icon className="h-5 w-5" />
            </div>
            <div className="flex-1">
              <p className="font-medium text-foreground group-hover:text-primary">{action.label}</p>
            </div>
          </Link>
        );
      })}
    </div>
  );
}
