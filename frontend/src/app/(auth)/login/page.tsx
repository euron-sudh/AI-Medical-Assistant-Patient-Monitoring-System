import { LoginForm } from "@/components/auth/login-form";
import Link from "next/link";

export default function LoginPage() {
  return (
    <div>
      <h2 className="mb-2 text-2xl font-semibold text-foreground">
        Welcome back
      </h2>
      <p className="mb-6 text-sm text-muted-foreground">
        Sign in to your MedAssist AI account
      </p>
      <LoginForm />
      <p className="mt-6 text-center text-sm text-muted-foreground">
        Don&apos;t have an account?{" "}
        <Link
          href="/register"
          className="font-medium text-primary hover:underline"
        >
          Create one
        </Link>
      </p>
    </div>
  );
}
