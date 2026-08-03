"use client";

import { useEffect, useState, useCallback } from "react";
import {
  ScrollText, Download, Filter, Loader2, Search, ChevronLeft,
  ChevronRight, Shield, Activity, User, Globe, Clock,
} from "lucide-react";
import { auditService, type AuditLogEntry, type AuditStats, type AuditFilters } from "@/services/audit/auditService";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { cn } from "@/lib/utils";
import { toast } from "@/components/ui/Toaster";

function formatDate(iso: string | null): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleString([], {
    month: "short", day: "numeric", year: "numeric",
    hour: "2-digit", minute: "2-digit", second: "2-digit",
  });
}

function getActionColor(action: string): string {
  if (action.includes("delete")) return "destructive";
  if (action.includes("create") || action.includes("upload")) return "success";
  if (action.includes("update") || action.includes("assign")) return "warning";
  if (action.includes("export")) return "info";
  return "secondary";
}

function getSeverityColor(severity: string): string {
  if (severity === "critical") return "destructive";
  if (severity === "warning") return "warning";
  return "secondary";
}

const PAGE_SIZE = 25;

export function AuditLogViewer() {
  const [logs, setLogs] = useState<AuditLogEntry[]>([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState<AuditStats | null>(null);
  const [filters, setFilters] = useState<AuditFilters | null>(null);
  const [activeTab, setActiveTab] = useState<"logs" | "stats" | "security">("logs");

  // Filter state
  const [actionFilter, setActionFilter] = useState("");
  const [resourceFilter, setResourceFilter] = useState("");
  const [search, setSearch] = useState("");

  const loadLogs = useCallback(async () => {
    setLoading(true);
    try {
      const data = await auditService.listLogs({
        action: actionFilter || undefined,
        resource_type: resourceFilter || undefined,
        limit: PAGE_SIZE,
        offset,
      });
      setLogs(data.logs);
      setTotal(data.total);
    } catch {
      toast.error("Failed to load audit logs");
    } finally {
      setLoading(false);
    }
  }, [actionFilter, resourceFilter, offset]);

  const loadStats = useCallback(async () => {
    try {
      const data = await auditService.getStats();
      setStats(data);
    } catch {
      // Silent
    }
  }, []);

  const loadFilters = useCallback(async () => {
    try {
      const data = await auditService.getFilters();
      setFilters(data);
    } catch {
      // Silent
    }
  }, []);

  useEffect(() => {
    loadFilters();
  }, [loadFilters]);

  useEffect(() => {
    if (activeTab === "logs") loadLogs();
    if (activeTab === "stats") loadStats();
  }, [activeTab, loadLogs, loadStats]);

  const handleExport = (format: "csv" | "json") => {
    const url = auditService.exportLogs(format, {
      action: actionFilter || undefined,
      resource_type: resourceFilter || undefined,
    });
    window.open(url, "_blank");
  };

  const filteredLogs = search
    ? logs.filter(
        (l) =>
          l.action.toLowerCase().includes(search.toLowerCase()) ||
          l.ip_address?.includes(search) ||
          l.resource_type?.toLowerCase().includes(search.toLowerCase())
      )
    : logs;

  const totalPages = Math.ceil(total / PAGE_SIZE);
  const currentPage = Math.floor(offset / PAGE_SIZE) + 1;

  return (
    <div className="space-y-4">
      {/* Tabs */}
      <div className="flex items-center gap-2 border-b pb-2">
        <Button
          variant={activeTab === "logs" ? "default" : "ghost"}
          size="sm"
          onClick={() => setActiveTab("logs")}
          className="gap-1.5"
        >
          <ScrollText className="h-4 w-4" />
          Audit Logs
        </Button>
        <Button
          variant={activeTab === "stats" ? "default" : "ghost"}
          size="sm"
          onClick={() => setActiveTab("stats")}
          className="gap-1.5"
        >
          <Activity className="h-4 w-4" />
          Statistics
        </Button>
        <Button
          variant={activeTab === "security" ? "default" : "ghost"}
          size="sm"
          onClick={() => setActiveTab("security")}
          className="gap-1.5"
        >
          <Shield className="h-4 w-4" />
          Security Events
        </Button>
      </div>

      {/* Logs Tab */}
      {activeTab === "logs" && (
        <>
          {/* Filters */}
          <div className="flex flex-wrap items-center gap-2">
            <div className="relative">
              <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <input
                type="text"
                placeholder="Search logs..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="rounded-md border bg-background pl-8 pr-3 py-1.5 text-sm w-48 focus:outline-none focus:ring-1 focus:ring-primary"
              />
            </div>
            {filters && (
              <>
                <select
                  value={actionFilter}
                  onChange={(e) => { setActionFilter(e.target.value); setOffset(0); }}
                  className="rounded-md border bg-background px-3 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-primary"
                >
                  <option value="">All actions</option>
                  {filters.actions.map((a) => (
                    <option key={a} value={a}>{a}</option>
                  ))}
                </select>
                <select
                  value={resourceFilter}
                  onChange={(e) => { setResourceFilter(e.target.value); setOffset(0); }}
                  className="rounded-md border bg-background px-3 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-primary"
                >
                  <option value="">All resources</option>
                  {filters.resource_types.map((r) => (
                    <option key={r} value={r}>{r}</option>
                  ))}
                </select>
              </>
            )}
            <div className="ml-auto flex items-center gap-1">
              <Button size="sm" variant="outline" onClick={() => handleExport("csv")} className="gap-1.5">
                <Download className="h-3.5 w-3.5" />
                CSV
              </Button>
              <Button size="sm" variant="outline" onClick={() => handleExport("json")} className="gap-1.5">
                <Download className="h-3.5 w-3.5" />
                JSON
              </Button>
            </div>
          </div>

          {/* Log entries */}
          <Card>
            <CardContent className="p-0">
              {loading ? (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                </div>
              ) : filteredLogs.length === 0 ? (
                <div className="py-12 text-center text-sm text-muted-foreground">
                  No audit logs found.
                </div>
              ) : (
                <div className="divide-y">
                  {filteredLogs.map((log) => (
                    <div key={log.id} className="p-4 hover:bg-muted/30 transition-colors">
                      <div className="flex items-start gap-3">
                        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-muted">
                          {log.action.includes("delete") ? (
                            <Shield className="h-3.5 w-3.5 text-destructive" />
                          ) : log.action.includes("security") ? (
                            <Shield className="h-3.5 w-3.5 text-warning" />
                          ) : (
                            <Activity className="h-3.5 w-3.5 text-muted-foreground" />
                          )}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 flex-wrap">
                            <Badge variant={getActionColor(log.action) as any} className="text-xs">
                              {log.action}
                            </Badge>
                            {log.resource_type && (
                              <span className="text-xs text-muted-foreground">
                                {log.resource_type}
                                {log.resource_id && ` #${log.resource_id}`}
                              </span>
                            )}
                          </div>
                          <div className="flex items-center gap-3 mt-1.5 text-xs text-muted-foreground flex-wrap">
                            {log.user_id && (
                              <span className="flex items-center gap-0.5">
                                <User className="h-3 w-3" />
                                User #{log.user_id}
                              </span>
                            )}
                            {log.ip_address && (
                              <span className="flex items-center gap-0.5">
                                <Globe className="h-3 w-3" />
                                {log.ip_address}
                              </span>
                            )}
                            <span className="flex items-center gap-0.5">
                              <Clock className="h-3 w-3" />
                              {formatDate(log.created_at)}
                            </span>
                          </div>
                          {log.metadata && Object.keys(log.metadata).length > 0 && (
                            <div className="mt-2 text-xs bg-muted/50 rounded px-2 py-1 font-mono text-muted-foreground">
                              {JSON.stringify(log.metadata)}
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Pagination */}
          {total > PAGE_SIZE && (
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">
                {total} total · Page {currentPage} of {totalPages}
              </span>
              <div className="flex items-center gap-1">
                <Button
                  size="sm"
                  variant="outline"
                  disabled={offset === 0}
                  onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}
                >
                  <ChevronLeft className="h-4 w-4" />
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  disabled={offset + PAGE_SIZE >= total}
                  onClick={() => setOffset(offset + PAGE_SIZE)}
                >
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>
            </div>
          )}
        </>
      )}

      {/* Stats Tab */}
      {activeTab === "stats" && (
        <div className="space-y-4">
          {stats ? (
            <>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Card>
                  <CardContent className="pt-6">
                    <div className="text-2xl font-bold">{stats.total}</div>
                    <p className="text-xs text-muted-foreground mt-1">Total Events</p>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="pt-6">
                    <div className="text-2xl font-bold">{Object.keys(stats.action_counts).length}</div>
                    <p className="text-xs text-muted-foreground mt-1">Unique Actions</p>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="pt-6">
                    <div className="text-2xl font-bold">{stats.top_users.length}</div>
                    <p className="text-xs text-muted-foreground mt-1">Active Users</p>
                  </CardContent>
                </Card>
              </div>

              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Actions by Type</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  {Object.entries(stats.action_counts)
                    .sort(([, a], [, b]) => b - a)
                    .slice(0, 15)
                    .map(([action, count]) => (
                      <div key={action} className="flex items-center justify-between">
                        <Badge variant={getActionColor(action) as any} className="text-xs">
                          {action}
                        </Badge>
                        <span className="text-sm font-medium">{count}</span>
                      </div>
                    ))}
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Top Users</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  {stats.top_users.map((u) => (
                    <div key={u.user_id} className="flex items-center justify-between">
                      <span className="flex items-center gap-2 text-sm">
                        <User className="h-3.5 w-3.5 text-muted-foreground" />
                        User #{u.user_id}
                      </span>
                      <span className="text-sm font-medium">{u.count} events</span>
                    </div>
                  ))}
                </CardContent>
              </Card>
            </>
          ) : (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          )}
        </div>
      )}

      {/* Security Tab */}
      {activeTab === "security" && <SecurityLogsTab />}
    </div>
  );
}

// ── Security Logs Sub-component ───────────────────────────────────

function SecurityLogsTab() {
  const [logs, setLogs] = useState<AuditLogEntry[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [severityFilter, setSeverityFilter] = useState("");

  useEffect(() => {
    (async () => {
      setLoading(true);
      try {
        const data = await auditService.listSecurityLogs({
          severity: severityFilter || undefined,
          limit: 50,
        });
        setLogs(data.logs as any);
        setTotal(data.total);
      } catch {
        // Silent
      } finally {
        setLoading(false);
      }
    })();
  }, [severityFilter]);

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <select
          value={severityFilter}
          onChange={(e) => setSeverityFilter(e.target.value)}
          className="rounded-md border bg-background px-3 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-primary"
        >
          <option value="">All severities</option>
          <option value="info">Info</option>
          <option value="warning">Warning</option>
          <option value="critical">Critical</option>
        </select>
        <Badge variant="secondary">{total} events</Badge>
      </div>

      <Card>
        <CardContent className="p-0">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          ) : logs.length === 0 ? (
            <div className="py-12 text-center text-sm text-muted-foreground">
              No security events found.
            </div>
          ) : (
            <div className="divide-y">
              {logs.map((log: any) => (
                <div key={log.id} className="p-4 hover:bg-muted/30 transition-colors">
                  <div className="flex items-start gap-3">
                    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-muted">
                      <Shield className={cn(
                        "h-3.5 w-3.5",
                        log.severity === "critical" && "text-destructive",
                        log.severity === "warning" && "text-warning",
                      )} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <Badge variant={getSeverityColor(log.severity) as any} className="text-xs">
                          {log.severity}
                        </Badge>
                        <span className="font-medium text-sm">{log.event_type}</span>
                      </div>
                      <div className="flex items-center gap-3 mt-1.5 text-xs text-muted-foreground flex-wrap">
                        {log.user_id && (
                          <span className="flex items-center gap-0.5">
                            <User className="h-3 w-3" />
                            User #{log.user_id}
                          </span>
                        )}
                        {log.ip_address && (
                          <span className="flex items-center gap-0.5">
                            <Globe className="h-3 w-3" />
                            {log.ip_address}
                          </span>
                        )}
                        <span className="flex items-center gap-0.5">
                          <Clock className="h-3 w-3" />
                          {formatDate(log.created_at)}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
