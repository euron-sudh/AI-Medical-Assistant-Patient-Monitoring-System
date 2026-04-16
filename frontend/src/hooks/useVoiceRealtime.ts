"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import apiClient from "@/lib/api-client";

type RealtimeSessionResponse = {
  model: string;
  voice: string;
  expires_at?: number | string | null;
  client_secret: string;
  listening_profile?: string;
  noise_reduction?: string;
};

export type VoiceLogItem = { id: string; ts: Date; type: string; data: unknown };

export type VoiceThreadMsg = {
  id: string;
  role: "user" | "assistant";
  content: string;
  ts: Date;
};

export type VoiceSessionStatus =
  | "idle"
  | "creating_session"
  | "connecting"
  | "connected"
  | "recording"
  | "error";

function safeJsonParse(input: string): unknown {
  try {
    return JSON.parse(input);
  } catch {
    return null;
  }
}

export const INTRO_TEXT =
  "Hello there I am Med Assist virtual doctor I am here to assist you on your symptoms.";

const LAB_TOOL_NAME = "request_lab_recommendations";

/** Realtime TTS voices to compare (OpenAI); session uses `voice` from session create. */
export const REALTIME_VOICE_OPTIONS = [
  { value: "marin", label: "Marin" },
  { value: "cedar", label: "Cedar" },
  { value: "alloy", label: "Alloy" },
  { value: "echo", label: "Echo" },
  { value: "shimmer", label: "Shimmer" },
] as const;

export type ListeningProfile = "quiet" | "noisy" | "speaker";

export const LISTENING_PROFILE_OPTIONS: {
  value: ListeningProfile;
  label: string;
  hint: string;
}[] = [
  { value: "quiet", label: "Quiet room", hint: "Headset, earbuds, or phone close to mouth" },
  { value: "noisy", label: "Noisy place", hint: "Hospital, TV, fan, waiting area, street" },
  { value: "speaker", label: "Laptop / room mic", hint: "Built-in mic or farther from you" },
];

/** Match backend LISTENING_PROFILES — interrupt off for closing message only. */
const CLOSING_TURN_DETECTION: Record<ListeningProfile, Record<string, unknown>> = {
  quiet: {
    type: "server_vad",
    threshold: 0.58,
    prefix_padding_ms: 300,
    silence_duration_ms: 550,
    create_response: true,
    interrupt_response: false,
  },
  noisy: {
    type: "server_vad",
    threshold: 0.72,
    prefix_padding_ms: 320,
    silence_duration_ms: 850,
    create_response: true,
    interrupt_response: false,
  },
  speaker: {
    type: "server_vad",
    threshold: 0.68,
    prefix_padding_ms: 350,
    silence_duration_ms: 750,
    create_response: true,
    interrupt_response: false,
  },
};

function defaultRealtimeModel() {
  return (
    (typeof process !== "undefined" && process.env.NEXT_PUBLIC_OPENAI_REALTIME_MODEL) || "gpt-realtime"
  );
}

function defaultRealtimeVoice() {
  return (
    (typeof process !== "undefined" && process.env.NEXT_PUBLIC_OPENAI_REALTIME_VOICE) || "marin"
  );
}

function defaultListeningProfile(): ListeningProfile {
  const v = (typeof process !== "undefined" && process.env.NEXT_PUBLIC_LISTENING_PROFILE) || "quiet";
  if (v === "noisy" || v === "speaker") return v;
  return "quiet";
}

/** Softer turn-taking for final goodbye: no interrupt on spurious VAD (same profile thresholds). */
function sendClosingSessionUpdate(dc: RTCDataChannel, profile: ListeningProfile) {
  dc.send(
    JSON.stringify({
      type: "session.update",
      session: {
        turn_detection: CLOSING_TURN_DETECTION[profile],
      },
    }),
  );
}

