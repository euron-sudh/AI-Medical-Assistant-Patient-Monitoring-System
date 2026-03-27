"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import {
  Baby,
  Bone,
  Brain,
  Heart,
  Layers,
  MessageCircle,
  Stethoscope,
  User,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

interface SpecialtyItem {
  id: string;
  name: string;
  description: string;
  icon: LucideIcon;
  color: string;
  bgColor: string;
}

const SPECIALTIES: SpecialtyItem[] = [
  {
    id: "general-physician",
    name: "General Physician",
    description: "Primary care, checkups, and everyday health concerns",
    icon: Stethoscope,
    color: "text-blue-600",
    bgColor: "bg-blue-100 dark:bg-blue-950/50",
  },
  {
    id: "cardiology",
    name: "Cardiology",
    description: "Heart and cardiovascular conditions",
    icon: Heart,
    color: "text-red-600",
    bgColor: "bg-red-100 dark:bg-red-950/50",
  },
  {
    id: "orthopedics",
    name: "Orthopedics",
    description: "Bones, joints, muscles, and injuries",
    icon: Bone,
    color: "text-amber-600",
    bgColor: "bg-amber-100 dark:bg-amber-950/50",
  },
  {
    id: "dermatology",
    name: "Dermatology",
    description: "Skin, hair, and nail conditions",
    icon: Layers,
    color: "text-orange-600",
    bgColor: "bg-orange-100 dark:bg-orange-950/50",
  },
  {
    id: "gynecology",
    name: "Gynecology",
    description: "Women's reproductive and pelvic health",
    icon: User,
    color: "text-pink-600",
    bgColor: "bg-pink-100 dark:bg-pink-950/50",
  },
  {
    id: "pediatrics",
    name: "Pediatrics",
    description: "Infant, child, and adolescent care",
    icon: Baby,
    color: "text-emerald-600",
    bgColor: "bg-emerald-100 dark:bg-emerald-950/50",
  },
  {
    id: "neurology",
    name: "Neurology",
    description: "Brain, spine, and nervous system disorders",
    icon: Brain,
    color: "text-purple-600",
    bgColor: "bg-purple-100 dark:bg-purple-950/50",
  },
  {
    id: "psychiatry",
    name: "Psychiatry",
    description: "Mental health and emotional wellbeing",
    icon: MessageCircle,
    color: "text-teal-600",
    bgColor: "bg-teal-100 dark:bg-teal-950/50",
  },
];

export interface SpecialtySelectorProps {
  /** Called with lowercase hyphenated specialty id (e.g. `general-physician`). */
  onSelect?: (specialty: string) => void;
  /**
   * `standalone` — centered container for a full page.
   * `modal` — minimal wrapper for use inside dialogs/overlays.
   * `inline` — default; fills parent width.
   */
  variant?: "standalone" | "modal" | "inline";
  /** Extra classes on the outer wrapper. */
  className?: string;
  /**
   * When `onSelect` is omitted, selection stores specialty and navigates to
   * `/patient/symptoms?specialty=...`. When `onSelect` is set, the parent
   * controls navigation unless this is set to `true` (navigate after callback).
   */
  navigateAfterParentSelect?: boolean;
}

const variantWrapper: Record<NonNullable<SpecialtySelectorProps["variant"]>, string> = {
  standalone: "mx-auto w-full max-w-6xl px-4 py-6 md:py-10",
  modal: "w-full",
  inline: "w-full",
};

export default function SpecialtySelector({
  onSelect,
  variant = "inline",
  className = "",
  navigateAfterParentSelect = false,
}: SpecialtySelectorProps) {
  const router = useRouter();
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const handleClick = (specialty: SpecialtyItem) => {
    setSelectedId(specialty.id);
    onSelect?.(specialty.id);

    const shouldNavigate =
      onSelect == null || navigateAfterParentSelect;

    if (shouldNavigate) {
      if (typeof window !== "undefined") {
        localStorage.setItem("medassist_specialty", specialty.id);
        localStorage.setItem("medassist_journey_step", "2");
      }
      router.push(`/patient/symptoms?specialty=${encodeURIComponent(specialty.id)}`);
    }
  };

  const grid = (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {SPECIALTIES.map((spec) => {
        const Icon = spec.icon;
        const isSelected = selectedId === spec.id;
        return (
          <button
            key={spec.id}
            type="button"
            aria-pressed={isSelected}
            onClick={() => handleClick(spec)}
            className={`group flex flex-col items-start gap-3 rounded-xl border bg-card p-5 text-left shadow-sm transition-all hover:border-primary/40 hover:shadow-md ${
              isSelected
                ? "border-primary ring-2 ring-primary/30 shadow-md"
                : "border-border"
            }`}
          >
            <div
              className={`flex h-12 w-12 items-center justify-center rounded-lg ${spec.bgColor} transition-transform group-hover:scale-110`}
            >
              <Icon className={`h-6 w-6 ${spec.color}`} aria-hidden />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-foreground group-hover:text-primary">
                {spec.name}
              </h3>
              <p className="mt-1 text-xs leading-relaxed text-muted-foreground">
                {spec.description}
              </p>
            </div>
          </button>
        );
      })}
    </div>
  );

  return (
    <div className={`${variantWrapper[variant]} ${className}`.trim()}>{grid}</div>
  );
}
