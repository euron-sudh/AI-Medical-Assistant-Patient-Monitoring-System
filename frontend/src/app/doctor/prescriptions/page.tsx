"use client";

import { useState, useEffect } from "react";
import apiClient from "@/lib/api-client";

interface Medication {
  id: string;
  patient_id: string;
  patient_name: string;
  drug_name: string;
  generic_name: string | null;
  dosage: string;
  frequency: string;
  route: string | null;
  start_date: string;
  end_date: string | null;
  status: string;
  reason: string | null;
  prescribed_by_name: string | null;
}

const STATUS_STYLES: Record<string, string> = {
  active: "bg-green-100 text-green-800",
  completed: "bg-gray-100 text-gray-600",
  discontinued: "bg-red-100 text-red-700",
  on_hold: "bg-amber-100 text-amber-800",
};

export default function PrescriptionsPage() {
  const [medications, setMedications] = useState<Medication[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");

  useEffect(() => {
    fetchMedications();
  }, []);

  const fetchMedications = async () => {
    try {
      setLoading(true);
      // Try fetching all medications (admin-style endpoint) or fall back to patients list
      const res = await apiClient.get("/medications");
      const data = res.data.medications ?? res.data ?? [];
      setMedications(Array.isArray(data) ? data : []);
      setError(null);
    } catch {
      // If no global medications endpoint, try fetching patients and their meds
      try {
        const patientsRes = await apiClient.get("/patients");
        const patients = patientsRes.data.patients ?? patientsRes.data ?? [];
        const allMeds: Medication[] = [];
        for (const p of (Array.isArray(patients) ? patients.slice(0, 10) : [])) {
          try {
            const medRes = await apiClient.get(`/medications/${p.user_id ?? p.id}`);
            const meds = medRes.data.medications ?? medRes.data ?? [];
            if (Array.isArray(meds)) {
              allMeds.push(
                ...meds.map((m: Medication) => ({
                  ...m,
                  patient_name: m.patient_name ?? `${p.first_name ?? ""} ${p.last_name ?? ""}`.trim(),
                }))
              );
            }
          } catch {
            // skip patients without medications
          }
        }
        setMedications(allMeds);
        setError(null);
      } catch {
        setError("Failed to load prescriptions.");
      }
    } finally {
      setLoading(false);
    }
  };

  const filtered = medications
    .filter((m) => {
      if (statusFilter !== "all" && m.status !== statusFilter) return false;
      if (search) {
        const q = search.toLowerCase();
        return (
          (m.drug_name ?? "").toLowerCase().includes(q) ||
          (m.patient_name ?? "").toLowerCase().includes(q) ||
          (m.generic_name ?? "").toLowerCase().includes(q)
        );
      }
      return true;
    })
    .sort((a, b) => new Date(b.start_date).getTime() - new Date(a.start_date).getTime());

  const activeMeds = medications.filter((m) => m.status === "active").length;
  const totalPatients = new Set(medications.map((m) => m.patient_id)).size;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Prescriptions</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Manage patient prescriptions with AI-powered drug interaction checking.
          </p>
        </div>
      </div>

      {/* Summary */}
      <div className="grid gap-4 md:grid-cols-3">
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <p className="text-sm font-medium text-muted-foreground">Total Prescriptions</p>
          <p className="mt-2 text-3xl font-bold text-foreground">{medications.length}</p>
        </div>
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <p className="text-sm font-medium text-muted-foreground">Active Medications</p>
          <p className="mt-2 text-3xl font-bold text-green-600">{activeMeds}</p>
        </div>
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <p className="text-sm font-medium text-muted-foreground">Patients on Medication</p>
          <p className="mt-2 text-3xl font-bold text-primary">{totalPatients}</p>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-4">
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search by drug name or patient..."
          className="w-64 rounded-md border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
        />
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
        >
          <option value="all">All statuses</option>
          <option value="active">Active</option>
          <option value="completed">Completed</option>
          <option value="discontinued">Discontinued</option>
          <option value="on_hold">On Hold</option>
        </select>
      </div>

      {loading && (
        <div className="flex items-center justify-center py-16">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
          <span className="ml-3 text-sm text-muted-foreground">Loading prescriptions...</span>
        </div>
      )}

      {error && (
        <div className="rounded-lg border border-destructive/30 bg-destructive/5 p-4">
          <p className="text-sm text-destructive">{error}</p>
          <button onClick={fetchMedications} className="mt-2 text-sm font-medium text-primary hover:underline">
            Retry
          </button>
        </div>
      )}

      {!loading && !error && filtered.length === 0 && (
        <div className="flex flex-col items-center justify-center rounded-lg border border-border bg-card py-16">
          <p className="text-lg font-medium text-foreground">No prescriptions found</p>
          <p className="mt-1 text-sm text-muted-foreground">
            {search || statusFilter !== "all"
              ? "Try adjusting your search or filter criteria."
              : "No prescription data available."}
          </p>
        </div>
      )}

      {!loading && !error && filtered.length > 0 && (
        <div className="rounded-lg border border-border bg-card shadow-sm">
          <div className="border-b border-border px-6 py-2">
            <div className="grid grid-cols-7 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              <span>Patient</span>
              <span>Drug Name</span>
              <span>Dosage</span>
              <span>Frequency</span>
              <span>Start Date</span>
              <span>Status</span>
              <span>Reason</span>
            </div>
          </div>
          <div className="divide-y divide-border">
            {filtered.map((m) => (
              <div
                key={m.id}
                className="grid grid-cols-7 items-center px-6 py-3 text-sm transition-colors hover:bg-muted/50"
              >
                <span className="font-medium text-foreground">{m.patient_name ?? "Unknown"}</span>
                <div>
                  <p className="font-medium text-foreground">{m.drug_name}</p>
                  {m.generic_name && (
                    <p className="text-xs text-muted-foreground">{m.generic_name}</p>
                  )}
                </div>
                <span className="text-muted-foreground">{m.dosage}</span>
                <span className="text-muted-foreground">{m.frequency}</span>
                <span className="text-muted-foreground">
                  {m.start_date ? new Date(m.start_date).toLocaleDateString() : "N/A"}
                </span>
                <span>
                  <span className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_STYLES[m.status] ?? "bg-gray-100 text-gray-600"}`}>
                    {m.status}
                  </span>
                </span>
                <span className="truncate text-muted-foreground">{m.reason ?? "--"}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
