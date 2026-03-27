"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import apiClient from "@/lib/api-client";

export interface MonitoringAlert {
  id: string;
  patient_id: string;
  patient_name: string;
  alert_type: string;
  severity: "emergency" | "critical" | "warning" | "info";
  title: string;
  description: string;
  vital_type: string | null;
  vital_value: number | null;
  status: "active" | "acknowledged" | "resolved" | "dismissed";
  created_at: string;
  acknowledged_by: string | null;
  acknowledged_at: string | null;
  resolved_by: string | null;
  resolved_at: string | null;
}

export function useAlerts({ pollingInterval = 0, enabled = true }: { pollingInterval?: number; enabled?: boolean } = {}) {
  const [alerts, setAlerts] = useState<MonitoringAlert[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetchAlerts = useCallback(async () => {
    if (!enabled) return;
    try {
      setIsLoading(true);
      const res = await apiClient.get("/monitoring/alerts");
      const data = res.data.alerts ?? res.data ?? [];
      setAlerts(Array.isArray(data) ? data : []);
      setError(null);
    } catch {
      setError("Failed to load monitoring alerts.");
    } finally {
      setIsLoading(false);
    }
  }, [enabled]);

  useEffect(() => { if (enabled) fetchAlerts(); }, [fetchAlerts, enabled]);

  useEffect(() => {
    if (pollingInterval > 0 && enabled) intervalRef.current = setInterval(fetchAlerts, pollingInterval);
    return () => { if (intervalRef.current) { clearInterval(intervalRef.current); intervalRef.current = null; } };
  }, [pollingInterval, fetchAlerts, enabled]);

  const unreadCount = alerts.filter((a) => a.status === "active").length;

  const acknowledgeAlert = useCallback(async (alertId: string) => {
    try {
      await apiClient.put(`/monitoring/alerts/${alertId}/acknowledge`);
      setAlerts((prev) => prev.map((a) => a.id === alertId ? { ...a, status: "acknowledged" as const, acknowledged_at: new Date().toISOString() } : a));
    } catch { /* may already be acknowledged */ }
  }, []);

  const resolveAlert = useCallback(async (alertId: string) => {
    try {
      await apiClient.put(`/monitoring/alerts/${alertId}/resolve`);
      setAlerts((prev) => prev.map((a) => a.id === alertId ? { ...a, status: "resolved" as const, resolved_at: new Date().toISOString() } : a));
    } catch { /* may already be resolved */ }
  }, []);

  return { alerts, unreadCount, isLoading, error, refetch: fetchAlerts, acknowledgeAlert, resolveAlert };
}
