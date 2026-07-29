import { apiClient } from "../api/client";

// ─── Types ───────────────────────────────────────────────

export interface SubscriptionPlan {
  id: number;
  plan_code: string;
  name: string;
  description: string;
  price_monthly: number;
  price_yearly: number;
  currency: string;
  max_users: number | null;
  max_storage_mb: number | null;
  features: string[];
  is_trial_available: boolean;
  trial_days: number;
}

export interface SubscriptionStatus {
  status: string;
  plan: string;
  plan_name: string;
  is_active: boolean;
  current_period_end: string | null;
  trial_end: string | null;
  usage?: UsageData;
}

export interface UsageData {
  active_users: number;
  storage_used_mb: number;
  ai_requests: number;
  api_calls: number;
  workflow_executions: number;
  scheduled_jobs: number;
  model_trainings: number;
  connector_usage: number;
  limits: Record<string, number | null>;
}

export interface OnboardingProgress {
  steps_completed: string[];
  current_step: string;
  completion_percentage: number;
  is_complete: boolean;
  all_steps: { key: string; name: string; weight: number }[];
}

export interface AdminOverview {
  organizations: { total: number; active: number };
  users: { total: number; active: number };
  subscriptions: number;
  monthly_revenue_estimate: number;
  marketplace: { plugins: number; installations: number };
  support: { open_tickets: number };
}

export interface Tenant {
  id: number;
  name: string;
  slug: string;
  is_active: boolean;
  user_count: number;
  plan: string;
  subscription_status: string;
  created_at: string | null;
}

export interface HealthScore {
  score: number;
  status: string;
  factors: Record<string, { score: number; weight: number; detail: string }>;
}

// ─── SaaS API ─────────────────────────────────────────────

export const saasService = {
  listPlans: () => apiClient.get<SubscriptionPlan[]>("/saas/plans"),
  getSubscription: () => apiClient.get<SubscriptionStatus>("/saas/subscription"),
  subscribe: (data: { plan_code: string; billing_cycle?: string; is_trial?: boolean }) =>
    apiClient.post("/saas/subscribe", data),
  upgrade: (plan_code: string) => apiClient.post("/saas/upgrade", { plan_code }),
  cancel: () => apiClient.post("/saas/cancel"),
  getUsage: () => apiClient.get("/saas/usage"),
  getInvoices: () => apiClient.get("/saas/invoices"),
  getFeatures: () => apiClient.get("/saas/features"),
  getOnboarding: () => apiClient.get("/saas/onboarding"),
  completeOnboardingStep: (step_key: string, industry?: string) =>
    apiClient.post("/saas/onboarding/complete-step", { step_key, industry }),
  getHealthScore: () => apiClient.get("/saas/health-score"),
  createSupportTicket: (data: { subject: string; description?: string; priority?: string }) =>
    apiClient.post("/saas/support/tickets", data),
  listSupportTickets: () => apiClient.get("/saas/support/tickets"),
  getNotificationPreferences: () => apiClient.get("/saas/notification-preferences"),
  updateNotificationPreferences: (data: any) => apiClient.put("/saas/notification-preferences", data),
  getAnnouncements: () => apiClient.get("/saas/announcements"),
};

// ─── Admin Portal API ─────────────────────────────────────

export const adminPortalService = {
  overview: () => apiClient.get<AdminOverview>("/admin-portal/overview"),
  listTenants: (search?: string) => apiClient.get<Tenant[]>("/admin-portal/tenants", { params: { search } }),
  getTenant: (orgId: number) => apiClient.get(`/admin-portal/tenants/${orgId}`),
  suspendTenant: (orgId: number) => apiClient.post(`/admin-portal/tenants/${orgId}/suspend`),
  activateTenant: (orgId: number) => apiClient.post(`/admin-portal/tenants/${orgId}/activate`),
  listSubscriptions: () => apiClient.get("/admin-portal/subscriptions"),
  usageSummary: (days?: number) => apiClient.get("/admin-portal/usage-summary", { params: { days } }),
  listTickets: (status?: string) => apiClient.get("/admin-portal/support/tickets", { params: { status } }),
  resolveTicket: (id: number) => apiClient.post(`/admin-portal/support/tickets/${id}/resolve`),
};
