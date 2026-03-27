"use client";

import { useState, useEffect } from "react";
import apiClient from "@/lib/api-client";
import { Settings as SettingsIcon, Shield, ToggleLeft, CheckCircle2, Server, RefreshCw } from "lucide-react";

export default function SettingsPage() {
  const [currentUser, setCurrentUser] = useState<{ first_name?: string; last_name?: string; role?: string; email?: string } | null>(null);

  useEffect(() => {
    try {
      const user = JSON.parse(localStorage.getItem("user") ?? "null");
      setCurrentUser(user);
    } catch {
      setCurrentUser(null);
    }
  }, []);

  const platformSettings = [
    { label: "Platform Name", value: "MedAssist AI", description: "Agentic AI Medical Assistant & Patient Monitoring System" },
    { label: "Version", value: "1.0.0", description: "Current deployed version" },
    { label: "Environment", value: typeof window !== "undefined" && window.location.hostname.includes("render") ? "Production" : "Development", description: "Current runtime environment" },
    { label: "Backend Framework", value: "Flask 3+ / Python 3.11+", description: "RESTful API + WebSocket (Flask-SocketIO)" },
    { label: "Frontend Framework", value: "Next.js 14+ / React 18+", description: "App Router with TypeScript strict mode" },
    { label: "Database", value: "PostgreSQL 16", description: "Primary relational database" },
  ];

  const securitySettings = [
    { label: "JWT Access Token Expiry", value: "15 minutes", enabled: true },
    { label: "JWT Refresh Token Expiry", value: "7 days", enabled: true },
    { label: "MFA for Providers", value: "Required", enabled: true },
    { label: "MFA for Patients", value: "Optional", enabled: false },
    { label: "Session Timeout (Admin)", value: "15 minutes", enabled: true },
    { label: "Rate Limiting", value: "Enabled", enabled: true },
    { label: "CORS Protection", value: "Enabled", enabled: true },
    { label: "TLS 1.3", value: "Required", enabled: true },
  ];

  const featureFlags = [
    { name: "AI Chat Assistant", enabled: true, description: "Patient and doctor AI chat" },
    { name: "Voice Interaction", enabled: true, description: "Whisper STT + TTS voice sessions" },
    { name: "Telemedicine Video", enabled: true, description: "Daily.co WebRTC video calls" },
    { name: "Real-time Monitoring", enabled: true, description: "WebSocket vitals monitoring" },
    { name: "Drug Interaction Checking", enabled: true, description: "AI-powered medication analysis" },
    { name: "AI Report Analysis", enabled: true, description: "Medical report AI interpretation" },
    { name: "Care Plan Generation", enabled: true, description: "AI-generated care plans" },
    { name: "Ambient Clinical Notes", enabled: false, description: "Auto SOAP notes from consultations" },
    { name: "Multi-language Support", enabled: false, description: "50+ languages via Whisper" },
    { name: "Push Notifications", enabled: false, description: "Browser push via Web Push API" },
  ];

  const complianceSettings = [
    { label: "HIPAA Audit Logging", value: "Enabled", status: "compliant" },
    { label: "PHI Encryption at Rest", value: "AES-256", status: "compliant" },
    { label: "PHI Encryption in Transit", value: "TLS 1.3", status: "compliant" },
    { label: "Audit Log Retention", value: "6+ years", status: "compliant" },
    { label: "Data Retention Policy", value: "7 years", status: "compliant" },
    { label: "PII Redaction for AI", value: "Enabled", status: "compliant" },
    { label: "Backup Frequency", value: "Daily", status: "compliant" },
    { label: "RPO", value: "1 hour", status: "compliant" },
    { label: "RTO", value: "4 hours", status: "compliant" },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Settings</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Platform configuration, security settings, and feature flags.
        </p>
      </div>

      {/* Current Admin Info */}
      {currentUser && (
        <div className="rounded-lg border border-primary/20 bg-primary/5 p-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary/10">
              <span className="text-sm font-bold text-primary">
                {(currentUser.first_name ?? "A")[0]}
              </span>
            </div>
            <div>
              <p className="font-medium text-foreground">
                {currentUser.first_name} {currentUser.last_name}
              </p>
              <p className="text-xs text-muted-foreground">
                {currentUser.email} / Role: {currentUser.role ?? "admin"}
              </p>
            </div>
          </div>
        </div>
      )}

      <div className="grid gap-6 md:grid-cols-2">
        {/* Platform Settings */}
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-foreground">Platform</h2>
          <div className="mt-4 space-y-4">
            {platformSettings.map((s) => (
              <div key={s.label} className="flex items-start justify-between gap-2">
                <div>
                  <p className="text-sm font-medium text-foreground">{s.label}</p>
                  <p className="text-xs text-muted-foreground">{s.description}</p>
                </div>
                <span className="shrink-0 rounded-md bg-muted px-2.5 py-1 text-xs font-mono font-medium text-foreground">
                  {s.value}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Security Settings */}
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-foreground">Security</h2>
          <div className="mt-4 space-y-3">
            {securitySettings.map((s) => (
              <div key={s.label} className="flex items-center justify-between">
                <span className="text-sm text-foreground">{s.label}</span>
                <div className="flex items-center gap-2">
                  <span className="text-xs font-medium text-muted-foreground">{s.value}</span>
                  <span className={`h-2 w-2 rounded-full ${s.enabled ? "bg-green-500" : "bg-gray-400"}`} />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Feature Flags */}
      <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-foreground">Feature Flags</h2>
        <p className="mt-1 text-xs text-muted-foreground">Feature availability status (display only)</p>
        <div className="mt-4 grid gap-3 md:grid-cols-2">
          {featureFlags.map((f) => (
            <div
              key={f.name}
              className={`flex items-center justify-between rounded-md border p-3 ${
                f.enabled ? "border-green-200 bg-green-50/30" : "border-border bg-muted/30"
              }`}
            >
              <div>
                <p className="text-sm font-medium text-foreground">{f.name}</p>
                <p className="text-xs text-muted-foreground">{f.description}</p>
              </div>
              <span
                className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${
                  f.enabled
                    ? "bg-green-100 text-green-800"
                    : "bg-gray-100 text-gray-600"
                }`}
              >
                {f.enabled ? "Enabled" : "Disabled"}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* HIPAA Compliance */}
      <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-foreground">HIPAA Compliance</h2>
        <div className="mt-4 grid gap-3 md:grid-cols-3">
          {complianceSettings.map((s) => (
            <div key={s.label} className="flex items-center justify-between rounded-md border border-green-200 bg-green-50/30 p-3">
              <div>
                <p className="text-sm font-medium text-foreground">{s.label}</p>
                <p className="text-xs text-muted-foreground">{s.value}</p>
              </div>
              <span className="inline-flex items-center gap-1 text-xs font-medium text-green-700">
                <span className="h-1.5 w-1.5 rounded-full bg-green-500" />
                OK
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Infrastructure */}
      <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-foreground">Infrastructure</h2>
        <div className="mt-4 grid gap-4 md:grid-cols-3">
          <div>
            <p className="text-xs font-medium text-muted-foreground">Containerization</p>
            <p className="mt-0.5 text-sm text-foreground">Docker + Docker Compose</p>
          </div>
          <div>
            <p className="text-xs font-medium text-muted-foreground">Orchestration</p>
            <p className="mt-0.5 text-sm text-foreground">Kubernetes (EKS)</p>
          </div>
          <div>
            <p className="text-xs font-medium text-muted-foreground">CI/CD</p>
            <p className="mt-0.5 text-sm text-foreground">GitHub Actions</p>
          </div>
          <div>
            <p className="text-xs font-medium text-muted-foreground">Monitoring</p>
            <p className="mt-0.5 text-sm text-foreground">Prometheus + Grafana</p>
          </div>
          <div>
            <p className="text-xs font-medium text-muted-foreground">Log Management</p>
            <p className="mt-0.5 text-sm text-foreground">ELK Stack</p>
          </div>
          <div>
            <p className="text-xs font-medium text-muted-foreground">IaC</p>
            <p className="mt-0.5 text-sm text-foreground">Terraform</p>
          </div>
        </div>
      </div>
    </div>
  );
}
