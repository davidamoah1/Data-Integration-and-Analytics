'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import {
  Loader2, CheckCircle2, ArrowRight, ArrowLeft,
  Building2, Heart, GraduationCap, Landmark, Store, Factory, Tractor,
  Truck, Shield, Users, Sparkles,
} from 'lucide-react';
import { authService, type OnboardingPayload } from '@/services/auth/authService';
import { useAuthStore } from '@/stores/authStore';
import { onboardingService, type OnboardingStatus } from '@/services/onboarding/onboardingService';
import { GuidedOnboarding } from '@/components/onboarding/GuidedOnboarding';
import { Button } from '@/components/ui/Button';
import { toast } from '@/components/ui/Toaster';

const STEPS = ['Industry', 'Organization', 'Goal', 'Setup'];

const INDUSTRIES = [
  { key: 'Healthcare', icon: Heart, color: 'bg-red-500' },
  { key: 'Education', icon: GraduationCap, color: 'bg-blue-500' },
  { key: 'Government', icon: Landmark, color: 'bg-indigo-500' },
  { key: 'Business', icon: Building2, color: 'bg-slate-600' },
  { key: 'Agriculture', icon: Tractor, color: 'bg-green-500' },
  { key: 'Retail', icon: Store, color: 'bg-orange-500' },
  { key: 'Manufacturing', icon: Factory, color: 'bg-amber-600' },
  { key: 'Logistics', icon: Truck, color: 'bg-cyan-600' },
  { key: 'Insurance', icon: Shield, color: 'bg-purple-500' },
  { key: 'NGO', icon: Users, color: 'bg-pink-500' },
];

const ORG_TYPES = [
  'Startup', 'Small Business', 'Enterprise', 'Government Agency',
  'Non-Profit', 'Educational Institution', 'Healthcare Facility', 'Research Organization', 'Other',
];

const GOALS = [
  { key: 'data_cleaning', label: 'Clean & Prepare Data', icon: Sparkles, desc: 'Automated data quality and transformation' },
  { key: 'analytics', label: 'Analyze Data', icon: Building2, desc: 'Statistical analysis and insights' },
  { key: 'reporting', label: 'Generate Reports', icon: CheckCircle2, desc: 'Automated reporting and dashboards' },
  { key: 'collaboration', label: 'Team Collaboration', icon: Users, desc: 'Share and collaborate on data projects' },
];

