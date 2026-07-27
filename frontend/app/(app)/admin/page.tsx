'use client';

import { Shield, Users, Building2, ScrollText } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { useAuthStore } from '@/stores/authStore';
import { ErrorState } from '@/components/ui/ErrorState';

export default function AdminPage() {
  const { hasPermission, user } = useAuthStore();

  if (!hasPermission('users.read')) {
    return <ErrorState title="Access Denied" message="You don't have permission to access the administration panel." />;
  }

  const sections = [
    { label: 'Users', icon: Users, href: '/admin/users', permission: 'users.read' },
    { label: 'Roles & Permissions', icon: Shield, href: '/admin/roles', permission: 'roles.read' },
    { label: 'Organizations', icon: Building2, href: '/admin/organizations', permission: 'organizations.manage' },
    { label: 'Audit Logs', icon: ScrollText, href: '/admin/audit', permission: 'audit.view' },
  ];

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Administration</h1>
      <p className="text-sm text-muted-foreground">Welcome, {user?.full_name}</p>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {sections.map((section) => {
          if (section.permission && !hasPermission(section.permission)) return null;
          const Icon = section.icon;
          return (
            <Card key={section.label} className="hover:shadow-md transition-shadow cursor-pointer">
              <CardContent className="flex flex-col items-center justify-center p-6">
                <Icon className="mb-3 h-8 w-8 text-primary" />
                <p className="font-medium">{section.label}</p>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
