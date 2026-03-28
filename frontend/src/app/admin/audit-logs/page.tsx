"use client";

import { useState, useEffect } from "react";
import apiClient from "@/lib/api-client";
import { Download } from "lucide-react";

interface AuditLog {
  id: string;
  user_id: string;
  user_name: string | null;
  user_email: string | null;
  action: string;
  resource_type: string;
  resource_id: string | null;
  patient_id: string | null;
  ip_address: string | null;
  user_agent: string | null;
  status_code: number | null;
  details: Record<string, unknown> | null;
  created_at: string;
}

const ACTION_STYLES: Record<string, string> = {
  view: "bg-blue-50 text-blue-700",
  create: "bg-green-50 text-green-700",
  update: "bg-amber-50 text-amber-700",
  delete: "bg-red-50 text-red-700",
  login: "bg-purple-50 text-purple-700",
  logout: "bg-gray-50 text-gray-600",
  export: "bg-teal-50 text-teal-700",
};

// Sample audit log data for display when the API endpoint is not available
const SAMPLE_LOGS: AuditLog[] = [
  { id: "1", user_id: "u1", user_name: "Dr. Sarah Chen", user_email: "sarah.chen@example.com", action: "view", resource_type: "patient_record", resource_id: "p1", patient_id: "p1", ip_address: "192.168.1.45", user_agent: "Chrome/120", status_code: 200, details: null, created_at: new Date(Date.now() - 300000).toISOString() },
  { id: "2", user_id: "u2", user_name: "Nurse Williams", user_email: "n.williams@example.com", action: "update", resource_type: "vitals_reading", resource_id: "v1", patient_id: "p2", ip_address: "192.168.1.52", user_agent: "Firefox/121", status_code: 200, details: null, created_at: new Date(Date.now() - 600000).toISOString() },
  { id: "3", user_id: "u3", user_name: "Admin User", user_email: "admin@example.com", action: "export", resource_type: "audit_logs", resource_id: null, patient_id: null, ip_address: "10.0.0.1", user_agent: "Chrome/120", status_code: 200, details: null, created_at: new Date(Date.now() - 900000).toISOString() },
  { id: "4", user_id: "u4", user_name: "Dr. Mike Johnson", user_email: "m.johnson@example.com", action: "create", resource_type: "prescription", resource_id: "rx1", patient_id: "p3", ip_address: "192.168.1.60", user_agent: "Safari/17", status_code: 201, details: null, created_at: new Date(Date.now() - 1200000).toISOString() },
  { id: "5", user_id: "u1", user_name: "Dr. Sarah Chen", user_email: "sarah.chen@example.com", action: "view", resource_type: "lab_values", resource_id: "l1", patient_id: "p1", ip_address: "192.168.1.45", user_agent: "Chrome/120", status_code: 200, details: null, created_at: new Date(Date.now() - 1800000).toISOString() },
  { id: "6", user_id: "u5", user_name: "Patient Demo", user_email: "patient@example.com", action: "login", resource_type: "auth", resource_id: null, patient_id: null, ip_address: "203.0.113.50", user_agent: "Mobile Safari/17", status_code: 200, details: null, created_at: new Date(Date.now() - 2400000).toISOString() },
  { id: "7", user_id: "u6", user_name: "Unknown User", user_email: "unknown@example.com", action: "view", resource_type: "patient_record", resource_id: "p5", patient_id: "p5", ip_address: "198.51.100.10", user_agent: "curl/7.88", status_code: 403, details: { reason: "Access denied - not assigned" }, created_at: new Date(Date.now() - 3600000).toISOString() },
  { id: "8", user_id: "u2", user_name: "Nurse Williams", user_email: "n.williams@example.com", action: "update", resource_type: "monitoring_alert", resource_id: "a1", patient_id: "p2", ip_address: "192.168.1.52", user_agent: "Firefox/121", status_code: 200, details: { action_taken: "acknowledged" }, created_at: new Date(Date.now() - 4200000).toISOString() },
  { id: "9", user_id: "u1", user_name: "Dr. Sarah Chen", user_email: "sarah.chen@example.com", action: "create", resource_type: "care_plan", resource_id: "cp1", patient_id: "p1", ip_address: "192.168.1.45", user_agent: "Chrome/120", status_code: 201, details: null, created_at: new Date(Date.now() - 5400000).toISOString() },
  { id: "10", user_id: "u3", user_name: "Admin User", user_email: "admin@example.com", action: "view", resource_type: "audit_logs", resource_id: null, patient_id: null, ip_address: "10.0.0.1", user_agent: "Chrome/120", status_code: 200, details: null, created_at: new Date(Date.now() - 7200000).toISOString() },
];

