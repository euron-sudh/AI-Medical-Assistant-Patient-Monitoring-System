"use client";

import { useRouter } from "next/navigation";
import { Stethoscope, Heart, Bone, Baby, Brain, SmilePlus, Eye, Activity } from "lucide-react";
import type { LucideIcon } from "lucide-react";

interface Specialty { id: string; name: string; description: string; icon: LucideIcon; color: string; bgColor: string; }

const SPECIALTIES: Specialty[] = [
  { id: "general", name: "General Medicine", description: "Primary care for common health concerns and routine checkups", icon: Stethoscope, color: "text-blue-600", bgColor: "bg-blue-100 dark:bg-blue-950/50" },
  { id: "cardiology", name: "Cardiology", description: "Heart and cardiovascular system conditions and diagnostics", icon: Heart, color: "text-red-600", bgColor: "bg-red-100 dark:bg-red-950/50" },
  { id: "orthopedics", name: "Orthopedics", description: "Bones, joints, muscles, and musculoskeletal injuries", icon: Bone, color: "text-amber-600", bgColor: "bg-amber-100 dark:bg-amber-950/50" },
  { id: "gynecology", name: "Gynecology", description: "Womens reproductive health, prenatal and postnatal care", icon: SmilePlus, color: "text-pink-600", bgColor: "bg-pink-100 dark:bg-pink-950/50" },
  { id: "dermatology", name: "Dermatology", description: "Skin, hair, and nail conditions and treatments", icon: Eye, color: "text-orange-600", bgColor: "bg-orange-100 dark:bg-orange-950/50" },
  { id: "pediatrics", name: "Pediatrics", description: "Childrens health, growth, development, and vaccinations", icon: Baby, color: "text-emerald-600", bgColor: "bg-emerald-100 dark:bg-emerald-950/50" },
  { id: "neurology", name: "Neurology", description: "Brain, spinal cord, and nervous system disorders", icon: Brain, color: "text-purple-600", bgColor: "bg-purple-100 dark:bg-purple-950/50" },
  { id: "psychiatry", name: "Psychiatry", description: "Mental health, behavioral disorders, and emotional well-being", icon: Activity, color: "text-teal-600", bgColor: "bg-teal-100 dark:bg-teal-950/50" },
];

interface SpecialtySelectorProps { onSelect?: (specialtyId: string) => void; }

export default function SpecialtySelector({ onSelect }: SpecialtySelectorProps) {
  const router = useRouter();
  const handleClick = (specialty: Specialty) => {
    if (onSelect) { onSelect(specialty.id); }
    else { localStorage.setItem("medassist_specialty", specialty.id); localStorage.setItem("medassist_journey_step", "1"); router.push(`/patient/symptoms?specialty=${specialty.id}`); }
  };
  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {SPECIALTIES.map((spec) => {
        const Icon = spec.icon;
        return (
          <button key={spec.id} type="button" onClick={() => handleClick(spec)} className="group flex flex-col items-start gap-3 rounded-xl border border-border bg-card p-5 text-left shadow-sm transition-all hover:border-primary/40 hover:shadow-md">
            <div className={`flex h-12 w-12 items-center justify-center rounded-lg ${spec.bgColor} transition-transform group-hover:scale-110`}><Icon className={`h-6 w-6 ${spec.color}`} /></div>
            <div>
              <h3 className="text-sm font-semibold text-foreground group-hover:text-primary">{spec.name}</h3>
              <p className="mt-1 text-xs leading-relaxed text-muted-foreground">{spec.description}</p>
            </div>
          </button>
        );
      })}
    </div>
  );
}
