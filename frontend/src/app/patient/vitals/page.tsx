"use client";

import { useEffect, useState, useCallback } from "react";
import apiClient from "@/lib/api-client";

interface VitalsReading {
  id: string;
  heart_rate: number | null;
  blood_pressure_systolic: number | null;
  blood_pressure_diastolic: number | null;
  oxygen_saturation: number | null;
  spo2: number | null;
  temperature: number | null;
  respiratory_rate: number | null;
  blood_glucose: number | null;
  recorded_at: string;
  is_anomalous: boolean;
  notes: string | null;
}

interface VitalsForm {
  heart_rate: string;
  blood_pressure_systolic: string;
  blood_pressure_diastolic: string;
  oxygen_saturation: string;
  temperature: string;
  respiratory_rate: string;
  notes: string;
}

const emptyForm: VitalsForm = {
  heart_rate: "",
  blood_pressure_systolic: "",
  blood_pressure_diastolic: "",
  oxygen_saturation: "",
  temperature: "",
  respiratory_rate: "",
  notes: "",
};

export default function VitalsPage() {
  const [vitals, setVitals] = useState<VitalsReading[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState<VitalsForm>(emptyForm);
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const getPatientId = (): string | null => {
    try {
      const userStr = localStorage.getItem("user");
      if (!userStr) return null;
      const user = JSON.parse(userStr);
      return user.id ?? user.patient_id ?? null;
    } catch {
      return null;
    }
  };

  const fetchVitals = useCallback(async () => {
    const patientId = getPatientId();
    if (!patientId) {
      setError("User not found. Please log in again.");
      setLoading(false);
      return;
    }

    try {
      const res = await apiClient.get(`/vitals/${patientId}`);
      const data = res.data?.vitals ?? res.data?.readings ?? res.data;
      setVitals(Array.isArray(data) ? data : []);
      setError(null);
    } catch (err: unknown) {
      const status =
        err && typeof err === "object" && "response" in err
          ? (err as { response?: { status?: number } }).response?.status
          : undefined;
      if (status === 404) {
        setVitals([]);
      } else {
        setError("Failed to load vitals data.");
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchVitals();
  }, [fetchVitals]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const patientId = getPatientId();
    if (!patientId) return;

    setSubmitting(true);
    setSubmitError(null);

    const payload: Record<string, unknown> = {
      patient_id: patientId,
    };

    if (form.heart_rate) payload.heart_rate = parseInt(form.heart_rate, 10);
    if (form.blood_pressure_systolic)
      payload.blood_pressure_systolic = parseInt(form.blood_pressure_systolic, 10);
    if (form.blood_pressure_diastolic)
      payload.blood_pressure_diastolic = parseInt(form.blood_pressure_diastolic, 10);
    if (form.oxygen_saturation)
      payload.oxygen_saturation = parseFloat(form.oxygen_saturation);
    if (form.temperature) payload.temperature = parseFloat(form.temperature);
    if (form.respiratory_rate)
      payload.respiratory_rate = parseInt(form.respiratory_rate, 10);
    if (form.notes) payload.notes = form.notes;

    try {
      await apiClient.post(`/vitals/${patientId}`, payload);
      setForm(emptyForm);
      setShowForm(false);
      await fetchVitals();
    } catch {
      setSubmitError("Failed to save vitals. Please try again.");
    } finally {
      setSubmitting(false);
    }
  };

  const latest = vitals.length > 0 ? vitals[0] : null;

  const hrClass = (v: number | null) => {
    if (v == null) return "";
    if (v > 100 || v < 60) return "text-red-600 font-semibold";
    return "text-foreground";
  };

  const spo2Class = (v: number | null) => {
    if (v == null) return "";
    if (v < 95) return "text-red-600 font-semibold";
    return "text-foreground";
  };

  const tempClass = (v: number | null) => {
    if (v == null) return "";
    if (v > 37.5) return "text-amber-600 font-semibold";
    if (v > 38.5) return "text-red-600 font-semibold";
    return "text-foreground";
  };

  const getSpo2 = (r: VitalsReading) => r.oxygen_saturation ?? r.spo2;

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">My Vitals</h1>
          <p className="mt-1 text-muted-foreground">
            Track and monitor your vital signs over time.
          </p>
        </div>
        <button
          onClick={() => setShowForm(!showForm)}
          className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
        >
          {showForm ? "Cancel" : "Log Vitals"}
        </button>
      </div>

      {/* Summary Cards */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <p className="text-sm font-medium text-muted-foreground">Heart Rate</p>
          <p className={`mt-2 text-3xl font-bold ${hrClass(latest?.heart_rate ?? null)}`}>
            {latest?.heart_rate ?? "--"}
            <span className="ml-1 text-sm font-normal text-muted-foreground">bpm</span>
          </p>
        </div>
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <p className="text-sm font-medium text-muted-foreground">Blood Pressure</p>
          <p className="mt-2 text-3xl font-bold text-foreground">
            {latest?.blood_pressure_systolic ?? "--"}/{latest?.blood_pressure_diastolic ?? "--"}
            <span className="ml-1 text-sm font-normal text-muted-foreground">mmHg</span>
          </p>
        </div>
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <p className="text-sm font-medium text-muted-foreground">SpO2</p>
          <p className={`mt-2 text-3xl font-bold ${spo2Class(latest ? getSpo2(latest) : null)}`}>
            {latest ? (getSpo2(latest) ?? "--") : "--"}
            <span className="ml-1 text-sm font-normal text-muted-foreground">%</span>
          </p>
        </div>
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <p className="text-sm font-medium text-muted-foreground">Temperature</p>
          <p className={`mt-2 text-3xl font-bold ${tempClass(latest?.temperature ?? null)}`}>
            {latest?.temperature ?? "--"}
            <span className="ml-1 text-sm font-normal text-muted-foreground">°C</span>
          </p>
        </div>
      </div>

      {/* Log Vitals Form */}
      {showForm && (
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-foreground">Log New Vitals</h2>
          <form onSubmit={handleSubmit} className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <div>
              <label className="block text-sm font-medium text-foreground">
                Heart Rate (bpm)
              </label>
              <input
                type="number"
                min="20"
                max="300"
                value={form.heart_rate}
                onChange={(e) => setForm({ ...form, heart_rate: e.target.value })}
                placeholder="72"
                className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-foreground">
                Systolic BP (mmHg)
              </label>
              <input
                type="number"
                min="50"
                max="300"
                value={form.blood_pressure_systolic}
                onChange={(e) =>
                  setForm({ ...form, blood_pressure_systolic: e.target.value })
                }
                placeholder="120"
                className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-foreground">
                Diastolic BP (mmHg)
              </label>
              <input
                type="number"
                min="20"
                max="200"
                value={form.blood_pressure_diastolic}
                onChange={(e) =>
                  setForm({ ...form, blood_pressure_diastolic: e.target.value })
                }
                placeholder="80"
                className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-foreground">SpO2 (%)</label>
              <input
                type="number"
                min="0"
                max="100"
                step="0.1"
                value={form.oxygen_saturation}
                onChange={(e) => setForm({ ...form, oxygen_saturation: e.target.value })}
                placeholder="98"
                className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-foreground">
                Temperature (°C)
              </label>
              <input
                type="number"
                min="30"
                max="45"
                step="0.1"
                value={form.temperature}
                onChange={(e) => setForm({ ...form, temperature: e.target.value })}
                placeholder="36.8"
                className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-foreground">
                Respiratory Rate (breaths/min)
              </label>
              <input
                type="number"
                min="4"
                max="60"
                value={form.respiratory_rate}
                onChange={(e) => setForm({ ...form, respiratory_rate: e.target.value })}
                placeholder="16"
                className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              />
            </div>
            <div className="sm:col-span-2 lg:col-span-3">
              <label className="block text-sm font-medium text-foreground">Notes</label>
              <input
                type="text"
                value={form.notes}
                onChange={(e) => setForm({ ...form, notes: e.target.value })}
                placeholder="Optional notes..."
                className="mt-1 w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              />
            </div>
            {submitError && (
              <div className="sm:col-span-2 lg:col-span-3 text-sm text-destructive">
                {submitError}
              </div>
            )}
            <div className="sm:col-span-2 lg:col-span-3">
              <button
                type="submit"
                disabled={submitting}
                className="rounded-md bg-primary px-6 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
              >
                {submitting ? "Saving..." : "Save Vitals"}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Vitals History Table */}
      <div className="rounded-lg border border-border bg-card shadow-sm">
        <div className="border-b border-border px-6 py-4">
          <h2 className="text-lg font-semibold text-foreground">Vitals History</h2>
        </div>

        {loading ? (
          <div className="px-6 py-12 text-center text-sm text-muted-foreground">
            Loading vitals data...
          </div>
        ) : error ? (
          <div className="px-6 py-12 text-center text-sm text-destructive">{error}</div>
        ) : vitals.length === 0 ? (
          <div className="px-6 py-12 text-center">
            <p className="text-sm text-muted-foreground">
              No vitals readings recorded yet. Click &quot;Log Vitals&quot; to start tracking
              your health.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border bg-muted/50">
                  <th className="px-4 py-3 text-left font-medium text-muted-foreground">
                    Date
                  </th>
                  <th className="px-4 py-3 text-left font-medium text-muted-foreground">
                    HR (bpm)
                  </th>
                  <th className="px-4 py-3 text-left font-medium text-muted-foreground">
                    BP (mmHg)
                  </th>
                  <th className="px-4 py-3 text-left font-medium text-muted-foreground">
                    SpO2 (%)
                  </th>
                  <th className="px-4 py-3 text-left font-medium text-muted-foreground">
                    Temp (°C)
                  </th>
                  <th className="px-4 py-3 text-left font-medium text-muted-foreground">
                    RR
                  </th>
                  <th className="px-4 py-3 text-left font-medium text-muted-foreground">
                    Status
                  </th>
                </tr>
              </thead>
              <tbody>
                {vitals.map((v) => (
                  <tr key={v.id} className="border-b border-border last:border-0">
                    <td className="px-4 py-3 text-muted-foreground">
                      {new Date(v.recorded_at).toLocaleString()}
                    </td>
                    <td className={`px-4 py-3 ${hrClass(v.heart_rate)}`}>
                      {v.heart_rate ?? "--"}
                    </td>
                    <td className="px-4 py-3 text-foreground">
                      {v.blood_pressure_systolic ?? "--"}/{v.blood_pressure_diastolic ?? "--"}
                    </td>
                    <td className={`px-4 py-3 ${spo2Class(getSpo2(v))}`}>
                      {getSpo2(v) ?? "--"}
                    </td>
                    <td className={`px-4 py-3 ${tempClass(v.temperature)}`}>
                      {v.temperature ?? "--"}
                    </td>
                    <td className="px-4 py-3 text-foreground">
                      {v.respiratory_rate ?? "--"}
                    </td>
                    <td className="px-4 py-3">
                      {v.is_anomalous ? (
                        <span className="inline-flex items-center rounded-full bg-red-100 px-2 py-0.5 text-xs font-medium text-red-700">
                          Anomalous
                        </span>
                      ) : (
                        <span className="inline-flex items-center rounded-full bg-green-100 px-2 py-0.5 text-xs font-medium text-green-700">
                          Normal
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
