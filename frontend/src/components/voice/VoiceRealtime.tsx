"use client";

import {
  Bot,
  Download,
  Loader2,
  MessageSquare,
  RefreshCcw,
  Share2,
  Square,
  User,
  Volume2,
  VolumeX,
} from "lucide-react";
import { useVoiceRealtime, type VoiceRealtimeState } from "@/hooks/useVoiceRealtime";

type Props = { voice: VoiceRealtimeState };

function formatTime(d: Date) {
  return d.toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit" });
}

export function VoiceTranscriptPanel({ voice }: Props) {
  const {
    thread,
    assistantText,
    userText,
    threadEndRef,
    exportTranscript,
    error,
    isSessionActive,
    status,
  } = voice;

  const showTyping = Boolean(assistantText);

  return (
    <div className="flex h-full min-h-0 flex-col overflow-hidden rounded-2xl border border-slate-200/80 bg-white shadow-[0_4px_24px_rgba(15,23,42,0.06)]">
      {/* Blue header — reference */}
      <div className="flex shrink-0 items-start justify-between gap-3 rounded-t-2xl bg-[#3B82F6] px-4 py-3 text-white">
        <div className="flex items-start gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-white/15">
            <MessageSquare className="h-5 w-5" />
          </div>
          <div>
            <h2 className="text-base font-semibold leading-tight">Conversation Transcript</h2>
            <p className="text-xs text-blue-100/90">Real-time voice-to-text</p>
          </div>
        </div>
        <button
          type="button"
          onClick={exportTranscript}
          className="shrink-0 rounded-lg bg-white/15 px-3 py-1.5 text-xs font-semibold transition-colors hover:bg-white/25"
        >
          Export
        </button>
      </div>

      {/* Thread */}
      <div className="min-h-0 flex-1 space-y-3 overflow-y-auto bg-slate-50/80 px-4 py-4 scrollbar-thin">
        {thread.length === 0 && !assistantText && !userText && (
          <div className="flex flex-col items-center justify-center gap-2 py-16 text-center">
            <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-blue-50 text-[#3B82F6]">
              <MessageSquare className="h-7 w-7" />
            </div>
            <p className="text-sm font-medium text-slate-700">No messages yet</p>
            <p className="max-w-xs text-xs text-slate-500">
              Use Start / Reconnect in the panel on the right. Your conversation will appear here.
            </p>
          </div>
        )}

        {thread.map((m) => (
          <div
            key={m.id}
            className={`flex gap-2 ${m.role === "user" ? "justify-end" : "justify-start"}`}
          >
            {m.role === "assistant" && (
              <div className="mt-1 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[#3B82F6] text-white shadow-sm">
                <Bot className="h-4 w-4" />
              </div>
            )}
            <div
              className={`max-w-[min(100%,28rem)] rounded-2xl px-3.5 py-2.5 text-sm leading-relaxed shadow-sm ${
                m.role === "user"
                  ? "rounded-br-md bg-[#3B82F6] text-white"
                  : "rounded-bl-md border border-slate-100 bg-white text-slate-800"
              }`}
            >
              <p className="whitespace-pre-wrap">{m.content}</p>
              <p
                className={`mt-1.5 text-[11px] ${
                  m.role === "user" ? "text-blue-100" : "text-slate-400"
                }`}
              >
                {formatTime(m.ts)}
              </p>
            </div>
            {m.role === "user" && (
              <div className="mt-1 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-slate-200 text-slate-600 ring-2 ring-white">
                <User className="h-4 w-4" />
              </div>
            )}
          </div>
        ))}

        {showTyping && (
          <div className="flex gap-2 justify-start">
            <div className="mt-1 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[#3B82F6] text-white shadow-sm">
              <Bot className="h-4 w-4" />
            </div>
            <div className="max-w-[min(100%,28rem)] rounded-2xl rounded-bl-md border border-slate-100 bg-white px-3.5 py-3 text-sm text-slate-700 shadow-sm">
              <div className="mb-2 flex gap-1">
                <span className="h-2 w-2 animate-bounce rounded-full bg-slate-400 [animation-delay:-0.2s]" />
                <span className="h-2 w-2 animate-bounce rounded-full bg-slate-400 [animation-delay:-0.1s]" />
                <span className="h-2 w-2 animate-bounce rounded-full bg-slate-400" />
              </div>
              {assistantText ? (
                <p className="whitespace-pre-wrap text-slate-800">{assistantText}</p>
              ) : null}
            </div>
          </div>
        )}

        {userText && !assistantText ? (
          <div className="flex gap-2 justify-end">
            <div className="max-w-[min(100%,28rem)] rounded-2xl rounded-br-md bg-[#3B82F6] px-3.5 py-2.5 text-sm text-white shadow-sm">
              <p className="whitespace-pre-wrap">{userText}</p>
              <p className="mt-1.5 text-[11px] text-blue-100">Transcribing…</p>
            </div>
            <div className="mt-1 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-slate-200 text-slate-600 ring-2 ring-white">
              <User className="h-4 w-4" />
            </div>
          </div>
        ) : null}

        <div ref={threadEndRef} />
      </div>

      {/* Footer strip */}
      <div className="flex shrink-0 items-center justify-between gap-3 border-t border-slate-200 bg-white px-4 py-3">
        <p className="text-xs text-slate-500">Voice input active — speak naturally…</p>
        <div className="flex items-center gap-2 text-xs font-medium text-slate-700">
          {isSessionActive && status === "connected" ? (
            <>
              <span className="relative flex h-2.5 w-2.5">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-red-500 opacity-60" />
                <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-red-500" />
              </span>
              Listening
            </>
          ) : status === "connecting" || status === "creating_session" ? (
            <>
              <Loader2 className="h-3.5 w-3.5 animate-spin text-[#3B82F6]" />
              Connecting
            </>
          ) : (
            <span className="text-slate-400">Idle</span>
          )}
        </div>
      </div>

      {error && (
        <div className="shrink-0 border-t border-red-100 bg-red-50 px-4 py-2 text-xs text-red-700">
          {error}
        </div>
      )}
    </div>
  );
}

export function VoiceControlsPanel({ voice }: Props) {
  const {
    status,
    cleanup,
    restart,
    ttsEnabled,
    setTtsEnabled,
    volume,
    setVolume,
    playbackRate,
    setPlaybackRate,
    remoteAudioRef,
    exportTranscript,
    isSessionActive,
    canUseWebRTC,
    logs,
    generateLabReportAndDownload,
    labReportLoading,
    labReportError,
  } = voice;

  const busy = status === "creating_session" || status === "connecting";

  return (
    <div className="flex flex-col gap-4">
      <audio ref={remoteAudioRef} className="hidden" />

      {/* Voice controls card */}
      <div className="rounded-2xl border border-slate-200/80 bg-white p-4 shadow-[0_4px_24px_rgba(15,23,42,0.06)]">
        <h3 className="mb-3 text-sm font-semibold text-slate-800">Voice</h3>

        {isSessionActive ? (
          <button
            type="button"
            onClick={cleanup}
            className="mb-4 flex w-full items-center justify-center gap-2 rounded-xl bg-red-600 py-3 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-red-700"
          >
            <Square className="h-4 w-4 fill-current" />
            Stop
          </button>
        ) : (
          <button
            type="button"
            onClick={() => void restart()}
            disabled={!canUseWebRTC || busy}
            className="mb-4 flex w-full items-center justify-center gap-2 rounded-xl bg-emerald-600 py-3 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-emerald-700 disabled:opacity-50"
          >
            {busy ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <RefreshCcw className="h-4 w-4" />
            )}
            Start / Reconnect
          </button>
        )}

        <div className="space-y-3 border-t border-slate-100 pt-4">
          <div>
            <div className="mb-1.5 flex justify-between text-xs font-medium text-slate-600">
              <span>Volume</span>
              <span>{Math.round(volume * 100)}%</span>
            </div>
            <input
              type="range"
              min={0}
              max={1}
              step={0.05}
              value={volume}
              onChange={(e) => setVolume(Number(e.target.value))}
              className="h-2 w-full cursor-pointer accent-[#3B82F6]"
            />
          </div>
          <div>
            <div className="mb-1.5 flex justify-between text-xs font-medium text-slate-600">
              <span>Speech speed</span>
              <span>{playbackRate.toFixed(1)}×</span>
            </div>
            <input
              type="range"
              min={0.75}
              max={1.5}
              step={0.05}
              value={playbackRate}
              onChange={(e) => setPlaybackRate(Number(e.target.value))}
              className="h-2 w-full cursor-pointer accent-[#3B82F6]"
            />
          </div>
        </div>

        <button
          type="button"
          onClick={() => setTtsEnabled((v) => !v)}
          className="mt-4 flex w-full items-center justify-center gap-2 rounded-xl border border-slate-200 bg-slate-50 py-2.5 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-100"
        >
          {ttsEnabled ? <Volume2 className="h-4 w-4" /> : <VolumeX className="h-4 w-4" />}
          {ttsEnabled ? "Mute audio" : "Unmute audio"}
        </button>
      </div>

      {/* Quick actions */}
      <div className="rounded-2xl border border-slate-200/80 bg-white p-4 shadow-[0_4px_24px_rgba(15,23,42,0.06)]">
        <h3 className="mb-3 text-sm font-semibold text-slate-800">Quick actions</h3>
        <div className="flex flex-col gap-2">
          <button
            type="button"
            onClick={() => void generateLabReportAndDownload()}
            disabled={labReportLoading}
            className="flex items-center gap-2 rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-left text-sm font-medium text-slate-700 transition-colors hover:bg-slate-100 disabled:opacity-60"
          >
            {labReportLoading ? (
              <Loader2 className="h-4 w-4 animate-spin text-slate-500" />
            ) : (
              <Download className="h-4 w-4 text-slate-500" />
            )}
            Download lab test
          </button>
          {labReportError ? (
            <p className="rounded-lg bg-red-50 px-2 py-1.5 text-xs text-red-700">{labReportError}</p>
          ) : null}
          <button
            type="button"
            onClick={exportTranscript}
            className="flex items-center gap-2 rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-left text-sm font-medium text-slate-700 transition-colors hover:bg-slate-100"
          >
            <Download className="h-4 w-4 text-slate-500" />
            Export transcript
          </button>
          <button
            type="button"
            onClick={() => {
              void navigator.clipboard?.writeText(window.location.href).catch(() => {});
            }}
            className="flex items-center gap-2 rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-left text-sm font-medium text-slate-700 transition-colors hover:bg-slate-100"
          >
            <Share2 className="h-4 w-4 text-slate-500" />
            Share session
          </button>
        </div>
      </div>

      <details className="rounded-xl border border-slate-200 bg-slate-50/80">
        <summary className="cursor-pointer px-3 py-2 text-[10px] font-semibold uppercase tracking-wider text-slate-500">
          Debug events
        </summary>
        <div className="max-h-[140px] space-y-2 overflow-auto px-2 pb-2">
          {logs.length === 0 ? (
            <p className="px-1 py-2 text-xs text-slate-500">No events yet.</p>
          ) : (
            logs
              .slice()
              .reverse()
              .map((l) => (
                <div key={l.id} className="rounded-lg border border-slate-200 bg-white p-2">
                  <div className="flex justify-between text-[10px] text-slate-500">
                    <span>{l.type}</span>
                    <span>{l.ts.toLocaleTimeString()}</span>
                  </div>
                  <pre className="mt-1 max-h-16 overflow-auto whitespace-pre-wrap text-[10px] text-slate-600">
                    {JSON.stringify(l.data, null, 2)}
                  </pre>
                </div>
              ))
          )}
        </div>
      </details>
    </div>
  );
}

/** @deprecated Use `useVoiceRealtime` with `VoiceTranscriptPanel` and `VoiceControlsPanel` on the page layout. */
export default function VoiceRealtime() {
  const voice = useVoiceRealtime();
  return (
    <div className="flex min-h-[420px] flex-col gap-4">
      <VoiceTranscriptPanel voice={voice} />
      <VoiceControlsPanel voice={voice} />
    </div>
  );
}
