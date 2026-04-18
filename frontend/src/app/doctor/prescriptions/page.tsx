"use client";

import { useState, useEffect } from "react";
import apiClient from "@/lib/api-client";
import { extractPatientList } from "@/lib/patient-list";
import { Pill, Plus, AlertTriangle, Search, X, CheckCircle, Clock, Users } from "lucide-react";

interface Medication { id: string; patient_id: string; patient_name: string; drug_name: string; name?: string; generic_name: string | null; dosage: string; frequency: string; route: string | null; start_date: string; end_date: string | null; status: string; reason: string | null; prescribed_by_name: string | null; }
interface Patient { id: string; user_id: string; first_name?: string | null; last_name?: string | null; name?: string | null; email?: string | null; }

function normalizePatientFromApi(raw: Record<string, unknown>): Patient {
  const userId = String(raw.user_id ?? raw.userId ?? "").trim();
  const profileId = String(raw.id ?? "").trim();
  return {
    id: profileId || userId,
    user_id: userId || profileId,
    first_name: (raw.first_name ?? raw.firstName ?? null) as string | null,
    last_name: (raw.last_name ?? raw.lastName ?? null) as string | null,
    name: (raw.name ?? null) as string | null,
    email: (raw.email ?? null) as string | null,
  };
}

function patientDropdownLabel(p: Patient): string {
  const fn = p.first_name?.trim();
  const ln = p.last_name?.trim();
  if (fn || ln) return [fn, ln].filter(Boolean).join(" ");
  if (p.name?.trim()) return p.name.trim();
  if (p.email?.trim()) return p.email.trim();
  if (p.user_id) return `Patient (${p.user_id.slice(0, 8)}…)`;
  return "Patient";
}
interface InteractionWarning { drug1: string; drug2: string; severity: string; description: string; }
interface PrescriptionFormData { patient_id: string; drug_name: string; generic_name: string; dosage: string; frequency: string; route: string; reason: string; start_date: string; end_date: string; }

const STATUS_STYLES: Record<string, string> = { active: "bg-green-100 text-green-800", completed: "bg-gray-100 text-gray-600", discontinued: "bg-red-100 text-red-700", on_hold: "bg-amber-100 text-amber-800" };

const KNOWN_INTERACTIONS: InteractionWarning[] = [
  { drug1: "warfarin", drug2: "aspirin", severity: "high", description: "Increased risk of bleeding when combined." },
  { drug1: "warfarin", drug2: "amiodarone", severity: "high", description: "Amiodarone increases warfarin levels significantly." },
  { drug1: "metformin", drug2: "contrast dye", severity: "high", description: "Risk of lactic acidosis with iodinated contrast." },
  { drug1: "lisinopril", drug2: "potassium", severity: "medium", description: "ACE inhibitors may increase potassium levels." },
  { drug1: "simvastatin", drug2: "amiodarone", severity: "high", description: "Increased risk of myopathy/rhabdomyolysis." },
  { drug1: "ciprofloxacin", drug2: "theophylline", severity: "high", description: "Ciprofloxacin increases theophylline levels." },
];

const FREQUENCIES = ["Once daily", "Twice daily", "Three times daily", "Every 8 hours", "Every 12 hours", "As needed", "Weekly"];
const ROUTES = ["Oral", "IV", "IM", "Subcutaneous", "Topical", "Inhaled", "Sublingual"];

const emptyForm: PrescriptionFormData = { patient_id: "", drug_name: "", generic_name: "", dosage: "", frequency: "", route: "", reason: "", start_date: new Date().toISOString().split("T")[0], end_date: "" };

