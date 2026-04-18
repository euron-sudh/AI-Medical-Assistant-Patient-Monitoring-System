"use client";

import { useEffect, useState } from "react";
import apiClient from "@/lib/api-client";
import { extractPatientList } from "@/lib/patient-list";
import {
  Users,
  CalendarClock,
  AlertTriangle,
  FileText,
  Stethoscope,
  ClipboardList,
  Brain,
  BarChart3,
  ArrowUpRight,
  Activity,
  Clock,
  Bell,
} from "lucide-react";

interface UserInfo {
  first_name: string;
  last_name: string;
  email: string;
  role: string;
}

interface Appointment {
  id: string;
  patient_name: string;
  scheduled_at: string;
  appointment_type: string;
  status: string;
  reason: string | null;
  duration_minutes: number;
}

interface Alert {
  id: string;
  patient_name: string;
  severity: string;
  message: string;
  status: string;
  created_at: string;
  vital_type?: string;
}

const SEVERITY_STYLES: Record<string, string> = {
  critical: "bg-red-100 text-red-800 border-red-200",
  emergency: "bg-red-100 text-red-800 border-red-200",
  high: "bg-orange-100 text-orange-800 border-orange-200",
  warning: "bg-amber-100 text-amber-800 border-amber-200",
  medium: "bg-amber-100 text-amber-800 border-amber-200",
  low: "bg-blue-100 text-blue-800 border-blue-200",
  info: "bg-blue-100 text-blue-800 border-blue-200",
};

