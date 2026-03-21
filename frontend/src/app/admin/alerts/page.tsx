"use client";

import { useState, useEffect } from "react";
import apiClient from "@/lib/api-client";

interface Alert {
  id: string;
  patient_id: string;
  patient_name: string;
  alert_type: string;
  severity: string;
  title: string;
  description: string;
  status: string;
  created_at: string;
  acknowledged_at: string | null;
  resolved_at: string | null;
}

const SEVERITY_STYLES: Record<string, string> = {
  emergency: "bg-red-100 text-red-800 border-red-200",
  critical: "bg-orange-100 text-orange-800 border-orange-200",
  warning: "bg-amber-100 text-amber-800 border-amber-200",
  info: "bg-blue-100 text-blue-800 border-blue-200",
};

const STATUS_STYLES: Record<string, string> = {
  active: "bg-red-50 text-red-700",
  acknowledged: "bg-amber-50 text-amber-700",
  resolved: "bg-green-50 text-green-700",
  dismissed: "bg-gray-50 text-gray-600",
};

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchAlerts();
  }, []);

  const fetchAlerts = async () => {
    try {
      setLoading(true);
      const res = await apiClient.get("/monitoring/alerts");
      const data = res.data.alerts ?? res.data ?? [];
      setAlerts(Array.isArray(data) ? data : []);
      setError(null);
    } catch {
      setError("Failed to load alerts.");
    } finally {
      setLoading(false);
    }
  };

  const activeAlerts = alerts.filter((a) => a.status === "active");
  const criticalCount = alerts.filter(
    (a) => (a.severity === "critical" || a.severity === "emergency") && a.status === "active"
  ).length;
  const acknowledgedCount = alerts.filter((a) => a.status === "acknowledged").length;
  const resolvedCount = alerts.filter((a) => a.status === "resolved").length;

  // Calculate response metrics
  const acknowledgedAlerts = alerts.filter((a) => a.acknowledged_at && a.created_at);
  const avgAcknowledgeTime = acknowledgedAlerts.length > 0
    ? Math.round(
        acknowledgedAlerts.reduce((sum, a) => {
          return sum + (new Date(a.acknowledged_at!).getTime() - new Date(a.created_at).getTime());
        }, 0) / acknowledgedAlerts.length / 60000
      )
    : null;

  const resolvedAlerts = alerts.filter((a) => a.resolved_at && a.created_at);
  const avgResolveTime = resolvedAlerts.length > 0
    ? Math.round(
        resolvedAlerts.reduce((sum, a) => {
          return sum + (new Date(a.resolved_at!).getTime() - new Date(a.created_at).getTime());
        }, 0) / resolvedAlerts.length / 60000
      )
    : null;

  const escalationRate = alerts.length > 0
    ? Math.round((alerts.filter((a) => a.status === "active" && new Date(a.created_at).getTime() < Date.now() - 300000).length / alerts.length) * 100)
    : 0;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Alert Summary</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Overview of all patient monitoring alerts and escalation metrics.
          </p>
        </div>
        <button
          onClick={fetchAlerts}
          className="rounded-md border border-input px-3 py-1.5 text-sm font-medium hover:bg-muted"
        >
          Refresh
        </button>
      </div>

      {/* Summary cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <p className="text-sm font-medium text-muted-foreground">Active Alerts</p>
          <p className="mt-2 text-3xl font-bold text-foreground">{activeAlerts.length}</p>
        </div>
        <div className="rounded-lg border border-red-200 bg-red-50/50 p-6 shadow-sm">
          <p className="text-sm font-medium text-red-700">Critical / Emergency</p>
          <p className="mt-2 text-3xl font-bold text-red-700">{criticalCount}</p>
        </div>
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <p className="text-sm font-medium text-muted-foreground">Acknowledged</p>
          <p className="mt-2 text-3xl font-bold text-amber-600">{acknowledgedCount}</p>
        </div>
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <p className="text-sm font-medium text-muted-foreground">Resolved</p>
          <p className="mt-2 text-3xl font-bold text-green-600">{resolvedCount}</p>
        </div>
      </div>

      {loading && (
        <div className="flex items-center justify-center py-12">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
          <span className="ml-3 text-sm text-muted-foreground">Loading alerts...</span>
        </div>
      )}

      {error && (
        <div className="rounded-lg border border-destructive/30 bg-destructive/5 p-4">
          <p className="text-sm text-destructive">{error}</p>
          <button onClick={fetchAlerts} className="mt-2 text-sm font-medium text-primary hover:underline">
            Retry
          </button>
        </div>
      )}

      {!loading && !error && (
        <div className="grid gap-6 md:grid-cols-2">
          {/* Recent alerts table */}
          <div className="rounded-lg border border-border bg-card shadow-sm">
            <div className="border-b border-border px-6 py-4">
              <h2 className="text-lg font-semibold text-foreground">Recent Alerts</h2>
            </div>
            {alerts.length === 0 ? (
              <div className="px-6 py-8 text-center text-sm text-muted-foreground">
                No alerts recorded.
              </div>
            ) : (
              <div className="divide-y divide-border">
                {alerts
                  .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
                  .slice(0, 10)
                  .map((alert) => (
                    <div key={alert.id} className="px-6 py-3">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span className={`inline-flex rounded-full border px-2 py-0.5 text-xs font-medium ${SEVERITY_STYLES[alert.severity] ?? "bg-gray-100 text-gray-700"}`}>
                            {alert.severity}
                          </span>
                          <span className="text-sm font-medium text-foreground">{alert.title}</span>
                        </div>
                        <span className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_STYLES[alert.status] ?? "bg-gray-100 text-gray-700"}`}>
                          {alert.status}
                        </span>
                      </div>
                      <div className="mt-1 flex items-center gap-3 text-xs text-muted-foreground">
                        <span>{alert.patient_name ?? "Unknown"}</span>
                        <span>{new Date(alert.created_at).toLocaleString()}</span>
                      </div>
                    </div>
                  ))}
              </div>
            )}
          </div>

          {/* Response Metrics */}
          <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
            <h2 className="text-lg font-semibold text-foreground">Response Metrics</h2>
            <div className="mt-4 space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Mean Time to Acknowledge</span>
                <span className="text-sm font-bold text-foreground">
                  {avgAcknowledgeTime !== null ? `${avgAcknowledgeTime} min` : "N/A"}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Mean Time to Resolve</span>
                <span className="text-sm font-bold text-foreground">
                  {avgResolveTime !== null ? `${avgResolveTime} min` : "N/A"}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Escalation Rate</span>
                <span className="text-sm font-bold text-foreground">{escalationRate}%</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">SLA Compliance</span>
                <span className="text-sm font-bold text-green-600">
                  {alerts.length > 0
                    ? `${Math.round(((acknowledgedCount + resolvedCount) / alerts.length) * 100)}%`
                    : "N/A"}
                </span>
              </div>
            </div>

            <div className="mt-6">
              <h3 className="text-sm font-semibold text-foreground">Severity Distribution</h3>
              <div className="mt-3 space-y-2">
                {["emergency", "critical", "warning", "info"].map((sev) => {
                  const count = alerts.filter((a) => a.severity === sev).length;
                  const pct = alerts.length > 0 ? (count / alerts.length) * 100 : 0;
                  return (
                    <div key={sev} className="flex items-center gap-3">
                      <span className="w-20 text-xs capitalize text-muted-foreground">{sev}</span>
                      <div className="flex-1">
                        <div className="h-2 rounded-full bg-muted">
                          <div
                            className={`h-2 rounded-full ${
                              sev === "emergency" ? "bg-red-500" :
                              sev === "critical" ? "bg-orange-500" :
                              sev === "warning" ? "bg-amber-500" : "bg-blue-500"
                            }`}
                            style={{ width: `${pct}%` }}
                          />
                        </div>
                      </div>
                      <span className="w-8 text-right text-xs font-medium text-foreground">{count}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
