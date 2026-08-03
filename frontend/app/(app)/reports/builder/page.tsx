'use client';

import { useSearchParams } from 'next/navigation';
import { ReportBuilder, ReportWorkflow } from '@/components/reports';
import { useAuthStore } from '@/stores/authStore';
import { RouteGuard } from '@/components/auth/RouteGuard';

export default function ReportBuilderPage() {
  const searchParams = useSearchParams();
  const reportId = searchParams.get('id') || undefined;

  return (
    <RouteGuard roles={['org_admin', 'org_owner', 'data_analyst', 'business_analyst', 'researcher', 'super_admin']}>
      <div className="space-y-6">
        <ReportWorkflow />
        <ReportBuilder reportId={reportId} />
      </div>
    </RouteGuard>
  );
}
