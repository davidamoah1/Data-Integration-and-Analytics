"use client";

import { useState, useEffect } from "react";
import {
  Webhook, Plus, Trash2, Loader2, CheckCircle2, XCircle,
  Clock, RefreshCw, Link as LinkIcon,
} from "lucide-react";
import { webhookService, type WebhookSubscription } from "@/services/ecosystem/ecosystemService";

export default function WebhooksPage() {
  const [webhooks, setWebhooks] = useState<WebhookSubscription[]>([]);
  const [events, setEvents] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [url, setUrl] = useState("");
  const [selectedEvents, setSelectedEvents] = useState<string[]>([]);
  const [creating, setCreating] = useState(false);
  const [createdSecret, setCreatedSecret] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [whResp, evResp] = await Promise.all([
        webhookService.list(),
        webhookService.listEvents(),
      ]);
      setWebhooks(whResp || []);
      setEvents(evResp || []);
    } catch (e) {
      console.error("Failed to load webhooks:", e);
      setError("Failed to load webhooks. Please try again later.");
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async () => {
    if (!url.trim() || selectedEvents.length === 0) return;
    setCreating(true);
    try {
      const resp = await webhookService.create({ url, events: selectedEvents });
      setCreatedSecret(resp.secret);
      setUrl("");
      setSelectedEvents([]);
      setShowCreate(false);
      loadData();
    } catch (e) {
      console.error("Failed to create webhook:", e);
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await webhookService.delete(id);
      loadData();
    } catch (e) {
      console.error("Failed to delete:", e);
    }
  };

  const toggleEvent = (event: string) => {
    setSelectedEvents((prev) =>
      prev.includes(event) ? prev.filter((e) => e !== event) : [...prev, event]
    );
  };

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white p-6">
      <div className="max-w-5xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold flex items-center gap-2">
              <Webhook className="w-6 h-6 text-blue-400" />
              Webhooks
            </h1>
            <p className="text-sm text-gray-400 mt-1">
              Subscribe to platform events and receive real-time notifications
            </p>
          </div>
          <button
            onClick={() => setShowCreate(!showCreate)}
            className="flex items-center gap-2 px-4 py-2 bg-white/10 hover:bg-white/20 rounded-lg text-sm font-medium transition-colors"
          >
            <Plus className="w-4 h-4" />
            New Webhook
          </button>
        </div>

        {/* Created Secret Banner */}
        {createdSecret && (
          <div className="bg-blue-500/10 border border-blue-500/30 rounded-xl p-4 mb-6">
            <div className="flex items-center gap-2 mb-2">
              <CheckCircle2 className="w-5 h-5 text-blue-400" />
              <span className="font-semibold text-sm">Webhook Secret — save it for signature verification</span>
            </div>
            <code className="block px-3 py-2 bg-black/30 rounded-lg text-sm font-mono text-blue-300 overflow-x-auto">
              {createdSecret}
            </code>
            <button
              onClick={() => setCreatedSecret(null)}
              className="mt-2 text-xs text-gray-400 hover:text-white"
            >
              Dismiss
            </button>
          </div>
        )}

        {/* Create Form */}
        {showCreate && (
          <div className="bg-white/5 border border-white/10 rounded-xl p-5 mb-6">
            <h3 className="font-semibold text-sm mb-4">Create Webhook Subscription</h3>
            <div className="space-y-4">
              <div>
                <label className="text-xs text-gray-400 mb-1 block">Endpoint URL</label>
                <input
                  type="url"
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  placeholder="https://your-app.com/webhook"
                  className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-sm focus:outline-none focus:border-white/30"
                />
              </div>
              <div>
                <label className="text-xs text-gray-400 mb-2 block">Events to Subscribe</label>
                <div className="grid grid-cols-2 gap-2">
                  {events.map((event) => (
                    <button
                      key={event}
                      onClick={() => toggleEvent(event)}
                      className={`px-3 py-2 rounded-lg text-xs font-mono text-left transition-colors ${
                        selectedEvents.includes(event)
                          ? "bg-blue-500/20 text-blue-400 border border-blue-500/30"
                          : "bg-white/5 text-gray-400 border border-white/10"
                      }`}
                    >
                      {event}
                    </button>
                  ))}
                </div>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={handleCreate}
                  disabled={!url.trim() || selectedEvents.length === 0 || creating}
                  className="px-4 py-2 bg-blue-500/20 text-blue-400 border border-blue-500/30 rounded-lg text-sm font-medium hover:bg-blue-500/30 transition-colors disabled:opacity-50"
                >
                  {creating ? <Loader2 className="w-4 h-4 animate-spin" /> : "Create Webhook"}
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

        {/* Webhooks List */}
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="w-8 h-8 animate-spin text-gray-500" />
          </div>
        ) : error ? (
          <div className="flex flex-col items-center justify-center py-20 text-center">
            <XCircle className="w-12 h-12 text-red-400 mb-4" />
            <p className="text-sm text-gray-400 mb-4">{error}</p>
            <button
              onClick={loadData}
              className="px-4 py-2 bg-white/10 hover:bg-white/20 rounded-lg text-sm transition-colors"
            >
              Retry
            </button>
          </div>
        ) : webhooks.length === 0 ? (
          <div className="text-center py-20 text-gray-500">
            <Webhook className="w-12 h-12 mx-auto mb-3 opacity-30" />
            <p className="text-sm">No webhooks configured. Create one to receive event notifications.</p>
          </div>
        ) : (
          <div className="space-y-2">
            {webhooks.map((wh) => (
              <div
                key={wh.id}
                className="bg-white/5 border border-white/10 rounded-lg px-4 py-3"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <LinkIcon className="w-4 h-4 text-gray-400" />
                    <div>
                      <p className="text-sm font-medium truncate max-w-md">{wh.url}</p>
                      <div className="flex flex-wrap gap-1 mt-1">
                        {wh.events.map((e) => (
                          <span key={e} className="text-xs px-1.5 py-0.5 rounded bg-white/5 text-gray-400 font-mono">
                            {e}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={`text-xs px-2 py-0.5 rounded-full ${
                      wh.is_active
                        ? "bg-green-500/20 text-green-400"
                        : "bg-gray-500/20 text-gray-400"
                    }`}>
                      {wh.is_active ? "Active" : "Inactive"}
                    </span>
                    <button
                      onClick={() => handleDelete(wh.id)}
                      className="p-2 hover:bg-red-500/10 rounded-lg transition-colors"
                    >
                      <Trash2 className="w-4 h-4 text-red-400" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
