import type { Metadata } from 'next';
import { Navbar } from '@/components/landing/Navbar';
import { Footer } from '@/components/landing/Footer';
import { Check, ArrowRight } from 'lucide-react';
import Link from 'next/link';

export const metadata: Metadata = {
  title: 'Pricing — DataFlow',
  description: 'Simple, transparent pricing for teams of all sizes.',
};

const plans = [
  {
    name: 'Free',
    price: '₵0',
    period: 'forever',
    description: 'For individuals getting started with data analytics',
    features: [
      'Up to 3 datasets',
      '5 dashboards',
      'Basic chart types',
      'CSV & Excel import',
      'Community support',
    ],
    cta: 'Get Started',
    href: '/signup',
    highlighted: false,
  },
  {
    name: 'Professional',
    price: '₵600',
    period: 'per month',
    description: 'For analysts and researchers who need more power',
    features: [
      'Unlimited datasets',
      'Unlimited dashboards',
      'All chart types & templates',
      'PDF, PowerPoint & Word export',
      'Smart Capture (OCR)',
      'AI Analytics Assistant',
      'Scheduled reports',
      'Email support',
    ],
    cta: 'Start Free Trial',
    href: '/signup',
    highlighted: true,
  },
  {
    name: 'Enterprise',
    price: 'Custom',
    period: 'contact us',
    description: 'For organizations with advanced security and scale needs',
    features: [
      'Everything in Professional',
      'SSO & SAML authentication',
      'Role-based access control',
      'Audit logs & compliance',
      'Dedicated support',
      'Custom integrations',
      'On-premise option',
      'SLA guarantee',
    ],
    cta: 'Contact Sales',
    href: '/contact',
    highlighted: false,
  },
];

export default function PricingPage() {
  return (
    <main className="min-h-screen bg-background">
      <Navbar />

      <section className="mx-auto max-w-7xl px-6 py-20">
        <div className="mx-auto max-w-2xl text-center">
          <h1 className="text-4xl font-bold tracking-tight text-slate-900 sm:text-5xl">
            Simple, transparent pricing
          </h1>
          <p className="mt-4 text-lg text-slate-600">
            Choose the plan that fits your team. Upgrade, downgrade, or cancel anytime.
          </p>
        </div>

        <div className="mt-16 grid gap-8 lg:grid-cols-3">
          {plans.map((plan) => (
            <div
              key={plan.name}
              className={`relative rounded-2xl border-2 p-8 ${
                plan.highlighted
                  ? 'border-blue-600 bg-blue-50/50 shadow-xl shadow-blue-200/50 dark:bg-blue-950/30 dark:shadow-blue-900/30'
                  : 'border-slate-200 bg-white dark:border-slate-700 dark:bg-slate-900'
              }`}
            >
              {plan.highlighted && (
                <div className="absolute -top-4 left-1/2 -translate-x-1/2 rounded-full bg-blue-600 px-4 py-1 text-xs font-semibold text-white">
                  Most Popular
                </div>
              )}
              <h3 className="text-lg font-bold text-slate-900">{plan.name}</h3>
              <p className="mt-1 text-sm text-slate-500">{plan.description}</p>
              <div className="mt-4 flex items-baseline gap-1">
                <span className="text-4xl font-bold text-slate-900">{plan.price}</span>
                <span className="text-sm text-slate-500">/{plan.period}</span>
              </div>
              <Link
                href={plan.href}
                className={`mt-6 flex w-full items-center justify-center gap-2 rounded-lg px-4 py-2.5 text-sm font-medium transition-colors ${
                  plan.highlighted
                    ? 'bg-blue-600 text-white hover:bg-blue-700'
                    : 'border border-slate-300 text-slate-700 hover:bg-slate-50 dark:border-slate-600 dark:text-slate-300 dark:hover:bg-slate-800'
                }`}
              >
                {plan.cta} <ArrowRight size={16} />
              </Link>
              <ul className="mt-8 space-y-3">
                {plan.features.map((feature) => (
                  <li key={feature} className="flex items-start gap-2 text-sm text-slate-700">
                    <Check className="mt-0.5 h-4 w-4 shrink-0 text-green-500" />
                    {feature}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="mt-16 rounded-2xl bg-slate-50 p-8 text-center dark:bg-slate-900">
          <h2 className="text-xl font-bold text-slate-900">Need a custom plan?</h2>
          <p className="mt-2 text-slate-600">We offer custom pricing for NGOs, educational institutions, and government agencies.</p>
          <Link href="/contact" className="mt-4 inline-block text-sm font-medium text-blue-600 hover:underline">
            Contact us →
          </Link>
        </div>
      </section>

      <Footer />
    </main>
  );
}
