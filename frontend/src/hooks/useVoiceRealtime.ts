"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import apiClient from "@/lib/api-client";

type RealtimeSessionResponse = {
  model: string;
  voice: string;
  expires_at?: number | string | null;
  client_secret: string;
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

function downloadMarkdownFile(content: string, filename: string) {
  const blob = new Blob([content], { type: "text/markdown;charset=utf-8" });
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

  const cleanup = useCallback(() => {
    awaitingLabClosureRef.current = false;
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
  }, []);

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
      downloadMarkdownFile(md, `med-assist-lab-report-${new Date().toISOString().slice(0, 10)}.md`);
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
    awaitingLabClosureRef.current = false;
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
                "Thank them warmly, state that this session is now complete, and do not ask any further questions.",
            },
          }),
        );
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
        dc.send(
          JSON.stringify({
            type: "response.create",
            response: {
              modalities: ["audio", "text"],
              instructions:
                "The lab recommendation service failed. Apologize briefly, suggest the patient use Download lab test or speak with their clinician, thank them, and end the session without further questions.",
            },
          }),
        );
      } finally {
        setLabReportLoading(false);
      }
    };

    let session: RealtimeSessionResponse;
    try {
      const res = await apiClient.post<RealtimeSessionResponse>("/realtime/session", {
        model: "gpt-4o-realtime-preview",
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
                "- Ask ONE question at a time about symptoms, timing, severity, and relevant history.\n" +
                "- When you have enough information, call the function request_lab_recommendations with a detailed symptoms_summary.\n" +
                "- After you receive lab_recommendations_markdown from the tool, explain suggestions briefly, mention Download lab test for the downloadable list, thank the patient, say the session is complete, and ask no further questions.\n" +
                "- If emergency symptoms are suspected, advise emergency services immediately before the tool.\n\n" +
                "Ask your first question now.",
            },
          };
          dc.send(JSON.stringify(followup));
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
            awaitingLabClosureRef.current = false;
            window.setTimeout(() => cleanupRef.current(), 4500);
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
  }, [appendLog, canUseWebRTC, cleanup]);

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
  };
}

export type VoiceRealtimeState = ReturnType<typeof useVoiceRealtime>;
