"use client";

import { useEffect, useState } from "react";
import apiClient from "@/lib/api-client";

interface Medication {
  id: string;
  name: string;
  drug_name?: string;
  generic_name?: string;
  dosage: string;
  frequency: string;
  route: string | null;
  start_date: string;
  end_date: string | null;
  status: string;
  reason: string | null;
  side_effects: string | null;
  prescribed_by: string | null;
  refills_remaining: number | null;
  notes: string | null;
  created_at: string;
}

const statusColors: Record<string, string> = {
  active: "bg-green-100 text-green-700 border-green-200",
  completed: "bg-gray-100 text-gray-700 border-gray-200",
  discontinued: "bg-red-100 text-red-700 border-red-200",
  on_hold: "bg-amber-100 text-amber-700 border-amber-200",
};

const statusDot: Record<string, string> = {
  active: "bg-green-500",
  completed: "bg-gray-400",
  discontinued: "bg-red-500",
  on_hold: "bg-amber-500",
};

export default function MedicationsPage() {
  const [medications, setMedications] = useState<Medication[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchMedications();
  }, []);

  const fetchMedications = async () => {
    try {
      const userStr = localStorage.getItem("user");
      if (!userStr) {
        setError("User not found. Please log in again.");
        setLoading(false);
        return;
      }
      const user = JSON.parse(userStr);
      const patientId = user.id ?? user.patient_id;

      const res = await apiClient.get(`/medications/${patientId}`);
      const data = res.data?.medications ?? res.data;
      setMedications(Array.isArray(data) ? data : []);
    } catch (err: unknown) {
      const status =
        err && typeof err === "object" && "response" in err
          ? (err as { response?: { status?: number } }).response?.status
          : undefined;
      if (status === 404) {
        setMedications([]);
      } else {
        setError("Failed to load medications.");
      }
    } finally {
      setLoading(false);
    }
  };

  const activeMeds = medications.filter((m) => m.status === "active");
  const otherMeds = medications.filter((m) => m.status !== "active");
  const refillsNeeded = medications.filter(
    (m) => m.status === "active" && m.refills_remaining != null && m.refills_remaining <= 1
  );

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Medications</h1>
        <p className="mt-1 text-muted-foreground">
          View your active medications, dosage schedules, and interaction alerts.
        </p>
      </div>

      {/* Summary Cards */}
      <div className="grid gap-6 md:grid-cols-3">
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <p className="text-sm font-medium text-muted-foreground">Active Medications</p>
          <p className="mt-2 text-3xl font-bold text-foreground">{activeMeds.length}</p>
        </div>
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <p className="text-sm font-medium text-muted-foreground">Refills Needed</p>
          <p className="mt-2 text-3xl font-bold text-foreground">{refillsNeeded.length}</p>
        </div>
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <p className="text-sm font-medium text-muted-foreground">Total on File</p>
          <p className="mt-2 text-3xl font-bold text-foreground">{medications.length}</p>
        </div>
      </div>

      {loading ? (
        <div className="rounded-lg border border-border bg-card p-12 text-center">
          <p className="text-sm text-muted-foreground">Loading medications...</p>
        </div>
      ) : error ? (
        <div className="rounded-lg border border-border bg-card p-12 text-center">
          <p className="text-sm text-destructive">{error}</p>
        </div>
      ) : medications.length === 0 ? (
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-foreground">Medication List</h2>
          <p className="mt-2 text-sm text-muted-foreground">
            No medications on file. Your prescribed medications and dosage schedules will
            appear here.
          </p>
        </div>
      ) : (
        <>
          {/* Active Medications */}
          {activeMeds.length > 0 && (
            <div>
              <h2 className="mb-3 text-lg font-semibold text-foreground">
                Active Medications
              </h2>
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {activeMeds.map((med) => (
                  <MedicationCard key={med.id} med={med} />
                ))}
              </div>
            </div>
          )}

          {/* Other Medications */}
          {otherMeds.length > 0 && (
            <div>
              <h2 className="mb-3 text-lg font-semibold text-foreground">
                Past / Inactive Medications
              </h2>
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {otherMeds.map((med) => (
                  <MedicationCard key={med.id} med={med} />
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}

function MedicationCard({ med }: { med: Medication }) {
  const drugName = med.name ?? med.drug_name ?? "Unknown Medication";

  return (
    <div
      className={`rounded-lg border bg-card p-5 shadow-sm ${
        med.status === "active" ? "border-green-200" : "border-border"
      }`}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <h3 className="text-sm font-semibold text-foreground">{drugName}</h3>
          {med.generic_name && (
            <p className="text-xs text-muted-foreground">{med.generic_name}</p>
          )}
        </div>
        <span
          className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium ${
            statusColors[med.status] ?? "bg-gray-100 text-gray-700"
          }`}
        >
          <span
            className={`inline-block h-1.5 w-1.5 rounded-full ${
              statusDot[med.status] ?? "bg-gray-400"
            }`}
          />
          {med.status}
        </span>
      </div>

      <div className="mt-3 space-y-1.5 text-sm">
        <div className="flex justify-between">
          <span className="text-muted-foreground">Dosage</span>
          <span className="font-medium text-foreground">{med.dosage}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-muted-foreground">Frequency</span>
          <span className="font-medium text-foreground">{med.frequency}</span>
        </div>
        {med.route && (
          <div className="flex justify-between">
            <span className="text-muted-foreground">Route</span>
            <span className="font-medium text-foreground">{med.route}</span>
          </div>
        )}
        <div className="flex justify-between">
          <span className="text-muted-foreground">Started</span>
          <span className="text-foreground">
            {new Date(med.start_date).toLocaleDateString()}
          </span>
        </div>
        {med.end_date && (
          <div className="flex justify-between">
            <span className="text-muted-foreground">Ended</span>
            <span className="text-foreground">
              {new Date(med.end_date).toLocaleDateString()}
            </span>
          </div>
        )}
        {med.refills_remaining != null && (
          <div className="flex justify-between">
            <span className="text-muted-foreground">Refills</span>
            <span
              className={`font-medium ${
                med.refills_remaining <= 1 ? "text-amber-600" : "text-foreground"
              }`}
            >
              {med.refills_remaining} remaining
            </span>
          </div>
        )}
      </div>

      {med.reason && (
        <p className="mt-3 text-xs text-muted-foreground">
          <span className="font-medium">Reason:</span> {med.reason}
        </p>
      )}
    </div>
  );
}
