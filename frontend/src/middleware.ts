import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const redirects: Record<string, string> = {
  "/patient": "/patient/dashboard",
  "/doctor": "/doctor/dashboard",
  "/admin": "/admin/dashboard",
};

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  const target = redirects[pathname];
  if (target) {
    const url = request.nextUrl.clone();
    url.pathname = target;
    return NextResponse.redirect(url);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/patient", "/doctor", "/admin"],
};
