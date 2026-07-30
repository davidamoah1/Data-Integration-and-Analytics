'use client';

import { useState, useEffect, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import {
  Eye, EyeOff, Loader2, CheckCircle2, AlertCircle, Building2,
  ArrowLeft, Mail, Lock, User as UserIcon,
} from 'lucide-react';
import { authService } from '@/services/auth/authService';
import { useAuthStore } from '@/stores/authStore';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Alert, AlertDescription } from '@/components/ui/Alert';
import { toast } from '@/components/ui/Toaster';

interface InvitationInfo {
  id: number;
  email: string;
  organization_name: string;
  organization_id: number;
  role_name: string;
  expires_at: string;
}

function AcceptInvitationContent() {
  const router = useRouter();
  const params = useSearchParams();
  const token = params.get('token') || '';
  const { fetchProfile } = useAuthStore();

  const [invitation, setInvitation] = useState<InvitationInfo | null>(null);
  const [loadingInfo, setLoadingInfo] = useState(true);
  const [infoError, setInfoError] = useState<string | null>(null);
  const [form, setForm] = useState({ full_name: '', password: '', confirm_password: '' });
  const [showPassword, setShowPassword] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    if (!token) {
      setInfoError('No invitation token provided. Please check your invitation link.');
      setLoadingInfo(false);
      return;
    }
    authService
      .getInvitationInfo(token)
      .then((data) => {
        setInvitation(data);
        setLoadingInfo(false);
      })
      .catch((err) => {
        const msg = err instanceof Error ? err.message : 'Invalid or expired invitation';
        setInfoError(msg);
        setLoadingInfo(false);
      });
  }, [token]);

  const update = (key: string, value: string) => {
    setForm((prev) => ({ ...prev, [key]: value }));
    setValidationErrors((prev) => ({ ...prev, [key]: '' }));
  };

  const validate = (): boolean => {
    const errors: Record<string, string> = {};
    if (!form.full_name.trim()) errors.full_name = 'Full name is required';
    if (!form.password) errors.password = 'Password is required';
    else if (form.password.length < 8) errors.password = 'Password must be at least 8 characters';
    if (form.confirm_password !== form.password) errors.confirm_password = 'Passwords do not match';
    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate() || !invitation) return;
    setSubmitting(true);
    try {
      await authService.acceptInvitation(token, form.full_name, form.password);
      await fetchProfile();
      toast.success('Welcome! Your account has been created.');
      router.push('/dashboard');
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Failed to accept invitation';
      setValidationErrors({ submit: msg });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 py-8">
      <Link href="/" className="absolute left-6 top-6 flex items-center gap-2 text-sm text-slate-400 transition-colors hover:text-white">
        <ArrowLeft size={16} /> Back to home
      </Link>

      <div className="w-full max-w-lg">
        <div className="mb-6 flex flex-col items-center">
          <div className="mb-2 flex h-12 w-12 items-center justify-center rounded-xl bg-primary text-2xl font-bold text-primary-foreground">
            D
          </div>
          <h1 className="text-2xl font-bold text-white">DataFlow</h1>
          <p className="text-sm text-slate-400">Accept Your Invitation</p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Join Your Team</CardTitle>
            <CardDescription>
              {loadingInfo ? 'Loading invitation details...' : invitation ? 'Complete your account to join' : 'Invitation not found'}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {loadingInfo && (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
              </div>
            )}

            {infoError && (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{infoError}</AlertDescription>
              </Alert>
            )}

            {invitation && (
              <>
                <div className="mb-6 rounded-lg border border-primary/30 bg-primary/5 p-4 space-y-2">
                  <div className="flex items-center gap-2">
                    <Building2 className="h-5 w-5 text-primary" />
                    <span className="font-medium text-primary">{invitation.organization_name}</span>
                  </div>
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <Mail className="h-4 w-4" />
                    <span>{invitation.email}</span>
                  </div>
                  <div className="text-sm">
                    <span className="text-muted-foreground">You will be assigned the role: </span>
                    <span className="font-medium capitalize">{invitation.role_name.replace(/_/g, ' ')}</span>
                  </div>
                </div>

                <form onSubmit={handleSubmit} className="space-y-4">
                  {validationErrors.submit && (
                    <Alert variant="destructive">
                      <AlertCircle className="h-4 w-4" />
                      <AlertDescription>{validationErrors.submit}</AlertDescription>
                    </Alert>
                  )}

                  <div className="space-y-2">
                    <label className="text-sm font-medium" htmlFor="full_name">Full Name *</label>
                    <div className="relative">
                      <UserIcon className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                      <Input id="full_name" className="pl-9" placeholder="Kwame Mensah" value={form.full_name} onChange={(e) => update('full_name', e.target.value)} />
                    </div>
                    {validationErrors.full_name && <p className="text-xs text-red-500">{validationErrors.full_name}</p>}
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <label className="text-sm font-medium" htmlFor="password">Password *</label>
                      <div className="relative">
                        <Lock className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                        <Input id="password" type={showPassword ? 'text' : 'password'} className="pl-9" placeholder="••••••••" value={form.password} onChange={(e) => update('password', e.target.value)} />
                        <button type="button" onClick={() => setShowPassword(!showPassword)} className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground">
                          {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                        </button>
                      </div>
                      {validationErrors.password && <p className="text-xs text-red-500">{validationErrors.password}</p>}
                    </div>

                    <div className="space-y-2">
                      <label className="text-sm font-medium" htmlFor="confirm_password">Confirm *</label>
                      <Input id="confirm_password" type={showPassword ? 'text' : 'password'} placeholder="••••••••" value={form.confirm_password} onChange={(e) => update('confirm_password', e.target.value)} />
                      {validationErrors.confirm_password && <p className="text-xs text-red-500">{validationErrors.confirm_password}</p>}
                    </div>
                  </div>

                  <Button type="submit" className="w-full" disabled={submitting}>
                    {submitting ? (
                      <><Loader2 className="mr-2 h-4 w-4 animate-spin" /> Creating account...</>
                    ) : (
                      <><CheckCircle2 className="mr-2 h-4 w-4" /> Accept Invitation & Create Account</>
                    )}
                  </Button>
                </form>
              </>
            )}

            {!loadingInfo && !invitation && !infoError && (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>Invitation not found or already used.</AlertDescription>
              </Alert>
            )}
          </CardContent>
        </Card>

        <div className="mt-4 text-center text-sm text-muted-foreground">
          Already have an account?{' '}
          <Link href="/login" className="font-medium text-primary hover:underline">Sign in</Link>
        </div>

        <p className="mt-4 text-center text-xs text-slate-500">
          © 2025 DataFlow. All rights reserved.
        </p>
      </div>
    </div>
  );
}

export default function AcceptInvitationPage() {
  return (
    <Suspense fallback={<div className="flex min-h-screen items-center justify-center"><Loader2 className="h-8 w-8 animate-spin text-primary" /></div>}>
      <AcceptInvitationContent />
    </Suspense>
  );
}
