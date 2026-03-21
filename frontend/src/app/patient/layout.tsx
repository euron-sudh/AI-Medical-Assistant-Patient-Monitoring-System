"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { ApiKeyButton } from "@/components/shared/api-key-modal";

interface PatientLayoutProps {
  children: React.ReactNode;
}

const navItems = [
  { href: "/patient/dashboard", label: "Dashboard", icon: "H" },
  { href: "/patient/symptoms", label: "Symptom Checker", icon: "S" },
  { href: "/patient/vitals", label: "My Vitals", icon: "V" },
  { href: "/patient/reports", label: "Reports", icon: "R" },
  { href: "/patient/medications", label: "Medications", icon: "M" },
  { href: "/patient/appointments", label: "Appointments", icon: "A" },
  { href: "/patient/chat", label: "AI Chat", icon: "C" },
  { href: "/patient/care-plan", label: "Care Plan", icon: "P" },
  { href: "/patient/profile", label: "Profile", icon: "U" },
];

export default function PatientLayout({ children }: PatientLayoutProps) {
  const pathname = usePathname();
  const router = useRouter();

  const handleLogout = () => {
    localStorage.removeItem("accessToken");
    localStorage.removeItem("refreshToken");
    localStorage.removeItem("user");
    router.push("/login");
  };

  return (
    <div className="flex min-h-screen bg-background">
      <aside className="fixed inset-y-0 left-0 z-30 flex w-64 flex-col border-r border-border bg-card">
        <div className="flex h-16 items-center gap-2 border-b border-border px-6">
          <span className="text-xl font-bold text-primary">MedAssist</span>
          <span className="rounded bg-primary/10 px-2 py-0.5 text-xs font-medium text-primary">
            Patient
          </span>
          <div className="ml-auto">
            <ApiKeyButton />
          </div>
        </div>

        <nav className="flex-1 space-y-1 overflow-y-auto p-4 scrollbar-thin">
          {navItems.map((item) => {
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                  isActive
                    ? "bg-primary/10 text-primary"
                    : "text-muted-foreground hover:bg-accent hover:text-foreground"
                }`}
              >
                <span className="flex h-7 w-7 items-center justify-center rounded-md bg-muted text-xs font-semibold">
                  {item.icon}
                </span>
                {item.label}
              </Link>
            );
          })}
        </nav>

        <div className="border-t border-border p-4">
          <button
            onClick={handleLogout}
            className="flex w-full items-center gap-3 rounded-md px-3 py-2 text-sm font-medium text-muted-foreground transition-colors hover:bg-destructive/10 hover:text-destructive"
          >
            Sign Out
          </button>
        </div>
      </aside>

      <main className="ml-64 flex-1">
        <header className="sticky top-0 z-20 flex h-16 items-center justify-between border-b border-border bg-card/80 px-8 backdrop-blur">
          <h2 className="text-lg font-semibold text-foreground">Patient Portal</h2>
        </header>
        <div className="p-8">{children}</div>
      </main>
    </div>
  );
}
