'use client';

import { useState, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { Loader2, CheckCircle2, AlertCircle, Mail, ArrowLeft } from 'lucide-react';
import { authService } from '@/services/auth/authService';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Alert, AlertDescription } from '@/components/ui/Alert';
import { toast } from '@/components/ui/Toaster';

function VerifyEmailContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get('token') || '';

  const [verifying, setVerifying] = useState(false);
  const [verified, setVerified] = useState(false);
  const [error, setError] = useState('');
  const [email, setEmail] = useState('');
  const [resending, setResending] = useState(false);
  const [resent, setResent] = useState(false);

  const handleVerify = async () => {
    if (!token) {
      setError('No verification token found. Please use the link from your email.');
      return;
    }
    setVerifying(true);
    setError('');
    try {
      await authService.verifyEmail(token);
      setVerified(true);
      toast.success('Email verified successfully!');
      setTimeout(() => router.push('/dashboard'), 2000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to verify email');
    } finally {
      setVerifying(false);
    }
  };

  const handleResend = async (e: React.FormEvent) => {
    e.preventDefault();
    setResending(true);
    setError('');
    try {
      await authService.resendEmailVerification(email);
      setResent(true);
      toast.success('Verification email sent. Check your inbox.');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to resend verification email');
    } finally {
      setResending(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-muted/30">
      <Link href="/" className="absolute left-6 top-6 flex items-center gap-2 text-sm text-muted-foreground transition-colors hover:text-foreground">
        <ArrowLeft size={16} /> Back to home
      </Link>

      <div className="w-full max-w-md">
        <div className="mb-6 flex flex-col items-center">
          <div className="mb-2 flex h-12 w-12 items-center justify-center rounded-xl bg-primary text-2xl font-bold text-primary-foreground">
            D
          </div>
          <h1 className="text-xl font-bold text-foreground">DataFlow</h1>
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Mail className="h-5 w-5" /> Email Verification
            </CardTitle>
            <CardDescription>Verify your email address to activate your account</CardDescription>
          </CardHeader>
          <CardContent>
            {verified ? (
              <div className="space-y-4">
                <div className="flex flex-col items-center text-center py-4">
                  <CheckCircle2 className="mb-3 h-12 w-12 text-green-500" />
                  <p className="text-sm text-muted-foreground">
                    Your email has been verified successfully. Redirecting to dashboard...
                  </p>
                </div>
                <Link href="/dashboard">
                  <Button className="w-full">Go to Dashboard</Button>
                </Link>
              </div>
            ) : token ? (
              <div className="space-y-4">
                {error && (
                  <Alert variant="destructive">
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription>{error}</AlertDescription>
                  </Alert>
                )}
                <p className="text-sm text-muted-foreground">
                  Click the button below to verify your email address.
                </p>
                <Button onClick={handleVerify} disabled={verifying} className="w-full">
                  {verifying ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Verifying...
                    </>
                  ) : (
                    <>
                      <CheckCircle2 className="mr-2 h-4 w-4" />
                      Verify Email
                    </>
                  )}
                </Button>
              </div>
            ) : resent ? (
              <div className="space-y-4">
                <div className="flex flex-col items-center text-center py-4">
                  <CheckCircle2 className="mb-3 h-12 w-12 text-green-500" />
                  <p className="text-sm text-muted-foreground">
                    If an account exists for <strong className="text-foreground">{email}</strong>,
                    a verification link has been sent.
                  </p>
                </div>
                <Link href="/login">
                  <Button variant="outline" className="w-full gap-2">
                    <ArrowLeft className="h-4 w-4" /> Back to Login
                  </Button>
                </Link>
              </div>
            ) : (
              <form onSubmit={handleResend} className="space-y-4">
                {error && (
                  <Alert variant="destructive">
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription>{error}</AlertDescription>
                  </Alert>
                )}
                <p className="text-sm text-muted-foreground">
                  No verification token found. Enter your email to receive a new verification link.
                </p>
                <div className="space-y-2">
                  <label className="text-sm font-medium" htmlFor="email">Email</label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                    <Input
                      id="email"
                      type="email"
                      className="pl-9"
                      placeholder="you@company.com"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      required
                      autoComplete="email"
                    />
                  </div>
                </div>
                <Button type="submit" disabled={resending} className="w-full">
                  {resending ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Sending...
                    </>
                  ) : (
                    'Send Verification Link'
                  )}
                </Button>
              </form>
            )}

            <div className="mt-4 text-center">
              <Link href="/login" className="text-sm text-muted-foreground hover:text-foreground">
                ← Back to login
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

export default function VerifyEmailPage() {
  return (
    <Suspense fallback={<div className="flex min-h-screen items-center justify-center"><Loader2 className="h-8 w-8 animate-spin text-primary" /></div>}>
      <VerifyEmailContent />
    </Suspense>
  );
}
