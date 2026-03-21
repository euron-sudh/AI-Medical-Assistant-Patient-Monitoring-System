"use client";

import { useEffect, useState } from "react";

interface UserInfo {
  first_name: string;
  last_name: string;
  email: string;
  role: string;
}

export default function AdminDashboard() {
  const [user, setUser] = useState<UserInfo | null>(null);

  useEffect(() => {
    const stored = localStorage.getItem("user");
    if (stored) {
      setUser(JSON.parse(stored));
    }
  }, []);

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-foreground">
          Admin Dashboard
        </h1>
        <p className="mt-1 text-muted-foreground">
          {user ? `Logged in as ${user.first_name} ${user.last_name}` : "System administration and monitoring"}
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <p className="text-sm font-medium text-muted-foreground">Total Users</p>
          <p className="mt-2 text-3xl font-bold text-foreground">3</p>
          <p className="mt-1 text-xs text-muted-foreground">1 patient, 1 doctor, 1 admin</p>
        </div>

        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <p className="text-sm font-medium text-muted-foreground">System Status</p>
          <p className="mt-2 text-3xl font-bold text-green-600">Healthy</p>
          <p className="mt-1 text-xs text-muted-foreground">All services operational</p>
        </div>

        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <p className="text-sm font-medium text-muted-foreground">Active Alerts</p>
          <p className="mt-2 text-3xl font-bold text-foreground">0</p>
          <p className="mt-1 text-xs text-muted-foreground">No unresolved alerts</p>
        </div>

        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <p className="text-sm font-medium text-muted-foreground">AI API Usage</p>
          <p className="mt-2 text-3xl font-bold text-foreground">0</p>
          <p className="mt-1 text-xs text-muted-foreground">Tokens used today</p>
        </div>
      </div>

      <div>
        <h2 className="mb-4 text-lg font-semibold text-foreground">Administration</h2>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          <a
            href="/admin/users"
            className="rounded-lg border border-border bg-card p-6 shadow-sm transition-colors hover:bg-accent"
          >
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-blue-100 text-blue-600">
                <span className="text-lg font-bold">U</span>
              </div>
              <div>
                <p className="text-sm font-medium text-foreground">User Management</p>
                <p className="text-xs text-muted-foreground">
                  Manage users, roles, and permissions
                </p>
              </div>
            </div>
          </a>

          <a
            href="/admin/audit-logs"
            className="rounded-lg border border-border bg-card p-6 shadow-sm transition-colors hover:bg-accent"
          >
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-amber-100 text-amber-600">
                <span className="text-lg font-bold">A</span>
              </div>
              <div>
                <p className="text-sm font-medium text-foreground">HIPAA Audit Logs</p>
                <p className="text-xs text-muted-foreground">
                  Review PHI access and compliance trail
                </p>
              </div>
            </div>
          </a>

          <a
            href="/admin/system-health"
            className="rounded-lg border border-border bg-card p-6 shadow-sm transition-colors hover:bg-accent"
          >
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-green-100 text-green-600">
                <span className="text-lg font-bold">H</span>
              </div>
              <div>
                <p className="text-sm font-medium text-foreground">System Health</p>
                <p className="text-xs text-muted-foreground">
                  Infrastructure and service monitoring
                </p>
              </div>
            </div>
          </a>

          <a
            href="/admin/ai-config"
            className="rounded-lg border border-border bg-card p-6 shadow-sm transition-colors hover:bg-accent"
          >
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-purple-100 text-purple-600">
                <span className="text-lg font-bold">AI</span>
              </div>
              <div>
                <p className="text-sm font-medium text-foreground">AI Configuration</p>
                <p className="text-xs text-muted-foreground">
                  Agent settings, thresholds, and prompts
                </p>
              </div>
            </div>
          </a>

          <a
            href="/admin/ai-analytics"
            className="rounded-lg border border-border bg-card p-6 shadow-sm transition-colors hover:bg-accent"
          >
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-indigo-100 text-indigo-600">
                <span className="text-lg font-bold">$</span>
              </div>
              <div>
                <p className="text-sm font-medium text-foreground">AI Usage Analytics</p>
                <p className="text-xs text-muted-foreground">
                  Token consumption and cost tracking
                </p>
              </div>
            </div>
          </a>

          <a
            href="/admin/alerts"
            className="rounded-lg border border-border bg-card p-6 shadow-sm transition-colors hover:bg-accent"
          >
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-red-100 text-red-600">
                <span className="text-lg font-bold">!</span>
              </div>
              <div>
                <p className="text-sm font-medium text-foreground">Alert Summary</p>
                <p className="text-xs text-muted-foreground">
                  Monitoring alerts overview and metrics
                </p>
              </div>
            </div>
          </a>
        </div>
      </div>
    </div>
  );
}
