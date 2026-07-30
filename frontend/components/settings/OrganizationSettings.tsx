'use client';

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Label } from '@/components/ui/Label';
import { Badge } from '@/components/ui/Badge';
import { useAuthStore } from '@/stores/authStore';
import { Building2, Users, Calendar } from 'lucide-react';

export function OrganizationSettings() {
  const { user } = useAuthStore();

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Building2 className="h-5 w-5" /> Organization Details
          </CardTitle>
          <CardDescription>Manage your organization profile</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="org-name">Organization Name</Label>
              <Input id="org-name" defaultValue={user?.organization_name || ''} placeholder="Acme Inc." />
            </div>
            <div className="space-y-2">
              <Label htmlFor="org-slug">Slug</Label>
              <Input id="org-slug" defaultValue={(user?.organization_name || '').toLowerCase().replace(/\s+/g, '-')} disabled />
            </div>
            <div className="space-y-2">
              <Label htmlFor="org-industry">Industry</Label>
              <Input id="org-industry" placeholder="Finance, Healthcare, Retail..." />
            </div>
            <div className="space-y-2">
              <Label htmlFor="org-type">Organization Type</Label>
              <Input id="org-type" placeholder="Enterprise, Startup, Government..." />
            </div>
          </div>
          <Button>Save Organization</Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="h-5 w-5" /> Departments
          </CardTitle>
          <CardDescription>Manage departments within your organization</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {['Engineering', 'Analytics', 'Operations', 'Finance'].map((dept) => (
              <div key={dept} className="flex items-center justify-between rounded-lg border p-3">
                <div className="flex items-center gap-3">
                  <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-muted">
                    <Users className="h-4 w-4 text-muted-foreground" />
                  </div>
                  <div>
                    <p className="text-sm font-medium">{dept}</p>
                    <p className="text-xs text-muted-foreground">0 members</p>
                  </div>
                </div>
                <Button variant="ghost" size="sm">Manage</Button>
              </div>
            ))}
          </div>
          <Button variant="outline" className="mt-3">Add Department</Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Plan & Usage</CardTitle>
          <CardDescription>Your current subscription and usage</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between rounded-lg bg-muted p-4">
            <div>
              <div className="flex items-center gap-2">
                <p className="font-semibold">Enterprise Plan</p>
                <Badge variant="secondary">Active</Badge>
              </div>
              <p className="mt-1 text-sm text-muted-foreground">Renews on January 1, 2027</p>
            </div>
            <Calendar className="h-8 w-8 text-muted-foreground" />
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