function downloadMarkdownFile(content: string, filename: string) {
  const blob = new Blob([content], { type: "text/markdown;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export function useVoiceRealtime() {
  const [status, setStatus] = useState<VoiceSessionStatus>("idle");
  const [error, setError] = useState<string | null>(null);
  const [ttsEnabled, setTtsEnabled] = useState(true);
  const [volume, setVolume] = useState(0.75);
  const [playbackRate, setPlaybackRate] = useState(1);
  const [assistantText, setAssistantText] = useState("");
  const [userText, setUserText] = useState("");
  const [thread, setThread] = useState<VoiceThreadMsg[]>([]);
  const [logs, setLogs] = useState<VoiceLogItem[]>([]);
  const [labReport, setLabReport] = useState<string | null>(null);
  const [labReportLoading, setLabReportLoading] = useState(false);
  const [labReportError, setLabReportError] = useState<string | null>(null);
  const [realtimeVoice, setRealtimeVoice] = useState<string>(defaultRealtimeVoice);
  const [listeningProfile, setListeningProfile] = useState<ListeningProfile>(defaultListeningProfile);
  const [noisyEnvironmentHint, setNoisyEnvironmentHint] = useState(false);
  const [lastSessionAudioDebug, setLastSessionAudioDebug] = useState<{
    listening_profile: string;
    noise_reduction?: string;
  } | null>(null);

  const pcRef = useRef<RTCPeerConnection | null>(null);
  const dcRef = useRef<RTCDataChannel | null>(null);
  const localStreamRef = useRef<MediaStream | null>(null);
  const remoteAudioRef = useRef<HTMLAudioElement | null>(null);
  const lastAssistantChunkRef = useRef<string>("");
  const lastUserChunkRef = useRef<string>("");
  const introPhaseRef = useRef<"idle" | "intro_sent" | "awaiting_user" | "followup_sent">("idle");
  const userTextRef = useRef("");
  const assistantTextRef = useRef("");
  const threadRef = useRef<VoiceThreadMsg[]>([]);
  const threadEndRef = useRef<HTMLDivElement | null>(null);
  const ttsEnabledRef = useRef(ttsEnabled);
  const awaitingLabClosureRef = useRef(false);
  const cleanupRef = useRef<() => void>(() => {});
  /** True after user speech_started while awaiting first turn (avoids noise-only speech_stopped). */
  const hadSpeechWhileAwaitingRef = useRef(false);
  const labClosureCleanupTimerRef = useRef<number | null>(null);
  const interruptDebounceTimerRef = useRef<number | null>(null);
  const lastSpeechStartedAtRef = useRef<number>(0);
  const noisyHintClearTimerRef = useRef<number | null>(null);

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

  useEffect(() => {
    userTextRef.current = userText;
  }, [userText]);

  useEffect(() => {
    assistantTextRef.current = assistantText;
  }, [assistantText]);

  useEffect(() => {
    threadRef.current = thread;
  }, [thread]);

  useEffect(() => {
    ttsEnabledRef.current = ttsEnabled;
  }, [ttsEnabled]);

  useEffect(() => {
    threadEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [thread, assistantText, userText]);

  useEffect(() => {
    const el = remoteAudioRef.current;
    if (!el) return;
    el.muted = !ttsEnabled;
    el.volume = volume;
    el.playbackRate = playbackRate;
  }, [ttsEnabled, volume, playbackRate, status]);

  const clearInterruptDebounce = useCallback(() => {
    if (interruptDebounceTimerRef.current !== null) {
      window.clearTimeout(interruptDebounceTimerRef.current);
      interruptDebounceTimerRef.current = null;
    }
  }, []);

  const cleanup = useCallback(() => {
    clearInterruptDebounce();
    if (labClosureCleanupTimerRef.current) {
      window.clearTimeout(labClosureCleanupTimerRef.current);
      labClosureCleanupTimerRef.current = null;
    }
    if (noisyHintClearTimerRef.current) {
      window.clearTimeout(noisyHintClearTimerRef.current);
      noisyHintClearTimerRef.current = null;
    }
    awaitingLabClosureRef.current = false;
    hadSpeechWhileAwaitingRef.current = false;
    setNoisyEnvironmentHint(false);
    setLastSessionAudioDebug(null);
    setStatus("idle");
    setError(null);
    setLabReport(null);
    setLabReportError(null);
    setLabReportLoading(false);
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
  }, [clearInterruptDebounce]);

  useEffect(() => {
    cleanupRef.current = cleanup;
  }, [cleanup]);

  const buildTranscriptFromState = useCallback(() => {
    const lines: string[] = [];
    for (const m of thread) {
      const who = m.role === "assistant" ? "Med Assist" : "Patient";
      lines.push(`${who}: ${m.content}`);
    }
    if (userText.trim()) lines.push(`Patient (live): ${userText.trim()}`);
    if (assistantText.trim()) lines.push(`Med Assist (live): ${assistantText.trim()}`);
    return lines.join("\n\n");
  }, [thread, userText, assistantText]);

  const generateLabReportAndDownload = useCallback(async () => {
    const transcript = buildTranscriptFromState().trim();
    if (!transcript) {
      setLabReportError("No conversation to analyze yet. Start a session and describe your symptoms.");
      return;
    }
    setLabReportLoading(true);
    setLabReportError(null);
    try {
      const res = await apiClient.post<{ report_markdown: string }>("/realtime/lab-recommendations", {
        transcript,
      });
      const md = res.data.report_markdown;
      setLabReport(md);
      const pdfRes = await apiClient.post<Blob>(
        "/realtime/lab-recommendations/pdf",
        { report_markdown: md },
        { responseType: "blob" },
      );
      downloadBlob(
        pdfRes.data,
        `medassist-lab-tests-${new Date().toISOString().slice(0, 10)}.pdf`,
      );
    } catch (e: unknown) {
      const data = (e as { response?: { data?: { error?: { message?: string } } } })?.response?.data;
      const msg = data?.error?.message ?? (e as Error)?.message ?? "Failed to generate lab report.";
      setLabReportError(msg);
    } finally {
      setLabReportLoading(false);
    }
  }, [buildTranscriptFromState]);

  const start = useCallback(async () => {
    if (!canUseWebRTC) {
      setError("WebRTC audio is not supported in this browser.");
      setStatus("error");
      return;
    }

    setAssistantText("");
    setUserText("");
    setThread([]);
    setLogs([]);
    setError(null);
    setLabReport(null);
    setLabReportError(null);
    setLabReportLoading(false);
    clearInterruptDebounce();
    if (labClosureCleanupTimerRef.current) {
      window.clearTimeout(labClosureCleanupTimerRef.current);
      labClosureCleanupTimerRef.current = null;
    }
    if (noisyHintClearTimerRef.current) {
      window.clearTimeout(noisyHintClearTimerRef.current);
      noisyHintClearTimerRef.current = null;
    }
    awaitingLabClosureRef.current = false;
    hadSpeechWhileAwaitingRef.current = false;
    setNoisyEnvironmentHint(false);
    setLastSessionAudioDebug(null);
    setStatus("creating_session");
    introPhaseRef.current = "idle";
    lastAssistantChunkRef.current = "";
    lastUserChunkRef.current = "";
    userTextRef.current = "";
    assistantTextRef.current = "";
    threadRef.current = [];

    const buildTranscriptString = () => {
      const lines: string[] = [];
      for (const m of threadRef.current) {
        const who = m.role === "assistant" ? "Med Assist" : "Patient";
        lines.push(`${who}: ${m.content}`);
      }
      if (userTextRef.current.trim()) lines.push(`Patient (live): ${userTextRef.current.trim()}`);
      if (assistantTextRef.current.trim()) lines.push(`Med Assist (live): ${assistantTextRef.current.trim()}`);
      return lines.join("\n\n");
    };

    const runLabTool = async (dc: RTCDataChannel, callId: string, argsRaw: string) => {
      let symptomsSummary = "";
      try {
        const parsed = JSON.parse(argsRaw) as { symptoms_summary?: string };
        symptomsSummary = (parsed.symptoms_summary ?? "").trim();
      } catch {
        /* ignore */
      }

      const parts: string[] = [];
      if (symptomsSummary) parts.push(`Clinical summary (assistant): ${symptomsSummary}`);
      parts.push("--- Conversation ---");
      parts.push(buildTranscriptString());
      const transcript = parts.join("\n\n");

      setLabReportLoading(true);
      setLabReportError(null);
      try {
        const res = await apiClient.post<{ report_markdown: string }>("/realtime/lab-recommendations", {
          transcript,
        });
        const md = res.data.report_markdown;
        setLabReport(md);

        const forVoice =
          md.length > 6000 ? `${md.slice(0, 6000)}\n\n... [Full list also available via Download lab test]` : md;
        const outputPayload = JSON.stringify({ lab_recommendations_markdown: forVoice });

        dc.send(
          JSON.stringify({
            type: "conversation.item.create",
            item: { type: "function_call_output", call_id: callId, output: outputPayload },
          }),
        );
        awaitingLabClosureRef.current = true;
        sendClosingSessionUpdate(dc, listeningProfile);
        window.setTimeout(() => {
          if (dc.readyState !== "open") return;
          dc.send(
            JSON.stringify({
              type: "response.create",
              response: {
                modalities: ["audio", "text"],
                instructions:
                  "The tool output JSON contains lab_recommendations_markdown. " +
                  "Explain the suggested lab tests clearly in the patient's language. " +
                  "Emphasize they are not a diagnosis and must be reviewed with a licensed clinician. " +
                  "Tell them they can download the full lab test list using the Download lab test button. " +
                  "Thank them warmly, state that this session is now complete, and do not ask any further questions. " +
                  "Speak at a calm pace and finish every sentence fully before stopping.",
              },
            }),
          );
        }, 100);
      } catch (e: unknown) {
        const data = (e as { response?: { data?: { error?: { message?: string } } } })?.response?.data;
        const msg = data?.error?.message ?? (e as Error)?.message ?? "Lab report generation failed.";
        setLabReportError(msg);
        dc.send(
          JSON.stringify({
            type: "conversation.item.create",
            item: {
              type: "function_call_output",
              call_id: callId,
              output: JSON.stringify({ error: msg }),
            },
          }),
        );
        awaitingLabClosureRef.current = true;
        sendClosingSessionUpdate(dc, listeningProfile);
        window.setTimeout(() => {
          if (dc.readyState !== "open") return;
          dc.send(
            JSON.stringify({
              type: "response.create",
              response: {
                modalities: ["audio", "text"],
                instructions:
                  "The lab recommendation service failed. Apologize briefly, suggest the patient use Download lab test or speak with their clinician, thank them, and end the session without further questions. " +
                  "Finish your last sentence completely at a calm pace.",
              },
            }),
          );
        }, 100);
      } finally {
        setLabReportLoading(false);
      }
    };

    let session: RealtimeSessionResponse;
    try {
      const res = await apiClient.post<RealtimeSessionResponse>("/realtime/session", {
        model: defaultRealtimeModel(),
        voice: realtimeVoice,
        listening_profile: listeningProfile,
      });
      session = res.data;
      const prof = session.listening_profile ?? listeningProfile;
      const nr = session.noise_reduction;
      setLastSessionAudioDebug({ listening_profile: prof, noise_reduction: nr });
      appendLog("voice_session_audio", {
        listening_profile: prof,
        noise_reduction: nr,
        model: session.model,
        voice: session.voice,
      });
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

      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
        video: false,
      });
      localStreamRef.current = stream;
      for (const track of stream.getTracks()) {
        pc.addTrack(track, stream);
      }

      pc.ontrack = (e) => {
        const [remoteStream] = e.streams;
        if (!remoteAudioRef.current) return;
        remoteAudioRef.current.srcObject = remoteStream;
        remoteAudioRef.current.muted = !ttsEnabledRef.current;
        remoteAudioRef.current.play().catch(() => {});
      };

      const dc = pc.createDataChannel("oai-events");
      dcRef.current = dc;

      dc.onopen = () => {
        appendLog("data_channel_open", {});
        setStatus("connected");

        introPhaseRef.current = "intro_sent";

        const msg = {
          type: "response.create",
          response: {
            modalities: ["audio", "text"],
            instructions:
              "Say ONLY this one sentence (verbatim) and then stop. Speak in a warm, natural tone—not robotic. " +
              "Do not add any other words in any language:\n" +
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

        if (type === "input_audio_buffer.speech_started") {
          // Final goodbye: do not clip tail audio (see awaitingLabClosureRef).
          if (awaitingLabClosureRef.current) {
            return;
          }
          lastSpeechStartedAtRef.current = Date.now();
          appendLog("vad_speech_started", { listening_profile: listeningProfile });
          const delayMs =
            listeningProfile === "noisy" ? 200 : listeningProfile === "speaker" ? 165 : 120;
          clearInterruptDebounce();
          interruptDebounceTimerRef.current = window.setTimeout(() => {
            interruptDebounceTimerRef.current = null;
            if (awaitingLabClosureRef.current) return;
            appendLog("interrupt_after_debounce", { delayMs });
            if (introPhaseRef.current === "awaiting_user") {
              hadSpeechWhileAwaitingRef.current = true;
            }
            const a = remoteAudioRef.current;
            if (a) {
              a.pause();
              a.currentTime = 0;
            }
            try {
              dc.send(JSON.stringify({ type: "response.cancel" }));
            } catch {
              // ignore
            }
          }, delayMs) as number;
        }

        if (type === "input_audio_buffer.speech_stopped") {
          clearInterruptDebounce();
          appendLog("vad_speech_stopped", { listening_profile: listeningProfile });
          const burstMs = Date.now() - lastSpeechStartedAtRef.current;
          if (burstMs > 0 && burstMs < 260) {
            setNoisyEnvironmentHint(true);
            appendLog("noise_burst_suspected", { burstMs });
            if (noisyHintClearTimerRef.current) {
              window.clearTimeout(noisyHintClearTimerRef.current);
            }
            noisyHintClearTimerRef.current = window.setTimeout(() => {
              noisyHintClearTimerRef.current = null;
              setNoisyEnvironmentHint(false);
            }, 12000) as number;
          }
          remoteAudioRef.current?.play().catch(() => {});
          // Enter interview phase after real speech: debounced interrupt fired, or utterance long enough.
          if (introPhaseRef.current === "awaiting_user") {
            if (hadSpeechWhileAwaitingRef.current || burstMs >= 100) {
              introPhaseRef.current = "followup_sent";
              hadSpeechWhileAwaitingRef.current = false;
            }
          }
        }

        const textPiece =
          (p.delta as unknown) ??
          (p.text as unknown) ??
          (p.transcript as unknown) ??
          (p.output_text as unknown);

        if (typeof textPiece === "string" && textPiece.length > 0) {
          if (type.includes("input") || type.includes("transcription")) {
            const chunk = textPiece;
            if (chunk === lastUserChunkRef.current) return;
            lastUserChunkRef.current = chunk;
            setUserText((prev) => {
              if (chunk.startsWith(prev)) return chunk;
              if (prev.endsWith(chunk)) return prev;
              return prev ? `${prev}${chunk}` : chunk;
            });
          } else if (type.includes("response") || type.includes("output")) {
            const chunk = textPiece;
            if (chunk === lastAssistantChunkRef.current) return;
            lastAssistantChunkRef.current = chunk;
            setAssistantText((prev) => {
              if (chunk.startsWith(prev)) return chunk;
              if (prev.endsWith(chunk)) return prev;
              return prev ? `${prev}${chunk}` : chunk;
            });
          }
        }

        const isMainResponseDone = type === "response.done";

        if (introPhaseRef.current === "intro_sent" && isMainResponseDone) {
          introPhaseRef.current = "awaiting_user";
          setThread((t) => {
            const introMsg: VoiceThreadMsg = {
              id: crypto.randomUUID(),
              role: "assistant",
              content: INTRO_TEXT,
              ts: new Date(),
            };
            const next = [...t, introMsg];
            threadRef.current = next;
            return next;
          });
          setAssistantText("");
          assistantTextRef.current = "";
          lastAssistantChunkRef.current = "";
          return;
        }

        if (isMainResponseDone && introPhaseRef.current === "followup_sent") {
          const response = p.response as Record<string, unknown> | undefined;
          const output = response?.output as Array<Record<string, unknown>> | undefined;
          if (Array.isArray(output)) {
            const fnItems = output.filter(
              (it) =>
                it &&
                it.type === "function_call" &&
                it.name === LAB_TOOL_NAME &&
                typeof it.call_id === "string",
            );
            if (fnItems.length > 0) {
              const u = userTextRef.current.trim();
              if (u) {
                const userMsg: VoiceThreadMsg = {
                  id: crypto.randomUUID(),
                  role: "user",
                  content: u,
                  ts: new Date(),
                };
                setThread((prev) => {
                  const next = [...prev, userMsg];
                  threadRef.current = next;
                  return next;
                });
                setUserText("");
                userTextRef.current = "";
                lastUserChunkRef.current = "";
              }
              for (const it of fnItems) {
                const args = typeof it.arguments === "string" ? it.arguments : "{}";
                void runLabTool(dc, String(it.call_id), args);
              }
              return;
            }
          }
        }

        if (introPhaseRef.current === "followup_sent" && isMainResponseDone) {
          const u = userTextRef.current.trim();
          const a = assistantTextRef.current.trim();
          setThread((prev) => {
            const next = [...prev];
            if (u)
              next.push({
                id: crypto.randomUUID(),
                role: "user",
                content: u,
                ts: new Date(),
              });
            if (a)
              next.push({
                id: crypto.randomUUID(),
                role: "assistant",
                content: a,
                ts: new Date(),
              });
            threadRef.current = next;
            return next;
          });
          setUserText("");
          setAssistantText("");
          userTextRef.current = "";
          assistantTextRef.current = "";
          lastUserChunkRef.current = "";
          lastAssistantChunkRef.current = "";
        }

        if (isMainResponseDone && awaitingLabClosureRef.current) {
          const response = p.response as Record<string, unknown> | undefined;
          const output = response?.output as Array<Record<string, unknown>> | undefined;
          const hasFn =
            Array.isArray(output) && output.some((it) => it && it.type === "function_call");
          if (!hasFn) {
            // Keep awaitingLabClosureRef true until cleanup so speech_started does not clip tail audio.
            if (labClosureCleanupTimerRef.current) {
              window.clearTimeout(labClosureCleanupTimerRef.current);
            }
            labClosureCleanupTimerRef.current = window.setTimeout(() => {
              labClosureCleanupTimerRef.current = null;
              awaitingLabClosureRef.current = false;
              cleanupRef.current();
            }, 22000) as number;
          }
        }
      };

      dc.onerror = () => {
        setError("Realtime connection error (data channel).");
        setStatus("error");
      };

      pc.oniceconnectionstatechange = () => {
        appendLog("ice_state", { state: pc.iceConnectionState });
      };

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
  }, [appendLog, canUseWebRTC, cleanup, clearInterruptDebounce, listeningProfile, realtimeVoice]);

  useEffect(() => {
    return () => cleanup();
  }, [cleanup]);

  const restart = useCallback(() => {
    cleanup();
    void start();
  }, [cleanup, start]);

  const exportTranscript = useCallback(() => {
    const lines: string[] = [];
    for (const m of thread) {
      const who = m.role === "assistant" ? "Med Assist" : "Patient";
      lines.push(`[${m.ts.toISOString()}] ${who}: ${m.content}`);
    }
    if (userText.trim()) lines.push(`[live] Patient: ${userText.trim()}`);
    if (assistantText.trim()) lines.push(`[live] Med Assist: ${assistantText.trim()}`);
    const blob = new Blob([lines.join("\n\n")], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `med-assist-transcript-${new Date().toISOString().slice(0, 10)}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  }, [thread, userText, assistantText]);

  const statusLabel =
    status === "creating_session"
      ? "Initializing…"
      : status === "connecting"
        ? "Connecting…"
        : status === "connected"
          ? "Live"
          : status === "error"
            ? "Error"
            : "Idle";

  const isSessionActive =
    status === "connected" || status === "connecting" || status === "creating_session";

  return {
    status,
    statusLabel,
    error,
    ttsEnabled,
    setTtsEnabled,
    volume,
    setVolume,
    playbackRate,
    setPlaybackRate,
    assistantText,
    userText,
    thread,
    logs,
    threadEndRef,
    remoteAudioRef,
    canUseWebRTC,
    start,
    cleanup,
    restart,
    exportTranscript,
    isSessionActive,
    labReport,
    labReportLoading,
    labReportError,
    generateLabReportAndDownload,
    realtimeVoice,
    setRealtimeVoice,
    realtimeVoiceOptions: REALTIME_VOICE_OPTIONS,
    listeningProfile,
    setListeningProfile,
    listeningProfileOptions: LISTENING_PROFILE_OPTIONS,
    noisyEnvironmentHint,
    lastSessionAudioDebug,
  };
}

export type VoiceRealtimeState = ReturnType<typeof useVoiceRealtime>;
