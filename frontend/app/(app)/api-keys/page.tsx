"use client";

import { useState, useEffect } from "react";
import {
  Key, Plus, Copy, Trash2, RefreshCw, AlertCircle, Loader2,
  CheckCircle2, Clock, Activity,
} from "lucide-react";
import { apiKeyService, type APIKey } from "@/services/ecosystem/ecosystemService";

const allScopes = ["datasets", "analytics", "ai", "workflows"];

export default function APIKeysPage() {
  const [keys, setKeys] = useState<APIKey[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [newKeyName, setNewKeyName] = useState("");
  const [newKeyScopes, setNewKeyScopes] = useState<string[]>(allScopes);
  const [newKeyLimit, setNewKeyLimit] = useState(1000);
  const [createdKey, setCreatedKey] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);
  const [usageData, setUsageData] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadKeys();
    loadUsage();
  }, []);

  const loadKeys = async () => {
    setLoading(true);
    setError(null);
    try {
      const resp = await apiKeyService.list();
      setKeys(resp || []);
    } catch (e) {
      console.error("Failed to load API keys:", e);
      setError("Failed to load API keys. Please try again later.");
    } finally {
      setLoading(false);
    }
  };

  const loadUsage = async () => {
    try {
      const resp = await apiKeyService.usage(7);
      setUsageData(resp);
    } catch (e) {
      console.error("Failed to load usage:", e);
    }
  };

  const handleCreate = async () => {
    if (!newKeyName.trim()) return;
    setCreating(true);
    try {
      const resp = await apiKeyService.create({
        name: newKeyName,
        scopes: newKeyScopes,
        rate_limit_per_hour: newKeyLimit,
      });
      setCreatedKey(resp.api_key);
      setNewKeyName("");
      setShowCreate(false);
      loadKeys();
      loadUsage();
    } catch (e) {
      console.error("Failed to create key:", e);
    } finally {
      setCreating(false);
    }
  };

  const handleRevoke = async (id: number) => {
    try {
      await apiKeyService.revoke(id);
      loadKeys();
    } catch (e) {
      console.error("Failed to revoke:", e);
    }
  };

  const handleRotate = async (id: number) => {
    try {
      const resp = await apiKeyService.rotate(id);
      setCreatedKey(resp.api_key);
      loadKeys();
    } catch (e) {
      console.error("Failed to rotate:", e);
    }
  };

  const toggleScope = (scope: string) => {
    setNewKeyScopes((prev) =>
      prev.includes(scope) ? prev.filter((s) => s !== scope) : [...prev, scope]
    );
  };

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white p-6">
      <div className="max-w-5xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold flex items-center gap-2">
              <Key className="w-6 h-6 text-green-400" />
              API Keys
            </h1>
            <p className="text-sm text-gray-400 mt-1">
              Manage API keys for external developer access
            </p>
          </div>
          <button
            onClick={() => setShowCreate(!showCreate)}
            className="flex items-center gap-2 px-4 py-2 bg-white/10 hover:bg-white/20 rounded-lg text-sm font-medium transition-colors"
          >
            <Plus className="w-4 h-4" />
            New Key
          </button>
        </div>

        {/* Usage Stats */}
        {usageData && (
          <div className="grid grid-cols-3 gap-4 mb-6">
            <div className="bg-white/5 border border-white/10 rounded-xl p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs text-gray-400">Calls (7d)</span>
                <Activity className="w-4 h-4 text-blue-400" />
              </div>
              <p className="text-2xl font-bold">{usageData.total_calls}</p>
            </div>
            <div className="bg-white/5 border border-white/10 rounded-xl p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs text-gray-400">Errors (7d)</span>
                <AlertCircle className="w-4 h-4 text-red-400" />
              </div>
              <p className="text-2xl font-bold">{usageData.error_count}</p>
            </div>
            <div className="bg-white/5 border border-white/10 rounded-xl p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs text-gray-400">Error Rate</span>
                <Activity className="w-4 h-4 text-yellow-400" />
              </div>
              <p className="text-2xl font-bold">{usageData.error_rate}%</p>
            </div>
          </div>
        )}

        {/* Created Key Banner */}
        {createdKey && (
          <div className="bg-green-500/10 border border-green-500/30 rounded-xl p-4 mb-6">
            <div className="flex items-center gap-2 mb-2">
              <CheckCircle2 className="w-5 h-5 text-green-400" />
              <span className="font-semibold text-sm">API Key Created — save it now!</span>
            </div>
            <div className="flex items-center gap-2">
              <code className="flex-1 px-3 py-2 bg-black/30 rounded-lg text-sm font-mono text-green-300 overflow-x-auto">
                {createdKey}
              </code>
              <button
                onClick={() => {
                  navigator.clipboard.writeText(createdKey);
                }}
                className="p-2 bg-white/10 hover:bg-white/20 rounded-lg"
              >
                <Copy className="w-4 h-4" />
              </button>
              <button
                onClick={() => setCreatedKey(null)}
                className="px-3 py-2 bg-white/10 hover:bg-white/20 rounded-lg text-xs"
              >
                Dismiss
              </button>
            </div>
          </div>
        )}

        {/* Create Form */}
        {showCreate && (
          <div className="bg-white/5 border border-white/10 rounded-xl p-5 mb-6">
            <h3 className="font-semibold text-sm mb-4">Create New API Key</h3>
            <div className="space-y-4">
              <div>
                <label className="text-xs text-gray-400 mb-1 block">Name</label>
                <input
                  type="text"
                  value={newKeyName}
                  onChange={(e) => setNewKeyName(e.target.value)}
                  placeholder="e.g. Production API Key"
                  className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-sm focus:outline-none focus:border-white/30"
                />
              </div>
              <div>
                <label className="text-xs text-gray-400 mb-2 block">Scopes</label>
                <div className="flex flex-wrap gap-2">
                  {allScopes.map((scope) => (
                    <button
                      key={scope}
                      onClick={() => toggleScope(scope)}
                      className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                        newKeyScopes.includes(scope)
                          ? "bg-green-500/20 text-green-400 border border-green-500/30"
                          : "bg-white/5 text-gray-400 border border-white/10"
                      }`}
                    >
                      {scope}
                    </button>
                  ))}
                </div>
              </div>
              <div>
                <label className="text-xs text-gray-400 mb-1 block">Rate Limit (requests/hour)</label>
                <input
                  type="number"
                  value={newKeyLimit}
                  onChange={(e) => setNewKeyLimit(parseInt(e.target.value) || 1000)}
                  className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-sm focus:outline-none focus:border-white/30"
                />
              </div>
              <div className="flex gap-2">
                <button
                  onClick={handleCreate}
                  disabled={!newKeyName.trim() || creating}
                  className="px-4 py-2 bg-green-500/20 text-green-400 border border-green-500/30 rounded-lg text-sm font-medium hover:bg-green-500/30 transition-colors disabled:opacity-50"
                >
                  {creating ? <Loader2 className="w-4 h-4 animate-spin" /> : "Create Key"}
                </button>
                <button
                  onClick={() => setShowCreate(false)}
                  className="px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-sm"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Keys List */}
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="w-8 h-8 animate-spin text-gray-500" />
          </div>
        ) : error ? (
          <div className="flex flex-col items-center justify-center py-20 text-center">
            <AlertCircle className="w-12 h-12 text-red-400 mb-4" />
            <p className="text-sm text-gray-400 mb-4">{error}</p>
            <button
              onClick={loadKeys}
              className="px-4 py-2 bg-white/10 hover:bg-white/20 rounded-lg text-sm transition-colors"
            >
              Retry
            </button>
          </div>
        ) : keys.length === 0 ? (
          <div className="text-center py-20 text-gray-500">
            <Key className="w-12 h-12 mx-auto mb-3 opacity-30" />
            <p className="text-sm">No API keys yet. Create one to get started.</p>
          </div>
        ) : (
          <div className="space-y-2">
            {keys.map((key) => (
              <div
                key={key.id}
                className="flex items-center justify-between bg-white/5 border border-white/10 rounded-lg px-4 py-3"
              >
                <div className="flex items-center gap-3">
                  <Key className="w-4 h-4 text-gray-400" />
                  <div>
                    <p className="text-sm font-medium">{key.name}</p>
                    <div className="flex items-center gap-2 text-xs text-gray-500">
                      <code className="font-mono">{key.key_prefix}...</code>
                      {key.scopes?.map((s) => (
                        <span key={s} className="px-1.5 py-0.5 rounded bg-white/5">{s}</span>
                      ))}
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {key.last_used_at && (
                    <span className="text-xs text-gray-500 flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      Used recently
                    </span>
                  )}
                  <button
                    onClick={() => handleRotate(key.id)}
                    className="p-2 hover:bg-white/10 rounded-lg transition-colors"
                    title="Rotate"
                  >
                    <RefreshCw className="w-4 h-4 text-gray-400" />
                  </button>
                  <button
                    onClick={() => handleRevoke(key.id)}
                    className="p-2 hover:bg-red-500/10 rounded-lg transition-colors"
                    title="Revoke"
                  >
                    <Trash2 className="w-4 h-4 text-red-400" />
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
