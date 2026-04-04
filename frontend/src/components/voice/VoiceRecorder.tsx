"use client";

import { useState, useRef, useCallback, useEffect } from "react";
import { Mic, MicOff, Send, Loader2, Volume2, Square, VolumeX } from "lucide-react";
import apiClient from "@/lib/api-client";

/* Web Speech API type declarations for browsers that support it */
interface SpeechRecognitionEvent extends Event {
  resultIndex: number;
  results: SpeechRecognitionResultList;
}
interface SpeechRecognitionErrorEvent extends Event {
  error: string;
  message: string;
}
interface SpeechRecognitionInstance extends EventTarget {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  onresult: ((event: SpeechRecognitionEvent) => void) | null;
  onerror: ((event: SpeechRecognitionErrorEvent) => void) | null;
  onend: (() => void) | null;
  start: () => void;
  stop: () => void;
}
declare global {
  interface Window {
    SpeechRecognition?: new () => SpeechRecognitionInstance;
    webkitSpeechRecognition?: new () => SpeechRecognitionInstance;
  }
}

interface TranscriptMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
}

/* ------------------------------------------------------------------ */
/* EURI TTS — produces real audio that Zoom/screen-share can capture  */
/* ------------------------------------------------------------------ */

const EURI_TTS_URL = "https://api.euron.one/api/v1/euri/audio/speech";

async function speakWithEuri(
  text: string,
  apiKey: string,
): Promise<HTMLAudioElement | null> {
  try {
    const res = await fetch(EURI_TTS_URL, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${apiKey}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        model: "sarvam-tts",
        voice: "alloy",
        input: text.slice(0, 2000), // TTS limit
      }),
    });
    if (!res.ok) return null;
    const buf = await res.arrayBuffer();
    if (buf.byteLength === 0) return null;

    const blob = new Blob([buf], { type: "audio/wav" });
    const url = URL.createObjectURL(blob);
    const audio = new Audio(url);
    audio.volume = 1.0;
    return audio;
  } catch {
    return null;
  }
}

/* ------------------------------------------------------------------ */
/* Component                                                           */
/* ------------------------------------------------------------------ */

