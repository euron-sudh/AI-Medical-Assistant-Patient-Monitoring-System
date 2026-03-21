"use client";

import { useState, useEffect } from "react";
import apiClient from "@/lib/api-client";

interface Stats {
  totalPatients: number;
  totalAppointments: number;
  appointmentsThisWeek: number;
  activeAlerts: number;
  criticalAlerts: number;
  totalReports: number;
  pendingReports: number;
  completedAppointments: number;
  telemedicineSessions: number;
}

export default function AnalyticsPage() {
  const [stats, setStats] = useState<Stats>({
    totalPatients: 0,
    totalAppointments: 0,
    appointmentsThisWeek: 0,
    activeAlerts: 0,
    criticalAlerts: 0,
    totalReports: 0,
    pendingReports: 0,
    completedAppointments: 0,
    telemedicineSessions: 0,
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    setLoading(true);
    const s: Stats = { ...stats };

    try {
      const pRes = await apiClient.get("/patients");
      const patients = pRes.data.patients ?? pRes.data ?? [];
      s.totalPatients = Array.isArray(patients) ? patients.length : 0;
    } catch { /* ignore */ }

    try {
      const aRes = await apiClient.get("/appointments");
      const appts = aRes.data.appointments ?? aRes.data ?? [];
      if (Array.isArray(appts)) {
        s.totalAppointments = appts.length;
        s.completedAppointments = appts.filter(
          (a: { status: string }) => a.status === "completed"
        ).length;
        s.telemedicineSessions = appts.filter(
          (a: { appointment_type: string }) => a.appointment_type === "telemedicine"
        ).length;

        const now = new Date();
        const weekStart = new Date(now);
        weekStart.setDate(now.getDate() - now.getDay());
        weekStart.setHours(0, 0, 0, 0);
        const weekEnd = new Date(weekStart);
        weekEnd.setDate(weekStart.getDate() + 7);
        s.appointmentsThisWeek = appts.filter((a: { scheduled_at: string }) => {
          const d = new Date(a.scheduled_at);
          return d >= weekStart && d < weekEnd;
        }).length;
      }
    } catch { /* ignore */ }

    try {
      const mRes = await apiClient.get("/monitoring/alerts");
      const alerts = mRes.data.alerts ?? mRes.data ?? [];
      if (Array.isArray(alerts)) {
        s.activeAlerts = alerts.filter(
          (a: { status: string }) => a.status === "active"
        ).length;
        s.criticalAlerts = alerts.filter(
          (a: { severity: string; status: string }) =>
            (a.severity === "critical" || a.severity === "emergency") && a.status === "active"
        ).length;
      }
    } catch { /* ignore */ }

    try {
      const rRes = await apiClient.get("/reports");
      const reports = rRes.data.reports ?? rRes.data ?? [];
      if (Array.isArray(reports)) {
        s.totalReports = reports.length;
        s.pendingReports = reports.filter(
          (r: { status: string }) => r.status === "pending"
        ).length;
      }
    } catch { /* ignore */ }

    setStats(s);
    setLoading(false);
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Analytics</h1>
          <p className="mt-1 text-sm text-muted-foreground">Loading clinical analytics...</p>
        </div>
        <div className="flex items-center justify-center py-16">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Analytics</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Clinical analytics, patient outcomes, and performance metrics.
        </p>
      </div>

      {/* Key Metrics */}
      <div className="grid gap-4 md:grid-cols-4">
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <p className="text-sm font-medium text-muted-foreground">Total Patients</p>
          <p className="mt-2 text-3xl font-bold text-foreground">{stats.totalPatients}</p>
          <p className="mt-1 text-xs text-muted-foreground">registered in system</p>
        </div>
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <p className="text-sm font-medium text-muted-foreground">This Week</p>
          <p className="mt-2 text-3xl font-bold text-primary">{stats.appointmentsThisWeek}</p>
          <p className="mt-1 text-xs text-muted-foreground">appointments</p>
        </div>
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <p className="text-sm font-medium text-muted-foreground">Active Alerts</p>
          <p className="mt-2 text-3xl font-bold text-amber-600">{stats.activeAlerts}</p>
          <p className="mt-1 text-xs text-muted-foreground">
            {stats.criticalAlerts > 0 && (
              <span className="font-medium text-red-600">{stats.criticalAlerts} critical</span>
            )}
            {stats.criticalAlerts === 0 && "none critical"}
          </p>
        </div>
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <p className="text-sm font-medium text-muted-foreground">Reports</p>
          <p className="mt-2 text-3xl font-bold text-foreground">{stats.totalReports}</p>
          <p className="mt-1 text-xs text-muted-foreground">
            {stats.pendingReports > 0 && (
              <span className="font-medium text-amber-600">{stats.pendingReports} pending review</span>
            )}
            {stats.pendingReports === 0 && "all reviewed"}
          </p>
        </div>
      </div>

      {/* Detailed Stats */}
      <div className="grid gap-6 md:grid-cols-2">
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-foreground">Appointment Statistics</h2>
          <div className="mt-4 space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">Total Appointments</span>
              <span className="text-sm font-bold text-foreground">{stats.totalAppointments}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">Completed</span>
              <span className="text-sm font-bold text-green-600">{stats.completedAppointments}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">Telemedicine Sessions</span>
              <span className="text-sm font-bold text-purple-600">{stats.telemedicineSessions}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">Completion Rate</span>
              <span className="text-sm font-bold text-foreground">
                {stats.totalAppointments > 0
                  ? `${Math.round((stats.completedAppointments / stats.totalAppointments) * 100)}%`
                  : "N/A"}
              </span>
            </div>
            {/* Visual bar */}
            {stats.totalAppointments > 0 && (
              <div className="mt-2">
                <div className="h-3 w-full rounded-full bg-muted">
                  <div
                    className="h-3 rounded-full bg-green-500"
                    style={{
                      width: `${Math.round((stats.completedAppointments / stats.totalAppointments) * 100)}%`,
                    }}
                  />
                </div>
                <p className="mt-1 text-xs text-muted-foreground">Completion rate</p>
              </div>
            )}
          </div>
        </div>

        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-foreground">Alert Overview</h2>
          <div className="mt-4 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="h-2.5 w-2.5 rounded-full bg-red-500" />
                <span className="text-sm text-muted-foreground">Critical / Emergency</span>
              </div>
              <span className="text-sm font-bold text-red-600">{stats.criticalAlerts}</span>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="h-2.5 w-2.5 rounded-full bg-amber-500" />
                <span className="text-sm text-muted-foreground">Active Alerts</span>
              </div>
              <span className="text-sm font-bold text-amber-600">{stats.activeAlerts}</span>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="h-2.5 w-2.5 rounded-full bg-blue-500" />
                <span className="text-sm text-muted-foreground">Total Reports</span>
              </div>
              <span className="text-sm font-bold text-foreground">{stats.totalReports}</span>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="h-2.5 w-2.5 rounded-full bg-amber-400" />
                <span className="text-sm text-muted-foreground">Pending Reports</span>
              </div>
              <span className="text-sm font-bold text-amber-600">{stats.pendingReports}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-foreground">Quick Actions</h2>
        <div className="mt-4 grid gap-3 md:grid-cols-4">
          <a
            href="/doctor/monitoring"
            className="rounded-md border border-border p-3 text-center text-sm font-medium text-foreground transition-colors hover:bg-muted"
          >
            View Monitoring
          </a>
          <a
            href="/doctor/patients"
            className="rounded-md border border-border p-3 text-center text-sm font-medium text-foreground transition-colors hover:bg-muted"
          >
            Patient List
          </a>
          <a
            href="/doctor/appointments"
            className="rounded-md border border-border p-3 text-center text-sm font-medium text-foreground transition-colors hover:bg-muted"
          >
            Appointments
          </a>
          <a
            href="/doctor/ai-assistant"
            className="rounded-md border border-border p-3 text-center text-sm font-medium text-primary transition-colors hover:bg-primary/5"
          >
            AI Assistant
          </a>
        </div>
      </div>
    </div>
  );
}
