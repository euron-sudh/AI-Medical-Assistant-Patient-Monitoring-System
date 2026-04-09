"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Loader2, Mic, Square, Volume2, VolumeX, RefreshCcw } from "lucide-react";
import apiClient from "@/lib/api-client";

type RealtimeSessionResponse = {
  model: string;
  voice: string;
  expires_at?: number | string | null;
  client_secret: string;
};

type LogItem = { id: string; ts: Date; type: string; data: unknown };

function safeJsonParse(input: string): unknown {
  try {
    return JSON.parse(input);
  } catch {
    return null;
  }
}

export default function VoiceRealtime() {
  const [status, setStatus] = useState<
    "idle" | "creating_session" | "connecting" | "connected" | "recording" | "error"
  >("idle");
  const [error, setError] = useState<string | null>(null);
  const [ttsEnabled, setTtsEnabled] = useState(true);
  const [assistantText, setAssistantText] = useState("");
  const [userText, setUserText] = useState("");
  const [logs, setLogs] = useState<LogItem[]>([]);

  const pcRef = useRef<RTCPeerConnection | null>(null);
  const dcRef = useRef<RTCDataChannel | null>(null);
  const localStreamRef = useRef<MediaStream | null>(null);
  const remoteAudioRef = useRef<HTMLAudioElement | null>(null);
  const lastAssistantChunkRef = useRef<string>("");
  const lastUserChunkRef = useRef<string>("");
  const introPhaseRef = useRef<"idle" | "intro_sent" | "awaiting_user" | "followup_sent">("idle");

  const canUseWebRTC = useMemo(() => {
    if (typeof window === "undefined") return false;
    return "RTCPeerConnection" in window && !!navigator.mediaDevices?.getUserMedia;
  }, []);

  const appendLog = useCallback((type: string, data: unknown) => {
    setLogs((prev) => [
      ...prev.slice(-80),
      { id: crypto.randomUUID(), ts: new Date(), type, data },
    ]);
  }, []);

  const INTRO_TEXT =
    "Hello there I am Med Assist virtual doctor I am here to assist you on your symptoms.";

  const cleanup = useCallback(() => {
    setStatus("idle");
    setError(null);
    introPhaseRef.current = "idle";
    lastAssistantChunkRef.current = "";
    lastUserChunkRef.current = "";

    try {
      dcRef.current?.close();
    } catch {
      // ignore
    }
    dcRef.current = null;

    try {
      pcRef.current?.close();
    } catch {
      // ignore
    }
    pcRef.current = null;

    const stream = localStreamRef.current;
    if (stream) stream.getTracks().forEach((t) => t.stop());
    localStreamRef.current = null;

    if (remoteAudioRef.current) remoteAudioRef.current.srcObject = null;
  }, []);

  const start = useCallback(async () => {
    if (!canUseWebRTC) {
      setError("WebRTC audio is not supported in this browser.");
      setStatus("error");
      return;
    }

    setAssistantText("");
    setUserText("");
    setLogs([]);
    setError(null);
    setStatus("creating_session");
    introPhaseRef.current = "idle";
    lastAssistantChunkRef.current = "";
    lastUserChunkRef.current = "";

    let session: RealtimeSessionResponse;
    try {
      const res = await apiClient.post<RealtimeSessionResponse>("/realtime/session", {
        model: "gpt-4o-realtime-preview",
        // Realtime voice list differs from TTS voices; use a supported preset.
        voice: "alloy",
      });
      session = res.data;
    } catch (e: unknown) {
      const data = (e as { response?: { data?: unknown } })?.response?.data;
      const details =
        (data as { error?: { details?: string; message?: string; status?: number } })?.error?.details ??
        (data as { error?: { details?: string; message?: string } })?.error?.message ??
        "";
      setError(
        details
          ? `Failed to create Realtime session: ${details}`
          : "Failed to create Realtime session. Check backend OPENAI_API_KEY and OPENAI_BASE_URL.",
      );
      setStatus("error");
      return;
    }

    setStatus("connecting");

    try {
      const pc = new RTCPeerConnection();
      pcRef.current = pc;

      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      localStreamRef.current = stream;
      for (const track of stream.getTracks()) {
        pc.addTrack(track, stream);
      }

      // Remote audio from the model
      pc.ontrack = (e) => {
        const [remoteStream] = e.streams;
        if (!remoteAudioRef.current) return;
        remoteAudioRef.current.srcObject = remoteStream;
        remoteAudioRef.current.muted = !ttsEnabled;
        remoteAudioRef.current
          .play()
          .catch(() => {
            // Autoplay may require user gesture; user can unmute/play manually
          });
      };

      const dc = pc.createDataChannel("oai-events");
      dcRef.current = dc;

      dc.onopen = () => {
        appendLog("data_channel_open", {});
        setStatus("connected");

        introPhaseRef.current = "intro_sent";

        // Phase 1: intro ONLY (no follow-up in same response)
        const msg = {
          type: "response.create",
          response: {
            modalities: ["audio", "text"],
            instructions:
              "Say ONLY this one sentence (verbatim) and then stop. Do not add any other words in any language:\n" +
              `"${INTRO_TEXT}"`,
          },
        };
        dc.send(JSON.stringify(msg));
      };

      dc.onmessage = (evt) => {
        const parsed = typeof evt.data === "string" ? safeJsonParse(evt.data) : null;
        if (!parsed || typeof parsed !== "object") return;

        const p = parsed as Record<string, unknown>;
        const type = String(p.type ?? "event");
        appendLog(type, parsed);

        // Best-effort extraction across possible event shapes.
        // Realtime often emits both incremental deltas AND full transcript snapshots,
        // which can cause duplicate text if we always append.
        const textPiece =
          (p.delta as unknown) ??
          (p.text as unknown) ??
          (p.transcript as unknown) ??
          (p.output_text as unknown);

        if (typeof textPiece === "string" && textPiece.length > 0) {
          // Heuristic: user transcription vs assistant text
          if (type.includes("input") || type.includes("transcription")) {
            const chunk = textPiece;
            if (chunk === lastUserChunkRef.current) return;
            lastUserChunkRef.current = chunk;
            setUserText((prev) => {
              // If upstream sends a full snapshot, prefer replace instead of append.
              if (chunk.startsWith(prev)) return chunk;
              if (prev.endsWith(chunk)) return prev; // duplicate
              return prev ? `${prev}${chunk}` : chunk;
            });
          } else if (type.includes("response") || type.includes("output")) {
            const chunk = textPiece;
            if (chunk === lastAssistantChunkRef.current) return;
            lastAssistantChunkRef.current = chunk;
            setAssistantText((prev) => {
              if (chunk.startsWith(prev)) return chunk; // snapshot update
              if (prev.endsWith(chunk)) return prev; // duplicate delta
              return prev ? `${prev}${chunk}` : chunk;
            });
          }
        }

        // After the intro response completes, wait for the patient's first utterance
        // before asking questions. If we ask immediately, the model may pick a random
        // language because it hasn't heard the patient yet.
        const isResponseDone =
          type.includes("response") && (type.includes("done") || type.includes("completed"));

        if (introPhaseRef.current === "intro_sent" && isResponseDone) {
          introPhaseRef.current = "awaiting_user";
        }

        const isUserSpeech =
          type.includes("input") && (type.includes("transcription") || type.includes("transcript"));

        if (introPhaseRef.current === "awaiting_user" && isUserSpeech) {
          introPhaseRef.current = "followup_sent";
          const followup = {
            type: "response.create",
            response: {
              modalities: ["audio", "text"],
              instructions:
                "Now start the medical interview.\n" +
                "- Continue in the same language as the patient's most recent utterance.\n" +
                "- If unsure, ask a short clarification question about language.\n" +
                "- Ask ONE question at a time to understand symptoms.\n" +
                "- When you have enough information, recommend appropriate medical tests and next steps.\n" +
                "- If emergency symptoms are suspected, advise calling emergency services immediately.\n\n" +
                "Ask your first question now.",
            },
          };
          dc.send(JSON.stringify(followup));
        }
      };

      dc.onerror = () => {
        setError("Realtime connection error (data channel).");
        setStatus("error");
      };

      pc.oniceconnectionstatechange = () => {
        appendLog("ice_state", { state: pc.iceConnectionState });
      };

      // SDP offer/answer exchange with OpenAI Realtime
      const offer = await pc.createOffer();
      await pc.setLocalDescription(offer);

      const sdpRes = await fetch(
        `https://api.openai.com/v1/realtime?model=${encodeURIComponent(session.model)}`,
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${session.client_secret}`,
            "Content-Type": "application/sdp",
          },
          body: offer.sdp ?? "",
        },
      );

      if (!sdpRes.ok) {
        const t = await sdpRes.text();
        throw new Error(`Realtime SDP exchange failed (${sdpRes.status}): ${t}`);
      }

      const answerSdp = await sdpRes.text();
      await pc.setRemoteDescription({ type: "answer", sdp: answerSdp });
    } catch (e: unknown) {
      const message = (e as Error)?.message ?? "Failed to connect to Realtime voice.";
      setError(message);
      setStatus("error");
      cleanup();
    }
  }, [appendLog, canUseWebRTC, cleanup, ttsEnabled]);

  useEffect(() => {
    return () => cleanup();
  }, [cleanup]);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => {
              cleanup();
              start();
            }}
            className="inline-flex items-center gap-1.5 rounded-full bg-muted px-3 py-1 text-xs font-medium text-foreground transition-colors hover:bg-muted/70"
            disabled={status === "creating_session" || status === "connecting"}
          >
            <RefreshCcw className="h-3.5 w-3.5" />
            Start / Reconnect
          </button>
          <button
            type="button"
            onClick={cleanup}
            className="inline-flex items-center gap-1.5 rounded-full bg-muted px-3 py-1 text-xs font-medium text-foreground transition-colors hover:bg-muted/70"
          >
            <Square className="h-3.5 w-3.5" />
            Stop
          </button>
        </div>

        <button
          type="button"
          onClick={() => setTtsEnabled((v) => !v)}
          className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium transition-colors ${
            ttsEnabled
              ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300"
              : "bg-muted text-muted-foreground"
          }`}
        >
          {ttsEnabled ? <Volume2 className="h-3.5 w-3.5" /> : <VolumeX className="h-3.5 w-3.5" />}
          {ttsEnabled ? "Audio On" : "Audio Off"}
        </button>
      </div>

      <div className="rounded-lg border border-border bg-card p-4">
        <div className="flex items-center gap-2 text-sm">
          <Mic className="h-4 w-4 text-muted-foreground" />
          <span className="font-medium text-foreground">Realtime voice</span>
          <span className="text-muted-foreground">({status})</span>
          {(status === "creating_session" || status === "connecting") && (
            <Loader2 className="ml-auto h-4 w-4 animate-spin text-muted-foreground" />
          )}
        </div>
        <audio ref={remoteAudioRef} className="mt-2 w-full" controls />
        <p className="mt-2 text-xs text-muted-foreground">
          Tip: If you don’t hear audio, click play on the audio control (browser autoplay policy).
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <div className="rounded-lg border border-border bg-card p-4">
          <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">You (transcript)</p>
          <p className="mt-2 whitespace-pre-wrap text-sm text-foreground">{userText || "—"}</p>
        </div>
        <div className="rounded-lg border border-border bg-card p-4">
          <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Assistant</p>
          <p className="mt-2 whitespace-pre-wrap text-sm text-foreground">{assistantText || "—"}</p>
        </div>
      </div>

      {error && (
        <div className="rounded-md bg-destructive/10 px-4 py-3 text-sm text-destructive">{error}</div>
      )}

      <details className="rounded-lg border border-border bg-card p-4">
        <summary className="cursor-pointer text-sm font-medium text-foreground">Debug events</summary>
        <div className="mt-3 max-h-[280px] overflow-auto space-y-2">
          {logs.length === 0 ? (
            <p className="text-sm text-muted-foreground">No events yet.</p>
          ) : (
            logs
              .slice()
              .reverse()
              .map((l) => (
                <div key={l.id} className="rounded-md border border-border bg-muted/20 p-3">
                  <div className="flex items-center justify-between text-xs text-muted-foreground">
                    <span>{l.type}</span>
                    <span>{l.ts.toLocaleTimeString()}</span>
                  </div>
                  <pre className="mt-2 whitespace-pre-wrap text-xs text-foreground">
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

