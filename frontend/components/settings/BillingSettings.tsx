'use client';

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { CreditCard, Download, Check } from 'lucide-react';

const plans = [
  {
    name: 'Starter',
    price: '$0',
    period: '/month',
    features: ['1 workspace', '5 datasets', 'Basic dashboards', 'Community support'],
    current: false,
  },
  {
    name: 'Professional',
    price: '$49',
    period: '/month',
    features: ['5 workspaces', '50 datasets', 'Advanced analytics', 'Email support', 'API access'],
    current: false,
  },
  {
    name: 'Enterprise',
    price: 'Custom',
    period: '',
    features: ['Unlimited workspaces', 'Unlimited datasets', 'Custom AI models', 'Priority support', 'SSO & SAML', 'Audit logs'],
    current: true,
  },
];

export function BillingSettings() {
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <CreditCard className="h-5 w-5" /> Current Plan
          </CardTitle>
          <CardDescription>Your subscription and billing details</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between rounded-lg bg-muted p-4">
            <div>
              <div className="flex items-center gap-2">
                <p className="text-lg font-semibold">Enterprise Plan</p>
                <Badge variant="secondary">Active</Badge>
              </div>
              <p className="mt-1 text-sm text-muted-foreground">Billed annually · Renews January 1, 2027</p>
            </div>
            <Button variant="outline">Manage Plan</Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Available Plans</CardTitle>
          <CardDescription>Upgrade or downgrade your subscription</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 sm:grid-cols-3">
            {plans.map((plan) => (
              <div
                key={plan.name}
                className={`flex flex-col rounded-lg border p-4 ${
                  plan.current ? 'border-primary ring-2 ring-primary/20' : ''
                }`}
              >
                <div className="mb-3">
                  <p className="font-semibold">{plan.name}</p>
                  <p className="mt-1 text-2xl font-bold">
                    {plan.price}
                    <span className="text-sm font-normal text-muted-foreground">{plan.period}</span>
                  </p>
                </div>
                <ul className="mb-4 space-y-1.5 text-sm">
                  {plan.features.map((feature) => (
                    <li key={feature} className="flex items-center gap-2">
                      <Check className="h-3.5 w-3.5 text-primary" />
                      <span className="text-muted-foreground">{feature}</span>
                    </li>
                  ))}
                </ul>
                <Button
                  variant={plan.current ? 'outline' : 'default'}
                  disabled={plan.current}
                  className="mt-auto"
                >
                  {plan.current ? 'Current Plan' : 'Upgrade'}
                </Button>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Billing History</CardTitle>
          <CardDescription>Download past invoices</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {['INV-2026-001', 'INV-2026-002', 'INV-2026-003'].map((invoice) => (
              <div key={invoice} className="flex items-center justify-between rounded-lg border p-3">
                <div>
                  <p className="text-sm font-medium">{invoice}</p>
                  <p className="text-xs text-muted-foreground">Jan 1, 2026 · $1,200.00</p>
                </div>
                <Button variant="ghost" size="sm">
                  <Download className="mr-2 h-4 w-4" />
                  Download
                </Button>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
