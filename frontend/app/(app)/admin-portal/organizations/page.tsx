'use client';

import { useEffect, useState } from 'react';
import { RouteGuard } from '@/components/auth/RouteGuard';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Building2, Users, Database, Activity } from 'lucide-react';

interface OrgInfo {
  id: number;
  name: string;
  slug: string;
  industry?: string;
  organization_type?: string;
  member_count: number;
  dataset_count: number;
  is_active: boolean;
  created_at: string;
}

export default function OrganizationsPage() {
  return (
    <RouteGuard role="super_admin">
      <OrganizationsContent />
    </RouteGuard>
  );
}

function OrganizationsContent() {
  const [orgs, setOrgs] = useState<OrgInfo[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(false);
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="flex items-center gap-2 text-2xl font-bold">
          <Building2 className="h-6 w-6" />
          Organizations
        </h1>
        <p className="mt-1 text-muted-foreground">
          Manage all customer organizations on the platform.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardContent className="flex items-center justify-between p-6">
            <div>
              <p className="text-sm text-muted-foreground">Total Orgs</p>
              <p className="text-2xl font-bold">{orgs.length}</p>
            </div>
            <Building2 className="h-8 w-8 text-blue-500" />
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex items-center justify-between p-6">
            <div>
              <p className="text-sm text-muted-foreground">Active</p>
              <p className="text-2xl font-bold">{orgs.filter((o) => o.is_active).length}</p>
            </div>
            <Activity className="h-8 w-8 text-green-500" />
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex items-center justify-between p-6">
            <div>
              <p className="text-sm text-muted-foreground">Total Members</p>
              <p className="text-2xl font-bold">{orgs.reduce((s, o) => s + o.member_count, 0)}</p>
            </div>
            <Users className="h-8 w-8 text-purple-500" />
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex items-center justify-between p-6">
            <div>
              <p className="text-sm text-muted-foreground">Total Datasets</p>
              <p className="text-2xl font-bold">{orgs.reduce((s, o) => s + o.dataset_count, 0)}</p>
            </div>
            <Database className="h-8 w-8 text-orange-500" />
          </CardContent>
        </Card>
      </div>

      {loading ? (
        <div className="animate-pulse text-muted-foreground">Loading organizations...</div>
      ) : orgs.length === 0 ? (
        <Card>
          <CardContent className="p-12 text-center">
            <Building2 className="mx-auto h-12 w-12 text-muted-foreground/50" />
            <p className="mt-4 text-lg font-medium">No organizations</p>
            <p className="mt-1 text-sm text-muted-foreground">
              Organizations will appear here once users sign up.
            </p>
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardHeader>
            <CardTitle>All Organizations</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {orgs.map((org) => (
                <div
                  key={org.id}
                  className="flex items-center justify-between rounded-lg border p-4"
                >
                  <div className="flex items-center gap-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                      <Building2 className="h-5 w-5 text-primary" />
                    </div>
                    <div>
                      <p className="font-medium">{org.name}</p>
                      <p className="text-xs text-muted-foreground">
                        {org.industry || 'Unknown industry'}
                        {org.organization_type ? ` · ${org.organization_type}` : ''}
                        {` · ${org.member_count} members`}
                      </p>
                    </div>
                  </div>
                  <Badge variant={org.is_active ? 'success' : 'destructive'}>
                    {org.is_active ? 'Active' : 'Suspended'}
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
