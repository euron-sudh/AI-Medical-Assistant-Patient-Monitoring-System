"use client";

import { useState, useEffect, useCallback } from "react";
import apiClient from "@/lib/api-client";
// lucide-react icons available if needed

interface HealthData {
  status: string;
  service?: string;
  version?: string;
  timestamp?: string;
  uptime_seconds?: number;
  dependencies?: Record<string, string | { status: string }>;
}

interface ServiceStatus {
  name: string;
  description: string;
  status: "healthy" | "unhealthy" | "unknown" | "checking";
  latencyMs: number | null;
  details: string | null;
}

export default function SystemHealthPage() {
  const [health, setHealth] = useState<HealthData | null>(null);
  const [services, setServices] = useState<ServiceStatus[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastChecked, setLastChecked] = useState<string>("");

  const checkHealth = useCallback(async () => {
    setLoading(true);
    setError(null);

    const defaultServices: ServiceStatus[] = [
      { name: "Flask Backend", description: "API server (Flask 3+)", status: "checking", latencyMs: null, details: null },
      { name: "PostgreSQL", description: "Primary relational database", status: "unknown", latencyMs: null, details: null },
      { name: "Redis", description: "Cache, sessions, pub/sub", status: "unknown", latencyMs: null, details: null },
      { name: "InfluxDB", description: "Time-series vitals data", status: "unknown", latencyMs: null, details: null },
      { name: "Elasticsearch", description: "Full-text search engine", status: "unknown", latencyMs: null, details: null },
      { name: "Celery Workers", description: "Background task processing", status: "unknown", latencyMs: null, details: null },
      { name: "MinIO / S3", description: "File and document storage", status: "unknown", latencyMs: null, details: null },
      { name: "OpenAI API", description: "AI model inference", status: "unknown", latencyMs: null, details: null },
    ];

    try {
      const start = performance.now();
      const res = await apiClient.get("/health");
      const latency = Math.round(performance.now() - start);
      const data: HealthData = res.data;
      setHealth(data);

      // Update backend service status
      defaultServices[0] = {
        ...defaultServices[0],
        status: data.status === "healthy" ? "healthy" : "unhealthy",
        latencyMs: latency,
        details: data.version ? `v${data.version}` : null,
      };

      // Update dependency statuses if provided
      if (data.dependencies) {
        for (const [depName, depStatus] of Object.entries(data.dependencies)) {
          const statusStr = typeof depStatus === "string" ? depStatus : depStatus?.status ?? "unknown";
          const isHealthy = statusStr === "healthy" || statusStr === "connected" || statusStr === "ok";
          const idx = defaultServices.findIndex(
            (s) => s.name.toLowerCase().includes(depName.toLowerCase()) ||
                   depName.toLowerCase().includes(s.name.toLowerCase().split(" ")[0].toLowerCase())
          );
          if (idx >= 0) {
            defaultServices[idx].status = isHealthy ? "healthy" : "unhealthy";
            defaultServices[idx].details = statusStr;
          }
        }
      }
    } catch {
      defaultServices[0] = {
        ...defaultServices[0],
        status: "unhealthy",
        details: "Connection failed",
      };
      setError("Could not reach backend health endpoint.");
    }

    setServices(defaultServices);
    setLastChecked(new Date().toLocaleTimeString());
    setLoading(false);
  }, []);

  useEffect(() => {
    checkHealth();
  }, [checkHealth]);

  const getStatusIndicator = (status: string) => {
    switch (status) {
      case "healthy":
        return { color: "bg-green-500", text: "text-green-700", bg: "bg-green-50 border-green-200", label: "Healthy" };
      case "unhealthy":
        return { color: "bg-red-500", text: "text-red-700", bg: "bg-red-50 border-red-200", label: "Unhealthy" };
      case "checking":
        return { color: "bg-blue-500 animate-pulse", text: "text-blue-700", bg: "bg-blue-50 border-blue-200", label: "Checking..." };
      default:
        return { color: "bg-gray-400", text: "text-gray-600", bg: "bg-gray-50 border-gray-200", label: "Unknown" };
    }
  };

  const healthyCount = services.filter((s) => s.status === "healthy").length;
  const unhealthyCount = services.filter((s) => s.status === "unhealthy").length;

  const formatUptime = (seconds: number | undefined): string => {
    if (!seconds) return "N/A";
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    if (days > 0) return `${days}d ${hours}h ${mins}m`;
    if (hours > 0) return `${hours}h ${mins}m`;
    return `${mins}m`;
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">System Health</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Monitor the health and status of all infrastructure components.
          </p>
        </div>
        <div className="flex items-center gap-3">
          {lastChecked && (
            <span className="text-xs text-muted-foreground">Last checked: {lastChecked}</span>
          )}
          <button
            onClick={checkHealth}
            disabled={loading}
            className="rounded-md border border-input px-3 py-1.5 text-sm font-medium hover:bg-muted disabled:opacity-50"
          >
            {loading ? "Checking..." : "Refresh"}
          </button>
        </div>
      </div>

      {/* Overall Status */}
      <div className="grid gap-4 md:grid-cols-4">
        <div className={`rounded-lg border p-6 shadow-sm ${
          unhealthyCount === 0 && healthyCount > 0
            ? "border-green-200 bg-green-50/50"
            : unhealthyCount > 0
            ? "border-red-200 bg-red-50/50"
            : "border-border bg-card"
        }`}>
          <p className="text-sm font-medium text-muted-foreground">Overall Status</p>
          <p className={`mt-2 text-2xl font-bold ${
            unhealthyCount === 0 && healthyCount > 0 ? "text-green-700" :
            unhealthyCount > 0 ? "text-red-700" : "text-foreground"
          }`}>
            {unhealthyCount === 0 && healthyCount > 0 ? "All Systems Go" :
             unhealthyCount > 0 ? "Degraded" : "Checking..."}
          </p>
        </div>
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <p className="text-sm font-medium text-muted-foreground">Services Healthy</p>
          <p className="mt-2 text-2xl font-bold text-green-600">{healthyCount} / {services.length}</p>
        </div>
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <p className="text-sm font-medium text-muted-foreground">Backend Version</p>
          <p className="mt-2 text-2xl font-bold text-foreground">
            {health?.version ? `v${health.version}` : "N/A"}
          </p>
        </div>
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <p className="text-sm font-medium text-muted-foreground">Uptime</p>
          <p className="mt-2 text-2xl font-bold text-foreground">
            {formatUptime(health?.uptime_seconds)}
          </p>
        </div>
      </div>

      {error && (
        <div className="rounded-lg border border-amber-200 bg-amber-50 p-4">
          <p className="text-sm text-amber-800">{error}</p>
        </div>
      )}

      {/* Service Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {services.map((service) => {
          const indicator = getStatusIndicator(service.status);
          return (
            <div
              key={service.name}
              className={`rounded-lg border p-4 shadow-sm ${indicator.bg}`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className={`h-3 w-3 rounded-full ${indicator.color}`} />
                  <span className="font-medium text-foreground">{service.name}</span>
                </div>
                <span className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium ${indicator.text}`}>
                  {indicator.label}
                </span>
              </div>
              <p className="mt-1 text-xs text-muted-foreground">{service.description}</p>
              <div className="mt-2 flex items-center gap-3 text-xs text-muted-foreground">
                {service.latencyMs !== null && (
                  <span>Latency: {service.latencyMs}ms</span>
                )}
                {service.details && (
                  <span>{service.details}</span>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Raw Health Response */}
      {health && (
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-foreground">Health Check Response</h2>
          <pre className="mt-3 overflow-x-auto rounded-md bg-muted p-4 text-xs text-foreground">
            {JSON.stringify(health, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}
