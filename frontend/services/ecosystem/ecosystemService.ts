import { apiClient } from "../api/client";

// ─── Types ───────────────────────────────────────────────

export interface ConnectorType {
  type_code: string;
  display_name: string;
  category: string;
  description: string;
  icon: string;
  is_africa_first: boolean;
  region: string;
}

export interface Connector {
  id: number;
  name: string;
  connector_type: string;
  category: string;
  description: string | null;
  status: string;
  last_tested_at: string | null;
  is_public: boolean;
  created_at: string | null;
}

export interface MarketplacePlugin {
  id: number;
  plugin_id: string;
  name: string;
  version: string;
  author: string;
  description: string | null;
  category: string;
  icon: string | null;
  is_verified: boolean;
  is_featured: boolean;
  install_count: number;
  rating: number;
  tags: string[] | null;
}

export interface IndustryPackage {
  id: number;
  package_id: string;
  industry: string;
  name: string;
  description: string | null;
  version: string;
  is_africa_optimized: boolean;
}

export interface APIKey {
  id: number;
  name: string;
  key_prefix: string;
  scopes: string[] | null;
  rate_limit_per_hour: number;
  is_active: boolean;
  expires_at: string | null;
  last_used_at: string | null;
  created_at: string | null;
}

export interface WebhookSubscription {
  id: number;
  url: string;
  events: string[];
  is_active: boolean;
  description: string | null;
  created_at: string | null;
}

export interface EcosystemOverview {
  connectors: { total: number; active: number };
  api_keys: number;
  installed_plugins: number;
  webhooks: { total: number; failed_24h: number };
  api_calls_24h: number;
}

// ─── Connector API ────────────────────────────────────────

export const connectorService = {
  listTypes: () => apiClient.get<ConnectorType[]>("/connectors/types"),
  listAfricaTypes: () => apiClient.get<ConnectorType[]>("/connectors/types/africa"),
  list: () => apiClient.get<Connector[]>("/connectors"),
  get: (id: number) => apiClient.get(`/connectors/${id}`),
  create: (data: any) => apiClient.post("/connectors", data),
  update: (id: number, data: any) => apiClient.put(`/connectors/${id}`, data),
  delete: (id: number) => apiClient.delete(`/connectors/${id}`),
  test: (id: number) => apiClient.post(`/connectors/${id}/test`),
  extract: (id: number, query?: any) => apiClient.post(`/connectors/${id}/extract`, query),
  executions: (id: number) => apiClient.get(`/connectors/${id}/executions`),
};

// ─── Marketplace API ──────────────────────────────────────

export const marketplaceService = {
  listPlugins: (params?: { category?: string; search?: string }) =>
    apiClient.get<MarketplacePlugin[]>("/marketplace/plugins", { params }),
  getPlugin: (pluginId: string) => apiClient.get(`/marketplace/plugins/${pluginId}`),
  installPlugin: (pluginId: string, config?: any) =>
    apiClient.post(`/marketplace/plugins/${pluginId}/install`, config),
  listInstallations: () => apiClient.get("/marketplace/installations"),
  enablePlugin: (id: number) => apiClient.post(`/marketplace/installations/${id}/enable`),
  disablePlugin: (id: number) => apiClient.post(`/marketplace/installations/${id}/disable`),
  uninstallPlugin: (id: number) => apiClient.delete(`/marketplace/installations/${id}`),
  listPackages: (industry?: string) =>
    apiClient.get<IndustryPackage[]>("/marketplace/industry-packages", { params: { industry } }),
  getPackage: (packageId: string) => apiClient.get(`/marketplace/industry-packages/${packageId}`),
  installPackage: (packageId: string) =>
    apiClient.post(`/marketplace/industry-packages/${packageId}/install`),
};

// ─── API Key Management ───────────────────────────────────

export const apiKeyService = {
  create: (data: { name: string; scopes?: string[]; rate_limit_per_hour?: number }) =>
    apiClient.post<{ api_key: string }>("/platform/api-keys", data),
  list: () => apiClient.get<APIKey[]>("/platform/api-keys"),
  revoke: (id: number) => apiClient.delete(`/platform/api-keys/${id}`),
  rotate: (id: number) => apiClient.post<{ api_key: string }>(`/platform/api-keys/${id}/rotate`),
  usage: (days?: number) => apiClient.get<any>("/platform/usage", { params: { days } }),
  usageByKey: (days?: number) => apiClient.get("/platform/usage/by-key", { params: { days } }),
};

// ─── Webhook Management ───────────────────────────────────

export const webhookService = {
  listEvents: () => apiClient.get<string[]>("/webhooks/events"),
  list: () => apiClient.get<WebhookSubscription[]>("/webhooks"),
  create: (data: { url: string; events: string[]; description?: string }) =>
    apiClient.post<{ secret: string }>("/webhooks", data),
  delete: (id: number) => apiClient.delete(`/webhooks/${id}`),
  deliveries: (id: number) => apiClient.get(`/webhooks/${id}/deliveries`),
  redeliver: (webhookId: number, deliveryId: number) =>
    apiClient.post(`/webhooks/${webhookId}/redeliver/${deliveryId}`),
};

// ─── Ecosystem Monitoring ─────────────────────────────────

export const ecosystemMonitorService = {
  overview: () => apiClient.get("/ecosystem/monitoring/overview"),
  connectorHealth: () => apiClient.get("/ecosystem/monitoring/connectors"),
  webhookHealth: (days?: number) =>
    apiClient.get("/ecosystem/monitoring/webhooks", { params: { days } }),
};
