'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import {
  Eye, EyeOff, Loader2, CheckCircle2, Building2, ArrowLeft, ArrowRight,
  User as UserIcon, Mail, Lock, Sparkles, Users, AlertCircle,
} from 'lucide-react';
import { useAuthStore } from '@/stores/authStore';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Alert, AlertDescription } from '@/components/ui/Alert';
import { toast } from '@/components/ui/Toaster';
import { cn } from '@/lib/utils';

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

type RegistrationMode = 'create_organization' | 'join_organization' | 'personal';

export default function SignUpPage() {
  const router = useRouter();
  const { signupV2, isLoading, error, clearError } = useAuthStore();

  const [step, setStep] = useState(1);
  const [mode, setMode] = useState<RegistrationMode | null>(null);
  const [form, setForm] = useState({
    full_name: '',
    email: '',
    password: '',
    confirm_password: '',
    organization_name: '',
    country: '',
    industry: '',
    organization_type: '',
    invitation_token: '',
  });
  const [showPassword, setShowPassword] = useState(false);
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});
  const [agreeToTerms, setAgreeToTerms] = useState(false);

  const update = (key: string, value: string) => {
    setForm((prev) => ({ ...prev, [key]: value }));
    setValidationErrors((prev) => ({ ...prev, [key]: '' }));
  };

  const modeOptions = [
    {
      value: 'create_organization' as RegistrationMode,
      title: 'Create Organization',
      description: 'For hospitals, universities, businesses, government agencies, and NGOs',
      icon: Building2,
      badge: 'You become the Organization Admin',
    },
    {
      value: 'join_organization' as RegistrationMode,
      title: 'Join Organization',
      description: 'Have an invitation? Accept it and join your team',
      icon: Users,
      badge: 'Requires invitation token',
    },
    {
      value: 'personal' as RegistrationMode,
      title: 'Personal Workspace',
      description: 'For students, independent researchers, and freelancers',
      icon: Sparkles,
      badge: 'Basic features',
    },
  ];

  const validateStep = (currentStep: number): boolean => {
    const errors: Record<string, string> = {};

    if (currentStep === 1) {
      if (!mode) errors.mode = 'Please select a registration option';
    }

    if (currentStep === 2) {
      if (!form.full_name.trim()) errors.full_name = 'Full name is required';
      if (!form.email.trim()) errors.email = 'Email is required';
      else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) errors.email = 'Invalid email format';
      if (!form.password) errors.password = 'Password is required';
      else if (form.password.length < 8) errors.password = 'Password must be at least 8 characters';
      if (form.confirm_password !== form.password) errors.confirm_password = 'Passwords do not match';
      if (!agreeToTerms) errors.terms = 'You must agree to the Terms and Privacy Policy';

      if (mode === 'join_organization' && !form.invitation_token.trim()) {
        errors.invitation_token = 'Invitation token is required';
      }
    }

    if (currentStep === 3 && mode === 'create_organization') {
      if (!form.organization_name.trim()) errors.organization_name = 'Organization name is required';
      if (!form.country) errors.country = 'Please select a country';
      if (!form.industry) errors.industry = 'Please select an industry';
      if (!form.organization_type) errors.organization_type = 'Please select organization type';
    }

    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleNext = () => {
    clearError();
    if (!validateStep(step)) return;

    if (step === 1 && mode === 'personal') {
      setStep(2);
      return;
    }
    if (step === 1 && mode === 'join_organization') {
      setStep(2);
      return;
    }
    if (step === 2 && mode === 'personal') {
      handleSubmit();
      return;
    }
    if (step === 2 && mode === 'join_organization') {
      handleSubmit();
      return;
    }
    setStep((prev) => Math.min(prev + 1, 4));
  };

  const handleBack = () => {
    setStep((prev) => Math.max(prev - 1, 1));
  };

  const handleSubmit = async () => {
    if (!mode) return;

    try {
      await signupV2({
        email: form.email,
        password: form.password,
        full_name: form.full_name,
        registration_mode: mode,
        organization_name: mode === 'create_organization' ? form.organization_name : undefined,
        industry: mode === 'create_organization' ? form.industry : undefined,
        country: mode === 'create_organization' ? form.country : undefined,
        organization_type: mode === 'create_organization' ? form.organization_type : undefined,
        invitation_token: mode === 'join_organization' ? form.invitation_token : undefined,
      });
      toast.success('Account created successfully!');
      router.push('/onboarding');
    } catch (err) {
      const apiErr = err as { status?: number; message?: string };
      if (apiErr?.status === 409) {
        toast.error('An account with this email already exists. Try signing in instead.');
      } else if (apiErr?.status === 422) {
        toast.error(apiErr?.message || 'Please check your input and try again.');
      } else if (apiErr?.status === 0 || apiErr?.message?.includes('Unable to connect')) {
        toast.error('We couldn\'t reach the server. Check your connection and try again.');
      } else if (apiErr?.status && apiErr.status >= 500) {
        toast.error(apiErr?.message || 'We couldn\'t create your account right now. Please try again in a moment.');
      } else {
        toast.error(apiErr?.message || 'We couldn\'t create your account. Please try again.');
      }
    }
  };

  const stepTitles = ['Choose Option', 'Account Details', 'Organization Details', 'Review & Complete'];

  return (
    <div className="flex min-h-screen items-center justify-center bg-muted/30 py-8">
      <Link href="/" className="absolute left-6 top-6 flex items-center gap-2 text-sm text-muted-foreground transition-colors hover:text-foreground">
        <ArrowLeft size={16} /> Back to home
      </Link>

      <div className="w-full max-w-lg">
        {/* Logo */}
        <div className="mb-6 flex flex-col items-center">
          <div className="mb-2 flex h-12 w-12 items-center justify-center rounded-xl bg-primary text-2xl font-bold text-primary-foreground">
            D
          </div>
          <h1 className="text-xl font-bold text-foreground">DataFlow</h1>
          <p className="text-sm text-muted-foreground">Enterprise Data Intelligence Platform</p>
        </div>

        {/* Step indicator */}
        <div className="mb-6 flex items-center justify-center gap-2">
          {stepTitles.map((title, index) => {
            const stepNum = index + 1;
            const isActive = step === stepNum;
            const isComplete = step > stepNum;
            // Hide step 3 (Organization Details) for non-create_organization modes
            if (index === 2 && mode !== 'create_organization') return null;

            return (
              <div key={title} className="flex items-center">
                <div className={cn(
                  'flex h-8 w-8 items-center justify-center rounded-full text-xs font-semibold transition-colors',
                  isActive ? 'bg-primary text-primary-foreground' :
                  isComplete ? 'bg-primary/20 text-primary' :
                  'bg-slate-700 text-slate-400',
                )}>
                  {isComplete ? <CheckCircle2 className="h-4 w-4" /> : stepNum}
                </div>
                {index < stepTitles.length - 1 && (
                  <div className={cn('h-0.5 w-8', isComplete ? 'bg-primary/40' : 'bg-slate-700')} />
                )}
              </div>
            );
          })}
        </div>

        <Card>
          <CardHeader>
            <CardTitle>{stepTitles[step - 1]}</CardTitle>
            <CardDescription>
              {step === 1 && 'How would you like to get started?'}
              {step === 2 && 'Enter your account details'}
              {step === 3 && 'Tell us about your organization'}
              {step === 4 && 'Review your information and create your account'}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {error && (
              <Alert variant="destructive" className="mb-4">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            {/* Step 1: Choose registration mode */}
            {step === 1 && (
              <div className="space-y-3">
                {modeOptions.map((opt) => {
                  const Icon = opt.icon;
                  const isSelected = mode === opt.value;
                  return (
                    <button
                      key={opt.value}
                      onClick={() => { setMode(opt.value); setValidationErrors({}); }}
                      className={cn(
                        'flex w-full items-start gap-3 rounded-lg border p-4 text-left transition-all',
                        isSelected
                          ? 'border-primary bg-primary/5 ring-2 ring-primary/20'
                          : 'border-border hover:border-primary/50 hover:bg-accent',
                      )}
                    >
                      <div className={cn(
                        'flex h-10 w-10 shrink-0 items-center justify-center rounded-lg',
                        isSelected ? 'bg-primary text-primary-foreground' : 'bg-muted text-muted-foreground',
                      )}>
                        <Icon className="h-5 w-5" />
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center justify-between">
                          <p className="font-medium">{opt.title}</p>
                          {isSelected && <CheckCircle2 className="h-4 w-4 text-primary" />}
                        </div>
                        <p className="mt-0.5 text-sm text-muted-foreground">{opt.description}</p>
                        <span className="mt-1.5 inline-block rounded bg-muted px-2 py-0.5 text-xs text-muted-foreground">
                          {opt.badge}
                        </span>
                      </div>
                    </button>
                  );
                })}
                {validationErrors.mode && <p className="text-xs text-red-500">{validationErrors.mode}</p>}
              </div>
            )}

            {/* Step 2: Account details */}
            {step === 2 && (
              <div className="space-y-4">
                {mode === 'join_organization' && (
                  <div className="rounded-lg border border-primary/30 bg-primary/5 p-3 text-sm">
                    <p className="font-medium text-primary">You are joining an organization</p>
                    <p className="mt-0.5 text-muted-foreground">Enter your invitation token below to get started.</p>
                  </div>
                )}
                {mode === 'personal' && (
                  <div className="rounded-lg border border-primary/30 bg-primary/5 p-3 text-sm">
                    <p className="font-medium text-primary">You are creating a personal workspace</p>
                    <p className="mt-0.5 text-muted-foreground">You can upgrade or join an organization later.</p>
                  </div>
                )}
                {mode === 'create_organization' && (
                  <div className="rounded-lg border border-primary/30 bg-primary/5 p-3 text-sm">
                    <p className="font-medium text-primary">You are creating an organization</p>
                    <p className="mt-0.5 text-muted-foreground">You will be the Organization Administrator with full access.</p>
                  </div>
                )}

                <div className="space-y-2">
                  <label className="text-sm font-medium" htmlFor="full_name">Full Name *</label>
                  <div className="relative">
                    <UserIcon className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                    <Input id="full_name" className="pl-9" placeholder="Kwame Mensah" value={form.full_name} onChange={(e) => update('full_name', e.target.value)} />
                  </div>
                  {validationErrors.full_name && <p className="text-xs text-red-500">{validationErrors.full_name}</p>}
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium" htmlFor="email">Email *</label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                    <Input id="email" type="email" className="pl-9" placeholder="you@company.com" value={form.email} onChange={(e) => update('email', e.target.value)} />
                  </div>
                  {validationErrors.email && <p className="text-xs text-red-500">{validationErrors.email}</p>}
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

                {mode === 'join_organization' && (
                  <div className="space-y-2">
                    <label className="text-sm font-medium" htmlFor="invitation_token">Invitation Token *</label>
                    <Input id="invitation_token" placeholder="Enter your invitation token" value={form.invitation_token} onChange={(e) => update('invitation_token', e.target.value)} />
                    {validationErrors.invitation_token && <p className="text-xs text-red-500">{validationErrors.invitation_token}</p>}
                  </div>
                )}

                <div className="flex items-start gap-2">
                  <input type="checkbox" id="terms" checked={agreeToTerms} onChange={(e) => { setAgreeToTerms(e.target.checked); setValidationErrors((prev) => ({ ...prev, terms: '' })); }} className="mt-1 h-4 w-4 rounded border-input" />
                  <label htmlFor="terms" className="text-sm text-muted-foreground">
                    I agree to the{' '}
                    <Link href="/terms" className="font-medium text-primary hover:underline">Terms of Service</Link>
                    {' '}and{' '}
                    <Link href="/privacy" className="font-medium text-primary hover:underline">Privacy Policy</Link>
                  </label>
                </div>
                {validationErrors.terms && <p className="text-xs text-red-500">{validationErrors.terms}</p>}
              </div>
            )}

            {/* Step 3: Organization details (only for create_organization) */}
            {step === 3 && mode === 'create_organization' && (
              <div className="space-y-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium" htmlFor="organization_name">Organization Name *</label>
                  <div className="relative">
                    <Building2 className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                    <Input id="organization_name" className="pl-9" placeholder="Acme Inc." value={form.organization_name} onChange={(e) => update('organization_name', e.target.value)} />
                  </div>
                  {validationErrors.organization_name && <p className="text-xs text-red-500">{validationErrors.organization_name}</p>}
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

                <div className="rounded-lg bg-muted p-3 text-xs text-muted-foreground">
                  <p className="font-medium text-foreground">Security Note:</p>
                  You will be automatically assigned the <span className="font-medium">Organization Administrator</span> role.
                  You cannot select Super Admin or other privileged roles during registration.
                </div>
              </div>
            )}

            {/* Step 4: Review & Complete */}
            {step === 4 && mode === 'create_organization' && (
              <div className="space-y-4">
                <div className="rounded-lg border p-4 space-y-2">
                  <div className="flex justify-between"><span className="text-muted-foreground">Name</span><span className="font-medium">{form.full_name}</span></div>
                  <div className="flex justify-between"><span className="text-muted-foreground">Email</span><span className="font-medium">{form.email}</span></div>
                  <div className="flex justify-between"><span className="text-muted-foreground">Organization</span><span className="font-medium">{form.organization_name}</span></div>
                  <div className="flex justify-between"><span className="text-muted-foreground">Country</span><span className="font-medium">{form.country}</span></div>
                  <div className="flex justify-between"><span className="text-muted-foreground">Industry</span><span className="font-medium">{form.industry}</span></div>
                  <div className="flex justify-between"><span className="text-muted-foreground">Role</span><span className="font-medium text-primary">Organization Admin</span></div>
                </div>
                <p className="text-center text-sm text-muted-foreground">Click &quot;Create Account&quot; to proceed to onboarding.</p>
              </div>
            )}

            {/* Navigation buttons */}
            <div className="mt-6 flex items-center justify-between gap-3">
              {step > 1 ? (
                <Button variant="outline" onClick={handleBack}>
                  <ArrowLeft className="mr-2 h-4 w-4" /> Back
                </Button>
              ) : (
                <div />
              )}

              {(step < 4 && !(step === 2 && (mode === 'personal' || mode === 'join_organization'))) ? (
                <Button onClick={handleNext} disabled={isLoading}>
                  {isLoading ? (
                    <><Loader2 className="mr-2 h-4 w-4 animate-spin" /> Processing...</>
                  ) : (
                    <>Next <ArrowRight className="ml-2 h-4 w-4" /></>
                  )}
                </Button>
              ) : (
                <Button onClick={handleSubmit} disabled={isLoading}>
                  {isLoading ? (
                    <><Loader2 className="mr-2 h-4 w-4 animate-spin" /> Creating...</>
                  ) : (
                    <><CheckCircle2 className="mr-2 h-4 w-4" /> Create Account</>
                  )}
                </Button>
              )}
            </div>
          </CardContent>
        </Card>

        <div className="mt-4 text-center text-sm text-muted-foreground">
          Already have an account?{' '}
          <Link href="/login" className="font-medium text-primary hover:underline">Sign in</Link>
        </div>

        <p className="mt-4 text-center text-xs text-slate-500">
          © 2026 DataFlow. All rights reserved.
        </p>
      </div>
    </div>
  );
}
