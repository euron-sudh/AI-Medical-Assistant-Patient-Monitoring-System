import { RegisterForm } from "@/components/auth/register-form";
import Link from "next/link";

export default function RegisterPage() {
  return (
    <div>
      <h2 className="mb-2 text-2xl font-semibold text-foreground">
        Create your account
      </h2>
      <p className="mb-6 text-sm text-muted-foreground">
        Join MedAssist AI to get started
      </p>
      <RegisterForm />
      <p className="mt-6 text-center text-sm text-muted-foreground">
        Already have an account?{" "}
        <Link
          href="/login"
          className="font-medium text-primary hover:underline"
        >
          Sign in
        </Link>
      </p>
    </div>
  );
}
