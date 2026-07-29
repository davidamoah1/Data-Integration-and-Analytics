"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import {
  Database, File, Cloud, Code, Wallet, Banknote, Building2,
  GraduationCap, Search, Plus, CheckCircle2, AlertCircle, Loader2,
  Settings, Trash2, Zap,
} from "lucide-react";
import { connectorService, type ConnectorType, type Connector } from "@/services/ecosystem/ecosystemService";

const categoryIcons: Record<string, any> = {
  database: Database,
  file: File,
  cloud_storage: Cloud,
  api: Code,
};

const categoryColors: Record<string, string> = {
  database: "bg-blue-500/10 text-blue-400 border-blue-500/20",
  file: "bg-green-500/10 text-green-400 border-green-500/20",
  cloud_storage: "bg-purple-500/10 text-purple-400 border-purple-500/20",
  api: "bg-orange-500/10 text-orange-400 border-orange-500/20",
};

export default function ConnectorsPage() {
  const router = useRouter();
  const [types, setTypes] = useState<ConnectorType[]>([]);
  const [connectors, setConnectors] = useState<Connector[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [filterCategory, setFilterCategory] = useState<string>("all");
  const [showAfricaOnly, setShowAfricaOnly] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [typesResp, connResp] = await Promise.all([
        connectorService.listTypes(),
        connectorService.list(),
      ]);
      setTypes(typesResp || []);
      setConnectors(connResp || []);
    } catch (e) {
      console.error("Failed to load connectors:", e);
    } finally {
      setLoading(false);
    }
  };

  const filteredTypes = types.filter((t) => {
    if (showAfricaOnly && !t.is_africa_first) return false;
    if (filterCategory !== "all" && t.category !== filterCategory) return false;
    if (search && !t.display_name.toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  });

  const categories = ["all", ...Array.from(new Set(types.map((t) => t.category)))];

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white p-6">
      <div className="max-w-7xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold flex items-center gap-2">
              <Zap className="w-6 h-6 text-yellow-400" />
              Data Connectors
            </h1>
            <p className="text-sm text-gray-400 mt-1">
              Connect to databases, files, cloud storage, and APIs
            </p>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-4 gap-4 mb-6">
          <StatCard label="Available Types" value={types.length} icon={Database} color="text-blue-400" />
          <StatCard label="Active Connectors" value={connectors.filter((c) => c.status === "active").length} icon={CheckCircle2} color="text-green-400" />
          <StatCard label="Africa-First" value={types.filter((t) => t.is_africa_first).length} icon={Wallet} color="text-orange-400" />
          <StatCard label="Total Configured" value={connectors.length} icon={Settings} color="text-purple-400" />
        </div>

        {/* Filters */}
        <div className="flex items-center gap-3 mb-6">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
            <input
              type="text"
              placeholder="Search connectors..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-white/5 border border-white/10 rounded-lg text-sm focus:outline-none focus:border-white/30"
            />
          </div>
          <select
            value={filterCategory}
            onChange={(e) => setFilterCategory(e.target.value)}
            className="px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-sm focus:outline-none focus:border-white/30"
          >
            {categories.map((c) => (
              <option key={c} value={c} className="bg-[#1a1a1a]">
                {c === "all" ? "All Categories" : c.charAt(0).toUpperCase() + c.slice(1)}
              </option>
            ))}
          </select>
          <button
            onClick={() => setShowAfricaOnly(!showAfricaOnly)}
            className={`px-3 py-2 rounded-lg text-sm border transition-colors ${
              showAfricaOnly
                ? "bg-orange-500/20 border-orange-500/40 text-orange-400"
                : "bg-white/5 border-white/10 text-gray-400"
            }`}
          >
            Africa-First
          </button>
        </div>

        {/* Connector Types Grid */}
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="w-8 h-8 animate-spin text-gray-500" />
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredTypes.map((type) => {
              const Icon = categoryIcons[type.category] || Code;
              return (
                <div
                  key={type.type_code}
                  className="bg-white/5 border border-white/10 rounded-xl p-5 hover:border-white/30 transition-all group cursor-pointer"
                >
                  <div className="flex items-start justify-between mb-3">
                    <div className={`w-10 h-10 rounded-lg flex items-center justify-center border ${categoryColors[type.category] || categoryColors.api}`}>
                      <Icon className="w-5 h-5" />
                    </div>
                    {type.is_africa_first && (
                      <span className="text-xs px-2 py-0.5 rounded-full bg-orange-500/20 text-orange-400 border border-orange-500/30">
                        Africa-First
                      </span>
                    )}
                  </div>
                  <h3 className="font-semibold text-sm mb-1 group-hover:text-white">
                    {type.display_name}
                  </h3>
                  <p className="text-xs text-gray-400 line-clamp-2">{type.description}</p>
                  <div className="flex items-center gap-2 mt-3">
                    <span className="text-xs text-gray-500 capitalize">{type.category}</span>
                    {type.region === "africa" && (
                      <span className="text-xs text-gray-500">• {type.region}</span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* Configured Connectors */}
        {connectors.length > 0 && (
          <div className="mt-8">
            <h2 className="text-lg font-semibold mb-4">Your Connectors</h2>
            <div className="space-y-2">
              {connectors.map((conn) => (
                <div
                  key={conn.id}
                  className="flex items-center justify-between bg-white/5 border border-white/10 rounded-lg px-4 py-3"
                >
                  <div className="flex items-center gap-3">
                    <div className={`w-8 h-8 rounded-lg flex items-center justify-center border ${categoryColors[conn.category] || categoryColors.api}`}>
                      {(() => {
                        const Icon = categoryIcons[conn.category] || Code;
                        return <Icon className="w-4 h-4" />;
                      })()}
                    </div>
                    <div>
                      <p className="text-sm font-medium">{conn.name}</p>
                      <p className="text-xs text-gray-500">{conn.connector_type}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className={`text-xs px-2 py-0.5 rounded-full ${
                      conn.status === "active"
                        ? "bg-green-500/20 text-green-400"
                        : conn.status === "error"
                        ? "bg-red-500/20 text-red-400"
                        : "bg-gray-500/20 text-gray-400"
                    }`}>
                      {conn.status}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function StatCard({ label, value, icon: Icon, color }: { label: string; value: number; icon: any; color: string }) {
  return (
    <div className="bg-white/5 border border-white/10 rounded-xl p-4">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs text-gray-400">{label}</span>
        <Icon className={`w-4 h-4 ${color}`} />
      </div>
      <p className="text-2xl font-bold">{value}</p>
    </div>
  );
}