export default function AuditLogsPage() {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [usingSample, setUsingSample] = useState(false);
  const [actionFilter, setActionFilter] = useState<string>("all");
  const [search, setSearch] = useState("");
  const [dateFrom, setDateFrom] = useState<string>("");
  const [dateTo, setDateTo] = useState<string>("");
  const [currentPage, setCurrentPage] = useState(1);
  const logsPerPage = 20;

  useEffect(() => {
    fetchLogs();
  }, []);

  const fetchLogs = async () => {
    try {
      setLoading(true);
      const res = await apiClient.get("/admin/audit-logs");
      const data = res.data.logs ?? res.data.audit_logs ?? res.data ?? [];
      if (Array.isArray(data) && data.length > 0) {
        setLogs(data);
        setUsingSample(false);
      } else {
        setLogs(SAMPLE_LOGS);
        setUsingSample(true);
      }
    } catch {
      // Use sample data if endpoint doesn't exist
      setLogs(SAMPLE_LOGS);
      setUsingSample(true);
    } finally {
      setLoading(false);
    }
  };

  const filtered = logs.filter((log) => {
    if (actionFilter !== "all" && log.action !== actionFilter) return false;
    if (dateFrom) {
      const logDate = new Date(log.created_at);
      const fromDate = new Date(dateFrom);
      if (logDate < fromDate) return false;
    }
    if (dateTo) {
      const logDate = new Date(log.created_at);
      const toDate = new Date(dateTo + "T23:59:59");
      if (logDate > toDate) return false;
    }
    if (search) {
      const q = search.toLowerCase();
      return (
        (log.user_name ?? "").toLowerCase().includes(q) ||
        (log.resource_type ?? "").toLowerCase().includes(q) ||
        (log.action ?? "").toLowerCase().includes(q)
      );
    }
    return true;
  });

  const totalEvents = logs.length;
  const phiEvents = logs.filter(
    (l) => l.resource_type === "patient_record" || l.resource_type === "vitals_reading" || l.resource_type === "lab_values"
  ).length;
  const deniedEvents = logs.filter((l) => l.status_code === 403).length;
  const todayEvents = logs.filter((l) => {
    const d = new Date(l.created_at);
    const now = new Date();
    return d.toDateString() === now.toDateString();
  }).length;

  const totalPages = Math.ceil(filtered.length / logsPerPage);
  const paginatedLogs = filtered.slice((currentPage - 1) * logsPerPage, currentPage * logsPerPage);

  const getActionStyle = (action: string): string => {
    for (const [key, style] of Object.entries(ACTION_STYLES)) {
      if (action.toLowerCase().includes(key)) return style;
    }
    return "bg-gray-50 text-gray-700";
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Audit Logs</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            HIPAA compliance audit trail - immutable record of all PHI access.
          </p>
        </div>
        <div className="flex items-center gap-3">{usingSample && (
          <span className="rounded-full bg-amber-100 px-3 py-1 text-xs font-medium text-amber-800">
            Showing sample data
          </span>
        )}<button onClick={() => { const hdr = "Timestamp,User,Action,Resource,IP,Status"; const rows = filtered.map(l => [new Date(l.created_at).toISOString(), l.user_name ?? "", l.action, l.resource_type, l.ip_address ?? "", String(l.status_code ?? "")].map(f => '"' + String(f).replace(/"/g, '""')+'"').join(",")).join("\n"); const b = new Blob([hdr+"\n"+rows], {type:"text/csv"}); const u = URL.createObjectURL(b); const a = document.createElement("a"); a.href = u; a.download = "audit-logs.csv"; a.click(); URL.revokeObjectURL(u); }} className="inline-flex items-center gap-2 rounded-md bg-primary px-3 py-1.5 text-sm font-medium text-primary-foreground hover:bg-primary/90"><Download className="h-4 w-4" />Export CSV</button></div>
      </div>

      {/* Summary cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <p className="text-sm font-medium text-muted-foreground">Total Events</p>
          <p className="mt-2 text-3xl font-bold text-foreground">{totalEvents}</p>
        </div>
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <p className="text-sm font-medium text-muted-foreground">Today</p>
          <p className="mt-2 text-3xl font-bold text-foreground">{todayEvents}</p>
        </div>
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <p className="text-sm font-medium text-muted-foreground">PHI Access Events</p>
          <p className="mt-2 text-3xl font-bold text-blue-600">{phiEvents}</p>
        </div>
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <p className="text-sm font-medium text-muted-foreground">Denied Access</p>
          <p className="mt-2 text-3xl font-bold text-red-600">{deniedEvents}</p>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-4">
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search by user, resource, or action..."
          className="w-64 rounded-md border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
        />
        <select
          value={actionFilter}
          onChange={(e) => setActionFilter(e.target.value)}
          className="rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
        >
          <option value="all">All actions</option>
          <option value="view">View</option>
          <option value="create">Create</option>
          <option value="update">Update</option>
          <option value="delete">Delete</option>
          <option value="login">Login</option>
          <option value="export">Export</option>
        </select>
        <div className="flex items-center gap-2">
          <label className="text-xs text-muted-foreground">From:</label>
          <input
            type="date"
            value={dateFrom}
            onChange={(e) => setDateFrom(e.target.value)}
            className="rounded-md border border-input bg-background px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
          />
        </div>
        <div className="flex items-center gap-2">
          <label className="text-xs text-muted-foreground">To:</label>
          <input
            type="date"
            value={dateTo}
            onChange={(e) => setDateTo(e.target.value)}
            className="rounded-md border border-input bg-background px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
          />
        </div>
        {(dateFrom || dateTo) && (
          <button
            onClick={() => { setDateFrom(""); setDateTo(""); }}
            className="text-xs text-primary hover:underline"
          >
            Clear dates
          </button>
        )}
      </div>

      {loading && (
        <div className="flex items-center justify-center py-16">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
          <span className="ml-3 text-sm text-muted-foreground">Loading audit logs...</span>
        </div>
      )}

      {!loading && (
        <div className="rounded-lg border border-border bg-card shadow-sm">
          <div className="border-b border-border px-6 py-2">
            <div className="grid grid-cols-6 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              <span>Timestamp</span>
              <span>User</span>
              <span>Action</span>
              <span>Resource</span>
              <span>IP Address</span>
              <span>Status</span>
            </div>
          </div>
          {paginatedLogs.length === 0 ? (
            <div className="px-6 py-8 text-center text-sm text-muted-foreground">
              No audit log entries match your criteria.
            </div>
          ) : (
            <div className="divide-y divide-border">
              {paginatedLogs.map((log) => (
                <div
                  key={log.id}
                  className={`grid grid-cols-6 items-center px-6 py-3 text-sm transition-colors hover:bg-muted/50 ${
                    log.status_code === 403 ? "bg-red-50/30" : ""
                  }`}
                >
                  <span className="text-xs text-muted-foreground">
                    {new Date(log.created_at).toLocaleString()}
                  </span>
                  <div>
                    <p className="text-xs font-medium text-foreground">{log.user_name ?? "Unknown"}</p>
                    <p className="text-xs text-muted-foreground">{log.user_email ?? ""}</p>
                  </div>
                  <span>
                    <span className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${getActionStyle(log.action)}`}>
                      {log.action}
                    </span>
                  </span>
                  <span className="text-xs text-muted-foreground">
                    {log.resource_type?.replace(/_/g, " ")}
                  </span>
                  <span className="font-mono text-xs text-muted-foreground">
                    {log.ip_address ?? "N/A"}
                  </span>
                  <span>
                    {log.status_code === 403 ? (
                      <span className="inline-flex rounded-full bg-red-100 px-2 py-0.5 text-xs font-medium text-red-700">
                        Denied
                      </span>
                    ) : log.status_code && log.status_code >= 200 && log.status_code < 300 ? (
                      <span className="inline-flex rounded-full bg-green-100 px-2 py-0.5 text-xs font-medium text-green-700">
                        Success
                      </span>
                    ) : (
                      <span className="text-xs text-muted-foreground">
                        {log.status_code ?? "N/A"}
                      </span>
                    )}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <p className="text-xs text-muted-foreground">
            Showing {(currentPage - 1) * logsPerPage + 1} to {Math.min(currentPage * logsPerPage, filtered.length)} of {filtered.length} entries
          </p>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
              disabled={currentPage === 1}
              className="rounded-md border border-input px-3 py-1 text-sm hover:bg-muted disabled:opacity-50"
            >
              Previous
            </button>
            <span className="text-sm text-muted-foreground">
              Page {currentPage} of {totalPages}
            </span>
            <button
              onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
              disabled={currentPage === totalPages}
              className="rounded-md border border-input px-3 py-1 text-sm hover:bg-muted disabled:opacity-50"
            >
              Next
            </button>
          </div>
        </div>
      )}

      <div className="rounded-md border border-border bg-muted/50 px-4 py-2">
        <p className="text-xs text-muted-foreground">
          Audit logs are immutable and retained for a minimum of 6 years per HIPAA requirements.
          Logs cannot be modified or deleted.
        </p>
      </div>
    </div>
  );
}
