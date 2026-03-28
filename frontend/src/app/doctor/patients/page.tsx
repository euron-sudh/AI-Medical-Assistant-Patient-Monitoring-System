"use client";

import { useState, useEffect } from "react";
import apiClient from "@/lib/api-client";

interface Patient {
  id: string;
  user_id: string;
  first_name: string;
  last_name: string;
  email: string;
  gender: string;
  blood_type: string;
  date_of_birth: string;
  height_cm: number | null;
  weight_kg: number | null;
  assigned_doctor_name: string | null;
  phone: string | null;
}

export default function PatientsPage() {
  const [patients, setPatients] = useState<Patient[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [expandedId, setExpandedId] = useState<string | null>(null);

  useEffect(() => {
    fetchPatients();
  }, []);

  const fetchPatients = async () => {
    try {
      setLoading(true);
      const res = await apiClient.get("/patients");
      const data = res.data.patients ?? res.data ?? [];
      setPatients(Array.isArray(data) ? data : []);
    } catch (err: unknown) {
      const msg =
        err && typeof err === "object" && "response" in err
          ? `Failed to load patients (${(err as { response?: { status?: number } }).response?.status ?? "unknown"})`
          : "Failed to load patients";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const filtered = patients.filter((p) => {
    const name = `${p.first_name ?? ""} ${p.last_name ?? ""}`.toLowerCase();
    const email = (p.email ?? "").toLowerCase();
    const q = search.toLowerCase();
    return name.includes(q) || email.includes(q);
  });

  const getAge = (dob: string): string => {
    if (!dob) return "N/A";
    const diff = Date.now() - new Date(dob).getTime();
    return `${Math.floor(diff / (365.25 * 24 * 60 * 60 * 1000))}y`;
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Patient List</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            View and manage your assigned patients.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <span className="rounded-full bg-primary/10 px-3 py-1 text-xs font-medium text-primary">
            {filtered.length} patient{filtered.length !== 1 ? "s" : ""}
          </span>
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by name or email..."
            className="w-64 rounded-md border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
          />
        </div>
      </div>

      {loading && (
        <div className="flex items-center justify-center py-16">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
          <span className="ml-3 text-sm text-muted-foreground">Loading patients...</span>
        </div>
      )}

      {error && (
        <div className="rounded-lg border border-destructive/30 bg-destructive/5 p-4">
          <p className="text-sm text-destructive">{error}</p>
          <button
            onClick={fetchPatients}
            className="mt-2 text-sm font-medium text-primary hover:underline"
          >
            Retry
          </button>
        </div>
      )}

      {!loading && !error && filtered.length === 0 && (
        <div className="flex flex-col items-center justify-center rounded-lg border border-border bg-card py-16">
          <p className="text-lg font-medium text-foreground">No patients found</p>
          <p className="mt-1 text-sm text-muted-foreground">
            {search ? "Try adjusting your search criteria." : "No patient data available."}
          </p>
        </div>
      )}

      {!loading && !error && filtered.length > 0 && (
        <div className="rounded-lg border border-border bg-card shadow-sm">
          <div className="border-b border-border px-6 py-3">
            <div className="grid grid-cols-6 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              <span>Patient Name</span>
              <span>Email</span>
              <span>Age / Gender</span>
              <span>Blood Type</span>
              <span>Assigned Doctor</span>
              <span className="text-right">Actions</span>
            </div>
          </div>
          <div className="divide-y divide-border">
            {filtered.map((p) => (
              <div key={p.id}>
                <div
                  className="grid cursor-pointer grid-cols-6 items-center px-6 py-3 text-sm transition-colors hover:bg-muted/50"
                  onClick={() => setExpandedId(expandedId === p.id ? null : p.id)}
                >
                  <span className="font-medium text-foreground">
                    {p.first_name} {p.last_name}
                  </span>
                  <span className="text-muted-foreground">{p.email ?? "N/A"}</span>
                  <span className="text-muted-foreground">
                    {getAge(p.date_of_birth)} / {p.gender ?? "N/A"}
                  </span>
                  <span>
                    {p.blood_type ? (
                      <span className="inline-flex items-center rounded-full bg-red-50 px-2.5 py-0.5 text-xs font-medium text-red-700">
                        {p.blood_type}
                      </span>
                    ) : (
                      <span className="text-muted-foreground">N/A</span>
                    )}
                  </span>
                  <span className="text-muted-foreground">
                    {p.assigned_doctor_name ?? "Unassigned"}
                  </span>
                  <span className="flex items-center justify-end gap-2">
                    <a
                      href={`/doctor/patients/${p.user_id ?? p.id}`}
                      onClick={(e) => e.stopPropagation()}
                      className="text-xs font-medium text-primary hover:underline"
                    >
                      View
                    </a>
                    <button className="text-xs font-medium text-muted-foreground hover:text-foreground">
                      {expandedId === p.id ? "Collapse" : "Expand"}
                    </button>
                  </span>
                </div>

                {expandedId === p.id && (
                  <div className="border-t border-border bg-muted/30 px-6 py-4">
                    <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
                      <div>
                        <p className="text-xs font-medium text-muted-foreground">Date of Birth</p>
                        <p className="mt-0.5 text-sm text-foreground">
                          {p.date_of_birth
                            ? new Date(p.date_of_birth).toLocaleDateString()
                            : "N/A"}
                        </p>
                      </div>
                      <div>
                        <p className="text-xs font-medium text-muted-foreground">Height</p>
                        <p className="mt-0.5 text-sm text-foreground">
                          {p.height_cm ? `${p.height_cm} cm` : "N/A"}
                        </p>
                      </div>
                      <div>
                        <p className="text-xs font-medium text-muted-foreground">Weight</p>
                        <p className="mt-0.5 text-sm text-foreground">
                          {p.weight_kg ? `${p.weight_kg} kg` : "N/A"}
                        </p>
                      </div>
                      <div>
                        <p className="text-xs font-medium text-muted-foreground">Phone</p>
                        <p className="mt-0.5 text-sm text-foreground">{p.phone ?? "N/A"}</p>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
