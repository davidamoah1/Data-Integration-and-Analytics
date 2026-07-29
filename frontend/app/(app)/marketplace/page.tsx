"use client";

import { useState, useEffect } from "react";
import {
  Package, Search, Star, Download, CheckCircle2, Loader2,
  Puzzle, Layout, Brain, Database, Sparkles, Power, Trash2,
  AlertCircle,
} from "lucide-react";
import {
  marketplaceService,
  type MarketplacePlugin,
  type IndustryPackage,
} from "@/services/ecosystem/ecosystemService";

const categoryIcons: Record<string, any> = {
  connector: Database,
  dashboard_template: Layout,
  ai_agent: Brain,
  industry_solution: Package,
  data_processor: Puzzle,
};

const categoryColors: Record<string, string> = {
  connector: "bg-blue-500/10 text-blue-400 border-blue-500/20",
  dashboard_template: "bg-purple-500/10 text-purple-400 border-purple-500/20",
  ai_agent: "bg-green-500/10 text-green-400 border-green-500/20",
  industry_solution: "bg-orange-500/10 text-orange-400 border-orange-500/20",
  data_processor: "bg-pink-500/10 text-pink-400 border-pink-500/20",
};

const industryColors: Record<string, string> = {
  healthcare: "bg-red-500/10 text-red-400 border-red-500/20",
  education: "bg-blue-500/10 text-blue-400 border-blue-500/20",
  banking: "bg-green-500/10 text-green-400 border-green-500/20",
  agriculture: "bg-yellow-500/10 text-yellow-400 border-yellow-500/20",
  retail: "bg-purple-500/10 text-purple-400 border-purple-500/20",
  government: "bg-indigo-500/10 text-indigo-400 border-indigo-500/20",
};

