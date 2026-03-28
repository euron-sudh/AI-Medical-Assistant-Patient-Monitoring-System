"use client";

import { useState, useEffect, useCallback } from "react";
import apiClient from "@/lib/api-client";

interface Alert {
  id: string;
  patient_id: string;
  patient_name: string;
  alert_type: string;
  severity: string;
  title: string;
  description: string;
  vital_type: string | null;
  vital_value: number | null;
  status: string;
  created_at: string;
  acknowledged_by: string | null;
  acknowledged_at: string | null;
  resolved_by: string | null;
  resolved_at: string | null;
}

const SEVERITY_ORDER: Record<string, number> = {
  emergency: 0,
  critical: 1,
  warning: 2,
  info: 3,
};

const SEVERITY_STYLES: Record<string, { badge: string; dot: string }> = {
  emergency: {
    badge: "bg-red-100 text-red-800 border-red-200",
    dot: "bg-red-500 animate-pulse",
  },
  critical: {
    badge: "bg-orange-100 text-orange-800 border-orange-200",
    dot: "bg-orange-500",
  },
  warning: {
    badge: "bg-amber-100 text-amber-800 border-amber-200",
    dot: "bg-amber-500",
  },
  info: {
    badge: "bg-blue-100 text-blue-800 border-blue-200",
    dot: "bg-blue-500",
  },
};

const STATUS_STYLES: Record<string, string> = {
  active: "bg-red-50 text-red-700",
  acknowledged: "bg-amber-50 text-amber-700",
  resolved: "bg-green-50 text-green-700",
  dismissed: "bg-gray-50 text-gray-600",
};

