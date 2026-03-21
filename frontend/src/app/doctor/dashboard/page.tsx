"use client";

import { useEffect, useState } from "react";

interface UserInfo {
  first_name: string;
  last_name: string;
  email: string;
  role: string;
}

export default function DoctorDashboard() {
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
          Welcome{user ? `, Dr. ${user.last_name}` : ""}
        </h1>
        <p className="mt-1 text-muted-foreground">
          Clinical overview and patient management
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <p className="text-sm font-medium text-muted-foreground">Active Patients</p>
          <p className="mt-2 text-3xl font-bold text-foreground">0</p>
          <p className="mt-1 text-xs text-muted-foreground">Assigned to you</p>
        </div>

        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <p className="text-sm font-medium text-muted-foreground">Active Alerts</p>
          <p className="mt-2 text-3xl font-bold text-foreground">0</p>
          <p className="mt-1 text-xs text-green-600">All clear</p>
        </div>

        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <p className="text-sm font-medium text-muted-foreground">Today&apos;s Appointments</p>
          <p className="mt-2 text-3xl font-bold text-foreground">0</p>
          <p className="mt-1 text-xs text-muted-foreground">No appointments scheduled</p>
        </div>

        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <p className="text-sm font-medium text-muted-foreground">Pending Reports</p>
          <p className="mt-2 text-3xl font-bold text-foreground">0</p>
          <p className="mt-1 text-xs text-muted-foreground">Awaiting your review</p>
        </div>
      </div>

      <div className="rounded-lg border border-border bg-card shadow-sm">
        <div className="flex items-center justify-between border-b border-border px-6 py-4">
          <h2 className="text-lg font-semibold text-foreground">Recent Patients</h2>
          <a
            href="/doctor/patients"
            className="text-sm font-medium text-primary hover:underline"
          >
            View All
          </a>
        </div>
        <div className="flex flex-col items-center justify-center py-12 text-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-muted">
            <span className="text-lg text-muted-foreground">P</span>
          </div>
          <p className="mt-3 text-sm font-medium text-foreground">No patients assigned yet</p>
          <p className="mt-1 text-xs text-muted-foreground">
            Patients will appear here when assigned to you.
          </p>
        </div>
      </div>

      <div className="rounded-lg border border-border bg-card shadow-sm">
        <div className="flex items-center justify-between border-b border-border px-6 py-4">
          <h2 className="text-lg font-semibold text-foreground">Monitoring Alerts</h2>
          <a
            href="/doctor/monitoring"
            className="text-sm font-medium text-primary hover:underline"
          >
            Monitoring Wall
          </a>
        </div>
        <div className="flex flex-col items-center justify-center py-12 text-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-green-100">
            <span className="text-lg text-green-600">OK</span>
          </div>
          <p className="mt-3 text-sm font-medium text-foreground">No active alerts</p>
          <p className="mt-1 text-xs text-muted-foreground">
            Patient monitoring alerts will appear here in real-time.
          </p>
        </div>
      </div>
    </div>
  );
}
