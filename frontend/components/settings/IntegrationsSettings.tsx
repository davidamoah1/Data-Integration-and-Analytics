'use client';

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Zap, Plus } from 'lucide-react';

const integrations = [
  { name: 'Slack', description: 'Send notifications to Slack channels', connected: false, icon: '💬' },
  { name: 'Microsoft Teams', description: 'Send notifications to Teams channels', connected: false, icon: '👥' },
  { name: 'Google Sheets', description: 'Import and export data from Google Sheets', connected: false, icon: '📊' },
  { name: 'AWS S3', description: 'Connect to S3 buckets for data storage', connected: false, icon: '🪣' },
  { name: 'PostgreSQL', description: 'Direct database connection for ETL', connected: false, icon: '🐘' },
  { name: 'Snowflake', description: 'Connect to Snowflake data warehouse', connected: false, icon: '❄️' },
];

export function IntegrationsSettings() {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Zap className="h-5 w-5" /> Integrations
            </CardTitle>
            <CardDescription>Connect DataFlow with your favorite tools</CardDescription>
          </div>
          <Button variant="outline">
            <Plus className="mr-2 h-4 w-4" />
            Browse Marketplace
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid gap-3 sm:grid-cols-2">
          {integrations.map((integration) => (
            <div key={integration.name} className="flex items-center justify-between rounded-lg border p-4">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-muted text-xl">
                  {integration.icon}
                </div>
                <div>
                  <p className="text-sm font-medium">{integration.name}</p>
                  <p className="text-xs text-muted-foreground">{integration.description}</p>
                </div>
              </div>
              {integration.connected ? (
                <Badge variant="secondary">Connected</Badge>
              ) : (
                <Button variant="outline" size="sm">Connect</Button>
              )}
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
