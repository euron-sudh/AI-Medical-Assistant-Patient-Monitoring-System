import Link from "next/link";

export default function LandingPage() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-gradient-to-b from-medical-blue-light to-white">
      <div className="text-center max-w-3xl px-6">
        <h1 className="text-5xl font-bold text-gray-900 mb-4">
          MedAssist AI
        </h1>
        <p className="text-xl text-gray-600 mb-8">
          Your intelligent medical assistant for symptom analysis, patient
          monitoring, and healthcare management.
        </p>
        {/* TODO: Siddhartha Borpuzari — Build full landing page with feature cards, hero section, CTA */}
        <div className="flex gap-4 justify-center">
          <Link
            href="/login"
            className="px-6 py-3 bg-primary text-white rounded-lg font-medium hover:opacity-90 transition"
          >
            Sign In
          </Link>
          <Link
            href="/register"
            className="px-6 py-3 border border-primary text-primary rounded-lg font-medium hover:bg-primary/5 transition"
          >
            Create Account
          </Link>
        </div>
      </div>
    </main>
  );
}
