'use client';

import { useRouter } from 'next/navigation';
import { Shield, Users, Building2, ScrollText, ArrowRight } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/Card';
import { useAuthStore } from '@/stores/authStore';
import { ErrorState } from '@/components/ui/ErrorState';

export default function AdminPage() {
  const router = useRouter();
  const { hasPermission, user } = useAuthStore();

  if (!hasPermission('users.read')) {
    return <ErrorState title="Access Denied" message="You don't have permission to access the administration panel." />;
  }

  const sections = [
    { label: 'Users', desc: 'Manage user accounts and access', icon: Users, href: '/admin/users', permission: 'users.read' },
    { label: 'Roles & Permissions', desc: 'Configure roles and access control', icon: Shield, href: '/admin/roles', permission: 'roles.read' },
    { label: 'Organizations', desc: 'Manage organizations and tenants', icon: Building2, href: '/admin/organizations', permission: 'organizations.manage' },
    { label: 'Audit Logs', desc: 'View system activity logs', icon: ScrollText, href: '/admin/audit', permission: 'audit.view' },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Administration</h1>
        <p className="text-sm text-muted-foreground">Welcome, {user?.full_name}</p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {sections.map((section) => {
          if (section.permission && !hasPermission(section.permission)) return null;
          const Icon = section.icon;
          return (
            <Card
              key={section.label}
              className="hover:shadow-md transition-shadow cursor-pointer group"
              onClick={() => router.push(section.href)}
            >
              <CardContent className="flex flex-col items-center justify-center p-6 text-center">
                <Icon className="mb-3 h-8 w-8 text-primary" />
                <p className="font-medium">{section.label}</p>
                <p className="mt-1 text-xs text-muted-foreground">{section.desc}</p>
                <ArrowRight className="mt-3 h-4 w-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
