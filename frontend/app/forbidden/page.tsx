'use client';

import Link from 'next/link';
import { ShieldAlert, ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui/Button';

export default function ForbiddenPage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-background px-4">
      <div className="flex flex-col items-center text-center">
        <div className="flex h-20 w-20 items-center justify-center rounded-2xl bg-destructive/10 text-destructive">
          <ShieldAlert className="h-10 w-10" />
        </div>
        <h1 className="mt-6 text-4xl font-bold tracking-tight">403</h1>
        <p className="mt-2 text-lg font-semibold text-foreground">Access Forbidden</p>
        <p className="mt-2 max-w-md text-sm text-muted-foreground">
          You do not have permission to access this page. If you believe this is an error,
          please contact your organization administrator.
        </p>
        <div className="mt-6 flex gap-3">
          <Link href="/dashboard">
            <Button variant="outline">
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back to Dashboard
            </Button>
          </Link>
          <Link href="/settings">
            <Button>Contact Admin</Button>
          </Link>
        </div>
      </div>
    </div>
  );
}
