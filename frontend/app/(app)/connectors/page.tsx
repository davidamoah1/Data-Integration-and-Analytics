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

const categoryColors: Record<string, { bg: string; text: string; border: string }> = {
  database: {
    bg: "bg-blue-50 dark:bg-blue-950/50",
    text: "text-blue-600 dark:text-blue-400",
    border: "border-blue-200 dark:border-blue-800",
  },
  file: {
    bg: "bg-emerald-50 dark:bg-emerald-950/50",
    text: "text-emerald-600 dark:text-emerald-400",
    border: "border-emerald-200 dark:border-emerald-800",
  },
  cloud_storage: {
    bg: "bg-purple-50 dark:bg-purple-950/50",
    text: "text-purple-600 dark:text-purple-400",
    border: "border-purple-200 dark:border-purple-800",
  },
  api: {
    bg: "bg-amber-50 dark:bg-amber-950/50",
    text: "text-amber-600 dark:text-amber-400",
    border: "border-amber-200 dark:border-amber-800",
  },
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
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white flex items-center gap-2">
            <Zap className="w-6 h-6 text-amber-500 fill-amber-500/20" />
            Data Connectors
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            Connect to databases, files, cloud storage, and APIs
          </p>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard
          label="Available Types"
          value={types.length}
          icon={Database}
          color="text-blue-600 dark:text-blue-400"
          bg="bg-blue-50 dark:bg-blue-950/50"
        />
        <StatCard
          label="Active Connectors"
          value={connectors.filter((c) => c.status === "active").length}
          icon={CheckCircle2}
          color="text-emerald-600 dark:text-emerald-400"
          bg="bg-emerald-50 dark:bg-emerald-950/50"
        />
        <StatCard
          label="Africa-First"
          value={types.filter((t) => t.is_africa_first).length}
          icon={Wallet}
          color="text-amber-600 dark:text-amber-400"
          bg="bg-amber-50 dark:bg-amber-950/50"
        />
        <StatCard
          label="Total Configured"
          value={connectors.length}
          icon={Settings}
          color="text-indigo-600 dark:text-indigo-400"
          bg="bg-indigo-50 dark:bg-indigo-950/50"
        />
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input
            type="text"
            placeholder="Search connectors..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-4 py-2 bg-white border border-slate-200 rounded-lg text-sm text-slate-900 placeholder:text-slate-400 shadow-sm focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 dark:bg-slate-900 dark:border-slate-800 dark:text-white"
          />
        </div>
        <select
          value={filterCategory}
          onChange={(e) => setFilterCategory(e.target.value)}
          className="px-3 py-2 bg-white border border-slate-200 rounded-lg text-sm text-slate-700 shadow-sm focus:outline-none focus:border-blue-500 dark:bg-slate-900 dark:border-slate-800 dark:text-slate-200"
        >
          {categories.map((c) => (
            <option key={c} value={c} className="bg-white text-slate-900 dark:bg-slate-900 dark:text-white">
              {c === "all" ? "All Categories" : c.charAt(0).toUpperCase() + c.slice(1).replace('_', ' ')}
            </option>
          ))}
        </select>
        <button
          onClick={() => setShowAfricaOnly(!showAfricaOnly)}
          className={`px-3.5 py-2 rounded-lg text-sm font-medium border shadow-sm transition-all ${
            showAfricaOnly
              ? "bg-amber-50 border-amber-300 text-amber-800 dark:bg-amber-950/40 dark:border-amber-800 dark:text-amber-300"
              : "bg-white border-slate-200 text-slate-700 hover:bg-slate-50 dark:bg-slate-900 dark:border-slate-800 dark:text-slate-300"
          }`}
        >
          Africa-First
        </button>
      </div>

      {/* Connector Types Grid */}
      {loading ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="w-8 h-8 animate-spin text-slate-400" />
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredTypes.map((type) => {
            const Icon = categoryIcons[type.category] || Code;
            const catTheme = categoryColors[type.category] || categoryColors.api;

            return (
              <div
                key={type.type_code}
                className="group relative flex flex-col justify-between overflow-hidden rounded-xl border border-slate-200/80 bg-white p-5 shadow-sm transition-all hover:border-blue-400 hover:shadow-md dark:border-slate-800 dark:bg-slate-900 dark:hover:border-blue-500 cursor-pointer"
              >
                <div>
                  <div className="flex items-start justify-between mb-3">
                    <div className={`w-10 h-10 rounded-lg flex items-center justify-center border ${catTheme.bg} ${catTheme.text} ${catTheme.border}`}>
                      <Icon className="w-5 h-5" />
                    </div>
                    {type.is_africa_first && (
                      <span className="text-[11px] font-semibold px-2.5 py-0.5 rounded-full bg-amber-50 text-amber-700 border border-amber-200 dark:bg-amber-950/50 dark:text-amber-300 dark:border-amber-800">
                        Africa-First
                      </span>
                    )}
                  </div>
                  <h3 className="font-bold text-sm text-slate-900 dark:text-white group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
                    {type.display_name}
                  </h3>
                  <p className="text-xs text-slate-500 dark:text-slate-400 line-clamp-2 mt-1">
                    {type.description}
                  </p>
                </div>
                <div className="flex items-center gap-2 mt-4 pt-3 border-t border-slate-100 dark:border-slate-800 text-xs text-slate-400">
                  <span className="capitalize font-medium text-slate-600 dark:text-slate-400">
                    {type.category.replace('_', ' ')}
                  </span>
                  {type.region === "africa" && (
                    <span>• {type.region}</span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Configured Connectors */}
      {connectors.length > 0 && (
        <div className="mt-8 space-y-3">
          <h2 className="text-lg font-bold text-slate-900 dark:text-white">Your Configured Connectors</h2>
          <div className="space-y-2">
            {connectors.map((conn) => {
              const Icon = categoryIcons[conn.category] || Code;
              const catTheme = categoryColors[conn.category] || categoryColors.api;

              return (
                <div
                  key={conn.id}
                  className="flex items-center justify-between border border-slate-200/80 bg-white rounded-xl px-4 py-3 shadow-sm dark:border-slate-800 dark:bg-slate-900"
                >
                  <div className="flex items-center gap-3">
                    <div className={`w-9 h-9 rounded-lg flex items-center justify-center border ${catTheme.bg} ${catTheme.text} ${catTheme.border}`}>
                      <Icon className="w-4 h-4" />
                    </div>
                    <div>
                      <p className="text-sm font-semibold text-slate-900 dark:text-white">{conn.name}</p>
                      <p className="text-xs text-slate-500 dark:text-slate-400">{conn.connector_type}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className={`text-xs font-medium px-2.5 py-0.5 rounded-full border ${
                      conn.status === "active"
                        ? "bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-300 dark:border-emerald-800"
                        : conn.status === "error"
                        ? "bg-rose-50 text-rose-700 border-rose-200 dark:bg-rose-950/40 dark:text-rose-300 dark:border-rose-800"
                        : "bg-slate-100 text-slate-600 border-slate-200 dark:bg-slate-800 dark:text-slate-400 dark:border-slate-700"
                    }`}>
                      {conn.status}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

function StatCard({
  label,
  value,
  icon: Icon,
  color,
  bg,
}: {
  label: string;
  value: number;
  icon: any;
  color: string;
  bg: string;
}) {
  return (
    <div className="relative overflow-hidden rounded-xl border border-slate-200/80 bg-white p-5 shadow-sm transition-all hover:shadow-md dark:border-slate-800 dark:bg-slate-900">
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
          {label}
        </span>
        <div className={`rounded-lg p-2 ${bg}`}>
          <Icon className={`w-4 h-4 ${color}`} />
        </div>
      </div>
      <p className="mt-3 text-3xl font-extrabold text-slate-900 dark:text-white">
        {value}
      </p>
    </div>
  );
}