export default function MonitoringPage() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [filterSeverity, setFilterSeverity] = useState<string>("all");
  const [filterStatus, setFilterStatus] = useState<string>("all");

  const fetchAlerts = useCallback(async () => {
    try {
      setLoading(true);
      const res = await apiClient.get("/monitoring/alerts");
      const data = res.data.alerts ?? res.data ?? [];
      setAlerts(Array.isArray(data) ? data : []);
      setError(null);
    } catch {
      setError("Failed to load monitoring alerts.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAlerts();
    // Auto-refresh alerts every 30 seconds for real-time monitoring
    const interval = setInterval(() => {
      fetchAlerts();
    }, 30000);
    return () => clearInterval(interval);
  }, [fetchAlerts]);

  const handleAcknowledge = async (alertId: string) => {
    setActionLoading(alertId);
    try {
      await apiClient.put(`/monitoring/alerts/${alertId}/acknowledge`);
      setAlerts((prev) =>
        prev.map((a) =>
          a.id === alertId
            ? { ...a, status: "acknowledged", acknowledged_at: new Date().toISOString() }
            : a
        )
      );
    } catch {
      // silently handle - alert may already be acknowledged
    } finally {
      setActionLoading(null);
    }
  };

  const handleResolve = async (alertId: string) => {
    setActionLoading(alertId);
    try {
      await apiClient.put(`/monitoring/alerts/${alertId}/resolve`);
      setAlerts((prev) =>
        prev.map((a) =>
          a.id === alertId
            ? { ...a, status: "resolved", resolved_at: new Date().toISOString() }
            : a
        )
      );
    } catch {
      // silently handle
    } finally {
      setActionLoading(null);
    }
  };

  const sorted = [...alerts]
    .filter((a) => filterSeverity === "all" || a.severity === filterSeverity)
    .filter((a) => filterStatus === "all" || a.status === filterStatus)
    .sort((a, b) => {
      const sevDiff = (SEVERITY_ORDER[a.severity] ?? 9) - (SEVERITY_ORDER[b.severity] ?? 9);
      if (sevDiff !== 0) return sevDiff;
      return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
    });

  const counts = {
    emergency: alerts.filter((a) => a.severity === "emergency" && a.status === "active").length,
    critical: alerts.filter((a) => a.severity === "critical" && a.status === "active").length,
    warning: alerts.filter((a) => a.severity === "warning" && a.status === "active").length,
    active: alerts.filter((a) => a.status === "active").length,
    acknowledged: alerts.filter((a) => a.status === "acknowledged").length,
    resolved: alerts.filter((a) => a.status === "resolved").length,
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Patient Monitoring</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Real-time monitoring alerts sorted by severity. Acknowledge and resolve alerts promptly.
        </p>
      </div>

      {/* Summary cards */}
      <div className="grid gap-4 md:grid-cols-3 lg:grid-cols-6">
        <div className="rounded-lg border border-red-200 bg-red-50/50 p-4">
          <div className="flex items-center gap-2">
            <span className="h-3 w-3 rounded-full bg-red-500 animate-pulse" />
            <span className="text-xs font-medium text-red-700">Emergency</span>
          </div>
          <p className="mt-1 text-2xl font-bold text-red-700">{counts.emergency}</p>
        </div>
        <div className="rounded-lg border border-orange-200 bg-orange-50/50 p-4">
          <div className="flex items-center gap-2">
            <span className="h-3 w-3 rounded-full bg-orange-500" />
            <span className="text-xs font-medium text-orange-700">Critical</span>
          </div>
          <p className="mt-1 text-2xl font-bold text-orange-700">{counts.critical}</p>
        </div>
        <div className="rounded-lg border border-amber-200 bg-amber-50/50 p-4">
          <div className="flex items-center gap-2">
            <span className="h-3 w-3 rounded-full bg-amber-500" />
            <span className="text-xs font-medium text-amber-700">Warning</span>
          </div>
          <p className="mt-1 text-2xl font-bold text-amber-700">{counts.warning}</p>
        </div>
        <div className="rounded-lg border border-border bg-card p-4">
          <p className="text-xs font-medium text-muted-foreground">Active</p>
          <p className="mt-1 text-2xl font-bold text-foreground">{counts.active}</p>
        </div>
        <div className="rounded-lg border border-border bg-card p-4">
          <p className="text-xs font-medium text-muted-foreground">Acknowledged</p>
          <p className="mt-1 text-2xl font-bold text-amber-600">{counts.acknowledged}</p>
        </div>
        <div className="rounded-lg border border-border bg-card p-4">
          <p className="text-xs font-medium text-muted-foreground">Resolved</p>
          <p className="mt-1 text-2xl font-bold text-green-600">{counts.resolved}</p>
        </div>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          <label className="text-xs font-medium text-muted-foreground">Severity:</label>
          <select
            value={filterSeverity}
            onChange={(e) => setFilterSeverity(e.target.value)}
            className="rounded-md border border-input bg-background px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
          >
            <option value="all">All</option>
            <option value="emergency">Emergency</option>
            <option value="critical">Critical</option>
            <option value="warning">Warning</option>
            <option value="info">Info</option>
          </select>
        </div>
        <div className="flex items-center gap-2">
          <label className="text-xs font-medium text-muted-foreground">Status:</label>
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="rounded-md border border-input bg-background px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
          >
            <option value="all">All</option>
            <option value="active">Active</option>
            <option value="acknowledged">Acknowledged</option>
            <option value="resolved">Resolved</option>
          </select>
        </div>
        <button
          onClick={fetchAlerts}
          className="ml-auto rounded-md border border-input px-3 py-1 text-sm font-medium hover:bg-muted"
        >
          Refresh
        </button>
      </div>

      {loading && (
        <div className="flex items-center justify-center py-16">
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

      {!loading && !error && sorted.length === 0 && (
        <div className="flex flex-col items-center justify-center rounded-lg border border-border bg-card py-16">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-green-100">
            <span className="text-xl text-green-600">&#10003;</span>
          </div>
          <p className="mt-3 text-lg font-medium text-foreground">No alerts</p>
          <p className="mt-1 text-sm text-muted-foreground">All patients are within normal parameters.</p>
        </div>
      )}

      {!loading && !error && sorted.length > 0 && (
        <div className="space-y-3">
          {sorted.map((alert) => {
            const sev = SEVERITY_STYLES[alert.severity] ?? SEVERITY_STYLES.info;
            const statusStyle = STATUS_STYLES[alert.status] ?? STATUS_STYLES.active;
            return (
              <div
                key={alert.id}
                className={`rounded-lg border bg-card p-4 shadow-sm ${
                  alert.severity === "emergency" && alert.status === "active"
                    ? "border-red-300 ring-1 ring-red-200"
                    : "border-border"
                }`}
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex items-start gap-3">
                    <span className={`mt-1 h-3 w-3 shrink-0 rounded-full ${sev.dot}`} />
                    <div>
                      <div className="flex flex-wrap items-center gap-2">
                        <h3 className="font-semibold text-foreground">{alert.title}</h3>
                        <span className={`inline-flex rounded-full border px-2 py-0.5 text-xs font-medium ${sev.badge}`}>
                          {alert.severity.toUpperCase()}
                        </span>
                        <span className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${statusStyle}`}>
                          {alert.status}
                        </span>
                      </div>
                      <p className="mt-1 text-sm text-muted-foreground">{alert.description}</p>
                      <div className="mt-2 flex flex-wrap gap-4 text-xs text-muted-foreground">
                        <span>Patient: <strong className="text-foreground">{alert.patient_name ?? "Unknown"}</strong></span>
                        {alert.vital_type && (
                          <span>Vital: {alert.vital_type} = {alert.vital_value}</span>
                        )}
                        <span>
                          {new Date(alert.created_at).toLocaleString()}
                        </span>
                      </div>
                    </div>
                  </div>
                  <div className="flex shrink-0 gap-2">
                    {alert.status === "active" && (
                      <button
                        onClick={() => handleAcknowledge(alert.id)}
                        disabled={actionLoading === alert.id}
                        className="rounded-md bg-amber-100 px-3 py-1.5 text-xs font-medium text-amber-800 hover:bg-amber-200 disabled:opacity-50"
                      >
                        {actionLoading === alert.id ? "..." : "Acknowledge"}
                      </button>
                    )}
                    {(alert.status === "active" || alert.status === "acknowledged") && (
                      <button
                        onClick={() => handleResolve(alert.id)}
                        disabled={actionLoading === alert.id}
                        className="rounded-md bg-green-100 px-3 py-1.5 text-xs font-medium text-green-800 hover:bg-green-200 disabled:opacity-50"
                      >
                        {actionLoading === alert.id ? "..." : "Resolve"}
                      </button>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