export default function OnboardingPage() {
  const router = useRouter();
  const { user } = useAuthStore();
  const [phase, setPhase] = useState<'profile' | 'guided'>('profile');
  const [step, setStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<OnboardingPayload>({
    industry: '',
    organization_type: '',
    primary_goal: '',
  });

  useEffect(() => {
    async function check() {
      try {
        const existingUser = user as any;
        if (existingUser?.industry && existingUser?.organization_type) {
          setPhase('guided');
        }
      } catch {
        // ignore
      }
    }
    check();
  }, [user]);

  const next = () => setStep((s) => Math.min(s + 1, STEPS.length - 1));
  const back = () => setStep((s) => Math.max(s - 1, 0));

  const finishProfile = async () => {
    setLoading(true);
    try {
      await authService.completeOnboarding(data);
      setPhase('guided');
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Failed to save profile');
    } finally {
      setLoading(false);
    }
  };

  const canProceed = () => {
    if (step === 0) return !!data.industry;
    if (step === 1) return !!data.organization_type;
    if (step === 2) return !!data.primary_goal;
    return true;
  };

  // Phase 2: Role-specific guided onboarding
  if (phase === 'guided') {
    return <GuidedOnboarding onComplete={() => router.push('/dashboard')} />;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-950 dark:to-slate-900">
      {/* Progress bar */}
      <div className="border-b border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
        <div className="mx-auto flex max-w-3xl items-center gap-2 px-6 py-4">
          {STEPS.map((label, i) => (
            <div key={label} className="flex flex-1 items-center gap-2">
              <div className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-xs font-bold transition-colors ${
                i < step ? 'bg-green-500 text-white' :
                i === step ? 'bg-primary text-primary-foreground' :
                'bg-slate-200 text-slate-400 dark:bg-slate-700 dark:text-slate-500'
              }`}>
                {i < step ? <CheckCircle2 size={16} /> : i + 1}
              </div>
              <span className={`hidden text-xs font-medium sm:inline ${i <= step ? 'text-slate-700 dark:text-slate-300' : 'text-slate-400 dark:text-slate-600'}`}>
                {label}
              </span>
              {i < STEPS.length - 1 && <div className={`h-0.5 flex-1 ${i < step ? 'bg-green-500' : 'bg-slate-200 dark:bg-slate-700'}`} />}
            </div>
          ))}
        </div>
      </div>

      <div className="mx-auto max-w-3xl px-6 py-12">
        {/* Step 0: Industry */}
        {step === 0 && (
          <div>
            <h2 className="mb-2 text-2xl font-bold text-slate-900 dark:text-slate-100">What industry are you in?</h2>
            <p className="mb-6 text-slate-500 dark:text-slate-400">Select the industry that best describes your work.</p>
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
              {INDUSTRIES.map((ind) => (
                <button
                  key={ind.key}
                  onClick={() => setData((d) => ({ ...d, industry: ind.key }))}
                  className={`flex flex-col items-center gap-2 rounded-xl border-2 p-4 transition-all hover:shadow-md ${
                    data.industry === ind.key
                      ? 'border-primary bg-primary/5'
                      : 'border-slate-200 bg-white hover:border-slate-300 dark:border-slate-700 dark:bg-slate-800 dark:hover:border-slate-600'
                  }`}
                >
                  <div className={`flex h-10 w-10 items-center justify-center rounded-lg ${ind.color} text-white`}>
                    <ind.icon size={20} />
                  </div>
                  <span className="text-xs font-medium text-slate-700 dark:text-slate-300">{ind.key}</span>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Step 1: Organization Type */}
        {step === 1 && (
          <div>
            <h2 className="mb-2 text-2xl font-bold text-slate-900 dark:text-slate-100">What type of organization?</h2>
            <p className="mb-6 text-slate-500 dark:text-slate-400">This helps us configure the right features for you.</p>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              {ORG_TYPES.map((type) => (
                <button
                  key={type}
                  onClick={() => setData((d) => ({ ...d, organization_type: type }))}
                  className={`flex items-center gap-3 rounded-xl border-2 p-4 text-left transition-all hover:shadow-md ${
                    data.organization_type === type
                      ? 'border-primary bg-primary/5'
                      : 'border-slate-200 bg-white hover:border-slate-300 dark:border-slate-700 dark:bg-slate-800 dark:hover:border-slate-600'
                  }`}
                >
                  <div className={`flex h-8 w-8 items-center justify-center rounded-lg ${
                    data.organization_type === type ? 'bg-primary text-primary-foreground' : 'bg-slate-100 text-slate-400 dark:bg-slate-700 dark:text-slate-500'
                  }`}>
                    {data.organization_type === type ? <CheckCircle2 size={16} /> : <Building2 size={16} />}
                  </div>
                  <span className="text-sm font-medium text-slate-700 dark:text-slate-300">{type}</span>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Step 2: Primary Goal */}
        {step === 2 && (
          <div>
            <h2 className="mb-2 text-2xl font-bold text-slate-900 dark:text-slate-100">What&apos;s your primary goal?</h2>
            <p className="mb-6 text-slate-500 dark:text-slate-400">What do you want to achieve with DataFlow first?</p>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              {GOALS.map((goal) => (
                <button
                  key={goal.key}
                  onClick={() => setData((d) => ({ ...d, primary_goal: goal.key }))}
                  className={`flex items-start gap-3 rounded-xl border-2 p-5 text-left transition-all hover:shadow-md ${
                    data.primary_goal === goal.key
                      ? 'border-primary bg-primary/5'
                      : 'border-slate-200 bg-white hover:border-slate-300 dark:border-slate-700 dark:bg-slate-800 dark:hover:border-slate-600'
                  }`}
                >
                  <div className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-lg ${
                    data.primary_goal === goal.key ? 'bg-primary text-primary-foreground' : 'bg-slate-100 text-slate-400 dark:bg-slate-700 dark:text-slate-500'
                  }`}>
                    <goal.icon size={20} />
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-slate-800 dark:text-slate-200">{goal.label}</p>
                    <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">{goal.desc}</p>
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Step 3: Preview & Continue to guided setup */}
        {step === 3 && (
          <div className="text-center">
            <div className="mx-auto mb-6 flex h-20 w-20 items-center justify-center rounded-2xl bg-primary text-primary-foreground shadow-lg">
              <Sparkles size={36} />
            </div>
            <h2 className="text-2xl font-bold text-slate-900 dark:text-slate-100">Ready to set up your workspace!</h2>
            <p className="mx-auto mt-3 max-w-md text-slate-500 dark:text-slate-400">
              Based on your role, we&apos;ve prepared a guided setup. You&apos;ll get a blank workspace — no demo data.
            </p>
            <div className="mx-auto mt-6 max-w-sm rounded-xl border bg-white p-4 text-left dark:bg-slate-800">
              <div className="space-y-2 text-sm">
                <div className="flex justify-between"><span className="text-muted-foreground">Industry</span><span className="font-medium">{data.industry}</span></div>
                <div className="flex justify-between"><span className="text-muted-foreground">Organization</span><span className="font-medium">{data.organization_type}</span></div>
                <div className="flex justify-between"><span className="text-muted-foreground">Goal</span><span className="font-medium">{data.primary_goal?.replace(/_/g, ' ')}</span></div>
              </div>
            </div>
            <div className="mt-8">
              <Button size="lg" onClick={finishProfile} disabled={loading} className="gap-2">
                {loading ? <Loader2 size={18} className="animate-spin" /> : <ArrowRight size={18} />}
                Start Guided Setup
              </Button>
            </div>
          </div>
        )}

        {/* Navigation buttons */}
        {step < 3 && (
          <div className="mt-8 flex items-center justify-between">
            <Button variant="outline" onClick={back} disabled={step === 0} className="gap-2">
              Back
            </Button>
            <Button onClick={next} disabled={!canProceed()} className="gap-2">
              Continue <ArrowRight size={16} />
            </Button>
          </div>
        )}
        {step === 3 && (
          <div className="mt-8 flex items-center justify-start">
            <Button variant="outline" onClick={back} className="gap-2">
              Back
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
