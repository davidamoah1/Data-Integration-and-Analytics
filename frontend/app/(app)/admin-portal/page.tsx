"use client";

import { useState, useEffect } from "react";
import {
  Shield, Building2, Users, DollarSign, Package, AlertCircle,
  Loader2, Search, Power, TrendingUp, Ticket,
} from "lucide-react";
import { adminPortalService, type AdminOverview, type Tenant } from "@/services/saas/saasService";

export default function AdminPortalPage() {
  const [overview, setOverview] = useState<AdminOverview | null>(null);
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [selectedTenant, setSelectedTenant] = useState<Tenant | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [ovResp, tenantsResp] = await Promise.all([
        adminPortalService.overview(),
        adminPortalService.listTenants(),
      ]);
      setOverview(ovResp);
      setTenants(tenantsResp || []);
    } catch (e) {
      console.error("Failed to load admin data:", e);
    } finally {
      setLoading(false);
    }
  };

  const handleSuspend = async (orgId: number) => {
    try {
      await adminPortalService.suspendTenant(orgId);
      loadData();
    } catch (e) {
      console.error("Suspend failed:", e);
    }
  };

  const handleActivate = async (orgId: number) => {
    try {
      await adminPortalService.activateTenant(orgId);
      loadData();
    } catch (e) {
      console.error("Activate failed:", e);
    }
  };

  const filteredTenants = tenants.filter((t) =>
    !search || t.name.toLowerCase().includes(search.toLowerCase())
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-[#0a0a0a]">
        <Loader2 className="w-8 h-8 animate-spin text-gray-500" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white p-6">
      <div className="max-w-7xl mx-auto">
        <div className="mb-6">
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Shield className="w-6 h-6 text-red-400" />
            Super Admin Portal
          </h1>
          <p className="text-sm text-gray-400 mt-1">Platform-wide management and oversight</p>
        </div>

        {/* Overview Stats */}
        {overview && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <StatCard label="Organizations" value={overview.organizations.total} sub={`${overview.organizations.active} active`} icon={Building2} color="text-blue-400" />
            <StatCard label="Users" value={overview.users.total} sub={`${overview.users.active} active`} icon={Users} color="text-green-400" />
            <StatCard label="Revenue/mo" value={`$${overview.monthly_revenue_estimate}`} sub={`${overview.subscriptions} subs`} icon={DollarSign} color="text-yellow-400" />
            <StatCard label="Open Tickets" value={overview.support.open_tickets} sub={`${overview.marketplace.plugins} plugins`} icon={Ticket} color="text-red-400" />
          </div>
        )}

        {/* Tenants */}
        <div className="bg-white/5 border border-white/10 rounded-xl p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold">Tenants</h2>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
              <input
                type="text"
                placeholder="Search organizations..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-10 pr-4 py-2 bg-white/5 border border-white/10 rounded-lg text-sm focus:outline-none focus:border-white/30"
              />
            </div>
          </div>

          <div className="space-y-2">
            {filteredTenants.map((tenant) => (
              <div
                key={tenant.id}
                className="flex items-center justify-between bg-white/5 border border-white/10 rounded-lg px-4 py-3"
              >
                <div className="flex items-center gap-3">
                  <Building2 className="w-5 h-5 text-gray-400" />
                  <div>
                    <p className="text-sm font-medium">{tenant.name}</p>
                    <div className="flex items-center gap-2 text-xs text-gray-500">
                      <span>{tenant.user_count} users</span>
                      <span>•</span>
                      <span className="capitalize">{tenant.plan}</span>
                      <span>•</span>
                      <span className={tenant.subscription_status === "active" ? "text-green-400" : "text-gray-400"}>
                        {tenant.subscription_status}
                      </span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className={`text-xs px-2 py-0.5 rounded-full ${
                    tenant.is_active ? "bg-green-500/20 text-green-400" : "bg-red-500/20 text-red-400"
                  }`}>
                    {tenant.is_active ? "Active" : "Suspended"}
                  </span>
                  {tenant.is_active ? (
                    <button
                      onClick={() => handleSuspend(tenant.id)}
                      className="p-2 hover:bg-red-500/10 rounded-lg transition-colors"
                      title="Suspend"
                    >
                      <Power className="w-4 h-4 text-red-400" />
                    </button>
                  ) : (
                    <button
                      onClick={() => handleActivate(tenant.id)}
                      className="p-2 hover:bg-green-500/10 rounded-lg transition-colors"
                      title="Activate"
                    >
                      <Power className="w-4 h-4 text-green-400" />
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function StatCard({ label, value, sub, icon: Icon, color }: { label: string; value: any; sub: string; icon: any; color: string }) {
  return (
    <div className="bg-white/5 border border-white/10 rounded-xl p-4">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs text-gray-400">{label}</span>
        <Icon className={`w-4 h-4 ${color}`} />
      </div>
      <p className="text-2xl font-bold">{value}</p>
      <p className="text-xs text-gray-500 mt-1">{sub}</p>
    </div>
  );
}
