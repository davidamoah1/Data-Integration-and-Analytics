'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Label } from '@/components/ui/Label';
import { authService } from '@/services/auth/authService';
import { toast } from '@/components/ui/Toaster';
import { Shield, Monitor, Smartphone, Tablet } from 'lucide-react';

export function SecuritySettings() {
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [saving, setSaving] = useState(false);
  const [sessions, setSessions] = useState<unknown[]>([]);
  const [loadingSessions, setLoadingSessions] = useState(false);

  const handleChangePassword = async () => {
    if (!currentPassword || !newPassword) return;
    if (newPassword !== confirmPassword) {
      toast.error('New passwords do not match');
      return;
    }
    if (newPassword.length < 8) {
      toast.error('Password must be at least 8 characters');
      return;
    }
    setSaving(true);
    try {
      await authService.changePassword(currentPassword, newPassword);
      toast.success('Password changed successfully');
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to change password');
    } finally {
      setSaving(false);
    }
  };

  const loadSessions = async () => {
    setLoadingSessions(true);
    try {
      const data = await authService.getSessions();
      setSessions(data as unknown[]);
    } catch {
      // ignore
    } finally {
      setLoadingSessions(false);
    }
  };

  const handleRevokeSession = async (sessionId: number) => {
    try {
      await authService.revokeSession(sessionId);
      setSessions((prev) => prev.filter((s) => (s as Record<string, unknown>).id !== sessionId));
      toast.success('Session revoked');
    } catch {
      toast.error('Failed to revoke session');
    }
  };

  const getDeviceIcon = (userAgent: string) => {
    if (/mobile/i.test(userAgent)) return Smartphone;
    if (/tablet/i.test(userAgent)) return Tablet;
    return Monitor;
  };

  return (
    <div className="space-y-6">
      {/* Change Password */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="h-5 w-5" /> Change Password
          </CardTitle>
          <CardDescription>Update your password to keep your account secure</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="current-pw">Current Password</Label>
            <Input id="current-pw" type="password" value={currentPassword} onChange={(e) => setCurrentPassword(e.target.value)} />
          </div>
          <div className="space-y-2">
            <Label htmlFor="new-pw">New Password</Label>
            <Input id="new-pw" type="password" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} />
          </div>
          <div className="space-y-2">
            <Label htmlFor="confirm-pw">Confirm New Password</Label>
            <Input id="confirm-pw" type="password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} />
          </div>
          <div className="rounded-lg bg-muted p-3 text-xs text-muted-foreground">
            Password must be at least 8 characters long and include a mix of letters, numbers, and symbols.
          </div>
          <Button onClick={handleChangePassword} disabled={saving || !currentPassword || !newPassword || !confirmPassword}>
            {saving ? 'Changing...' : 'Change Password'}
          </Button>
        </CardContent>
      </Card>

      {/* Active Sessions */}
      <Card>
        <CardHeader>
          <CardTitle>Active Sessions</CardTitle>
          <CardDescription>Manage devices currently signed in to your account</CardDescription>
        </CardHeader>
        <CardContent>
          {sessions.length === 0 && !loadingSessions ? (
            <div className="space-y-3">
              <p className="text-sm text-muted-foreground">Click below to load your active sessions.</p>
              <Button variant="outline" onClick={loadSessions}>Load Sessions</Button>
            </div>
          ) : loadingSessions ? (
            <p className="text-sm text-muted-foreground">Loading sessions...</p>
          ) : (
            <div className="space-y-2">
              {sessions.map((s) => {
                const session = s as Record<string, unknown>;
                const Icon = getDeviceIcon(String(session.user_agent || ''));
                return (
                  <div key={String(session.id)} className="flex items-center justify-between rounded-lg border p-3">
                    <div className="flex items-center gap-3">
                      <Icon className="h-5 w-5 text-muted-foreground" />
                      <div>
                        <p className="text-sm font-medium">{String(session.device || session.user_agent || 'Unknown device')}</p>
                        <p className="text-xs text-muted-foreground">IP: {String(session.ip_address || 'Unknown')}</p>
                      </div>
                    </div>
                    <Button variant="ghost" size="sm" onClick={() => handleRevokeSession(Number(session.id))}>
                      Revoke
                    </Button>
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Login History */}
      <Card>
        <CardHeader>
          <CardTitle>Login History</CardTitle>
          <CardDescription>Recent login attempts on your account</CardDescription>
        </CardHeader>
        <CardContent>
          <Button variant="outline" onClick={async () => {
            try {
              await authService.getLoginHistory();
              toast.success('Login history loaded');
            } catch {
              toast.error('Failed to load login history');
            }
          }}>
            View Login History
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