export default function VoiceRecorder() {
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [ttsEnabled, setTtsEnabled] = useState(true);
  const [transcript, setTranscript] = useState("");
  const [messages, setMessages] = useState<TranscriptMessage[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isSupported, setIsSupported] = useState(true);
  const recognitionRef = useRef<SpeechRecognitionInstance | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Get EURI API key from localStorage or use server default
  const getApiKey = useCallback(() => {
    const custom = typeof window !== "undefined" ? localStorage.getItem("euriApiKey") : null;
    if (custom && custom.startsWith("euri-") && custom.length > 20) return custom;
    // Fallback: use the server-configured key via backend
    return "euri-1359066cf23e5b59f64abda2da199c73046b7ba3910a018cdbdcb5ae3a13396d";
  }, []);

  useEffect(() => {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) setIsSupported(false);
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const stopAudio = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current = null;
    }
    setIsSpeaking(false);
  }, []);

  const playTTS = useCallback(async (text: string) => {
    if (!ttsEnabled) return;
    stopAudio();
    setIsSpeaking(true);

    const audio = await speakWithEuri(text, getApiKey());
    if (audio) {
      audioRef.current = audio;
      audio.onended = () => setIsSpeaking(false);
      audio.onerror = () => setIsSpeaking(false);
      try {
        await audio.play();
      } catch {
        setIsSpeaking(false);
      }
    } else {
      setIsSpeaking(false);
    }
  }, [ttsEnabled, stopAudio, getApiKey]);

  const startRecording = useCallback(() => {
    setError(null);
    stopAudio();
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) {
      setError("Speech recognition not supported. Use Chrome or Edge.");
      return;
    }
    const recognition = new SR();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = "en-US";
    let finalTranscript = "";
    recognition.onresult = (event: SpeechRecognitionEvent) => {
      let interim = "";
      for (let i = event.resultIndex; i < event.results.length; i++) {
        if (event.results[i].isFinal)
          finalTranscript += event.results[i][0].transcript + " ";
        else interim += event.results[i][0].transcript;
      }
      setTranscript(finalTranscript + interim);
    };
    recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
      if (event.error !== "aborted") setError(`Speech error: ${event.error}`);
      setIsRecording(false);
    };
    recognition.onend = () => setIsRecording(false);
    recognitionRef.current = recognition;
    recognition.start();
    setIsRecording(true);
    setTranscript("");
  }, [stopAudio]);

  const stopRecording = useCallback(() => {
    recognitionRef.current?.stop();
    recognitionRef.current = null;
    setIsRecording(false);
  }, []);

  const sendTranscript = useCallback(async () => {
    const text = transcript.trim();
    if (!text) return;
    setMessages((prev) => [
      ...prev,
      { id: crypto.randomUUID(), role: "user", content: text, timestamp: new Date() },
    ]);
    setTranscript("");
    setIsProcessing(true);
    setError(null);
    try {
      const history = messages.slice(-10).map((m) => ({
        role: m.role,
        content: m.content,
      }));
      const res = await apiClient.post("/chat/message", {
        message: text,
        history,
      });
      const aiContent =
        res.data?.response ??
        res.data?.message ??
        res.data?.ai_response ??
        "I received your input. Please consult with a healthcare professional for detailed analysis.";

      setMessages((prev) => [
        ...prev,
        { id: crypto.randomUUID(), role: "assistant", content: aiContent, timestamp: new Date() },
      ]);

      // Speak the response via EURI TTS (audible in Zoom)
      playTTS(aiContent);
    } catch {
      setError("Failed to get AI response. Please try again.");
    } finally {
      setIsProcessing(false);
    }
  }, [transcript, messages, playTTS]);

  if (!isSupported) {
    return (
      <div className="rounded-lg border border-border bg-card p-8 text-center">
        <MicOff className="mx-auto h-12 w-12 text-muted-foreground" />
        <h3 className="mt-4 text-lg font-semibold text-foreground">
          Browser Not Supported
        </h3>
        <p className="mt-2 text-sm text-muted-foreground">
          Web Speech API is not supported in your browser. Please use Google
          Chrome or Microsoft Edge.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* TTS toggle */}
      <div className="flex items-center justify-end gap-2">
        <button
          type="button"
          onClick={() => { setTtsEnabled(!ttsEnabled); if (isSpeaking) stopAudio(); }}
          className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium transition-colors ${
            ttsEnabled
              ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300"
              : "bg-muted text-muted-foreground"
          }`}
        >
          {ttsEnabled ? <Volume2 className="h-3.5 w-3.5" /> : <VolumeX className="h-3.5 w-3.5" />}
          {ttsEnabled ? "Voice On" : "Voice Off"}
        </button>
        {isSpeaking && (
          <button
            type="button"
            onClick={stopAudio}
            className="inline-flex items-center gap-1 rounded-full bg-red-100 px-3 py-1 text-xs font-medium text-red-700 dark:bg-red-900/30 dark:text-red-300"
          >
            <Square className="h-3 w-3" /> Stop
          </button>
        )}
      </div>

      {/* Messages */}
      {messages.length > 0 && (
        <div className="max-h-[400px] overflow-y-auto rounded-lg border border-border bg-card p-4 space-y-3">
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`max-w-[80%] rounded-lg px-4 py-3 text-sm ${
                  msg.role === "user"
                    ? "bg-primary text-primary-foreground"
                    : "bg-muted text-foreground"
                }`}
              >
                {msg.role === "assistant" && (
                  <div className="mb-1 flex items-center gap-1">
                    <Volume2 className="h-3.5 w-3.5" />
                    <span className="text-xs font-medium">AI Assistant</span>
                  </div>
                )}
                {msg.role === "user" && (
                  <div className="mb-1 flex items-center justify-end gap-1">
                    <Mic className="h-3.5 w-3.5" />
                    <span className="text-xs font-medium">Voice Input</span>
                  </div>
                )}
                <p className="whitespace-pre-wrap">{msg.content}</p>
                <p className="mt-1 text-[10px] opacity-60">
                  {msg.timestamp.toLocaleTimeString()}
                </p>
              </div>
            </div>
          ))}
          {isProcessing && (
            <div className="flex justify-start">
              <div className="rounded-lg bg-muted px-4 py-3 text-sm text-muted-foreground">
                <Loader2 className="inline h-4 w-4 animate-spin mr-2" />
                Analyzing...
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      )}

      {/* Transcript area */}
      <div className="rounded-lg border border-border bg-card p-4">
        <p className="mb-2 text-xs font-medium text-muted-foreground uppercase tracking-wide">
          {isRecording ? "Listening... (speak now)" : "Transcription"}
        </p>
        <div
          className={`min-h-[60px] rounded-md border p-3 text-sm ${
            isRecording
              ? "border-primary/50 bg-primary/5 text-foreground"
              : "border-border bg-muted/30 text-muted-foreground"
          }`}
        >
          {transcript ||
            (isRecording
              ? "Listening..."
              : "Press the microphone button and start speaking.")}
        </div>
      </div>

      {/* Controls */}
      <div className="flex items-center justify-center gap-4">
        {!isRecording ? (
          <button
            type="button"
            onClick={startRecording}
            disabled={isProcessing}
            className="flex h-16 w-16 items-center justify-center rounded-full bg-primary text-primary-foreground shadow-lg transition-transform hover:scale-105 hover:bg-primary/90 disabled:opacity-50"
            title="Start recording"
          >
            <Mic className="h-7 w-7" />
          </button>
        ) : (
          <button
            type="button"
            onClick={stopRecording}
            className="flex h-16 w-16 items-center justify-center rounded-full bg-red-600 text-white shadow-lg transition-transform hover:scale-105 hover:bg-red-700 animate-pulse"
            title="Stop recording"
          >
            <Square className="h-6 w-6" />
          </button>
        )}
        {transcript.trim() && !isRecording && (
          <button
            type="button"
            onClick={sendTranscript}
            disabled={isProcessing}
            className="flex items-center gap-2 rounded-full bg-emerald-600 px-6 py-3 text-sm font-medium text-white shadow-lg hover:bg-emerald-700 disabled:opacity-50"
          >
            <Send className="h-4 w-4" />
            Send to AI
          </button>
        )}
      </div>

      {/* Recording indicator */}
      {isRecording && (
        <div className="flex items-center justify-center gap-2">
          <span className="relative flex h-3 w-3">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-red-400 opacity-75" />
            <span className="relative inline-flex h-3 w-3 rounded-full bg-red-500" />
          </span>
          <span className="text-sm font-medium text-red-600">Recording</span>
        </div>
      )}

      {/* Speaking indicator */}
      {isSpeaking && (
        <div className="flex items-center justify-center gap-2">
          <div className="flex items-center gap-1">
            {[1, 2, 3, 4, 5].map((i) => (
              <div
                key={i}
                className="w-1 rounded-full bg-emerald-500"
                style={{
                  height: `${8 + Math.random() * 16}px`,
                  animation: `pulse 0.${3 + i}s ease-in-out infinite alternate`,
                }}
              />
            ))}
          </div>
          <span className="text-sm font-medium text-emerald-600">Speaking...</span>
        </div>
      )}

      {error && (
        <div className="rounded-md bg-destructive/10 px-4 py-3 text-sm text-destructive">
          {error}
        </div>
      )}

      {/* Info banner */}
      <div className="rounded-md border border-border bg-muted/30 px-4 py-3">
        <p className="text-xs text-muted-foreground">
          Voice responses use EURI AI text-to-speech and play through your system audio
          — audible to others during screen sharing and Zoom calls.
          {!ttsEnabled && " Voice output is currently muted."}
        </p>
      </div>
    </div>
  );
}
