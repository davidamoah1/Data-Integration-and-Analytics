'use client';

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { ScrollText, Search } from 'lucide-react';
import { Input } from '@/components/ui/Input';
import { useState } from 'react';

interface AuditEntry {
  id: number;
  action: string;
  user: string;
  ip: string;
  timestamp: string;
  details: string;
}

const mockEntries: AuditEntry[] = [
  { id: 1, action: 'login', user: 'admin@dataflow.io', ip: '192.168.1.1', timestamp: '2026-07-29 20:00:00', details: 'Successful login' },
  { id: 2, action: 'dataset.upload', user: 'admin@dataflow.io', ip: '192.168.1.1', timestamp: '2026-07-29 19:30:00', details: 'Uploaded sales_data.csv (2.4 MB)' },
  { id: 3, action: 'report.generate', user: 'analyst@dataflow.io', ip: '10.0.0.5', timestamp: '2026-07-29 18:00:00', details: 'Generated Q3 Executive Summary' },
  { id: 4, action: 'user.invite', user: 'admin@dataflow.io', ip: '192.168.1.1', timestamp: '2026-07-29 17:00:00', details: 'Invited user@example.com as viewer' },
  { id: 5, action: 'role.update', user: 'admin@dataflow.io', ip: '192.168.1.1', timestamp: '2026-07-29 16:00:00', details: 'Updated permissions for analyst role' },
];

export function AuditLogSettings() {
  const [search, setSearch] = useState('');
  const [entries] = useState(mockEntries);

  const filtered = entries.filter(
    (e) => e.action.includes(search) || e.user.includes(search) || e.details.includes(search),
  );

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <ScrollText className="h-5 w-5" /> Audit Logs
        </CardTitle>
        <CardDescription>Track all key actions performed in your organization</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="mb-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              className="pl-9"
              placeholder="Search by action, user, or details..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b text-left text-xs font-semibold text-muted-foreground">
                <th className="pb-2 pr-4">Action</th>
                <th className="pb-2 pr-4">User</th>
                <th className="pb-2 pr-4">IP Address</th>
                <th className="pb-2 pr-4">Timestamp</th>
                <th className="pb-2">Details</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((entry) => (
                <tr key={entry.id} className="border-b last:border-0">
                  <td className="py-2 pr-4">
                    <Badge variant="secondary" className="text-xs">{entry.action}</Badge>
                  </td>
                  <td className="py-2 pr-4 text-muted-foreground">{entry.user}</td>
                  <td className="py-2 pr-4 text-muted-foreground">{entry.ip}</td>
                  <td className="py-2 pr-4 text-muted-foreground">{entry.timestamp}</td>
                  <td className="py-2">{entry.details}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {filtered.length === 0 && (
          <p className="py-8 text-center text-sm text-muted-foreground">No audit entries found</p>
        )}
      </CardContent>
    </Card>
  );
}
