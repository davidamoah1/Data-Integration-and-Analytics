'use client';

import { useEffect, useState } from 'react';
import { useAuthStore } from '@/stores/authStore';
import { RouteGuard } from '@/components/auth/RouteGuard';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { ClipboardList, ArrowRight } from 'lucide-react';
import Link from 'next/link';

interface QueueItem {
  id: number;
  name: string;
  status: string;
  created_at: string;
  assigned_to?: string;
}

export default function CaptureQueuePage() {
  return (
    <RouteGuard roles={['data_entry_officer', 'org_admin', 'org_owner', 'super_admin']}>
      <CaptureQueueContent />
    </RouteGuard>
  );
}

function CaptureQueueContent() {
  const { user } = useAuthStore();
  const [items, setItems] = useState<QueueItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(false);
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="flex items-center gap-2 text-2xl font-bold">
          <ClipboardList className="h-6 w-6" />
          Capture Queue
        </h1>
        <p className="mt-1 text-muted-foreground">
          Documents and records awaiting data capture.
        </p>
      </div>

      {loading ? (
        <div className="animate-pulse text-muted-foreground">Loading queue...</div>
      ) : items.length === 0 ? (
        <Card>
          <CardContent className="p-12 text-center">
            <ClipboardList className="mx-auto h-12 w-12 text-muted-foreground/50" />
            <p className="mt-4 text-lg font-medium">Queue is empty</p>
            <p className="mt-1 text-sm text-muted-foreground">
              New documents will appear here when assigned to you.
            </p>
            <Link
              href="/capture"
              className="mt-4 inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
            >
              Start Capturing <ArrowRight className="h-4 w-4" />
            </Link>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {items.map((item) => (
            <Card key={item.id}>
              <CardContent className="flex items-center justify-between p-4">
                <div>
                  <p className="font-medium">{item.name}</p>
                  <p className="text-xs text-muted-foreground">
                    {item.assigned_to ? `Assigned to ${item.assigned_to}` : 'Unassigned'}
                  </p>
                </div>
                <Badge variant={item.status === 'processing' ? 'warning' : 'default'}>
                  {item.status}
                </Badge>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
