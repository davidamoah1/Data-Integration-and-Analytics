'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Label } from '@/components/ui/Label';
import { Alert, AlertDescription } from '@/components/ui/Alert';
import { authService } from '@/services/auth/authService';
import { toast } from '@/components/ui/Toaster';
import {
  Shield, Monitor, Smartphone, Tablet, Key, Loader2, CheckCircle2,
  AlertCircle, Clock, MapPin, Copy,
} from 'lucide-react';
import type { SessionInfo, LoginHistoryEntry, MFAStatus, MFASetupResult } from '@/types';

export function SecuritySettings() {
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [saving, setSaving] = useState(false);
  const [sessions, setSessions] = useState<SessionInfo[]>([]);
  const [loadingSessions, setLoadingSessions] = useState(false);

  // Login history state
  const [loginHistory, setLoginHistory] = useState<LoginHistoryEntry[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [showHistory, setShowHistory] = useState(false);

  // MFA state
  const [mfaStatus, setMfaStatus] = useState<MFAStatus | null>(null);
  const [mfaSetup, setMfaSetup] = useState<MFASetupResult | null>(null);
  const [mfaCode, setMfaCode] = useState('');
  const [mfaDisabling, setMfaDisabling] = useState(false);
  const [mfaEnabling, setMfaEnabling] = useState(false);
  const [copiedSecret, setCopiedSecret] = useState(false);

  useEffect(() => {
    loadMFAStatus();
  }, []);

  const loadMFAStatus = async () => {
    try {
      const status = await authService.getMFAStatus();
      setMfaStatus(status);
    } catch {
      // MFA might not be available
    }
  };

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
      toast.success('Password changed successfully. Please log in again.');
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
      setSessions(data);
    } catch {
      toast.error('Failed to load sessions');
    } finally {
      setLoadingSessions(false);
    }
  };

  const handleRevokeSession = async (sessionId: number) => {
    try {
      await authService.revokeSession(sessionId);
      setSessions((prev) => prev.filter((s) => s.id !== sessionId));
      toast.success('Session revoked');
    } catch {
      toast.error('Failed to revoke session');
    }
  };

  const loadLoginHistory = async () => {
    setLoadingHistory(true);
    setShowHistory(true);
    try {
      const data = await authService.getLoginHistory();
      setLoginHistory(data);
    } catch {
      toast.error('Failed to load login history');
    } finally {
      setLoadingHistory(false);
    }
  };

  const handleSetupMFA = async () => {
    setMfaEnabling(true);
    try {
      const result = await authService.setupMFA();
      setMfaSetup(result);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to setup MFA');
    } finally {
      setMfaEnabling(false);
    }
  };

  const handleVerifyMFA = async () => {
    if (!mfaCode || mfaCode.length < 6) {
      toast.error('Please enter a 6-digit code');
      return;
    }
    setMfaEnabling(true);
    try {
      await authService.verifyMFA(mfaCode);
      toast.success('MFA enabled successfully');
      setMfaSetup(null);
      setMfaCode('');
      await loadMFAStatus();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Invalid MFA code');
    } finally {
      setMfaEnabling(false);
    }
  };

  const handleDisableMFA = async () => {
    if (!mfaCode || mfaCode.length < 6) {
      toast.error('Please enter a 6-digit code');
      return;
    }
    setMfaDisabling(true);
    try {
      await authService.disableMFA(mfaCode);
      toast.success('MFA disabled');
      setMfaCode('');
      await loadMFAStatus();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to disable MFA');
    } finally {
      setMfaDisabling(false);
    }
  };

  const copySecret = () => {
    if (mfaSetup?.secret) {
      navigator.clipboard.writeText(mfaSetup.secret);
      setCopiedSecret(true);
      setTimeout(() => setCopiedSecret(false), 2000);
    }
  };

  const getDeviceIcon = (userAgent: string) => {
    if (/mobile/i.test(userAgent)) return Smartphone;
    if (/tablet/i.test(userAgent)) return Tablet;
    return Monitor;
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleString(undefined, {
      year: 'numeric', month: 'short', day: 'numeric',
      hour: '2-digit', minute: '2-digit',
    });
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

      {/* MFA Setup */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Key className="h-5 w-5" /> Multi-Factor Authentication
          </CardTitle>
          <CardDescription>
            Add an extra layer of security with TOTP-based authentication
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {mfaStatus?.enabled ? (
            <div className="space-y-3">
              <Alert>
                <CheckCircle2 className="h-4 w-4" />
                <AlertDescription>
                  MFA is enabled{mfaStatus.last_used_at ? ` (last used: ${formatDate(mfaStatus.last_used_at)})` : ''}.
                  {mfaStatus.backup_codes_remaining > 0 && ` ${mfaStatus.backup_codes_remaining} backup codes remaining.`}
                </AlertDescription>
              </Alert>
              <div className="space-y-2">
                <Label htmlFor="disable-mfa-code">Enter TOTP code to disable</Label>
                <Input
                  id="disable-mfa-code"
                  type="text"
                  inputMode="numeric"
                  maxLength={8}
                  placeholder="123456"
                  value={mfaCode}
                  onChange={(e) => setMfaCode(e.target.value)}
                />
              </div>
              <Button variant="destructive" onClick={handleDisableMFA} disabled={mfaDisabling || !mfaCode}>
                {mfaDisabling ? 'Disabling...' : 'Disable MFA'}
              </Button>
            </div>
          ) : mfaSetup ? (
            <div className="space-y-4">
              <Alert>
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>
                  Scan the QR URI below with your authenticator app (Google Authenticator, Authy, etc.)
                  or manually enter the secret key.
                </AlertDescription>
              </Alert>
              <div className="rounded-lg border p-4 space-y-2">
                <div>
                  <Label className="text-xs">Secret Key</Label>
                  <div className="flex items-center gap-2">
                    <code className="flex-1 rounded bg-muted px-2 py-1 text-sm font-mono break-all">
                      {mfaSetup.secret}
                    </code>
                    <Button variant="ghost" size="sm" onClick={copySecret}>
                      <Copy className="h-4 w-4" />
                    </Button>
                  </div>
                  {copiedSecret && <p className="mt-1 text-xs text-green-500">Copied!</p>}
                </div>
                <div>
                  <Label className="text-xs">QR URI</Label>
                  <code className="block rounded bg-muted px-2 py-1 text-xs font-mono break-all">
                    {mfaSetup.qr_uri}
                  </code>
                </div>
              </div>
              <div>
                <Label className="text-xs">Backup Codes (save these — each can be used once)</Label>
                <div className="grid grid-cols-2 gap-2 rounded-lg border p-3">
                  {mfaSetup.backup_codes.map((code, i) => (
                    <code key={i} className="text-sm font-mono text-center">{code}</code>
                  ))}
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="mfa-verify-code">Enter the 6-digit code from your authenticator app</Label>
                <Input
                  id="mfa-verify-code"
                  type="text"
                  inputMode="numeric"
                  maxLength={8}
                  placeholder="123456"
                  value={mfaCode}
                  onChange={(e) => setMfaCode(e.target.value)}
                />
              </div>
              <div className="flex gap-2">
                <Button onClick={handleVerifyMFA} disabled={mfaEnabling || !mfaCode}>
                  {mfaEnabling ? 'Verifying...' : 'Verify & Enable'}
                </Button>
                <Button variant="outline" onClick={() => { setMfaSetup(null); setMfaCode(''); }}>
                  Cancel
                </Button>
              </div>
            </div>
          ) : (
            <div className="space-y-3">
              <p className="text-sm text-muted-foreground">
                MFA is not enabled. Enable it to require a verification code at login in addition to your password.
              </p>
              <Button onClick={handleSetupMFA} disabled={mfaEnabling}>
                {mfaEnabling ? (
                  <><Loader2 className="mr-2 h-4 w-4 animate-spin" /> Setting up...</>
                ) : (
                  <><Key className="mr-2 h-4 w-4" /> Setup MFA</>
                )}
              </Button>
            </div>
          )}
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
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" /> Loading sessions...
            </div>
          ) : (
            <div className="space-y-2">
              {sessions.map((s) => {
                const Icon = getDeviceIcon(s.user_agent || '');
                return (
                  <div key={s.id} className="flex items-center justify-between rounded-lg border p-3">
                    <div className="flex items-center gap-3">
                      <Icon className="h-5 w-5 text-muted-foreground" />
                      <div>
                        <p className="text-sm font-medium">{s.device || s.user_agent || 'Unknown device'}</p>
                        <div className="flex items-center gap-3 text-xs text-muted-foreground">
                          {s.ip_address && (
                            <span className="flex items-center gap-1">
                              <MapPin className="h-3 w-3" /> {s.ip_address}
                            </span>
                          )}
                          <span className="flex items-center gap-1">
                            <Clock className="h-3 w-3" /> {formatDate(s.last_activity_at)}
                          </span>
                        </div>
                      </div>
                    </div>
                    <Button variant="ghost" size="sm" onClick={() => handleRevokeSession(s.id)}>
                      Revoke
                    </Button>
                  </div>
                );
              })}
              <Button variant="outline" size="sm" onClick={loadSessions} className="mt-2">
                Refresh
              </Button>
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
          {!showHistory ? (
            <Button variant="outline" onClick={loadLoginHistory}>View Login History</Button>
          ) : loadingHistory ? (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" /> Loading...
            </div>
          ) : loginHistory.length === 0 ? (
            <p className="text-sm text-muted-foreground">No login history found.</p>
          ) : (
            <div className="space-y-2">
              {loginHistory.map((entry) => (
                <div key={entry.id} className="flex items-start justify-between rounded-lg border p-3">
                  <div className="flex items-start gap-3">
                    {entry.success ? (
                      <CheckCircle2 className="mt-0.5 h-4 w-4 text-green-500" />
                    ) : (
                      <AlertCircle className="mt-0.5 h-4 w-4 text-red-500" />
                    )}
                    <div>
                      <p className="text-sm font-medium">
                        {entry.success ? 'Successful login' : 'Failed login'}
                        {entry.failure_reason && ` — ${entry.failure_reason}`}
                      </p>
                      <div className="flex items-center gap-3 text-xs text-muted-foreground">
                        {entry.ip_address && <span>{entry.ip_address}</span>}
                        <span>{formatDate(entry.created_at)}</span>
                      </div>
                    </div>
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
