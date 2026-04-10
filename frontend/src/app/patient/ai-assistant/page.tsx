"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { Bell, FileText, Globe, Upload, Video } from "lucide-react";
import VoiceRealtime from "@/components/voice/VoiceRealtime";
import { useAuth } from "@/hooks/useAuth";

const LANGUAGES: { code: string; label: string; flag: string }[] = [
  { code: "en", label: "English", flag: "🇬🇧" },
  { code: "hi", label: "हिन्दी Hindi", flag: "🇮🇳" },
  { code: "es", label: "Español", flag: "🇪🇸" },
  { code: "fr", label: "Français", flag: "🇫🇷" },
  { code: "de", label: "Deutsch", flag: "🇩🇪" },
  { code: "ar", label: "العربية", flag: "🇸🇦" },
  { code: "zh", label: "中文", flag: "🇨🇳" },
];

function StatusPill() {
  return (
    <div className="flex items-center gap-2 text-xs text-muted-foreground">
      <span className="flex items-center gap-2">
        <span className="relative flex h-2 w-2">
          <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-70" />
          <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-500" />
        </span>
        Session Active
      </span>
      <span>•</span>
      <span>Realtime</span>
    </div>
  );
}

function VoiceVisualizer() {
  // lightweight CSS visualizer (no Plotly)
  return (
    <div className="pointer-events-none absolute bottom-24 left-0 right-0 z-20 flex h-40 items-end justify-center gap-2 opacity-80">
      {Array.from({ length: 18 }).map((_, i) => (
        <div
          key={i}
          className="w-1.5 rounded-full bg-sky-400/80"
          style={{
            height: `${12 + ((i * 37) % 32)}px`,
            animation: `voicePulse 0.${(i % 7) + 6}s ease-in-out infinite alternate`,
          }}
        />
      ))}
      <style jsx>{`
        @keyframes voicePulse {
          from {
            transform: scaleY(0.35);
            opacity: 0.55;
          }
          to {
            transform: scaleY(1);
            opacity: 1;
          }
        }
      `}</style>
    </div>
  );
}

function DoctorAvatar() {
  // Inline SVG doctor portrait — no external dependency, always loads.
  return (
    <svg
      viewBox="0 0 400 500"
      className="absolute inset-0 h-full w-full"
      preserveAspectRatio="xMidYMid slice"
      aria-hidden="true"
    >
      <defs>
        <radialGradient id="halo" cx="50%" cy="30%" r="70%">
          <stop offset="0%" stopColor="#38bdf8" stopOpacity="0.45" />
          <stop offset="60%" stopColor="#0ea5e9" stopOpacity="0.12" />
          <stop offset="100%" stopColor="#020617" stopOpacity="0" />
        </radialGradient>
        <linearGradient id="coat" x1="0" x2="0" y1="0" y2="1">
          <stop offset="0%" stopColor="#f8fafc" />
          <stop offset="100%" stopColor="#cbd5e1" />
        </linearGradient>
        <linearGradient id="skin" x1="0" x2="0" y1="0" y2="1">
          <stop offset="0%" stopColor="#fde6d3" />
          <stop offset="100%" stopColor="#e9c4a4" />
        </linearGradient>
      </defs>
      <rect width="400" height="500" fill="#050b18" />
      <circle cx="200" cy="180" r="260" fill="url(#halo)" />

      {/* Shoulders / coat */}
      <path
        d="M 60 500 Q 60 360 150 330 L 250 330 Q 340 360 340 500 Z"
        fill="url(#coat)"
      />
      {/* Stethoscope loop */}
      <path
        d="M 150 345 Q 200 430 250 345"
        fill="none"
        stroke="#0f172a"
        strokeWidth="6"
        strokeLinecap="round"
        opacity="0.85"
      />
      <circle cx="200" cy="430" r="9" fill="#e2e8f0" stroke="#0f172a" strokeWidth="3" />
      {/* Collar line */}
      <path d="M 150 330 L 200 380 L 250 330" fill="#f1f5f9" stroke="#94a3b8" strokeWidth="2" />

      {/* Neck */}
      <rect x="180" y="290" width="40" height="50" rx="8" fill="url(#skin)" />

      {/* Head */}
      <ellipse cx="200" cy="220" rx="78" ry="92" fill="url(#skin)" />
      {/* Hair */}
      <path
        d="M 130 200 Q 140 120 200 115 Q 265 115 275 200 Q 260 165 200 160 Q 145 170 130 200 Z"
        fill="#1e293b"
      />
      {/* Eyes */}
      <ellipse cx="175" cy="225" rx="6" ry="4" fill="#0f172a" />
      <ellipse cx="225" cy="225" rx="6" ry="4" fill="#0f172a" />
      {/* Smile */}
      <path
        d="M 180 260 Q 200 278 220 260"
        fill="none"
        stroke="#9a3412"
        strokeWidth="3"
        strokeLinecap="round"
      />
      {/* Glow ring around head */}
      <circle
        cx="200"
        cy="220"
        r="108"
        fill="none"
        stroke="#38bdf8"
        strokeWidth="1.5"
        opacity="0.4"
      />
    </svg>
  );
}

