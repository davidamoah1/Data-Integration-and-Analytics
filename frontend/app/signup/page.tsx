'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Eye, EyeOff, Loader2, CheckCircle2, Building2, ArrowLeft } from 'lucide-react';
import { useAuthStore } from '@/stores/authStore';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Alert, AlertDescription } from '@/components/ui/Alert';
import { toast } from '@/components/ui/Toaster';

const COUNTRIES = [
  'Ghana', 'Nigeria', 'Kenya', 'South Africa', 'United States', 'United Kingdom',
  'Canada', 'Australia', 'Germany', 'France', 'India', 'Other',
];

const INDUSTRIES = [
  'Healthcare', 'Education', 'Government', 'Business', 'Agriculture',
  'Retail', 'Manufacturing', 'NGO', 'Logistics', 'Insurance', 'Finance', 'Other',
];

const ORG_TYPES = [
  'Startup', 'Small Business', 'Enterprise', 'Government Agency',
  'Non-Profit', 'Educational Institution', 'Healthcare Facility', 'Research Organization', 'Other',
];

export default function SignUpPage() {
  const router = useRouter();
  const { signup, isLoading, error, clearError } = useAuthStore();

  const [form, setForm] = useState({
    full_name: '',
    organization_name: '',
    email: '',
    password: '',
    confirm_password: '',
    country: '',
    industry: '',
    organization_type: '',
  });
  const [agreeToTerms, setAgreeToTerms] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});

  const update = (key: string, value: string) => {
    setForm((prev) => ({ ...prev, [key]: value }));
    setValidationErrors((prev) => ({ ...prev, [key]: '' }));
  };

  const validate = (): boolean => {
    const errors: Record<string, string> = {};
    if (!form.full_name.trim()) errors.full_name = 'Full name is required';
    if (!form.email.trim()) errors.email = 'Email is required';
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) errors.email = 'Invalid email format';
    if (!form.password) errors.password = 'Password is required';
    else if (form.password.length < 8) errors.password = 'Password must be at least 8 characters';
    if (form.confirm_password !== form.password) errors.confirm_password = 'Passwords do not match';
    if (!form.country) errors.country = 'Please select a country';
    if (!form.industry) errors.industry = 'Please select an industry';
    if (!form.organization_type) errors.organization_type = 'Please select organization type';
    if (!agreeToTerms) errors.terms = 'You must agree to the Terms and Privacy Policy';
    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    clearError();
    if (!validate()) return;

    try {
      await signup({
        email: form.email,
        password: form.password,
        full_name: form.full_name,
        organization_name: form.organization_name || undefined,
        country: form.country,
        industry: form.industry,
        organization_type: form.organization_type,
      });
      toast.success("Account created! Let's set up your workspace.");
      router.push('/onboarding');
    } catch {
      // error is set in store
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 py-8">
      {/* Back to home */}
      <Link href="/" className="absolute left-6 top-6 flex items-center gap-2 text-sm text-slate-400 transition-colors hover:text-white">
        <ArrowLeft size={16} /> Back to home
      </Link>

      <div className="w-full max-w-lg">
        {/* Logo */}
        <div className="mb-6 flex flex-col items-center">
          <div className="mb-2 flex h-12 w-12 items-center justify-center rounded-xl bg-primary text-2xl font-bold text-primary-foreground">
            D
          </div>
          <h1 className="text-2xl font-bold text-white">DataFlow</h1>
          <p className="text-sm text-slate-400">Enterprise Data Intelligence Platform</p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Create Your Account</CardTitle>
            <CardDescription>Get started with a free account — no credit card required</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              {error && (
                <Alert variant="destructive">
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}

              <div className="space-y-2">
                <label className="text-sm font-medium" htmlFor="full_name">Full Name *</label>
                <Input
                  id="full_name"
                  placeholder="John Doe"
                  value={form.full_name}
                  onChange={(e) => update('full_name', e.target.value)}
                  required
                  autoComplete="name"
                />
                {validationErrors.full_name && <p className="text-xs text-red-500">{validationErrors.full_name}</p>}
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium" htmlFor="organization_name">
                  Organization Name <span className="text-muted-foreground">(optional)</span>
                </label>
                <div className="relative">
                  <Building2 className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                  <Input
                    id="organization_name"
                    className="pl-9"
                    placeholder="Acme Inc."
                    value={form.organization_name}
                    onChange={(e) => update('organization_name', e.target.value)}
                  />
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium" htmlFor="email">Email *</label>
                <Input
                  id="email"
                  type="email"
                  placeholder="you@company.com"
                  value={form.email}
                  onChange={(e) => update('email', e.target.value)}
                  required
                  autoComplete="email"
                />
                {validationErrors.email && <p className="text-xs text-red-500">{validationErrors.email}</p>}
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium" htmlFor="password">Password *</label>
                  <div className="relative">
                    <Input
                      id="password"
                      type={showPassword ? 'text' : 'password'}
                      placeholder="••••••••"
                      value={form.password}
                      onChange={(e) => update('password', e.target.value)}
                      required
                      autoComplete="new-password"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                    >
                      {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </button>
                  </div>
                  {validationErrors.password && <p className="text-xs text-red-500">{validationErrors.password}</p>}
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium" htmlFor="confirm_password">Confirm Password *</label>
                  <Input
                    id="confirm_password"
                    type={showPassword ? 'text' : 'password'}
                    placeholder="••••••••"
                    value={form.confirm_password}
                    onChange={(e) => update('confirm_password', e.target.value)}
                    required
                    autoComplete="new-password"
                  />
                  {validationErrors.confirm_password && <p className="text-xs text-red-500">{validationErrors.confirm_password}</p>}
                </div>
              </div>

              <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
                <div className="space-y-2">
                  <label className="text-sm font-medium" htmlFor="country">Country *</label>
                  <Select id="country" value={form.country} onChange={(e) => update('country', e.target.value)}>
                    <option value="">Select...</option>
                    {COUNTRIES.map((c) => <option key={c} value={c}>{c}</option>)}
                  </Select>
                  {validationErrors.country && <p className="text-xs text-red-500">{validationErrors.country}</p>}
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium" htmlFor="industry">Industry *</label>
                  <Select id="industry" value={form.industry} onChange={(e) => update('industry', e.target.value)}>
                    <option value="">Select...</option>
                    {INDUSTRIES.map((i) => <option key={i} value={i}>{i}</option>)}
                  </Select>
                  {validationErrors.industry && <p className="text-xs text-red-500">{validationErrors.industry}</p>}
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium" htmlFor="organization_type">Org Type *</label>
                  <Select id="organization_type" value={form.organization_type} onChange={(e) => update('organization_type', e.target.value)}>
                    <option value="">Select...</option>
                    {ORG_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
                  </Select>
                  {validationErrors.organization_type && <p className="text-xs text-red-500">{validationErrors.organization_type}</p>}
                </div>
              </div>

              <div className="flex items-start gap-2">
                <input
                  type="checkbox"
                  id="terms"
                  checked={agreeToTerms}
                  onChange={(e) => {
                    setAgreeToTerms(e.target.checked);
                    setValidationErrors((prev) => ({ ...prev, terms: '' }));
                  }}
                  className="mt-1 h-4 w-4 rounded border-input"
                />
                <label htmlFor="terms" className="text-sm text-muted-foreground">
                  I agree to the{' '}
                  <Link href="/terms" className="font-medium text-primary hover:underline">Terms of Service</Link>
                  {' '}and{' '}
                  <Link href="/privacy" className="font-medium text-primary hover:underline">Privacy Policy</Link>
                </label>
              </div>
              {validationErrors.terms && <p className="text-xs text-red-500">{validationErrors.terms}</p>}

              <Button type="submit" className="w-full" disabled={isLoading}>
                {isLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Creating account...
                  </>
                ) : (
                  <>
                    <CheckCircle2 className="mr-2 h-4 w-4" />
                    Create Account
                  </>
                )}
              </Button>
            </form>

            <div className="mt-4 text-center text-sm text-muted-foreground">
              Already have an account?{' '}
              <Link href="/login" className="font-medium text-primary hover:underline">
                Sign in
              </Link>
            </div>
          </CardContent>
        </Card>

        <div className="mt-6 text-center">
          <Link href="/" className="text-sm text-slate-400 transition-colors hover:text-white">
            ← Back to home
          </Link>
        </div>

        <p className="mt-4 text-center text-xs text-slate-500">
          © 2025 DataFlow. All rights reserved.
        </p>
      </div>
    </div>
  );
}
