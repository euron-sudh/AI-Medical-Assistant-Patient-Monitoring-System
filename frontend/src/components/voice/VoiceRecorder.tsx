"use client";

import { useState, useRef, useCallback, useEffect } from "react";
import { Mic, MicOff, Send, Loader2, Volume2, Square } from "lucide-react";
import apiClient from "@/lib/api-client";

interface TranscriptMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
}

export default function VoiceRecorder() {
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [messages, setMessages] = useState<TranscriptMessage[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isSupported, setIsSupported] = useState(true);
  const recognitionRef = useRef<SpeechRecognition | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) setIsSupported(false);
  }, []);

  useEffect(() => { messagesEndRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages]);

  const startRecording = useCallback(() => {
    setError(null);
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) { setError("Speech recognition not supported. Use Chrome or Edge."); return; }
    const recognition = new SR();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = "en-US";
    let finalTranscript = "";
    recognition.onresult = (event: SpeechRecognitionEvent) => {
      let interim = "";
      for (let i = event.resultIndex; i < event.results.length; i++) {
        if (event.results[i].isFinal) finalTranscript += event.results[i][0].transcript + " ";
        else interim += event.results[i][0].transcript;
      }
      setTranscript(finalTranscript + interim);
    };
    recognition.onerror = (event: SpeechRecognitionErrorEvent) => { if (event.error !== "aborted") setError(`Speech error: ${event.error}`); setIsRecording(false); };
    recognition.onend = () => setIsRecording(false);
    recognitionRef.current = recognition;
    recognition.start();
    setIsRecording(true);
    setTranscript("");
  }, []);

  const stopRecording = useCallback(() => { recognitionRef.current?.stop(); recognitionRef.current = null; setIsRecording(false); }, []);

  const sendTranscript = useCallback(async () => {
    const text = transcript.trim();
    if (!text) return;
    setMessages((prev) => [...prev, { id: crypto.randomUUID(), role: "user", content: text, timestamp: new Date() }]);
    setTranscript("");
    setIsProcessing(true);
    setError(null);
    try {
      const res = await apiClient.post("/chat/message", { message: `[Voice input] Patient says: ${text}. Please analyze these symptoms and provide medical guidance.`, conversation_type: "general" });
      const aiContent = res.data?.response ?? res.data?.message ?? res.data?.ai_response ?? "I received your input. Please consult with a healthcare professional for detailed analysis.";
      setMessages((prev) => [...prev, { id: crypto.randomUUID(), role: "assistant", content: aiContent, timestamp: new Date() }]);
    } catch { setError("Failed to get AI response. Please try again."); }
    finally { setIsProcessing(false); }
  }, [transcript]);

  if (!isSupported) {
    return (
      <div className="rounded-lg border border-border bg-card p-8 text-center">
        <MicOff className="mx-auto h-12 w-12 text-muted-foreground" />
        <h3 className="mt-4 text-lg font-semibold text-foreground">Browser Not Supported</h3>
        <p className="mt-2 text-sm text-muted-foreground">Web Speech API is not supported in your browser. Please use Google Chrome or Microsoft Edge.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {messages.length > 0 && (
        <div className="max-h-[400px] overflow-y-auto rounded-lg border border-border bg-card p-4 space-y-3">
          {messages.map((msg) => (
            <div key={msg.id} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
              <div className={`max-w-[80%] rounded-lg px-4 py-3 text-sm ${msg.role === "user" ? "bg-primary text-primary-foreground" : "bg-muted text-foreground"}`}>
                {msg.role === "assistant" && <div className="mb-1 flex items-center gap-1"><Volume2 className="h-3.5 w-3.5" /><span className="text-xs font-medium">AI Assistant</span></div>}
                {msg.role === "user" && <div className="mb-1 flex items-center justify-end gap-1"><Mic className="h-3.5 w-3.5" /><span className="text-xs font-medium">Voice Input</span></div>}
                <p className="whitespace-pre-wrap">{msg.content}</p>
                <p className="mt-1 text-[10px] opacity-60">{msg.timestamp.toLocaleTimeString()}</p>
              </div>
            </div>
          ))}
          {isProcessing && <div className="flex justify-start"><div className="rounded-lg bg-muted px-4 py-3 text-sm text-muted-foreground"><Loader2 className="inline h-4 w-4 animate-spin mr-2" />Analyzing...</div></div>}
          <div ref={messagesEndRef} />
        </div>
      )}
      <div className="rounded-lg border border-border bg-card p-4">
        <p className="mb-2 text-xs font-medium text-muted-foreground uppercase tracking-wide">{isRecording ? "Listening... (speak now)" : "Transcription"}</p>
        <div className={`min-h-[60px] rounded-md border p-3 text-sm ${isRecording ? "border-primary/50 bg-primary/5 text-foreground" : "border-border bg-muted/30 text-muted-foreground"}`}>
          {transcript || (isRecording ? "Listening..." : "Press the microphone button and start speaking.")}
        </div>
      </div>
      <div className="flex items-center justify-center gap-4">
        {!isRecording ? (
          <button type="button" onClick={startRecording} disabled={isProcessing} className="flex h-16 w-16 items-center justify-center rounded-full bg-primary text-primary-foreground shadow-lg transition-transform hover:scale-105 hover:bg-primary/90 disabled:opacity-50" title="Start recording"><Mic className="h-7 w-7" /></button>
        ) : (
          <button type="button" onClick={stopRecording} className="flex h-16 w-16 items-center justify-center rounded-full bg-red-600 text-white shadow-lg transition-transform hover:scale-105 hover:bg-red-700 animate-pulse" title="Stop recording"><Square className="h-6 w-6" /></button>
        )}
        {transcript.trim() && !isRecording && (
          <button type="button" onClick={sendTranscript} disabled={isProcessing} className="flex items-center gap-2 rounded-full bg-emerald-600 px-6 py-3 text-sm font-medium text-white shadow-lg hover:bg-emerald-700 disabled:opacity-50"><Send className="h-4 w-4" />Send to AI</button>
        )}
      </div>
      {isRecording && <div className="flex items-center justify-center gap-2"><span className="relative flex h-3 w-3"><span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-red-400 opacity-75" /><span className="relative inline-flex h-3 w-3 rounded-full bg-red-500" /></span><span className="text-sm font-medium text-red-600">Recording</span></div>}
      {error && <div className="rounded-md bg-destructive/10 px-4 py-3 text-sm text-destructive">{error}</div>}
    </div>
  );
}