export default function PrescriptionsPage() {
  const [medications, setMedications] = useState<Medication[]>([]);
  const [patients, setPatients] = useState<Patient[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState<PrescriptionFormData>({ ...emptyForm });
  const [formSubmitting, setFormSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [interactions, setInteractions] = useState<InteractionWarning[]>([]);

  useEffect(() => {
    fetchMedications();
  }, []);

  useEffect(() => {
    if (form.drug_name && form.patient_id) {
      const patientMeds = medications.filter((m) => m.patient_id === form.patient_id && m.status === "active").map((m) => m.drug_name.toLowerCase());
      const nd = form.drug_name.toLowerCase();
      const found: InteractionWarning[] = [];
      for (const ix of KNOWN_INTERACTIONS) {
        for (const ex of patientMeds) {
          if ((nd.includes(ix.drug1) && ex.includes(ix.drug2)) || (nd.includes(ix.drug2) && ex.includes(ix.drug1)))
            found.push({ ...ix, drug1: form.drug_name, drug2: ex });
        }
      }
      setInteractions(found);
    } else { setInteractions([]); }
  }, [form.drug_name, form.patient_id, medications]);

  const fetchMedications = async () => {
    try {
      setLoading(true);
      const pR = await apiClient.get("/patients");
      const rawList = extractPatientList(pR.data);
      const normalized = rawList.map((row) => normalizePatientFromApi(row));
      setPatients(normalized);

      const all: Medication[] = [];
      for (const p of normalized.slice(0, 20)) {
        const pid = p.user_id || p.id;
        if (!pid) continue;
        try {
          const mR = await apiClient.get(`/medications/${pid}`);
          const ms = mR.data.medications ?? mR.data ?? [];
          if (Array.isArray(ms))
            all.push(
              ...ms.map((m: Medication) => ({
                ...m,
                drug_name: m.drug_name ?? m.name ?? "",
                patient_name: m.patient_name ?? patientDropdownLabel(p),
                patient_id: m.patient_id ?? pid,
              }))
            );
        } catch {
          /* patient may have no medications */
        }
      }
      setMedications(all);
      setError(null);
    } catch {
      setError("Failed to load prescriptions.");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.patient_id || !form.drug_name || !form.dosage || !form.frequency) { setFormError("Fill all required fields."); return; }
    setFormSubmitting(true); setFormError(null);
    try {
      await apiClient.post(`/medications/${form.patient_id}`, { drug_name: form.drug_name, generic_name: form.generic_name || null, dosage: form.dosage, frequency: form.frequency, route: form.route || null, reason: form.reason || null, start_date: form.start_date, end_date: form.end_date || null });
      setForm({ ...emptyForm }); setShowForm(false); setInteractions([]); fetchMedications();
    } catch { setFormError("Failed to create prescription."); }
    finally { setFormSubmitting(false); }
  };

  const filtered = medications.filter((m) => { if (statusFilter !== "all" && m.status !== statusFilter) return false; if (search) { const q = search.toLowerCase(); return (m.drug_name ?? "").toLowerCase().includes(q) || (m.patient_name ?? "").toLowerCase().includes(q) || (m.generic_name ?? "").toLowerCase().includes(q); } return true; }).sort((a, b) => new Date(b.start_date).getTime() - new Date(a.start_date).getTime());
  const activeMeds = medications.filter((m) => m.status === "active");
  const totalPatients = new Set(medications.map((m) => m.patient_id)).size;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div><h1 className="text-2xl font-bold text-foreground">Prescriptions</h1><p className="mt-1 text-sm text-muted-foreground">Manage patient prescriptions with drug interaction checking.</p></div>
        <button onClick={() => setShowForm(!showForm)} className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90">
          {showForm ? <X className="h-4 w-4" /> : <Plus className="h-4 w-4" />} {showForm ? "Cancel" : "New Prescription"}
        </button>
      </div>

      {showForm && (
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-foreground">New Prescription</h2>
          <form onSubmit={handleSubmit} className="mt-4 space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
              <div><label className="mb-1 block text-sm font-medium text-foreground">Patient *</label><select value={form.patient_id} onChange={(e) => setForm({...form, patient_id: e.target.value})} className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring" required><option value="">Select patient...</option>{patients.map((p) => { const v = p.user_id || p.id; return (<option key={v} value={v}>{patientDropdownLabel(p)}</option>); })}</select></div>
              <div><label className="mb-1 block text-sm font-medium text-foreground">Drug Name *</label><input type="text" value={form.drug_name} onChange={(e) => setForm({...form, drug_name: e.target.value})} placeholder="e.g., Metformin" className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring" required /></div>
              <div><label className="mb-1 block text-sm font-medium text-foreground">Generic Name</label><input type="text" value={form.generic_name} onChange={(e) => setForm({...form, generic_name: e.target.value})} className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring" /></div>
              <div><label className="mb-1 block text-sm font-medium text-foreground">Dosage *</label><input type="text" value={form.dosage} onChange={(e) => setForm({...form, dosage: e.target.value})} placeholder="e.g., 500mg" className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring" required /></div>
              <div><label className="mb-1 block text-sm font-medium text-foreground">Frequency *</label><select value={form.frequency} onChange={(e) => setForm({...form, frequency: e.target.value})} className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring" required><option value="">Select...</option>{FREQUENCIES.map((f) => (<option key={f} value={f}>{f}</option>))}</select></div>
              <div><label className="mb-1 block text-sm font-medium text-foreground">Route</label><select value={form.route} onChange={(e) => setForm({...form, route: e.target.value})} className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"><option value="">Select...</option>{ROUTES.map((r) => (<option key={r} value={r}>{r}</option>))}</select></div>
              <div><label className="mb-1 block text-sm font-medium text-foreground">Start Date</label><input type="date" value={form.start_date} onChange={(e) => setForm({...form, start_date: e.target.value})} className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring" /></div>
              <div><label className="mb-1 block text-sm font-medium text-foreground">End Date</label><input type="date" value={form.end_date} onChange={(e) => setForm({...form, end_date: e.target.value})} className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring" /></div>
            </div>
            <div><label className="mb-1 block text-sm font-medium text-foreground">Reason</label><input type="text" value={form.reason} onChange={(e) => setForm({...form, reason: e.target.value})} placeholder="Reason..." className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring" /></div>
            {interactions.length > 0 && (<div className="rounded-lg border border-amber-300 bg-amber-50 p-4"><div className="flex items-center gap-2"><AlertTriangle className="h-5 w-5 text-amber-600" /><h3 className="text-sm font-semibold text-amber-800">Drug Interaction Warning</h3></div><div className="mt-2 space-y-2">{interactions.map((w, i) => (<div key={i} className="flex items-start gap-2 text-sm"><span className={`mt-0.5 inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${w.severity === "critical" ? "bg-red-100 text-red-800" : w.severity === "high" ? "bg-orange-100 text-orange-800" : "bg-yellow-100 text-yellow-800"}`}>{w.severity}</span><div><p className="font-medium text-amber-900">{w.drug1} + {w.drug2}</p><p className="text-amber-700">{w.description}</p></div></div>))}</div></div>)}
            {formError && <p className="text-sm text-destructive">{formError}</p>}
            <div className="flex justify-end gap-2"><button type="button" onClick={() => {setShowForm(false);setForm({...emptyForm});setInteractions([]);}} className="rounded-md border border-input px-4 py-2 text-sm font-medium hover:bg-muted">Cancel</button><button type="submit" disabled={formSubmitting} className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50">{formSubmitting ? "Creating..." : "Create Prescription"}</button></div>
          </form>
        </div>
      )}

      <div className="grid gap-4 md:grid-cols-3">
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm"><div className="flex items-center gap-2"><Pill className="h-5 w-5 text-blue-500" /><p className="text-sm font-medium text-muted-foreground">Total Prescriptions</p></div><p className="mt-2 text-3xl font-bold text-foreground">{medications.length}</p></div>
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm"><div className="flex items-center gap-2"><CheckCircle className="h-5 w-5 text-green-500" /><p className="text-sm font-medium text-muted-foreground">Active</p></div><p className="mt-2 text-3xl font-bold text-green-600">{activeMeds.length}</p></div>
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm"><div className="flex items-center gap-2"><Users className="h-5 w-5 text-purple-500" /><p className="text-sm font-medium text-muted-foreground">Patients on Medication</p></div><p className="mt-2 text-3xl font-bold text-primary">{totalPatients}</p></div>
      </div>

      {activeMeds.length > 0 && (<div className="rounded-lg border border-green-200 bg-green-50/50 p-6 shadow-sm"><div className="flex items-center gap-2"><Clock className="h-5 w-5 text-green-600" /><h2 className="text-lg font-semibold text-foreground">Active Medications</h2><span className="rounded-full bg-green-100 px-2 py-0.5 text-xs font-medium text-green-700">{activeMeds.length}</span></div><div className="mt-3 grid gap-2 md:grid-cols-2 lg:grid-cols-3">{activeMeds.slice(0,9).map((m) => (<div key={m.id} className="flex items-center gap-3 rounded-md bg-white p-3 shadow-sm"><Pill className="h-4 w-4 text-green-500" /><div className="min-w-0 flex-1"><p className="truncate text-sm font-medium text-foreground">{m.drug_name}</p><p className="truncate text-xs text-muted-foreground">{m.patient_name} - {m.dosage}</p></div></div>))}</div></div>)}

      <div className="flex flex-wrap items-center gap-4">
        <div className="relative"><Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" /><input type="text" value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search..." className="w-64 rounded-md border border-input bg-background pl-9 pr-3 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring" /></div>
        <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} className="rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"><option value="all">All statuses</option><option value="active">Active</option><option value="completed">Completed</option><option value="discontinued">Discontinued</option><option value="on_hold">On Hold</option></select>
      </div>

      {loading && (<div className="flex items-center justify-center py-16"><div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" /><span className="ml-3 text-sm text-muted-foreground">Loading...</span></div>)}
      {error && (<div className="rounded-lg border border-destructive/30 bg-destructive/5 p-4"><p className="text-sm text-destructive">{error}</p><button onClick={fetchMedications} className="mt-2 text-sm font-medium text-primary hover:underline">Retry</button></div>)}
      {!loading && !error && filtered.length === 0 && (<div className="flex flex-col items-center justify-center rounded-lg border border-border bg-card py-16"><p className="text-lg font-medium text-foreground">No prescriptions found</p></div>)}

      {!loading && !error && filtered.length > 0 && (
        <div className="rounded-lg border border-border bg-card shadow-sm">
          <div className="border-b border-border px-6 py-2"><div className="grid grid-cols-7 text-xs font-semibold uppercase tracking-wider text-muted-foreground"><span>Patient</span><span>Drug Name</span><span>Dosage</span><span>Frequency</span><span>Start Date</span><span>Status</span><span>Reason</span></div></div>
          <div className="divide-y divide-border">{filtered.map((m) => (<div key={m.id} className="grid grid-cols-7 items-center px-6 py-3 text-sm transition-colors hover:bg-muted/50"><span className="font-medium text-foreground">{m.patient_name ?? "Unknown"}</span><div><p className="font-medium text-foreground">{m.drug_name}</p>{m.generic_name && <p className="text-xs text-muted-foreground">{m.generic_name}</p>}</div><span className="text-muted-foreground">{m.dosage}</span><span className="text-muted-foreground">{m.frequency}</span><span className="text-muted-foreground">{m.start_date ? new Date(m.start_date).toLocaleDateString() : "N/A"}</span><span><span className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_STYLES[m.status] ?? "bg-gray-100 text-gray-600"}`}>{m.status}</span></span><span className="truncate text-muted-foreground">{m.reason ?? "--"}</span></div>))}</div>
        </div>
      )}
    </div>
  );
}
