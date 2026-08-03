"use client";

import { useState, useEffect } from "react";
import {
  CreditCard, Check, Loader2, Zap, TrendingUp, Building2,
  Crown, Sparkles, X, Calendar, AlertCircle,
} from "lucide-react";
import { saasService, type SubscriptionPlan, type SubscriptionStatus } from "@/services/saas/saasService";
import { RouteGuard } from "@/components/auth/RouteGuard";

export default function BillingPage() {
  return (
    <RouteGuard role="super_admin">
      <BillingContent />
    </RouteGuard>
  );
}

function BillingContent() {
  const planIcons: Record<string, any> = {
    free: Zap,
    starter: TrendingUp,
    professional: Building2,
    business: Crown,
    enterprise: Sparkles,
  };

  const planColors: Record<string, string> = {
    free: "border-gray-500/30",
    starter: "border-blue-500/30",
    professional: "border-purple-500/30",
    business: "border-orange-500/30",
    enterprise: "border-yellow-500/30",
  };

  const [plans, setPlans] = useState<SubscriptionPlan[]>([]);
  const [subscription, setSubscription] = useState<SubscriptionStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [billingCycle, setBillingCycle] = useState<"monthly" | "yearly">("monthly");
  const [subscribing, setSubscribing] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [plansResp, subResp] = await Promise.all([
        saasService.listPlans(),
        saasService.getSubscription(),
      ]);
      setPlans(plansResp || []);
      setSubscription(subResp);
    } catch (e) {
      console.error("Failed to load billing data:", e);
      setError("Failed to load billing information. Please try again later.");
    } finally {
      setLoading(false);
    }
  };

  const handleSubscribe = async (planCode: string, isTrial: boolean = false) => {
    setSubscribing(planCode);
    try {
      if (subscription?.status === "none") {
        await saasService.subscribe({ plan_code: planCode, billing_cycle: billingCycle, is_trial: isTrial });
      } else {
        await saasService.upgrade(planCode);
      }
      loadData();
    } catch (e) {
      console.error("Subscribe failed:", e);
    } finally {
      setSubscribing(null);
    }
  };

  const handleCancel = async () => {
    try {
      await saasService.cancel();
      loadData();
    } catch (e) {
      console.error("Cancel failed:", e);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-[#0a0a0a]">
        <Loader2 className="w-8 h-8 animate-spin text-gray-500" />
      </div>
    );
  }

  if (error && plans.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-[#0a0a0a] text-white">
        <AlertCircle className="w-12 h-12 text-red-400 mb-4" />
        <p className="text-sm text-gray-400 mb-4">{error}</p>
        <button
          onClick={loadData}
          className="px-4 py-2 bg-white/10 hover:bg-white/20 rounded-lg text-sm transition-colors"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white p-6">
      <div className="max-w-6xl mx-auto">
        <div className="mb-6">
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <CreditCard className="w-6 h-6 text-green-400" />
            Billing & Subscription
          </h1>
          <p className="text-sm text-gray-400 mt-1">Manage your subscription plan and billing</p>
        </div>

        {/* Current Subscription */}
        {subscription && subscription.status !== "none" && (
          <div className="bg-white/5 border border-white/10 rounded-xl p-5 mb-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400">Current Plan</p>
                <p className="text-xl font-bold capitalize">{subscription.plan_name}</p>
                <p className="text-xs text-gray-500 mt-1">Status: {subscription.status}</p>
              </div>
              <div className="flex items-center gap-3">
                {subscription.current_period_end && (
                  <span className="text-xs text-gray-400 flex items-center gap-1">
                    <Calendar className="w-3 h-3" />
                    Renews {new Date(subscription.current_period_end).toLocaleDateString()}
                  </span>
                )}
                <button
                  onClick={handleCancel}
                  className="px-3 py-1.5 bg-red-500/10 text-red-400 border border-red-500/20 rounded-lg text-xs hover:bg-red-500/20"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Billing Cycle Toggle */}
        <div className="flex items-center gap-2 mb-6">
          <button
            onClick={() => setBillingCycle("monthly")}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              billingCycle === "monthly" ? "bg-white/10 text-white" : "text-gray-400"
            }`}
          >
            Monthly
          </button>
          <button
            onClick={() => setBillingCycle("yearly")}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              billingCycle === "yearly" ? "bg-white/10 text-white" : "text-gray-400"
            }`}
          >
            Yearly <span className="text-xs text-green-400 ml-1">Save ~17%</span>
          </button>
        </div>

        {/* Plans Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
          {plans.map((plan) => {
            const Icon = planIcons[plan.plan_code] || Zap;
            const isCurrent = subscription?.plan === plan.plan_code;
            const price = billingCycle === "yearly" ? plan.price_yearly : plan.price_monthly;
            return (
              <div
                key={plan.plan_code}
                className={`bg-white/5 border-2 rounded-xl p-5 flex flex-col ${
                  planColors[plan.plan_code] || "border-white/10"
                } ${isCurrent ? "ring-2 ring-green-500/30" : ""}`}
              >
                <div className="flex items-center gap-2 mb-3">
                  <Icon className="w-5 h-5 text-gray-300" />
                  <h3 className="font-bold text-sm">{plan.name}</h3>
                </div>
                <p className="text-xs text-gray-400 mb-3 line-clamp-2">{plan.description}</p>
                <div className="mb-4">
                  <span className="text-2xl font-bold">₵{price}</span>
                  <span className="text-xs text-gray-500">/{billingCycle === "yearly" ? "yr" : "mo"}</span>
                </div>
                <div className="space-y-1.5 mb-4 flex-1">
                  {plan.features.slice(0, 6).map((f) => (
                    <div key={f} className="flex items-center gap-1.5 text-xs">
                      <Check className="w-3 h-3 text-green-400 flex-shrink-0" />
                      <span className="text-gray-300">{f.replace(/_/g, " ")}</span>
                    </div>
                  ))}
                  {plan.features.length > 6 && (
                    <p className="text-xs text-gray-500">+{plan.features.length - 6} more</p>
                  )}
                </div>
                {isCurrent ? (
                  <div className="text-center py-2 bg-green-500/10 text-green-400 rounded-lg text-xs font-medium">
                    Current Plan
                  </div>
                ) : (
                  <div className="space-y-2">
                    <button
                      onClick={() => handleSubscribe(plan.plan_code)}
                      disabled={subscribing === plan.plan_code}
                      className="w-full py-2 bg-white/10 hover:bg-white/20 rounded-lg text-xs font-medium transition-colors disabled:opacity-50"
                    >
                      {subscribing === plan.plan_code ? (
                        <Loader2 className="w-3 h-3 animate-spin mx-auto" />
                      ) : subscription?.status === "none" ? "Subscribe" : "Switch"}
                    </button>
                    {plan.is_trial_available && (
                      <button
                        onClick={() => handleSubscribe(plan.plan_code, true)}
                        disabled={subscribing === plan.plan_code}
                        className="w-full py-1.5 text-xs text-gray-400 hover:text-white transition-colors"
                      >
                        Start {plan.trial_days}-day trial
                      </button>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
