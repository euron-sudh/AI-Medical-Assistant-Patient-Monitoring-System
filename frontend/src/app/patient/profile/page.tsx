"use client";

import { useEffect, useState } from "react";
import { Pencil, Save, X } from "lucide-react";
import { ApiKeyButton } from "@/components/shared/api-key-modal";
import apiClient from "@/lib/api-client";

interface UserProfile {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  role: string;
  phone: string | null;
  is_active: boolean;
  email_verified: boolean;
  last_login_at: string | null;
  created_at: string;
  patient_profile?: {
    date_of_birth: string | null;
    gender: string | null;
    blood_type: string | null;
    height_cm: number | null;
    weight_kg: number | null;
    emergency_contact: Record<string, string> | null;
    insurance_info: Record<string, string> | null;
  };
}

interface EditFormData {
  phone: string;
  gender: string;
  blood_type: string;
  height_cm: string;
  weight_kg: string;
  emergency_contact_name: string;
  emergency_contact_phone: string;
  emergency_contact_relation: string;
  insurance_provider: string;
  insurance_policy_number: string;
}

export default function ProfilePage() {
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [apiKeyStatus, setApiKeyStatus] = useState<string>("Not configured");
  const [isEditing, setIsEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [formData, setFormData] = useState<EditFormData>({
    phone: "",
    gender: "",
    blood_type: "",
    height_cm: "",
    weight_kg: "",
    emergency_contact_name: "",
    emergency_contact_phone: "",
    emergency_contact_relation: "",
    insurance_provider: "",
    insurance_policy_number: "",
  });

  useEffect(() => {
    fetchProfile();
    checkApiKey();
  }, []);

  const fetchProfile = async () => {
    try {
      const res = await apiClient.get("/auth/me");
      const data = res.data?.user ?? res.data;
      setProfile(data);
      populateForm(data);
    } catch {
      try {
        const userStr = localStorage.getItem("user");
        if (userStr) {
          const data = JSON.parse(userStr);
          setProfile(data);
          populateForm(data);
        } else {
          setError("Unable to load profile. Please log in again.");
        }
      } catch {
        setError("Unable to load profile.");
      }
    } finally {
      setLoading(false);
    }
  };

  const populateForm = (data: UserProfile) => {
    const pp = data.patient_profile;
    const ec = pp?.emergency_contact ?? {};
    const ins = pp?.insurance_info ?? {};
    setFormData({
      phone: data.phone ?? "",
      gender: pp?.gender ?? "",
      blood_type: pp?.blood_type ?? "",
      height_cm: pp?.height_cm != null ? String(pp.height_cm) : "",
      weight_kg: pp?.weight_kg != null ? String(pp.weight_kg) : "",
      emergency_contact_name: ec.name ?? "",
      emergency_contact_phone: ec.phone ?? "",
      emergency_contact_relation: ec.relation ?? "",
      insurance_provider: ins.provider ?? "",
      insurance_policy_number: ins.policy_number ?? "",
    });
  };

  const checkApiKey = () => {
    const key = localStorage.getItem("euriApiKey");
    if (key && key.startsWith("euri-") && key.length > 20) {
      setApiKeyStatus("Configured (custom key)");
    } else if (key) {
      setApiKeyStatus("Set but may be invalid");
    } else {
      setApiKeyStatus("Configured (server default)");
    }
  };

  const handleInputChange = (field: keyof EditFormData, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const handleSave = async () => {
    if (!profile) return;
    setSaving(true);
    setSaveError(null);
    setSaveSuccess(false);

    const emergency_contact: Record<string, string> = {};
    if (formData.emergency_contact_name) emergency_contact.name = formData.emergency_contact_name;
    if (formData.emergency_contact_phone) emergency_contact.phone = formData.emergency_contact_phone;
    if (formData.emergency_contact_relation) emergency_contact.relation = formData.emergency_contact_relation;

    const insurance_info: Record<string, string> = {};
    if (formData.insurance_provider) insurance_info.provider = formData.insurance_provider;
    if (formData.insurance_policy_number) insurance_info.policy_number = formData.insurance_policy_number;

    const payload: Record<string, unknown> = {};
    if (formData.phone) payload.phone = formData.phone;
    if (formData.gender) payload.gender = formData.gender;
    if (formData.blood_type) payload.blood_type = formData.blood_type;
    if (formData.height_cm) payload.height_cm = parseFloat(formData.height_cm);
    if (formData.weight_kg) payload.weight_kg = parseFloat(formData.weight_kg);
    if (Object.keys(emergency_contact).length > 0) payload.emergency_contact = emergency_contact;
    if (Object.keys(insurance_info).length > 0) payload.insurance_info = insurance_info;

    try {
      await apiClient.put(`/patients/${profile.id}`, payload);
      setSaveSuccess(true);
      setIsEditing(false);
      // Refresh profile data
      await fetchProfile();
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err: unknown) {
      const msg =
        err && typeof err === "object" && "response" in err
          ? ((err as { response?: { data?: { error?: { message?: string } } } }).response?.data
              ?.error?.message ?? "Failed to save profile.")
          : "Failed to save profile.";
      setSaveError(msg);
    } finally {
      setSaving(false);
    }
  };

  const handleCancel = () => {
    setIsEditing(false);
    setSaveError(null);
    if (profile) populateForm(profile);
  };

  if (loading) {
    return (
      <div className="space-y-8">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Profile</h1>
          <p className="mt-1 text-muted-foreground">Loading your profile...</p>
        </div>
        <div className="rounded-lg border border-border bg-card p-12 text-center">
          <p className="text-sm text-muted-foreground">Loading...</p>
        </div>
      </div>
    );
  }

  if (error || !profile) {
    return (
      <div className="space-y-8">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Profile</h1>
        </div>
        <div className="rounded-lg border border-border bg-card p-12 text-center">
          <p className="text-sm text-destructive">{error ?? "Profile not available."}</p>
        </div>
      </div>
    );
  }

  const pp = profile.patient_profile;

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Profile</h1>
          <p className="mt-1 text-muted-foreground">
            Manage your personal information and account settings.
          </p>
        </div>
        {!isEditing ? (
          <button
            onClick={() => setIsEditing(true)}
            className="flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
          >
            <Pencil className="h-4 w-4" />
            Edit Profile
          </button>
        ) : (
          <div className="flex items-center gap-2">
            <button
              onClick={handleCancel}
              className="flex items-center gap-2 rounded-md border border-border px-4 py-2 text-sm font-medium hover:bg-muted transition-colors"
            >
              <X className="h-4 w-4" />
              Cancel
            </button>
            <button
              onClick={handleSave}
              disabled={saving}
              className="flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50 transition-colors"
            >
              <Save className="h-4 w-4" />
              {saving ? "Saving..." : "Save Changes"}
            </button>
          </div>
        )}
      </div>

      {saveSuccess && (
        <div className="rounded-md bg-green-50 border border-green-200 px-4 py-3 text-sm text-green-700 dark:bg-green-950/30 dark:border-green-900 dark:text-green-300">
          Profile updated successfully.
        </div>
      )}
      {saveError && (
        <div className="rounded-md bg-destructive/10 border border-destructive/20 px-4 py-3 text-sm text-destructive">
          {saveError}
        </div>
      )}

      <div className="grid gap-6 md:grid-cols-2">
        {/* Personal Information */}
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-foreground">Personal Information</h2>
          <div className="mt-4 space-y-3">
            <InfoRow label="Name" value={`${profile.first_name} ${profile.last_name}`} />
            <InfoRow label="Email" value={profile.email} />
            {isEditing ? (
              <EditRow label="Phone" value={formData.phone} onChange={(v) => handleInputChange("phone", v)} placeholder="e.g., +1 555-123-4567" />
            ) : (
              <InfoRow label="Phone" value={profile.phone ?? "Not set"} />
            )}
            <InfoRow label="Role" value={profile.role} />
            {isEditing ? (
              <>
                <EditSelect label="Gender" value={formData.gender} onChange={(v) => handleInputChange("gender", v)} options={[{ value: "", label: "Select..." }, { value: "male", label: "Male" }, { value: "female", label: "Female" }, { value: "other", label: "Other" }, { value: "prefer_not_to_say", label: "Prefer not to say" }]} />
                <EditSelect label="Blood Type" value={formData.blood_type} onChange={(v) => handleInputChange("blood_type", v)} options={[{ value: "", label: "Select..." }, { value: "A+", label: "A+" }, { value: "A-", label: "A-" }, { value: "B+", label: "B+" }, { value: "B-", label: "B-" }, { value: "AB+", label: "AB+" }, { value: "AB-", label: "AB-" }, { value: "O+", label: "O+" }, { value: "O-", label: "O-" }]} />
              </>
            ) : (
              <>
                {pp?.gender && <InfoRow label="Gender" value={pp.gender} />}
                {pp?.date_of_birth && <InfoRow label="Date of Birth" value={new Date(pp.date_of_birth).toLocaleDateString()} />}
                {pp?.blood_type && <InfoRow label="Blood Type" value={pp.blood_type} />}
              </>
            )}
          </div>
        </div>

        {/* Account Status */}
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-foreground">Account Status</h2>
          <div className="mt-4 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">Account Active</span>
              <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium ${profile.is_active ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"}`}>
                <span className={`inline-block h-1.5 w-1.5 rounded-full ${profile.is_active ? "bg-green-500" : "bg-red-500"}`} />
                {profile.is_active ? "Active" : "Inactive"}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">Email Verified</span>
              <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${profile.email_verified ? "bg-green-100 text-green-700" : "bg-amber-100 text-amber-700"}`}>
                {profile.email_verified ? "Verified" : "Pending"}
              </span>
            </div>
            <InfoRow label="Member Since" value={new Date(profile.created_at).toLocaleDateString()} />
            {profile.last_login_at && (
              <InfoRow label="Last Login" value={new Date(profile.last_login_at).toLocaleString()} />
            )}
          </div>
        </div>

        {/* Medical Details */}
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-foreground">Medical Details</h2>
          <div className="mt-4 space-y-3">
            {isEditing ? (
              <>
                <EditRow label="Height (cm)" value={formData.height_cm} onChange={(v) => handleInputChange("height_cm", v)} placeholder="e.g., 170" type="number" />
                <EditRow label="Weight (kg)" value={formData.weight_kg} onChange={(v) => handleInputChange("weight_kg", v)} placeholder="e.g., 70" type="number" />
                <div className="pt-2">
                  <p className="text-sm font-medium text-muted-foreground mb-2">Emergency Contact</p>
                  <div className="space-y-2 rounded-md bg-muted/30 p-3">
                    <EditRow label="Name" value={formData.emergency_contact_name} onChange={(v) => handleInputChange("emergency_contact_name", v)} placeholder="Contact name" />
                    <EditRow label="Phone" value={formData.emergency_contact_phone} onChange={(v) => handleInputChange("emergency_contact_phone", v)} placeholder="Contact phone" />
                    <EditRow label="Relation" value={formData.emergency_contact_relation} onChange={(v) => handleInputChange("emergency_contact_relation", v)} placeholder="e.g., Spouse, Parent" />
                  </div>
                </div>
                <div className="pt-2">
                  <p className="text-sm font-medium text-muted-foreground mb-2">Insurance Info</p>
                  <div className="space-y-2 rounded-md bg-muted/30 p-3">
                    <EditRow label="Provider" value={formData.insurance_provider} onChange={(v) => handleInputChange("insurance_provider", v)} placeholder="Insurance provider" />
                    <EditRow label="Policy #" value={formData.insurance_policy_number} onChange={(v) => handleInputChange("insurance_policy_number", v)} placeholder="Policy number" />
                  </div>
                </div>
              </>
            ) : (
              <>
                {pp?.height_cm && <InfoRow label="Height" value={`${pp.height_cm} cm`} />}
                {pp?.weight_kg && <InfoRow label="Weight" value={`${pp.weight_kg} kg`} />}
                {pp?.emergency_contact && (
                  <div>
                    <p className="text-sm text-muted-foreground">Emergency Contact</p>
                    <div className="mt-1 rounded-md bg-muted/50 p-2 text-sm text-foreground">
                      {Object.entries(pp.emergency_contact).map(([key, val]) => (
                        <p key={key}>
                          <span className="font-medium capitalize">{key.replace("_", " ")}:</span>{" "}{val}
                        </p>
                      ))}
                    </div>
                  </div>
                )}
                {pp?.insurance_info && (
                  <div>
                    <p className="text-sm text-muted-foreground">Insurance Info</p>
                    <div className="mt-1 rounded-md bg-muted/50 p-2 text-sm text-foreground">
                      {Object.entries(pp.insurance_info).map(([key, val]) => (
                        <p key={key}>
                          <span className="font-medium capitalize">{key.replace("_", " ")}:</span>{" "}{val}
                        </p>
                      ))}
                    </div>
                  </div>
                )}
                {!pp?.height_cm && !pp?.weight_kg && !pp?.emergency_contact && !pp?.insurance_info && (
                  <p className="text-sm text-muted-foreground italic">No additional medical details on file.</p>
                )}
              </>
            )}
          </div>
        </div>

        {/* AI API Key Status */}
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-foreground">AI Features</h2>
          <p className="mt-2 text-sm text-muted-foreground">
            Configure your EURI API key to enable AI-powered features like symptom analysis,
            medical chat, and report reading.
          </p>
          <div className="mt-4 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">API Key Status</span>
              <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium ${apiKeyStatus.includes("Configured") ? "bg-green-100 text-green-700" : "bg-amber-100 text-amber-700"}`}>
                <span className={`inline-block h-1.5 w-1.5 rounded-full ${apiKeyStatus.includes("Configured") ? "bg-green-500" : "bg-amber-500"}`} />
                {apiKeyStatus}
              </span>
            </div>
            <div className="pt-1">
              <ApiKeyButton />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-sm text-muted-foreground">{label}</span>
      <span className="text-sm font-medium text-foreground">{value}</span>
    </div>
  );
}

function EditRow({
  label,
  value,
  onChange,
  placeholder,
  type = "text",
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  type?: string;
}) {
  return (
    <div className="flex items-center justify-between gap-4">
      <span className="text-sm text-muted-foreground shrink-0">{label}</span>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full max-w-[220px] rounded-md border border-border bg-background px-3 py-1.5 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
      />
    </div>
  );
}

function EditSelect({
  label,
  value,
  onChange,
  options,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  options: { value: string; label: string }[];
}) {
  return (
    <div className="flex items-center justify-between gap-4">
      <span className="text-sm text-muted-foreground shrink-0">{label}</span>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full max-w-[220px] rounded-md border border-border bg-background px-3 py-1.5 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
      >
        {options.map((o) => (
          <option key={o.value} value={o.value}>{o.label}</option>
        ))}
      </select>
    </div>
  );
}
