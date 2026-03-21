"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import type { UserRole } from "@/types/auth";

interface NavItem {
  label: string;
  href: string;
}

const NAV_ITEMS: Record<UserRole, NavItem[]> = {
  patient: [
    { label: "Dashboard", href: "/patient" },
    { label: "Symptoms", href: "/patient/symptoms" },
    { label: "Vitals", href: "/patient/vitals" },
    { label: "Reports", href: "/patient/reports" },
    { label: "Medications", href: "/patient/medications" },
    { label: "Appointments", href: "/patient/appointments" },
    { label: "Care Plan", href: "/patient/care-plan" },
    { label: "Chat", href: "/patient/chat" },
  ],
  doctor: [
    { label: "Dashboard", href: "/doctor" },
    { label: "Patients", href: "/doctor/patients" },
    { label: "Monitoring", href: "/doctor/monitoring" },
    { label: "Appointments", href: "/doctor/appointments" },
    { label: "Prescriptions", href: "/doctor/prescriptions" },
    { label: "Analytics", href: "/doctor/analytics" },
    { label: "AI Assistant", href: "/doctor/ai-assistant" },
  ],
  nurse: [
    { label: "Dashboard", href: "/doctor" },
    { label: "Patients", href: "/doctor/patients" },
    { label: "Monitoring", href: "/doctor/monitoring" },
    { label: "Appointments", href: "/doctor/appointments" },
  ],
  admin: [
    { label: "Dashboard", href: "/admin" },
    { label: "Users", href: "/admin/users" },
    { label: "System Health", href: "/admin/system-health" },
    { label: "AI Config", href: "/admin/ai-config" },
    { label: "Audit Logs", href: "/admin/audit-logs" },
    { label: "Analytics", href: "/admin/ai-analytics" },
    { label: "Settings", href: "/admin/settings" },
  ],
};

interface SidebarProps {
  role: UserRole;
}

export function Sidebar({ role }: SidebarProps) {
  const pathname = usePathname();
  const items = NAV_ITEMS[role] ?? [];

  return (
    <aside className="hidden w-64 shrink-0 border-r bg-background md:block">
      <nav className="flex flex-col gap-1 p-4">
        {items.map((item) => {
          const isActive =
            pathname === item.href ||
            (item.href !== `/${role}` && pathname.startsWith(item.href));

          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "rounded-md px-3 py-2 text-sm font-medium transition-colors",
                isActive
                  ? "bg-primary/10 text-primary"
                  : "text-muted-foreground hover:bg-muted hover:text-foreground"
              )}
            >
              {item.label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
