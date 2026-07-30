'use client';

import { useEffect, useState } from 'react';
import { ScrollText, Search } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import { Badge } from '@/components/ui/Badge';
import { Skeleton } from '@/components/ui/Skeleton';
import { EmptyState } from '@/components/ui/EmptyState';
import { ErrorState } from '@/components/ui/ErrorState';
import { apiClient } from '@/services/api/client';
import { useAuthStore } from '@/stores/authStore';
import { formatDate, timeAgo } from '@/lib/utils';

interface AuditLog {
  id: number;
  action: string;
  resource_type: string;
  resource_id?: number;
  user_email?: string;
  user_name?: string;
  ip_address?: string;
  details?: Record<string, unknown>;
  created_at: string;
}

export default function AuditPage() {
  const { hasPermission } = useAuthStore();
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState('');

  useEffect(() => {
    if (!hasPermission('audit.view')) return;
    loadLogs();
  }, [hasPermission]);

  async function loadLogs() {
    try {
      setLoading(true);
      const data = await apiClient.get<{ logs: AuditLog[] } | AuditLog[]>('/audit/logs');
      const logsArray = Array.isArray(data) ? data : (data?.logs ?? []);
      setLogs(logsArray);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load audit logs');
    } finally {
      setLoading(false);
    }
  }

  if (!hasPermission('audit.view')) {
    return (
      <ErrorState
        title="Access Denied"
        message="You don't have permission to view audit logs."
      />
    );
  }

  const filtered = logs.filter((l) => {
    const q = search.toLowerCase();
    return (
      l.action.toLowerCase().includes(q) ||
      l.resource_type.toLowerCase().includes(q) ||
      (l.user_email || '').toLowerCase().includes(q) ||
      (l.user_name || '').toLowerCase().includes(q)
    );
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Audit Logs</h1>
        <p className="text-sm text-muted-foreground">System activity and security event logs</p>
      </div>

      <div className="relative max-w-sm">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          placeholder="Search audit logs..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="pl-10"
        />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Activity Log ({filtered.length})</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="space-y-3">
              {Array.from({ length: 5 }).map((_, i) => (
                <Skeleton key={i} className="h-16 w-full" />
              ))}
            </div>
          ) : error ? (
            <ErrorState message={error} onRetry={loadLogs} />
          ) : filtered.length === 0 ? (
            <EmptyState
              icon={<ScrollText className="h-10 w-10" />}
              title="No audit logs"
              description={search ? 'Try a different search term.' : 'No activity has been logged yet.'}
            />
          ) : (
            <div className="space-y-2">
              {filtered.map((log) => (
                <div key={log.id} className="flex items-start gap-3 rounded-lg border p-4">
                  <div className="mt-1">
                    <Badge variant="secondary">{log.action}</Badge>
                  </div>
                  <div className="flex-1">
                    <p className="font-medium">
                      {log.resource_type}
                      {log.resource_id != null && ` #${log.resource_id}`}
                    </p>
                    <p className="text-sm text-muted-foreground">
                      {log.user_name || log.user_email || 'System'}
                      {log.ip_address && ` · ${log.ip_address}`}
                    </p>
                    <p className="mt-1 text-xs text-muted-foreground">
                      {formatDate(log.created_at)} · {timeAgo(log.created_at)}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