export default function MarketplacePage() {
  const [plugins, setPlugins] = useState<MarketplacePlugin[]>([]);
  const [packages, setPackages] = useState<IndustryPackage[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [filterCategory, setFilterCategory] = useState("all");
  const [tab, setTab] = useState<"plugins" | "packages">("plugins");
  const [installing, setInstalling] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [pluginsResp, packagesResp] = await Promise.all([
        marketplaceService.listPlugins(),
        marketplaceService.listPackages(),
      ]);
      setPlugins(pluginsResp || []);
      setPackages(packagesResp || []);
    } catch (e) {
      console.error("Failed to load marketplace:", e);
      setError("Failed to load marketplace. Please try again later.");
    } finally {
      setLoading(false);
    }
  };

  const handleInstall = async (pluginId: string) => {
    setInstalling(pluginId);
    try {
      await marketplaceService.installPlugin(pluginId);
    } catch (e) {
      console.error("Install failed:", e);
    } finally {
      setInstalling(null);
    }
  };

  const handleInstallPackage = async (packageId: string) => {
    setInstalling(packageId);
    try {
      await marketplaceService.installPackage(packageId);
    } catch (e) {
      console.error("Package install failed:", e);
    } finally {
      setInstalling(null);
    }
  };

  const filteredPlugins = plugins.filter((p) => {
    if (filterCategory !== "all" && p.category !== filterCategory) return false;
    if (search && !p.name.toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  });

  const categories = ["all", ...Array.from(new Set(plugins.map((p) => p.category)))];

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white p-6">
      <div className="max-w-7xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold flex items-center gap-2">
              <Package className="w-6 h-6 text-purple-400" />
              Marketplace
            </h1>
            <p className="text-sm text-gray-400 mt-1">
              Discover and install plugins, connectors, and industry solutions
            </p>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex items-center gap-2 mb-6">
          <button
            onClick={() => setTab("plugins")}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              tab === "plugins" ? "bg-white/10 text-white" : "text-gray-400 hover:text-white"
            }`}
          >
            Plugins ({plugins.length})
          </button>
          <button
            onClick={() => setTab("packages")}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              tab === "packages" ? "bg-white/10 text-white" : "text-gray-400 hover:text-white"
            }`}
          >
            Industry Packages ({packages.length})
          </button>
        </div>

        {/* Filters */}
        {tab === "plugins" && (
          <div className="flex items-center gap-3 mb-6">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
              <input
                type="text"
                placeholder="Search plugins..."
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
                  {c === "all" ? "All Categories" : c.replace(/_/g, " ")}
                </option>
              ))}
            </select>
          </div>
        )}

        {loading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="w-8 h-8 animate-spin text-gray-500" />
          </div>
        ) : error ? (
          <div className="flex flex-col items-center justify-center py-20 text-center">
            <AlertCircle className="w-12 h-12 text-red-400 mb-4" />
            <p className="text-sm text-gray-400 mb-4">{error}</p>
            <button
              onClick={loadData}
              className="px-4 py-2 bg-white/10 hover:bg-white/20 rounded-lg text-sm transition-colors"
            >
              Retry
            </button>
          </div>
        ) : tab === "plugins" ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredPlugins.map((plugin) => {
              const Icon = categoryIcons[plugin.category] || Puzzle;
              return (
                <div
                  key={plugin.plugin_id}
                  className="bg-white/5 border border-white/10 rounded-xl p-5 hover:border-white/30 transition-all"
                >
                  <div className="flex items-start justify-between mb-3">
                    <div className={`w-10 h-10 rounded-lg flex items-center justify-center border ${categoryColors[plugin.category] || categoryColors.data_processor}`}>
                      <Icon className="w-5 h-5" />
                    </div>
                    <div className="flex items-center gap-1">
                      {plugin.is_featured && (
                        <Sparkles className="w-4 h-4 text-yellow-400" />
                      )}
                      {plugin.is_verified && (
                        <CheckCircle2 className="w-4 h-4 text-blue-400" />
                      )}
                    </div>
                  </div>
                  <h3 className="font-semibold text-sm mb-1">{plugin.name}</h3>
                  <p className="text-xs text-gray-400 line-clamp-2 mb-3">{plugin.description}</p>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2 text-xs text-gray-500">
                      <span>v{plugin.version}</span>
                      <span>•</span>
                      <Download className="w-3 h-3" />
                      <span>{plugin.install_count}</span>
                    </div>
                    <button
                      onClick={() => handleInstall(plugin.plugin_id)}
                      disabled={installing === plugin.plugin_id}
                      className="text-xs px-3 py-1.5 rounded-lg bg-white/10 hover:bg-white/20 transition-colors disabled:opacity-50"
                    >
                      {installing === plugin.plugin_id ? (
                        <Loader2 className="w-3 h-3 animate-spin" />
                      ) : (
                        "Install"
                      )}
                    </button>
                  </div>
                  {plugin.tags && plugin.tags.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-3">
                      {plugin.tags.slice(0, 3).map((tag) => (
                        <span key={tag} className="text-xs px-2 py-0.5 rounded-full bg-white/5 text-gray-500">
                          {tag}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {packages.map((pkg) => (
              <div
                key={pkg.package_id}
                className="bg-white/5 border border-white/10 rounded-xl p-5 hover:border-white/30 transition-all"
              >
                <div className="flex items-start justify-between mb-3">
                  <div className={`w-10 h-10 rounded-lg flex items-center justify-center border ${industryColors[pkg.industry] || "bg-white/5 text-gray-400 border-white/10"}`}>
                    <Package className="w-5 h-5" />
                  </div>
                  {pkg.is_africa_optimized && (
                    <span className="text-xs px-2 py-0.5 rounded-full bg-orange-500/20 text-orange-400 border border-orange-500/30">
                      Africa-Optimized
                    </span>
                  )}
                </div>
                <h3 className="font-semibold text-sm mb-1">{pkg.name}</h3>
                <p className="text-xs text-gray-400 line-clamp-2 mb-3">{pkg.description}</p>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-gray-500 capitalize">{pkg.industry}</span>
                  <button
                    onClick={() => handleInstallPackage(pkg.package_id)}
                    disabled={installing === pkg.package_id}
                    className="text-xs px-3 py-1.5 rounded-lg bg-white/10 hover:bg-white/20 transition-colors disabled:opacity-50"
                  >
                    {installing === pkg.package_id ? (
                      <Loader2 className="w-3 h-3 animate-spin" />
                    ) : (
                      "Install Package"
                    )}
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
