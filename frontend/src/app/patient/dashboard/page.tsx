"use client";

import { useEffect, useState } from "react";

interface UserInfo {
  first_name: string;
  last_name: string;
  email: string;
  role: string;
}

export default function PatientDashboard() {
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
          Welcome{user ? `, ${user.first_name}` : ""}
        </h1>
        <p className="mt-1 text-muted-foreground">
          Your personal health dashboard
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-green-100 text-green-600">
              <span className="text-lg font-bold">V</span>
            </div>
            <div>
              <p className="text-sm font-medium text-muted-foreground">Latest Vitals</p>
              <p className="text-xl font-bold text-foreground">Normal</p>
            </div>
          </div>
          <p className="mt-4 text-sm text-muted-foreground">
            No recent vitals recorded. Log your vitals to track your health.
          </p>
        </div>

        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-blue-100 text-blue-600">
              <span className="text-lg font-bold">A</span>
            </div>
            <div>
              <p className="text-sm font-medium text-muted-foreground">Appointments</p>
              <p className="text-xl font-bold text-foreground">0 Upcoming</p>
            </div>
          </div>
          <p className="mt-4 text-sm text-muted-foreground">
            No upcoming appointments. Schedule one with your care team.
          </p>
        </div>

        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-purple-100 text-purple-600">
              <span className="text-lg font-bold">M</span>
            </div>
            <div>
              <p className="text-sm font-medium text-muted-foreground">Medications</p>
              <p className="text-xl font-bold text-foreground">0 Active</p>
            </div>
          </div>
          <p className="mt-4 text-sm text-muted-foreground">
            No active medications on file.
          </p>
        </div>
      </div>

      <div>
        <h2 className="mb-4 text-lg font-semibold text-foreground">Quick Actions</h2>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <a
            href="/patient/symptoms"
            className="flex items-center gap-3 rounded-lg border border-border bg-card p-4 shadow-sm transition-colors hover:bg-accent"
          >
            <span className="flex h-9 w-9 items-center justify-center rounded-md bg-primary/10 text-sm font-bold text-primary">
              S
            </span>
            <div>
              <p className="text-sm font-medium text-foreground">Check Symptoms</p>
              <p className="text-xs text-muted-foreground">AI-powered analysis</p>
            </div>
          </a>
          <a
            href="/patient/vitals"
            className="flex items-center gap-3 rounded-lg border border-border bg-card p-4 shadow-sm transition-colors hover:bg-accent"
          >
            <span className="flex h-9 w-9 items-center justify-center rounded-md bg-green-100 text-sm font-bold text-green-600">
              V
            </span>
            <div>
              <p className="text-sm font-medium text-foreground">Log Vitals</p>
              <p className="text-xs text-muted-foreground">Record your readings</p>
            </div>
          </a>
          <a
            href="/patient/reports"
            className="flex items-center gap-3 rounded-lg border border-border bg-card p-4 shadow-sm transition-colors hover:bg-accent"
          >
            <span className="flex h-9 w-9 items-center justify-center rounded-md bg-orange-100 text-sm font-bold text-orange-600">
              R
            </span>
            <div>
              <p className="text-sm font-medium text-foreground">View Reports</p>
              <p className="text-xs text-muted-foreground">Medical reports & labs</p>
            </div>
          </a>
          <a
            href="/patient/chat"
            className="flex items-center gap-3 rounded-lg border border-border bg-card p-4 shadow-sm transition-colors hover:bg-accent"
          >
            <span className="flex h-9 w-9 items-center justify-center rounded-md bg-blue-100 text-sm font-bold text-blue-600">
              C
            </span>
            <div>
              <p className="text-sm font-medium text-foreground">AI Chat</p>
              <p className="text-xs text-muted-foreground">Ask a health question</p>
            </div>
          </a>
        </div>
      </div>

      <div className="rounded-md border border-border bg-muted/50 px-4 py-3">
        <p className="text-xs text-muted-foreground">
          AI-generated content is for informational purposes only and is not a substitute
          for professional medical advice, diagnosis, or treatment. Always consult your
          healthcare provider.
        </p>
      </div>
    </div>
  );
}
