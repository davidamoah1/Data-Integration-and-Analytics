'use client';

import { useEffect, useState } from 'react';
import { RouteGuard } from '@/components/auth/RouteGuard';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { CreditCard, TrendingUp, Users, DollarSign } from 'lucide-react';

interface Subscription {
  id: number;
  org_name: string;
  plan: string;
  status: 'active' | 'trialing' | 'canceled' | 'past_due';
  mrr: number;
  seats: number;
  current_period_end: string;
}

export default function SubscriptionsPage() {
  return (
    <RouteGuard role="super_admin">
      <SubscriptionsContent />
    </RouteGuard>
  );
}

function SubscriptionsContent() {
  const [subscriptions, setSubscriptions] = useState<Subscription[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(false);
  }, []);

  const totalMRR = subscriptions.reduce((s, sub) => s + sub.mrr, 0);
  const activeCount = subscriptions.filter((s) => s.status === 'active').length;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="flex items-center gap-2 text-2xl font-bold">
          <CreditCard className="h-6 w-6" />
          Subscriptions
        </h1>
        <p className="mt-1 text-muted-foreground">
          Manage platform subscriptions and billing.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardContent className="flex items-center justify-between p-6">
            <div>
              <p className="text-sm text-muted-foreground">Total MRR</p>
              <p className="text-2xl font-bold">${totalMRR.toLocaleString()}</p>
            </div>
            <DollarSign className="h-8 w-8 text-green-500" />
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex items-center justify-between p-6">
            <div>
              <p className="text-sm text-muted-foreground">Active Subs</p>
              <p className="text-2xl font-bold">{activeCount}</p>
            </div>
            <TrendingUp className="h-8 w-8 text-blue-500" />
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex items-center justify-between p-6">
            <div>
              <p className="text-sm text-muted-foreground">Total Seats</p>
              <p className="text-2xl font-bold">
                {subscriptions.reduce((s, sub) => s + sub.seats, 0)}
              </p>
            </div>
            <Users className="h-8 w-8 text-purple-500" />
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex items-center justify-between p-6">
            <div>
              <p className="text-sm text-muted-foreground">Past Due</p>
              <p className="text-2xl font-bold">
                {subscriptions.filter((s) => s.status === 'past_due').length}
              </p>
            </div>
            <CreditCard className="h-8 w-8 text-red-500" />
          </CardContent>
        </Card>
      </div>

      {loading ? (
        <div className="animate-pulse text-muted-foreground">Loading subscriptions...</div>
      ) : subscriptions.length === 0 ? (
        <Card>
          <CardContent className="p-12 text-center">
            <CreditCard className="mx-auto h-12 w-12 text-muted-foreground/50" />
            <p className="mt-4 text-lg font-medium">No subscriptions</p>
            <p className="mt-1 text-sm text-muted-foreground">
              Subscription data will appear here once organizations upgrade.
            </p>
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardHeader>
            <CardTitle>Active Subscriptions</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {subscriptions.map((sub) => (
                <div
                  key={sub.id}
                  className="flex items-center justify-between rounded-lg border p-4"
                >
                  <div>
                    <p className="font-medium">{sub.org_name}</p>
                    <p className="text-xs text-muted-foreground">
                      {sub.plan} · {sub.seats} seats · ${sub.mrr}/mo · Renews {sub.current_period_end}
                    </p>
                  </div>
                  <Badge
                    variant={
                      sub.status === 'active'
                        ? 'success'
                        : sub.status === 'trialing'
                          ? 'warning'
                          : sub.status === 'past_due'
                            ? 'destructive'
                            : 'default'
                    }
                  >
                    {sub.status}
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
