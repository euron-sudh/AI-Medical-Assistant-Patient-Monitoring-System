"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState, useEffect } from "react";
import type { User } from "@/types/auth";

export function Header() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    const token = localStorage.getItem("accessToken");
    if (token) {
      try {
        const payload = JSON.parse(atob(token.split(".")[1]));
        setUser({
          id: payload.sub,
          email: payload.email ?? "",
          firstName: payload.firstName ?? "",
          lastName: payload.lastName ?? "",
          role: payload.role,
          isActive: true,
          isVerified: true,
          createdAt: "",
        });
      } catch {
        setUser(null);
      }
    }
  }, []);

  const handleLogout = () => {
    localStorage.removeItem("accessToken");
    localStorage.removeItem("refreshToken");
    setUser(null);
    router.push("/login");
  };

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="flex h-14 items-center justify-between px-4 md:px-6">
        <Link href="/" className="flex items-center gap-2">
          <span className="text-xl font-bold text-primary">MedAssist AI</span>
        </Link>

        <nav className="flex items-center gap-4">
          {user ? (
            <>
              <span className="hidden text-sm text-muted-foreground md:inline-block">
                {user.firstName} {user.lastName}
              </span>
              <span className="rounded-full bg-primary/10 px-2 py-0.5 text-xs font-medium capitalize text-primary">
                {user.role}
              </span>
              <button
                onClick={handleLogout}
                className="text-sm text-muted-foreground hover:text-foreground"
              >
                Sign out
              </button>
            </>
          ) : (
            <>
              <Link
                href="/login"
                className="text-sm text-muted-foreground hover:text-foreground"
              >
                Sign in
              </Link>
              <Link
                href="/register"
                className="rounded-md bg-primary px-3 py-1.5 text-sm font-medium text-primary-foreground hover:bg-primary/90"
              >
                Get started
              </Link>
            </>
          )}
        </nav>
      </div>
    </header>
  );
}
