"use client";

import { Bell, Bot, Search, Video } from "lucide-react";
import {
  VoiceControlsPanel,
  VoiceTranscriptPanel,
} from "@/components/voice/VoiceRealtime";
import { useVoiceRealtime } from "@/hooks/useVoiceRealtime";

function StatusPill() {
  return (
    <div className="flex items-center gap-2 text-xs text-slate-500">
      <span className="flex items-center gap-2">
        <span className="relative flex h-2 w-2">
          <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-70" />
          <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-500" />
        </span>
        Online
      </span>
      <span>•</span>
      <span className="text-slate-400">Realtime voice</span>
    </div>
  );
}

function VoiceVisualizerLight() {
  return (
    <div className="pointer-events-none flex h-16 items-end justify-center gap-1 opacity-90">
      {Array.from({ length: 16 }).map((_, i) => (
        <div
          key={i}
          className="w-1 rounded-full bg-[#3B82F6]/70"
          style={{
            height: `${8 + ((i * 31) % 24)}px`,
            animation: `voicePulseLight 0.${(i % 6) + 5}s ease-in-out infinite alternate`,
          }}
        />
      ))}
      <style jsx>{`
        @keyframes voicePulseLight {
          from {
            transform: scaleY(0.35);
            opacity: 0.45;
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
  const voice = useVoiceRealtime();

  return (
    <div className="-m-8 flex h-[calc(100vh-4rem)] flex-col overflow-hidden bg-slate-100">
      <div className="flex min-h-0 flex-1 flex-col overflow-hidden rounded-l-[2rem] border-l border-slate-200/80 bg-slate-50 shadow-[inset_0_1px_0_rgba(255,255,255,0.8)]">
        {/* Header — light */}
        <header className="z-20 flex h-[4.5rem] shrink-0 items-center justify-between border-b border-slate-200/90 bg-white/90 px-6 backdrop-blur-md md:px-8">
          <div className="flex items-center gap-4">
            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-[#3B82F6] text-white shadow-sm">
              <Video className="h-5 w-5" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-slate-900">AI Medical Assistant</h1>
              <StatusPill />
            </div>
          </div>

          <div className="flex items-center gap-3 md:gap-4">
            <div className="relative hidden w-56 lg:block xl:w-64">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
              <input
                type="text"
                placeholder="Search medical terms..."
                className="w-full rounded-full border border-slate-200 bg-slate-50 py-2 pl-9 pr-4 text-sm text-slate-800 outline-none placeholder:text-slate-400 focus:border-[#3B82F6]/40 focus:bg-white focus:ring-2 focus:ring-blue-500/15"
              />
            </div>
            <button
              type="button"
              className="flex h-10 w-10 items-center justify-center rounded-xl border border-slate-200 bg-white text-slate-600 shadow-sm transition-colors hover:border-slate-300 hover:text-[#3B82F6]"
            >
              <Bell className="h-4 w-4" />
            </button>
            <button
              type="button"
              onClick={voice.cleanup}
              className="rounded-xl border border-red-100 bg-red-50 px-4 py-2 text-sm font-semibold text-red-600 transition-colors hover:bg-red-100"
            >
              End session
            </button>
          </div>
        </header>

        {/* Three columns — reference layout */}
        <div className="grid min-h-0 flex-1 grid-cols-1 gap-5 overflow-hidden p-5 lg:grid-cols-12 lg:gap-6 lg:p-6">
          {/* Left — avatar & identity */}
          <aside className="flex min-h-0 flex-col gap-4 lg:col-span-3 lg:overflow-y-auto">
            <div className="rounded-2xl border border-slate-200/80 bg-white p-6 shadow-[0_4px_24px_rgba(15,23,42,0.06)]">
              <div className="flex flex-col items-center text-center">
                <div className="relative mb-5">
                  <div className="absolute inset-0 scale-110 rounded-full bg-gradient-to-br from-blue-100/80 to-sky-100/40 blur-xl" />
                  <div className="relative flex h-36 w-36 items-center justify-center rounded-full bg-gradient-to-br from-slate-50 to-blue-50 p-1 shadow-inner ring-4 ring-[#3B82F6]/15">
                    <div className="flex h-full w-full items-center justify-center rounded-full bg-white shadow-sm">
                      <Bot className="h-16 w-16 text-[#3B82F6]" strokeWidth={1.15} />
                    </div>
                  </div>
                  <span
                    className="absolute bottom-2 right-2 h-4 w-4 rounded-full border-[3px] border-white bg-emerald-500 shadow-sm"
                    title="Online"
                  />
                </div>

                <h2 className="text-base font-bold text-slate-900">AI Medical Assistant</h2>
                <p className="mt-1 text-sm text-slate-500">Specialized in General Medicine</p>

                <div className="mt-6 w-full">
                  <VoiceVisualizerLight />
                </div>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="rounded-xl border border-sky-100 bg-sky-50 px-3 py-3 shadow-sm">
                <div className="text-[10px] font-semibold uppercase tracking-wide text-sky-700/80">
                  Response time
                </div>
                <div className="text-xl font-bold text-sky-900">~24ms</div>
              </div>
              <div className="rounded-xl border border-emerald-100 bg-emerald-50 px-3 py-3 shadow-sm">
                <div className="text-[10px] font-semibold uppercase tracking-wide text-emerald-700/80">
                  Accuracy
                </div>
                <div className="text-xl font-bold text-emerald-900">99.8%</div>
              </div>
            </div>
          </aside>

          {/* Center — transcript */}
          <section className="flex h-full min-h-0 flex-col lg:col-span-6">
            <VoiceTranscriptPanel voice={voice} />
          </section>

          {/* Right — controls & vitals */}
          <aside className="min-h-0 overflow-y-auto lg:col-span-3 scrollbar-thin">
            <VoiceControlsPanel voice={voice} />
          </aside>
        </div>
      </div>
    </div>
  );
}
