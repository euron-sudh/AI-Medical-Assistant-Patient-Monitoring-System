"use client";

import dynamic from "next/dynamic";
import { Mic, Shield, Globe, Brain } from "lucide-react";

const VoiceRecorder = dynamic(() => import("@/components/voice/VoiceRecorder"), {
  ssr: false,
  loading: () => (
    <div className="flex items-center justify-center py-16">
      <p className="text-sm text-muted-foreground">Loading voice assistant...</p>
    </div>
  ),
});

export default function VoicePage() {
  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Voice Assistant</h1>
        <p className="mt-1 text-muted-foreground">
          Speak with an AI-powered medical assistant using voice interaction.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <div className="flex items-start gap-3 rounded-lg border border-border bg-card p-4 shadow-sm">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-primary/10">
            <Mic className="h-5 w-5 text-primary" />
          </div>
          <div>
            <p className="text-sm font-semibold text-foreground">Real-time Transcription</p>
            <p className="mt-0.5 text-xs text-muted-foreground">
              Your speech is transcribed in real time using the Web Speech API.
            </p>
          </div>
        </div>
        <div className="flex items-start gap-3 rounded-lg border border-border bg-card p-4 shadow-sm">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-emerald-100 dark:bg-emerald-950/50">
            <Brain className="h-5 w-5 text-emerald-600" />
          </div>
          <div>
            <p className="text-sm font-semibold text-foreground">AI Analysis</p>
            <p className="mt-0.5 text-xs text-muted-foreground">
              Transcribed text is sent for AI-powered symptom analysis and guidance.
            </p>
          </div>
        </div>
        <div className="flex items-start gap-3 rounded-lg border border-border bg-card p-4 shadow-sm">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-blue-100 dark:bg-blue-950/50">
            <Globe className="h-5 w-5 text-blue-600" />
          </div>
          <div>
            <p className="text-sm font-semibold text-foreground">Multi-Language</p>
            <p className="mt-0.5 text-xs text-muted-foreground">
              Supports multiple languages via browser speech recognition.
            </p>
          </div>
        </div>
      </div>

      <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
        <VoiceRecorder />
      </div>

      <div className="rounded-md border border-border bg-muted/50 px-4 py-3">
        <div className="flex items-start gap-2">
          <Shield className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" />
          <p className="text-xs text-muted-foreground">
            Voice interactions are processed using your browser&#39;s built-in speech recognition.
            Audio is not recorded or stored on our servers. AI-generated responses are for
            informational purposes only and are not a substitute for professional medical advice.
            All data transmission is encrypted in compliance with HIPAA regulations.
          </p>
        </div>
      </div>
    </div>
  );
}
