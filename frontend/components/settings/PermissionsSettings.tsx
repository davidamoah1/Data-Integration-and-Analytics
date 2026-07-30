'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { useAuthStore } from '@/stores/authStore';
import { ROLE_LABELS, ROLE_DESCRIPTIONS, PERMISSION_GROUPS, ROLES } from '@/lib/permissions';
import { Shield, ChevronDown, ChevronRight } from 'lucide-react';
import { cn } from '@/lib/utils';

export function PermissionsSettings() {
  const { hasPermission } = useAuthStore();
  const canManage = hasPermission('roles.manage');
  const [expandedRole, setExpandedRole] = useState<string | null>(null);

  const roles = Object.values(ROLES);

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="h-5 w-5" /> Roles & Permissions
          </CardTitle>
          <CardDescription>
            View and manage role-based access control settings
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {roles.map((role) => {
              const isExpanded = expandedRole === role;
              return (
                <div key={role} className="rounded-lg border">
                  <button
                    onClick={() => setExpandedRole(isExpanded ? null : role)}
                    className="flex w-full items-center justify-between p-3 text-left"
                  >
                    <div className="flex items-center gap-3">
                      {isExpanded ? (
                        <ChevronDown className="h-4 w-4 text-muted-foreground" />
                      ) : (
                        <ChevronRight className="h-4 w-4 text-muted-foreground" />
                      )}
                      <div>
                        <p className="text-sm font-medium">{ROLE_LABELS[role]}</p>
                        <p className="text-xs text-muted-foreground">{ROLE_DESCRIPTIONS[role]}</p>
                      </div>
                    </div>
                    <Badge variant="secondary" className="text-xs">{role}</Badge>
                  </button>
                  {isExpanded && (
                    <div className="border-t p-3">
                      <div className="space-y-3">
                        {PERMISSION_GROUPS.map((group) => (
                          <div key={group.module}>
                            <p className="mb-1.5 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                              {group.label}
                            </p>
                            <div className="flex flex-wrap gap-2">
                              {group.permissions.map((perm) => (
                                <span
                                  key={perm.name}
                                  className={cn(
                                    'rounded-md px-2 py-1 text-xs',
                                    'bg-muted text-muted-foreground',
                                  )}
                                >
                                  {perm.label}
                                </span>
                              ))}
                            </div>
                          </div>
                        ))}
                      </div>
                      {canManage && (
                        <Button variant="outline" size="sm" className="mt-3">
                          Edit Permissions
                        </Button>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
