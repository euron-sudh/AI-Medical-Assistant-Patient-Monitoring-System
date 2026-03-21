import Link from "next/link";

interface AuthLayoutProps {
  children: React.ReactNode;
}

export default function AuthLayout({ children }: AuthLayoutProps) {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-gradient-to-b from-medical-blue-light to-white px-4">
      <div className="mb-8 text-center">
        <Link href="/" className="inline-block">
          <h1 className="text-3xl font-bold text-primary">MedAssist AI</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Intelligent Medical Assistant
          </p>
        </Link>
      </div>
      <div className="w-full max-w-md rounded-lg border bg-card p-6 shadow-sm">
        {children}
      </div>
    </div>
  );
}
