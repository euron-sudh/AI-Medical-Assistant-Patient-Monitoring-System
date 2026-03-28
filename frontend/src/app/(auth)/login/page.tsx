import { LoginForm } from "@/components/auth/login-form";
import Link from "next/link";

export default function LoginPage() {
  return (
    <div>
      <h2 className="text-2xl font-bold tracking-tight text-gray-900">
        Sign in
      </h2>
      <p className="mt-2 mb-8 text-sm text-gray-500">
        Welcome back. Enter your credentials to continue.
      </p>
      <LoginForm />
      <p className="mt-8 text-center text-sm text-gray-500">
        Don&apos;t have an account?{" "}
        <Link
          href="/register"
          className="font-semibold text-blue-600 transition-colors hover:text-teal-600"
        >
          Create one
        </Link>
      </p>
    </div>
  );
}
