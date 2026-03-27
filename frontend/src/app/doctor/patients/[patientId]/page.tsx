"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import apiClient from "@/lib/api-client";
import { ArrowLeft, User, Heart, Pill, AlertCircle, FileText, Activity, Thermometer, Droplets, Wind, Scale } from "lucide-react";

interface PatientProfile { id: string; user_id: string; first_name: string; last_name: string; email: string; gender: string; blood_type: string; date_of_birth: string; height_cm: number|null; weight_kg: number|null; phone: string|null; assigned_doctor_name: string|null; allergies?: string[]; medical_conditions?: string[]; }
interface VitalRecord { id: string; recorded_at: string; heart_rate: number|null; blood_pressure_systolic: number|null; blood_pressure_diastolic: number|null; temperature: number|null; oxygen_saturation: number|null; respiratory_rate: number|null; weight_kg: number|null; }
interface Medication { id: string; drug_name: string; generic_name: string|null; dosage: string; frequency: string; route: string|null; start_date: string; end_date: string|null; status: string; reason: string|null; }
interface MedicalHistoryEntry { id: string; condition: string; diagnosed_date: string|null; status: string; notes: string|null; }

const getAge = (dob: string) => dob ? Math.floor((Date.now() - new Date(dob).getTime()) / (365.25*24*60*60*1000)) : 0;
const MS: Record<string, string> = { active: "bg-green-100 text-green-800", completed: "bg-gray-100 text-gray-600", discontinued: "bg-red-100 text-red-700", on_hold: "bg-amber-100 text-amber-800" };

