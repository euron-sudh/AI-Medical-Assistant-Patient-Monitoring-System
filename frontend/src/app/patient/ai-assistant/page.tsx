"use client";

import { Bell, Bot, Search, Video } from "lucide-react";
import {
  VoiceControlsPanel,
  VoiceTranscriptPanel,
} from "@/components/voice/VoiceRealtime";
import { useVoiceRealtime } from "@/hooks/useVoiceRealtime";

function StatusPill() {
  return (
    <div className="flex items-center gap-2 rounded-full border border-border bg-muted/60 px-3 py-1.5 text-xs text-muted-foreground dark:bg-muted/40">
      <span className="flex items-center gap-2">
        <span className="relative flex h-2 w-2">
          <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-70" />
          <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-500" />
        </span>
        <span className="font-medium text-foreground">AI Connected</span>
      </span>
      <span className="text-muted-foreground/35" aria-hidden>
        |
      </span>
      <span className="hidden text-muted-foreground sm:inline">Realtime voice</span>
      <span className="sm:hidden">Voice</span>
    </div>
  );
}

function VoiceVisualizerLight() {
  return (
    <div className="pointer-events-none flex h-16 items-end justify-center gap-1 opacity-90">
      {Array.from({ length: 16 }).map((_, i) => (
        <div
          key={i}
          className="w-1 rounded-full bg-[#3B82F6]/70 dark:bg-sky-400/80"
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
    <div className="-m-8 flex h-[calc(100vh-4rem)] flex-col overflow-hidden bg-slate-100 dark:bg-background">
      <div className="flex min-h-0 flex-1 flex-col overflow-hidden rounded-l-[2rem] border-l border-slate-200/80 bg-slate-50 shadow-[inset_0_1px_0_rgba(255,255,255,0.8)] dark:border-slate-800 dark:bg-slate-950/40 dark:shadow-none">
        <header className="z-20 flex min-h-[4.5rem] shrink-0 flex-wrap items-center justify-between gap-3 border-b border-slate-200/90 bg-white/90 px-4 py-2 backdrop-blur-md dark:border-slate-800 dark:bg-card/95 md:flex-nowrap md:px-8 md:py-0">
          <div className="flex min-w-0 items-center gap-3 md:gap-4">
            <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-[#3B82F6] text-white shadow-sm dark:bg-sky-600">
              <Video className="h-5 w-5" />
            </div>
            <div className="min-w-0">
              <h1 className="truncate text-base font-bold text-slate-900 dark:text-foreground md:text-lg">
                AI Medical Assistant
              </h1>
              <p className="text-xs text-muted-foreground">Voice session</p>
            </div>
          </div>

          <div className="flex w-full flex-wrap items-center justify-end gap-2 sm:w-auto md:gap-3">
            <StatusPill />
            <div className="relative hidden w-56 lg:block xl:w-64">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <input
                type="text"
                placeholder="Search medical terms..."
                className="w-full rounded-full border border-input bg-muted/40 py-2 pl-9 pr-4 text-sm text-foreground outline-none placeholder:text-muted-foreground focus:border-primary/40 focus:bg-background focus:ring-2 focus:ring-primary/15"
              />
            </div>
            <button
              type="button"
              className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-input bg-background text-muted-foreground shadow-sm transition-colors hover:border-primary/30 hover:text-primary"
            >
              <Bell className="h-4 w-4" />
            </button>
            <button
              type="button"
              onClick={voice.cleanup}
              className="rounded-xl border border-destructive/20 bg-destructive/10 px-3 py-2 text-sm font-semibold text-destructive transition-colors hover:bg-destructive/15 dark:border-destructive/30 dark:bg-destructive/20"
            >
              End session
            </button>
          </div>
        </header>

        {/* Three columns — reference layout */}
        <div className="grid min-h-0 flex-1 grid-cols-1 gap-5 overflow-hidden p-5 lg:grid-cols-12 lg:gap-6 lg:p-6">
          {/* Left — avatar & identity */}
          <aside className="flex min-h-0 flex-col gap-4 lg:col-span-3 lg:overflow-y-auto">
            <div className="rounded-2xl border border-slate-200/80 bg-card p-6 shadow-[0_4px_24px_rgba(15,23,42,0.06)] dark:border-slate-800 dark:shadow-[0_4px_24px_rgba(0,0,0,0.35)]">
              <div className="flex flex-col items-center text-center">
                <div className="relative mb-5">
                  <div className="absolute inset-0 scale-110 rounded-full bg-gradient-to-br from-blue-100/80 to-sky-100/40 blur-xl dark:from-blue-900/30 dark:to-sky-900/20" />
                  <div className="relative flex h-36 w-36 items-center justify-center rounded-full bg-gradient-to-br from-slate-50 to-blue-50 p-1 shadow-inner ring-4 ring-[#3B82F6]/15 dark:from-slate-800 dark:to-slate-900 dark:ring-sky-500/25">
                    <div className="flex h-full w-full items-center justify-center rounded-full bg-background shadow-sm dark:bg-slate-900">
                      <Bot className="h-16 w-16 text-[#3B82F6] dark:text-sky-400" strokeWidth={1.15} />
                    </div>
                  </div>
                  <span
                    className="absolute bottom-2 right-2 h-4 w-4 rounded-full border-[3px] border-white bg-emerald-500 shadow-sm dark:border-slate-900"
                    title="Online"
                  />
                </div>

                <h2 className="text-base font-bold text-foreground">AI Medical Assistant</h2>
                <p className="mt-1 text-sm text-muted-foreground">Specialized in General Medicine</p>

                <div className="mt-6 w-full">
                  <VoiceVisualizerLight />
                </div>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="rounded-xl border border-sky-100 bg-sky-50 px-3 py-3 shadow-sm dark:border-sky-900/50 dark:bg-sky-950/40">
                <div className="text-[10px] font-semibold uppercase tracking-wide text-sky-700/80 dark:text-sky-300/90">
                  Response time
                </div>
                <div className="text-xl font-bold text-sky-900 dark:text-sky-100">~24ms</div>
              </div>
              <div className="rounded-xl border border-emerald-100 bg-emerald-50 px-3 py-3 shadow-sm dark:border-emerald-900/50 dark:bg-emerald-950/40">
                <div className="text-[10px] font-semibold uppercase tracking-wide text-emerald-700/80 dark:text-emerald-300/90">
                  Accuracy
                </div>
                <div className="text-xl font-bold text-emerald-900 dark:text-emerald-100">99.8%</div>
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