export default function AiAssistantPage() {
  const { user } = useAuth();
  const _patientId = user?.id ?? "";
  const [language, setLanguage] = useState<string>("en");
  const [langOpen, setLangOpen] = useState(false);

  const currentLang = useMemo(
    () => LANGUAGES.find((l) => l.code === language) ?? LANGUAGES[0],
    [language],
  );

  return (
    <div className="-m-8 h-[calc(100vh-4rem)] overflow-hidden bg-[#0F1115]">
      {/* Main content wrapper styled like reference */}
      <div className="relative flex h-full flex-col overflow-hidden rounded-l-[2rem] bg-slate-50 shadow-[-10px_0_30px_rgba(0,0,0,0.5)]">
        {/* Header */}
        <header className="z-20 flex h-20 items-center justify-between border-b border-slate-100 bg-white/60 px-8 backdrop-blur">
          <div className="flex items-center gap-4">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-sky-50 text-sky-600">
              <Video className="h-5 w-5" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-slate-900">AI Medical Assistant</h1>
              <StatusPill />
            </div>
          </div>

          <div className="flex items-center gap-3">
            {/* Language picker */}
            <div className="relative">
              <button
                type="button"
                onClick={() => setLangOpen((v) => !v)}
                className="flex items-center gap-2 rounded-full border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-700 shadow-sm transition-colors hover:border-sky-200 hover:text-sky-700"
                aria-haspopup="menu"
                aria-expanded={langOpen}
              >
                <Globe className="h-4 w-4 text-sky-600" />
                <span className="hidden sm:inline">
                  {currentLang.flag} {currentLang.label}
                </span>
                <span className="sm:hidden">{currentLang.flag}</span>
              </button>
              {langOpen && (
                <div
                  className="absolute right-0 z-50 mt-2 w-48 overflow-hidden rounded-xl border border-slate-200 bg-white shadow-lg"
                  role="menu"
                >
                  {LANGUAGES.map((lang) => (
                    <button
                      key={lang.code}
                      type="button"
                      onClick={() => {
                        setLanguage(lang.code);
                        setLangOpen(false);
                      }}
                      className={`flex w-full items-center gap-2 px-4 py-2 text-left text-sm transition-colors hover:bg-slate-50 ${
                        language === lang.code ? "bg-sky-50 text-sky-700" : "text-slate-700"
                      }`}
                      role="menuitem"
                    >
                      <span>{lang.flag}</span>
                      <span>{lang.label}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>

            <Link
              href="/patient/reports"
              className="hidden items-center gap-2 rounded-full border border-sky-100 bg-sky-50 px-3 py-2 text-sm font-medium text-sky-700 shadow-sm transition-colors hover:bg-sky-100 sm:flex"
            >
              <Upload className="h-4 w-4" />
              Upload Report
            </Link>

            <button
              className="flex h-10 w-10 items-center justify-center rounded-full border border-slate-200 bg-white text-slate-600 shadow-sm transition-colors hover:border-sky-200 hover:text-sky-600"
              aria-label="Notifications"
            >
              <Bell className="h-4 w-4" />
            </button>
            <button className="rounded-lg border border-red-100 bg-red-50 px-4 py-2 text-sm font-medium text-red-600 transition-colors hover:bg-red-100">
              End Session
            </button>
          </div>
        </header>

        {/* Content */}
        <div className="flex flex-1 gap-6 overflow-hidden p-6">
          {/* Left: Avatar stage */}
          <div className="group relative flex flex-1 flex-col overflow-hidden rounded-[24px] border border-slate-800/30 bg-[#0F1115] shadow-lg">
            <div className="absolute inset-0 bg-gradient-to-br from-slate-900 via-[#0F1115] to-black" />
            <DoctorAvatar />
            <div className="absolute inset-0 bg-gradient-to-t from-black via-black/40 to-transparent" />
            <div className="absolute inset-0 bg-sky-500/10 mix-blend-overlay" />

            {/* HUD */}
            <div className="pointer-events-none absolute left-6 right-6 top-6 z-20 flex items-start justify-between">
              <div className="pointer-events-auto rounded-2xl border border-white/10 bg-white/5 p-3 backdrop-blur-xl">
                <div className="flex items-center gap-3">
                  <div className="relative flex h-8 w-8 items-center justify-center">
                    <div className="absolute inset-0 rounded-full bg-sky-500/30 blur-sm" />
                    <div className="h-3 w-3 rounded-full bg-sky-400 shadow-[0_0_10px_rgba(96,165,250,0.8)]" />
                  </div>
                  <div>
                    <div className="text-[10px] font-medium uppercase tracking-wider text-slate-300/70">
                      System Status
                    </div>
                    <div className="text-sm font-semibold text-white">
                      Always Listening <span className="text-slate-400">•</span> Dr. Sarah
                    </div>
                  </div>
                </div>
              </div>

              <div className="pointer-events-auto rounded-xl border border-white/10 bg-white/5 px-4 py-2 text-xs font-medium text-white backdrop-blur-xl">
                Latency: ~ realtime
              </div>
            </div>

            <VoiceVisualizer />

            {/* Action */}
            <div className="absolute bottom-8 right-8 z-30">
              <button className="flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-sm font-medium text-white shadow-lg backdrop-blur-xl transition-colors hover:bg-white/10">
                <FileText className="h-4 w-4 text-sky-300" />
                Generate Report
              </button>
            </div>
          </div>

          {/* Right: Realtime controls + History */}
          <div className="flex w-80 flex-shrink-0 flex-col gap-6 overflow-y-auto pb-4">
            <div className="rounded-[24px] border border-slate-100 bg-white p-4 shadow-sm">
              <VoiceRealtime language={language} />
            </div>

            <div className="flex-1 rounded-[24px] border border-slate-100 bg-white p-5 shadow-sm">
              <div className="mb-4 flex items-center justify-between">
                <h3 className="text-sm font-semibold text-slate-800">Recent History</h3>
                <button className="text-slate-400 hover:text-slate-600">•••</button>
              </div>
              <div className="relative mt-2 space-y-6 border-l-2 border-slate-100 pl-3">
                <div className="relative">
                  <div className="absolute -left-[19px] top-1 h-3 w-3 rounded-full border-2 border-white bg-sky-500" />
                  <div className="mb-1 text-xs text-slate-400">Today</div>
                  <div className="text-sm font-medium text-slate-800">Voice session</div>
                  <div className="mt-1 text-xs text-slate-500">
                    AI is collecting symptoms and recommending tests.
                  </div>
                </div>
                <div className="relative">
                  <div className="absolute -left-[19px] top-1 h-3 w-3 rounded-full border-2 border-white bg-slate-300" />
                  <div className="mb-1 text-xs text-slate-400">Last week</div>
                  <div className="text-sm font-medium text-slate-800">Vitals upload</div>
                  <div className="mt-1 text-xs text-slate-500">Monitoring data received from device.</div>
                </div>
                <div className="relative">
                  <div className="absolute -left-[19px] top-1 h-3 w-3 rounded-full border-2 border-white bg-slate-300" />
                  <div className="mb-1 text-xs text-slate-400">Last month</div>
                  <div className="text-sm font-medium text-slate-800">Routine checkup</div>
                  <div className="mt-1 text-xs text-slate-500">Follow-up recommended.</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

