'use client';

import { ScrollText } from 'lucide-react';
import { RouteGuard } from '@/components/auth/RouteGuard';
import { AuditLogViewer } from '@/components/audit';

export default function AuditPage() {
  return (
    <RouteGuard permission="audit.view" excludeRoles={['viewer', 'data_entry_officer']}>
      <div className="container mx-auto max-w-5xl space-y-6 p-6">
        <div>
          <h1 className="flex items-center gap-2 text-2xl font-bold">
            <ScrollText className="h-6 w-6" />
            Audit Logs
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            Enterprise audit trails — track user actions, resource changes, and security events
          </p>
        </div>

        <AuditLogViewer />
      </div>
    </RouteGuard>
  );
}