export default function PatientDetailPage() {
  const params = useParams();
  const patientId = params.patientId as string;
  const [patient, setPatient] = useState<PatientProfile|null>(null);
  const [vitals, setVitals] = useState<VitalRecord[]>([]);
  const [medications, setMedications] = useState<Medication[]>([]);
  const [history, setHistory] = useState<MedicalHistoryEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string|null>(null);
  const [activeTab, setActiveTab] = useState<"vitals"|"medications"|"history">("vitals");

  useEffect(() => { if (patientId) fetchAll(); }, [patientId]); // eslint-disable-line react-hooks/exhaustive-deps

  const fetchAll = async () => {
    setLoading(true); setError(null);
    try { const r = await apiClient.get(`/patients/${patientId}`); setPatient(r.data.patient ?? r.data); } catch { setError("Failed to load patient."); setLoading(false); return; }
    try { const r = await apiClient.get(`/vitals/${patientId}`); const d = r.data.vitals ?? r.data ?? []; setVitals((Array.isArray(d)?d:[]).sort((a:VitalRecord,b:VitalRecord)=>new Date(b.recorded_at).getTime()-new Date(a.recorded_at).getTime())); } catch {}
    try { const r = await apiClient.get(`/medications/${patientId}`); setMedications(Array.isArray(r.data.medications??r.data)?r.data.medications??r.data:[]); } catch {}
    try { const r = await apiClient.get(`/patients/${patientId}/history`); setHistory(Array.isArray(r.data.history??r.data)?r.data.history??r.data:[]); } catch {}
    setLoading(false);
  };

  if (loading) return (<div className="space-y-6"><a href="/doctor/patients" className="inline-flex items-center gap-1 text-sm text-primary hover:underline"><ArrowLeft className="h-4 w-4" /> Back</a><div className="flex items-center justify-center py-20"><div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" /><span className="ml-3 text-sm text-muted-foreground">Loading...</span></div></div>);
  if (error || !patient) return (<div className="space-y-6"><a href="/doctor/patients" className="inline-flex items-center gap-1 text-sm text-primary hover:underline"><ArrowLeft className="h-4 w-4" /> Back</a><div className="rounded-lg border border-destructive/30 bg-destructive/5 p-6 text-center"><p className="text-sm text-destructive">{error ?? "Patient not found."}</p></div></div>);

  const lv = vitals[0]; const am = medications.filter((m) => m.status === "active");

  return (
    <div className="space-y-6">
      <a href="/doctor/patients" className="inline-flex items-center gap-1 text-sm text-primary hover:underline"><ArrowLeft className="h-4 w-4" /> Back to Patients</a>

      <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
        <div className="flex flex-col gap-6 md:flex-row md:items-start">
          <div className="flex h-20 w-20 items-center justify-center rounded-full bg-primary/10"><User className="h-10 w-10 text-primary" /></div>
          <div className="flex-1">
            <h1 className="text-2xl font-bold text-foreground">{patient.first_name} {patient.last_name}</h1>
            <p className="mt-1 text-sm text-muted-foreground">{patient.email}</p>
            <div className="mt-4 grid grid-cols-2 gap-4 md:grid-cols-4 lg:grid-cols-6">
              <div><p className="text-xs font-medium text-muted-foreground">Age</p><p className="text-sm font-semibold text-foreground">{patient.date_of_birth ? `${getAge(patient.date_of_birth)}y` : "N/A"}</p></div>
              <div><p className="text-xs font-medium text-muted-foreground">Gender</p><p className="text-sm font-semibold text-foreground capitalize">{patient.gender ?? "N/A"}</p></div>
              <div><p className="text-xs font-medium text-muted-foreground">Blood Type</p>{patient.blood_type ? <span className="inline-flex rounded-full bg-red-50 px-2 py-0.5 text-xs font-medium text-red-700">{patient.blood_type}</span> : <p className="text-sm">N/A</p>}</div>
              <div><p className="text-xs font-medium text-muted-foreground">Height</p><p className="text-sm font-semibold text-foreground">{patient.height_cm ? `${patient.height_cm} cm` : "N/A"}</p></div>
              <div><p className="text-xs font-medium text-muted-foreground">Weight</p><p className="text-sm font-semibold text-foreground">{patient.weight_kg ? `${patient.weight_kg} kg` : "N/A"}</p></div>
              <div><p className="text-xs font-medium text-muted-foreground">Phone</p><p className="text-sm font-semibold text-foreground">{patient.phone ?? "N/A"}</p></div>
            </div>
          </div>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm"><div className="flex items-center gap-2"><AlertCircle className="h-5 w-5 text-red-500" /><h2 className="text-lg font-semibold text-foreground">Allergies</h2></div>{(patient.allergies??[]).length === 0 ? <p className="mt-3 text-sm text-muted-foreground">No known allergies.</p> : <div className="mt-3 flex flex-wrap gap-2">{(patient.allergies??[]).map((a,i) => <span key={i} className="inline-flex rounded-full border border-red-200 bg-red-50 px-3 py-1 text-xs font-medium text-red-700">{a}</span>)}</div>}</div>
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm"><div className="flex items-center gap-2"><FileText className="h-5 w-5 text-blue-500" /><h2 className="text-lg font-semibold text-foreground">Medical Conditions</h2></div>{(patient.medical_conditions??[]).length === 0 ? <p className="mt-3 text-sm text-muted-foreground">No conditions on record.</p> : <div className="mt-3 flex flex-wrap gap-2">{(patient.medical_conditions??[]).map((c,i) => <span key={i} className="inline-flex rounded-full border border-blue-200 bg-blue-50 px-3 py-1 text-xs font-medium text-blue-700">{c}</span>)}</div>}</div>
      </div>

      {lv && (<div className="rounded-lg border border-border bg-card p-6 shadow-sm"><div className="flex items-center justify-between"><div className="flex items-center gap-2"><Activity className="h-5 w-5 text-green-500" /><h2 className="text-lg font-semibold text-foreground">Latest Vitals</h2></div><span className="text-xs text-muted-foreground">Recorded: {new Date(lv.recorded_at).toLocaleString()}</span></div>
        <div className="mt-4 grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-6">
          <div className="rounded-lg bg-muted/50 p-3 text-center"><Heart className="mx-auto h-5 w-5 text-red-500" /><p className="mt-1 text-lg font-bold">{lv.heart_rate ?? "--"}</p><p className="text-xs text-muted-foreground">HR</p></div>
          <div className="rounded-lg bg-muted/50 p-3 text-center"><Droplets className="mx-auto h-5 w-5 text-blue-500" /><p className="mt-1 text-lg font-bold">{lv.blood_pressure_systolic&&lv.blood_pressure_diastolic ? `${lv.blood_pressure_systolic}/${lv.blood_pressure_diastolic}` : "--"}</p><p className="text-xs text-muted-foreground">BP</p></div>
          <div className="rounded-lg bg-muted/50 p-3 text-center"><Thermometer className="mx-auto h-5 w-5 text-orange-500" /><p className="mt-1 text-lg font-bold">{lv.temperature ? `${lv.temperature}\u00b0` : "--"}</p><p className="text-xs text-muted-foreground">Temp</p></div>
          <div className="rounded-lg bg-muted/50 p-3 text-center"><Wind className="mx-auto h-5 w-5 text-teal-500" /><p className="mt-1 text-lg font-bold">{lv.oxygen_saturation ? `${lv.oxygen_saturation}%` : "--"}</p><p className="text-xs text-muted-foreground">SpO2</p></div>
          <div className="rounded-lg bg-muted/50 p-3 text-center"><Activity className="mx-auto h-5 w-5 text-purple-500" /><p className="mt-1 text-lg font-bold">{lv.respiratory_rate ?? "--"}</p><p className="text-xs text-muted-foreground">Resp</p></div>
          <div className="rounded-lg bg-muted/50 p-3 text-center"><Scale className="mx-auto h-5 w-5 text-gray-500" /><p className="mt-1 text-lg font-bold">{lv.weight_kg ? `${lv.weight_kg}kg` : "--"}</p><p className="text-xs text-muted-foreground">Weight</p></div>
        </div>
      </div>)}

      <div className="rounded-lg border border-border bg-card shadow-sm">
        <div className="flex border-b border-border">{(["vitals","medications","history"] as const).map((t) => (<button key={t} onClick={() => setActiveTab(t)} className={`px-6 py-3 text-sm font-medium transition-colors ${activeTab===t ? "border-b-2 border-primary text-primary" : "text-muted-foreground hover:text-foreground"}`}>{t==="vitals"?"Vitals History":t==="medications"?`Medications (${medications.length})`:"Medical History"}</button>))}</div>
        <div className="p-6">
          {activeTab==="vitals" && (vitals.length===0 ? <p className="py-8 text-center text-sm text-muted-foreground">No vital records.</p> : <div className="overflow-x-auto"><table className="w-full text-sm"><thead><tr className="border-b border-border text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground"><th className="pb-2 pr-4">Date</th><th className="pb-2 pr-4">HR</th><th className="pb-2 pr-4">BP</th><th className="pb-2 pr-4">Temp</th><th className="pb-2 pr-4">SpO2</th><th className="pb-2 pr-4">Resp</th><th className="pb-2">Weight</th></tr></thead><tbody className="divide-y divide-border">{vitals.slice(0,20).map((v) => (<tr key={v.id} className="hover:bg-muted/50"><td className="py-2 pr-4 text-muted-foreground">{new Date(v.recorded_at).toLocaleString()}</td><td className="py-2 pr-4 font-medium">{v.heart_rate??"-"}</td><td className="py-2 pr-4">{v.blood_pressure_systolic&&v.blood_pressure_diastolic?`${v.blood_pressure_systolic}/${v.blood_pressure_diastolic}`:"-"}</td><td className="py-2 pr-4">{v.temperature?`${v.temperature}\u00b0`:"-"}</td><td className="py-2 pr-4">{v.oxygen_saturation?`${v.oxygen_saturation}%`:"-"}</td><td className="py-2 pr-4">{v.respiratory_rate??"-"}</td><td className="py-2">{v.weight_kg?`${v.weight_kg}kg`:"-"}</td></tr>))}</tbody></table></div>)}
          {activeTab==="medications" && (medications.length===0 ? <p className="py-8 text-center text-sm text-muted-foreground">No medications.</p> : <div className="space-y-3">{am.length>0 && <h3 className="text-sm font-semibold">Active ({am.length})</h3>}{medications.map((m) => (<div key={m.id} className="flex items-center justify-between rounded-lg border border-border p-4"><div className="flex items-start gap-3"><Pill className="mt-0.5 h-5 w-5 text-green-500" /><div><p className="font-medium text-foreground">{m.drug_name}</p>{m.generic_name && <p className="text-xs text-muted-foreground">{m.generic_name}</p>}<p className="mt-1 text-xs text-muted-foreground">{m.dosage} - {m.frequency}{m.route?` (${m.route})`:""}</p>{m.reason && <p className="text-xs text-muted-foreground">Reason: {m.reason}</p>}</div></div><div className="text-right"><span className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${MS[m.status]??"bg-gray-100 text-gray-600"}`}>{m.status}</span><p className="mt-1 text-xs text-muted-foreground">{m.start_date?new Date(m.start_date).toLocaleDateString():"N/A"}{m.end_date?` - ${new Date(m.end_date).toLocaleDateString()}`:""}</p></div></div>))}</div>)}
          {activeTab==="history" && (history.length===0 ? <p className="py-8 text-center text-sm text-muted-foreground">No history entries.</p> : <div className="space-y-3">{history.map((h) => (<div key={h.id} className="rounded-lg border border-border p-4"><div className="flex items-center justify-between"><p className="font-medium text-foreground">{h.condition}</p><span className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${h.status==="active"?"bg-amber-100 text-amber-800":"bg-green-100 text-green-800"}`}>{h.status}</span></div>{h.diagnosed_date && <p className="mt-1 text-xs text-muted-foreground">Diagnosed: {new Date(h.diagnosed_date).toLocaleDateString()}</p>}{h.notes && <p className="mt-1 text-xs text-muted-foreground">{h.notes}</p>}</div>))}</div>)}
        </div>
      </div>
    </div>
  );
}
