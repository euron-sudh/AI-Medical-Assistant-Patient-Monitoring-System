export default function VoicePage() {
  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Voice Assistant</h1>
        <p className="mt-1 text-muted-foreground">
          Speak with an AI-powered medical assistant using voice interaction.
        </p>
      </div>

      <div className="rounded-lg border border-border bg-card shadow-sm">
        <div className="flex flex-col items-center justify-center py-16 px-6">
          <div className="flex h-16 w-16 items-center justify-center rounded-full bg-primary/10">
            <svg
              className="h-8 w-8 text-primary"
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth={1.5}
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M12 18.75a6 6 0 0 0 6-6v-1.5m-6 7.5a6 6 0 0 1-6-6v-1.5m6 7.5v3.75m-3.75 0h7.5M12 15.75a3 3 0 0 1-3-3V4.5a3 3 0 1 1 6 0v8.25a3 3 0 0 1-3 3Z"
              />
            </svg>
          </div>
          <h3 className="mt-4 text-lg font-semibold text-foreground">
            Voice-Powered Health Assistant
          </h3>
          <p className="mt-2 max-w-md text-center text-sm text-muted-foreground">
            Report symptoms, ask health questions, and get AI-powered guidance
            through natural voice conversation. Supports 50+ languages via
            OpenAI Whisper.
          </p>
          <div className="mt-6">
            <span className="inline-flex items-center rounded-full bg-amber-100 px-3 py-1 text-xs font-medium text-amber-800">
              Coming Soon
            </span>
          </div>
          <button
            disabled
            className="mt-4 flex items-center gap-2 rounded-full bg-primary px-6 py-3 text-sm font-medium text-primary-foreground opacity-50"
          >
            <svg
              className="h-5 w-5"
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth={1.5}
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M12 18.75a6 6 0 0 0 6-6v-1.5m-6 7.5a6 6 0 0 1-6-6v-1.5m6 7.5v3.75m-3.75 0h7.5M12 15.75a3 3 0 0 1-3-3V4.5a3 3 0 1 1 6 0v8.25a3 3 0 0 1-3 3Z"
              />
            </svg>
            Start Voice Session
          </button>
        </div>
      </div>

      <div className="rounded-md border border-border bg-muted/50 px-4 py-3">
        <p className="text-xs text-muted-foreground">
          Voice interactions are transcribed using AI. By using this feature, you
          consent to audio recording for the duration of the session. All
          recordings are encrypted and stored in compliance with HIPAA
          regulations.
        </p>
      </div>
    </div>
  );
}
