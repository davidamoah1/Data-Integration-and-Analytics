'use client';

import { useCallback, useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Label } from '@/components/ui/Label';
import { Select } from '@/components/ui/Select';
import { ScrollText, Search, Loader2, AlertCircle } from 'lucide-react';
import { apiClient } from '@/services/api/client';
import {
  auditService,
  type AuditLogEntry,
  type AuditFilters,
} from '@/services/audit/auditService';

interface MemberOption {
  id: number;
  full_name: string;
  email: string;
}

const PAGE_SIZE = 50;

export function AuditLogSettings() {
  const [entries, setEntries] = useState<AuditLogEntry[]>([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [search, setSearch] = useState('');
  const [actionFilter, setActionFilter] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');

  const [filters, setFilters] = useState<AuditFilters>({ actions: [], resource_types: [] });
  const [userLookup, setUserLookup] = useState<Record<number, string>>({});

  useEffect(() => {
    auditService.getFilters().then(setFilters).catch(() => {});
    apiClient
      .get<{ users: MemberOption[] }>('/api/users?page=1&page_size=200')
      .then((res) => {
        const lookup: Record<number, string> = {};
        for (const u of res.users || []) {
          lookup[u.id] = u.full_name || u.email;
        }
        setUserLookup(lookup);
      })
      .catch(() => {
        // Non-fatal — falls back to showing raw user IDs.
      });
  }, []);

  const loadLogs = useCallback(async (nextOffset: number) => {
    setLoading(true);
    setError(null);
    try {
      const res = await auditService.listLogs({
        action: actionFilter || undefined,
        start_date: startDate ? new Date(startDate).toISOString() : undefined,
        end_date: endDate ? new Date(endDate).toISOString() : undefined,
        limit: PAGE_SIZE,
        offset: nextOffset,
      });
      setEntries((prev) => (nextOffset === 0 ? res.logs : [...prev, ...res.logs]));
      setTotal(res.total);
      setOffset(nextOffset);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load audit logs');
    } finally {
      setLoading(false);
    }
  }, [actionFilter, startDate, endDate]);

  useEffect(() => {
    loadLogs(0);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [actionFilter, startDate, endDate]);

  const userLabel = (entry: AuditLogEntry) =>
    entry.user_id != null ? userLookup[entry.user_id] || `User #${entry.user_id}` : 'System';

  const filtered = entries.filter((e) => {
    if (!search) return true;
    const haystack = `${e.action} ${e.resource_type ?? ''} ${userLabel(e)}`.toLowerCase();
    return haystack.includes(search.toLowerCase());
  });

  const hasMore = entries.length < total;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <ScrollText className="h-5 w-5" /> Audit Logs
        </CardTitle>
        <CardDescription>Track all key actions performed in your organization</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="mb-4 grid gap-3 sm:grid-cols-4">
          <div className="space-y-2 sm:col-span-2">
            <Label htmlFor="audit-search">Search</Label>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                id="audit-search"
                className="pl-9"
                placeholder="Search by action, resource, or user..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
          </div>
          <div className="space-y-2">
            <Label htmlFor="audit-action">Action</Label>
            <Select id="audit-action" value={actionFilter} onChange={(e) => setActionFilter(e.target.value)}>
              <option value="">All actions</option>
              {filters.actions.map((a) => (
                <option key={a} value={a}>{a}</option>
              ))}
            </Select>
          </div>
          <div className="grid grid-cols-2 gap-2">
            <div className="space-y-2">
              <Label htmlFor="audit-start">From</Label>
              <Input id="audit-start" type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="audit-end">To</Label>
              <Input id="audit-end" type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} />
            </div>
          </div>
        </div>

        {loading && entries.length === 0 ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          </div>
        ) : error ? (
          <div className="flex items-center gap-2 py-8 text-sm text-destructive">
            <AlertCircle className="h-4 w-4" /> {error}
          </div>
        ) : filtered.length === 0 ? (
          <p className="py-8 text-center text-sm text-muted-foreground">
            No activity has been recorded yet.
          </p>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-left text-xs font-semibold text-muted-foreground">
                    <th className="pb-2 pr-4">Action</th>
                    <th className="pb-2 pr-4">User</th>
                    <th className="pb-2 pr-4">Resource</th>
                    <th className="pb-2 pr-4">IP Address</th>
                    <th className="pb-2">Timestamp</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((entry) => (
                    <tr key={entry.id} className="border-b last:border-0">
                      <td className="py-2 pr-4">
                        <Badge variant="secondary" className="text-xs">{entry.action}</Badge>
                      </td>
                      <td className="py-2 pr-4 text-muted-foreground">{userLabel(entry)}</td>
                      <td className="py-2 pr-4 text-muted-foreground">
                        {entry.resource_type ? `${entry.resource_type}${entry.resource_id != null ? ` #${entry.resource_id}` : ''}` : '—'}
                      </td>
                      <td className="py-2 pr-4 text-muted-foreground">{entry.ip_address || '—'}</td>
                      <td className="py-2 text-muted-foreground">
                        {entry.created_at ? new Date(entry.created_at).toLocaleString() : '—'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {hasMore && (
              <div className="mt-4 flex justify-center">
                <Button variant="outline" size="sm" disabled={loading} onClick={() => loadLogs(offset + PAGE_SIZE)}>
                  {loading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
                  Load more
                </Button>
              </div>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
}
