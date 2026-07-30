'use client';

import { useState, useEffect } from 'react';
import { useSearchParams } from 'next/navigation';
import {
  User,
  Building2,
  Palette,
  Bell,
  Lock,
  Users,
  Shield,
  Key,
  Zap,
  CreditCard,
  ScrollText,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useAuthStore } from '@/stores/authStore';
import { ProfileSettings } from '@/components/settings/ProfileSettings';
import { AppearanceSettings } from '@/components/settings/AppearanceSettings';
import { SecuritySettings } from '@/components/settings/SecuritySettings';
import { NotificationSettings } from '@/components/settings/NotificationSettings';
import { OrganizationSettings } from '@/components/settings/OrganizationSettings';
import { MembersSettings } from '@/components/settings/MembersSettings';
import { PermissionsSettings } from '@/components/settings/PermissionsSettings';
import { AuditLogSettings } from '@/components/settings/AuditLogSettings';
import { ApiKeysSettings } from '@/components/settings/ApiKeysSettings';
import { IntegrationsSettings } from '@/components/settings/IntegrationsSettings';
import { BillingSettings } from '@/components/settings/BillingSettings';

interface SettingsTab {
  id: string;
  label: string;
  icon: typeof User;
  permission?: string;
  role?: string;
  component: React.ComponentType;
}

const tabs: SettingsTab[] = [
  { id: 'profile', label: 'Profile', icon: User, component: ProfileSettings },
  { id: 'appearance', label: 'Appearance', icon: Palette, component: AppearanceSettings },
  { id: 'notifications', label: 'Notifications', icon: Bell, component: NotificationSettings },
  { id: 'security', label: 'Security', icon: Lock, component: SecuritySettings },
  { id: 'organization', label: 'Organization', icon: Building2, permission: 'organizations.manage', component: OrganizationSettings },
  { id: 'members', label: 'Members', icon: Users, permission: 'users.read', component: MembersSettings },
  { id: 'permissions', label: 'Permissions', icon: Shield, permission: 'roles.read', component: PermissionsSettings },
  { id: 'audit', label: 'Audit Logs', icon: ScrollText, permission: 'audit.view', component: AuditLogSettings },
  { id: 'api-keys', label: 'API Keys', icon: Key, component: ApiKeysSettings },
  { id: 'integrations', label: 'Integrations', icon: Zap, component: IntegrationsSettings },
  { id: 'billing', label: 'Billing', icon: CreditCard, component: BillingSettings },
];

export default function SettingsPage() {
  const { hasPermission, hasRole } = useAuthStore();
  const searchParams = useSearchParams();
  const [activeTab, setActiveTab] = useState('profile');

  useEffect(() => {
    const tab = searchParams.get('tab');
    if (tab) {
      const exists = tabs.find((t) => t.id === tab);
      if (exists) {
        const allowed = (!exists.permission || hasPermission(exists.permission)) && (!exists.role || hasRole(exists.role));
        if (allowed) setActiveTab(tab);
      }
    }
  }, [searchParams, hasPermission, hasRole]);

  const visibleTabs = tabs.filter((tab) => {
    if (tab.permission && !hasPermission(tab.permission)) return false;
    if (tab.role && !hasRole(tab.role)) return false;
    return true;
  });

  const ActiveComponent = visibleTabs.find((t) => t.id === activeTab)?.component || ProfileSettings;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Settings</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Manage your account, organization, and platform preferences.
        </p>
      </div>

      <div className="flex flex-col gap-6 lg:flex-row">
        {/* Tab sidebar */}
        <nav className="flex shrink-0 flex-row gap-1 overflow-x-auto lg:w-56 lg:flex-col">
          {visibleTabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={cn(
                  'flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm font-medium transition-colors whitespace-nowrap',
                  activeTab === tab.id
                    ? 'bg-primary text-primary-foreground'
                    : 'text-muted-foreground hover:bg-accent hover:text-foreground',
                )}
              >
                <Icon className="h-4 w-4 shrink-0" />
                {tab.label}
              </button>
            );
          })}
        </nav>

        {/* Tab content */}
        <div className="min-w-0 flex-1">
          <ActiveComponent />
        </div>
      </div>
    </div>
  );
}
