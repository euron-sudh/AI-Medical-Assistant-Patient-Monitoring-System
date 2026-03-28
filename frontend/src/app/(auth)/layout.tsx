import Link from "next/link";

interface AuthLayoutProps {
  children: React.ReactNode;
}

export default function AuthLayout({ children }: AuthLayoutProps) {
  return (
    <div className="flex min-h-screen flex-col lg:flex-row">
      {/* LEFT SIDE - Hero / Branding */}
      <div className="relative flex w-full flex-col items-center justify-center overflow-hidden bg-gradient-to-br from-slate-900 via-blue-950 to-teal-900 px-8 py-12 lg:w-[60%] lg:px-16 lg:py-0">
        {/* Grid pattern overlay */}
        <div
          className="pointer-events-none absolute inset-0 opacity-[0.07]"
          style={{
            backgroundImage:
              "linear-gradient(rgba(255,255,255,.4) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.4) 1px, transparent 1px)",
            backgroundSize: "48px 48px",
          }}
        />

        {/* Animated pulse circles */}
        <div className="pointer-events-none absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2">
          <div className="absolute h-[500px] w-[500px] animate-[ping_4s_cubic-bezier(0,0,0.2,1)_infinite] rounded-full border border-teal-400/10" />
          <div className="absolute h-[400px] w-[400px] translate-x-[50px] translate-y-[50px] animate-[ping_5s_cubic-bezier(0,0,0.2,1)_infinite_1s] rounded-full border border-blue-400/10" />
          <div className="absolute h-[300px] w-[300px] translate-x-[100px] translate-y-[100px] animate-[ping_6s_cubic-bezier(0,0,0.2,1)_infinite_2s] rounded-full border border-cyan-400/10" />
        </div>

        {/* Floating gradient orbs */}
        <div className="pointer-events-none absolute -left-32 -top-32 h-96 w-96 rounded-full bg-blue-500/20 blur-3xl" />
        <div className="pointer-events-none absolute -bottom-32 -right-32 h-96 w-96 rounded-full bg-teal-500/20 blur-3xl" />

        <div className="relative z-10 max-w-lg text-center lg:text-left">
          {/* Logo and heartbeat line */}
          <Link href="/" className="mb-8 inline-block">
            <div className="flex items-center gap-3">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-blue-400 to-teal-400 shadow-lg shadow-teal-500/20">
                <svg
                  className="h-7 w-7 text-white"
                  fill="none"
                  viewBox="0 0 24 24"
                  strokeWidth={2}
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M21 8.25c0-2.485-2.099-4.5-4.688-4.5-1.935 0-3.597 1.126-4.312 2.733-.715-1.607-2.377-2.733-4.313-2.733C5.1 3.75 3 5.765 3 8.25c0 7.22 9 12 9 12s9-4.78 9-12z"
                  />
                </svg>
              </div>
              <span className="text-2xl font-bold text-white">
                MedAssist <span className="text-teal-400">AI</span>
              </span>
            </div>
          </Link>

          {/* Heartbeat animation line */}
          <div className="mb-10 flex items-center gap-2">
            <svg
              viewBox="0 0 200 40"
              className="h-8 w-48 text-teal-400"
              fill="none"
              strokeWidth={2}
              stroke="currentColor"
            >
              <polyline
                points="0,20 30,20 40,20 50,5 60,35 70,10 80,30 90,20 120,20 200,20"
                className="animate-[dash_2.5s_ease-in-out_infinite]"
                strokeDasharray="200"
                strokeDashoffset="200"
                style={{
                  animation: "dash 2.5s ease-in-out infinite",
                }}
              />
              <style>{`
                @keyframes dash {
                  0% { stroke-dashoffset: 200; opacity: 0.3; }
                  50% { stroke-dashoffset: 0; opacity: 1; }
                  100% { stroke-dashoffset: -200; opacity: 0.3; }
                }
              `}</style>
            </svg>
          </div>

          {/* Tagline */}
          <h1 className="mb-4 text-4xl font-bold leading-tight tracking-tight text-white lg:text-5xl">
            AI-Powered Healthcare,{" "}
            <span className="bg-gradient-to-r from-blue-400 to-teal-400 bg-clip-text text-transparent">
              Reimagined
            </span>
          </h1>
          <p className="mb-12 text-lg text-blue-200/70">
            The intelligent medical platform that empowers clinicians with
            real-time insights, automated monitoring, and AI-driven decision
            support.
          </p>

          {/* Feature cards */}
          <div className="flex flex-col gap-4 sm:flex-row lg:flex-col xl:flex-row">
            {/* Card 1 */}
            <div className="group flex-1 rounded-2xl border border-white/10 bg-white/5 p-5 backdrop-blur-md transition-all duration-300 hover:border-white/20 hover:bg-white/10">
              <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-lg bg-blue-500/20 text-blue-400 transition-colors group-hover:bg-blue-500/30">
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 00-2.455 2.456z" />
                </svg>
              </div>
              <h3 className="mb-1 text-sm font-semibold text-white">7 AI Agents</h3>
              <p className="text-xs leading-relaxed text-blue-200/50">
                Specialized medical intelligence
              </p>
            </div>

            {/* Card 2 */}
            <div className="group flex-1 rounded-2xl border border-white/10 bg-white/5 p-5 backdrop-blur-md transition-all duration-300 hover:border-white/20 hover:bg-white/10">
              <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-lg bg-teal-500/20 text-teal-400 transition-colors group-hover:bg-teal-500/30">
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z" />
                </svg>
              </div>
              <h3 className="mb-1 text-sm font-semibold text-white">Real-Time Monitoring</h3>
              <p className="text-xs leading-relaxed text-blue-200/50">
                24/7 patient surveillance
              </p>
            </div>

            {/* Card 3 */}
            <div className="group flex-1 rounded-2xl border border-white/10 bg-white/5 p-5 backdrop-blur-md transition-all duration-300 hover:border-white/20 hover:bg-white/10">
              <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-lg bg-emerald-500/20 text-emerald-400 transition-colors group-hover:bg-emerald-500/30">
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
                </svg>
              </div>
              <h3 className="mb-1 text-sm font-semibold text-white">HIPAA Compliant</h3>
              <p className="text-xs leading-relaxed text-blue-200/50">
                Enterprise-grade security
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* RIGHT SIDE - Form */}
      <div className="flex w-full items-center justify-center bg-white px-6 py-12 lg:w-[40%] lg:px-12">
        <div className="w-full max-w-md">{children}</div>
      </div>
    </div>
  );
}
