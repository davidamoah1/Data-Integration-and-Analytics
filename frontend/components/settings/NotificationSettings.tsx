'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { cn } from '@/lib/utils';
import { toast } from '@/components/ui/Toaster';

interface NotificationPref {
  key: string;
  label: string;
  description: string;
  email: boolean;
  push: boolean;
}

export function NotificationSettings() {
  const [prefs, setPrefs] = useState<NotificationPref[]>([
    { key: 'dataset_uploaded', label: 'Dataset Uploaded', description: 'When a new dataset is uploaded to your organization', email: true, push: true },
    { key: 'report_ready', label: 'Report Ready', description: 'When a generated report is available for download', email: true, push: false },
    { key: 'pipeline_completed', label: 'Pipeline Completed', description: 'When an ETL pipeline finishes running', email: false, push: true },
    { key: 'pipeline_failed', label: 'Pipeline Failed', description: 'When an ETL pipeline fails', email: true, push: true },
    { key: 'member_invited', label: 'Member Invited', description: 'When a new member is invited to your organization', email: true, push: false },
    { key: 'security_alert', label: 'Security Alerts', description: 'Suspicious login attempts and security events', email: true, push: true },
    { key: 'weekly_summary', label: 'Weekly Summary', description: 'A weekly digest of your organization activity', email: true, push: false },
    { key: 'product_updates', label: 'Product Updates', description: 'New features and improvements to DataFlow', email: false, push: false },
  ]);

  const togglePref = (index: number, channel: 'email' | 'push') => {
    setPrefs((prev) => prev.map((p, i) => i === index ? { ...p, [channel]: !p[channel] } : p));
  };

  const handleSave = () => {
    localStorage.setItem('dataflow-notification-prefs', JSON.stringify(prefs));
    toast.success('Notification preferences saved');
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Notification Preferences</CardTitle>
        <CardDescription>Choose which notifications you want to receive and how</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-1">
          {/* Header */}
          <div className="grid grid-cols-[1fr_auto_auto] gap-4 border-b pb-2 text-xs font-semibold text-muted-foreground">
            <span>Notification</span>
            <span className="w-16 text-center">Email</span>
            <span className="w-16 text-center">Push</span>
          </div>

          {prefs.map((pref, index) => (
            <div key={pref.key} className="grid grid-cols-[1fr_auto_auto] gap-4 border-b py-3 last:border-0">
              <div>
                <p className="text-sm font-medium">{pref.label}</p>
                <p className="text-xs text-muted-foreground">{pref.description}</p>
              </div>
              <div className="flex w-16 items-center justify-center">
                <button
                  onClick={() => togglePref(index, 'email')}
                  className={cn(
                    'relative h-6 w-11 rounded-full transition-colors',
                    pref.email ? 'bg-primary' : 'bg-muted',
                  )}
                >
                  <span className={cn(
                    'absolute top-0.5 h-5 w-5 rounded-full bg-white shadow transition-transform',
                    pref.email ? 'translate-x-5' : 'translate-x-0.5',
                  )} />
                </button>
              </div>
              <div className="flex w-16 items-center justify-center">
                <button
                  onClick={() => togglePref(index, 'push')}
                  className={cn(
                    'relative h-6 w-11 rounded-full transition-colors',
                    pref.push ? 'bg-primary' : 'bg-muted',
                  )}
                >
                  <span className={cn(
                    'absolute top-0.5 h-5 w-5 rounded-full bg-white shadow transition-transform',
                    pref.push ? 'translate-x-5' : 'translate-x-0.5',
                  )} />
                </button>
              </div>
            </div>
          ))}
        </div>

        <Button className="mt-4" onClick={handleSave}>Save Preferences</Button>
      </CardContent>
    </Card>
  );
}
