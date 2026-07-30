'use client';

import Link from 'next/link';
import { useAuthStore } from '@/stores/authStore';
import { getDashboardConfigsForRoles, type EmptyStateAction } from '@/lib/dashboards';
import { EmptyState as BaseEmptyState } from '@/components/ui/EmptyState';
import { cn } from '@/lib/utils';
import type { ReactNode } from 'react';

interface AdaptiveEmptyStateProps {
  icon?: ReactNode;
  title: string;
  description?: string;
  context?: 'datasets' | 'dashboards' | 'reports' | 'general';
  className?: string;
}

export function AdaptiveEmptyState({
  icon,
  title,
  description,
  context = 'general',
  className,
}: AdaptiveEmptyStateProps) {
  const { user, hasPermission } = useAuthStore();

  const config = user ? getDashboardConfigsForRoles(user.roles) : null;
  const emptyActions = config?.emptyStateActions || [];

  const filteredActions = emptyActions.filter((a) => {
    if (context === 'datasets' && !['upload', 'connect', 'import', 'capture'].includes(a.id)) return false;
    if (context === 'dashboards' && !['create-dashboard', 'browse-dashboards', 'templates'].includes(a.id)) return false;
    if (context === 'reports' && !['generate-report', 'view-reports'].includes(a.id)) return false;
    return true;
  });

  const actions = filteredActions.slice(0, 4);

  const actionNode = actions.length > 0 ? (
    <div className="mt-6 grid gap-2 sm:grid-cols-2">
      {actions.map((action) => {
        const Icon = action.icon;
        return (
          <Link
            key={action.id}
            href={action.href}
            className="group flex items-start gap-3 rounded-lg border p-3 text-left transition-all hover:border-primary/50 hover:bg-accent"
          >
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
              <Icon className="h-4 w-4" />
            </div>
            <div>
              <p className="text-sm font-medium text-foreground group-hover:text-primary">{action.label}</p>
              <p className="mt-0.5 text-xs text-muted-foreground">{action.description}</p>
            </div>
          </Link>
        );
      })}
    </div>
  ) : undefined;

  return (
    <BaseEmptyState
      icon={icon}
      title={title}
      description={description}
      action={actionNode}
      className={className}
    />
  );
}
