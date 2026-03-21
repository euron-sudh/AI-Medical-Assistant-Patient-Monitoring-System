"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";

interface AdminLayoutProps {
  children: React.ReactNode;
}

const navItems = [
  { href: "/admin/dashboard", label: "Dashboard", icon: "D" },
  { href: "/admin/users", label: "User Management", icon: "U" },
  { href: "/admin/system-health", label: "System Health", icon: "H" },
  { href: "/admin/ai-config", label: "AI Configuration", icon: "AI" },
  { href: "/admin/audit-logs", label: "Audit Logs", icon: "AL" },
  { href: "/admin/ai-analytics", label: "AI Analytics", icon: "An" },
  { href: "/admin/alerts", label: "Alert Summary", icon: "As" },
  { href: "/admin/settings", label: "Settings", icon: "S" },
];

export default function AdminLayout({ children }: AdminLayoutProps) {
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
          <span className="rounded bg-red-100 px-2 py-0.5 text-xs font-medium text-red-700">
            Admin
          </span>
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
          <h2 className="text-lg font-semibold text-foreground">Admin Panel</h2>
        </header>
        <div className="p-8">{children}</div>
      </main>
    </div>
  );
}
