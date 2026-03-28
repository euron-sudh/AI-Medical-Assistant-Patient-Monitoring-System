import { RegisterForm } from "@/components/auth/register-form";
import Link from "next/link";

export default function RegisterPage() {
  return (
    <div>
      <h2 className="text-2xl font-bold tracking-tight text-gray-900">
        Create your account
      </h2>
      <p className="mt-2 mb-8 text-sm text-gray-500">
        Get started with MedAssist AI in seconds.
      </p>
      <RegisterForm />
      <p className="mt-8 text-center text-sm text-gray-500">
        Already have an account?{" "}
        <Link
          href="/login"
          className="font-semibold text-blue-600 transition-colors hover:text-teal-600"
        >
          Sign in
        </Link>
      </p>
    </div>
  );
}
