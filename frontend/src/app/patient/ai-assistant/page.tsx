"use client";

import { useMemo } from "react";
import { Bell, FileText, Search, Video } from "lucide-react";
import VoiceRealtime from "@/components/voice/VoiceRealtime";
import { useAuth } from "@/hooks/useAuth";

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

export default function AiAssistantPage() {
  const { user } = useAuth();
  const _patientId = user?.id ?? "";

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

          <div className="flex items-center gap-4">
            <div className="relative hidden w-64 md:block">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
              <input
                type="text"
                placeholder="Search medical terms..."
                className="w-full rounded-full bg-slate-100/80 py-2 pl-9 pr-4 text-sm outline-none ring-0 focus:bg-white focus:ring-2 focus:ring-sky-500/20"
              />
            </div>
            <button className="flex h-10 w-10 items-center justify-center rounded-full border border-slate-200 bg-white text-slate-600 shadow-sm transition-colors hover:border-sky-200 hover:text-sky-600">
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
            <div
              className="absolute inset-0 opacity-80 mix-blend-luminosity"
              style={{
                backgroundImage:
                  "url('https://storage.googleapis.com/uxpilot-auth.appspot.com/843cfccd25-cb61b2ec80857f53f340.png')",
                backgroundSize: "cover",
                backgroundPosition: "center",
              }}
            />
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
              <VoiceRealtime />
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