export default function DoctorDashboard() {
  const [user, setUser] = useState<UserInfo | null>(null);
  const [patientCount, setPatientCount] = useState(0);
  const [upcomingAppointments, setUpcomingAppointments] = useState<Appointment[]>([]);
  const [todayCount, setTodayCount] = useState(0);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [pendingReports, setPendingReports] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const stored = localStorage.getItem("user");
    if (stored) {
      setUser(JSON.parse(stored));
    }
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    setLoading(true);

    try {
      const pRes = await apiClient.get("/patients");
      const patients = extractPatientList(pRes.data);
      setPatientCount(patients.length);
    } catch {
      /* ignore */
    }

    try {
      const aRes = await apiClient.get("/appointments");
      const appts: Appointment[] = aRes.data.appointments ?? aRes.data ?? [];
      if (Array.isArray(appts)) {
        const now = new Date();
        const todayStr = now.toISOString().split("T")[0];
        setTodayCount(appts.filter((a) => a.scheduled_at?.startsWith(todayStr)).length);
        const upcoming = appts
          .filter(
            (a) =>
              new Date(a.scheduled_at) > now &&
              a.status !== "cancelled" &&
              a.status !== "completed"
          )
          .sort((a, b) => new Date(a.scheduled_at).getTime() - new Date(b.scheduled_at).getTime())
          .slice(0, 5);
        setUpcomingAppointments(upcoming);
      }
    } catch {
      /* ignore */
    }

    try {
      const mRes = await apiClient.get("/monitoring/alerts");
      const allAlerts: Alert[] = mRes.data.alerts ?? mRes.data ?? [];
      if (Array.isArray(allAlerts)) {
        setAlerts(
          allAlerts
            .filter((a) => a.status === "active")
            .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
            .slice(0, 5)
        );
      }
    } catch {
      /* ignore */
    }

    // Reports endpoint requires a patient_id; pending count comes from per-patient data
    // For dashboard overview, we skip this to avoid unnecessary 404 calls

    setLoading(false);
  };

  const quickActions = [
    { label: "Patients", href: "/doctor/patients", icon: Users, color: "text-blue-600 bg-blue-50" },
    { label: "Appointments", href: "/doctor/appointments", icon: CalendarClock, color: "text-purple-600 bg-purple-50" },
    { label: "Prescriptions", href: "/doctor/prescriptions", icon: ClipboardList, color: "text-green-600 bg-green-50" },
    { label: "AI Assistant", href: "/doctor/ai-assistant", icon: Brain, color: "text-emerald-600 bg-emerald-50" },
    { label: "Monitoring", href: "/doctor/monitoring", icon: Activity, color: "text-red-600 bg-red-50" },
    { label: "Analytics", href: "/doctor/analytics", icon: BarChart3, color: "text-indigo-600 bg-indigo-50" },
  ];

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-foreground">
          Welcome{user ? `, Dr. ${user.last_name}` : ""}
        </h1>
        <p className="mt-1 text-muted-foreground">
          Clinical overview and patient management
        </p>
      </div>

      {/* Patient Count Cards */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-muted-foreground">Active Patients</p>
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-blue-50">
              <Users className="h-5 w-5 text-blue-600" />
            </div>
          </div>
          <p className="mt-2 text-3xl font-bold text-foreground">
            {loading ? "--" : patientCount}
          </p>
          <p className="mt-1 text-xs text-muted-foreground">Assigned to you</p>
        </div>

        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-muted-foreground">Today&apos;s Appointments</p>
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-purple-50">
              <CalendarClock className="h-5 w-5 text-purple-600" />
            </div>
          </div>
          <p className="mt-2 text-3xl font-bold text-foreground">
            {loading ? "--" : todayCount}
          </p>
          <p className="mt-1 text-xs text-muted-foreground">
            {todayCount === 0 ? "No appointments scheduled" : "scheduled for today"}
          </p>
        </div>

        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-muted-foreground">Active Alerts</p>
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-amber-50">
              <AlertTriangle className="h-5 w-5 text-amber-600" />
            </div>
          </div>
          <p className="mt-2 text-3xl font-bold text-foreground">
            {loading ? "--" : alerts.length}
          </p>
          <p className="mt-1 text-xs text-muted-foreground">
            {alerts.length === 0 ? (
              <span className="text-green-600">All clear</span>
            ) : (
              <span className="text-amber-600">Requires attention</span>
            )}
          </p>
        </div>

        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-muted-foreground">Pending Reports</p>
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-orange-50">
              <FileText className="h-5 w-5 text-orange-600" />
            </div>
          </div>
          <p className="mt-2 text-3xl font-bold text-foreground">
            {loading ? "--" : pendingReports}
          </p>
          <p className="mt-1 text-xs text-muted-foreground">Awaiting your review</p>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-foreground">Quick Actions</h2>
        <div className="mt-4 grid grid-cols-2 gap-3 md:grid-cols-3 lg:grid-cols-6">
          {quickActions.map((action) => (
            <a
              key={action.label}
              href={action.href}
              className="flex flex-col items-center gap-2 rounded-lg border border-border p-4 text-center transition-colors hover:bg-muted/50"
            >
              <div className={`flex h-10 w-10 items-center justify-center rounded-full ${action.color}`}>
                <action.icon className="h-5 w-5" />
              </div>
              <span className="text-sm font-medium text-foreground">{action.label}</span>
            </a>
          ))}
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Upcoming Appointments */}
        <div className="rounded-lg border border-border bg-card shadow-sm">
          <div className="flex items-center justify-between border-b border-border px-6 py-4">
            <div className="flex items-center gap-2">
              <Clock className="h-5 w-5 text-muted-foreground" />
              <h2 className="text-lg font-semibold text-foreground">Upcoming Appointments</h2>
            </div>
            <a
              href="/doctor/appointments"
              className="flex items-center gap-1 text-sm font-medium text-primary hover:underline"
            >
              View All <ArrowUpRight className="h-3.5 w-3.5" />
            </a>
          </div>
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent" />
            </div>
          ) : upcomingAppointments.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-muted">
                <Stethoscope className="h-6 w-6 text-muted-foreground" />
              </div>
              <p className="mt-3 text-sm font-medium text-foreground">No upcoming appointments</p>
              <p className="mt-1 text-xs text-muted-foreground">
                Your schedule is clear for now.
              </p>
            </div>
          ) : (
            <div className="divide-y divide-border">
              {upcomingAppointments.map((appt) => (
                <div key={appt.id} className="flex items-center justify-between px-6 py-3">
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium text-foreground">
                      {appt.patient_name ?? "Unknown Patient"}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {new Date(appt.scheduled_at).toLocaleDateString()} at{" "}
                      {new Date(appt.scheduled_at).toLocaleTimeString([], {
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                      {" - "}
                      {appt.duration_minutes ?? 30} min
                    </p>
                  </div>
                  <span className="inline-flex rounded-full bg-blue-50 px-2 py-0.5 text-xs font-medium text-blue-700">
                    {(appt.appointment_type ?? "").replace("_", " ")}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Recent Alerts */}
        <div className="rounded-lg border border-border bg-card shadow-sm">
          <div className="flex items-center justify-between border-b border-border px-6 py-4">
            <div className="flex items-center gap-2">
              <Bell className="h-5 w-5 text-muted-foreground" />
              <h2 className="text-lg font-semibold text-foreground">Recent Alerts</h2>
            </div>
            <a
              href="/doctor/monitoring"
              className="flex items-center gap-1 text-sm font-medium text-primary hover:underline"
            >
              Monitoring Wall <ArrowUpRight className="h-3.5 w-3.5" />
            </a>
          </div>
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent" />
            </div>
          ) : alerts.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-green-100">
                <span className="text-lg text-green-600">OK</span>
              </div>
              <p className="mt-3 text-sm font-medium text-foreground">No active alerts</p>
              <p className="mt-1 text-xs text-muted-foreground">
                Patient monitoring alerts will appear here in real-time.
              </p>
            </div>
          ) : (
            <div className="divide-y divide-border">
              {alerts.map((alert) => (
                <div key={alert.id} className="px-6 py-3">
                  <div className="flex items-start justify-between">
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        <span
                          className={`inline-flex rounded-full border px-2 py-0.5 text-xs font-medium ${
                            SEVERITY_STYLES[alert.severity] ?? "bg-gray-100 text-gray-700 border-gray-200"
                          }`}
                        >
                          {alert.severity}
                        </span>
                        <span className="text-sm font-medium text-foreground">
                          {alert.patient_name ?? "Unknown"}
                        </span>
                      </div>
                      <p className="mt-1 text-xs text-muted-foreground">{alert.message}</p>
                    </div>
                    <span className="ml-2 whitespace-nowrap text-xs text-muted-foreground">
                      {alert.created_at
                        ? new Date(alert.created_at).toLocaleTimeString([], {
                            hour: "2-digit",
                            minute: "2-digit",
                          })
                        : ""}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
