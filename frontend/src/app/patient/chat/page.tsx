export default function ChatPage() {
  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-foreground">AI Chat</h1>
        <p className="mt-1 text-muted-foreground">
          Ask health questions and get AI-powered medical guidance.
        </p>
      </div>

      <div className="rounded-lg border border-border bg-card shadow-sm">
        <div className="flex flex-col items-center justify-center py-16 px-6">
          <div className="flex h-16 w-16 items-center justify-center rounded-full bg-primary/10">
            <span className="text-2xl font-bold text-primary">AI</span>
          </div>
          <h3 className="mt-4 text-lg font-semibold text-foreground">MedAssist AI Assistant</h3>
          <p className="mt-2 max-w-md text-center text-sm text-muted-foreground">
            Chat with our AI assistant about your health concerns. Get information about
            symptoms, medications, lab results, and general health questions.
          </p>
          <div className="mt-6">
            <span className="inline-flex items-center rounded-full bg-amber-100 px-3 py-1 text-xs font-medium text-amber-800">
              Coming Soon
            </span>
          </div>
        </div>

        <div className="border-t border-border p-4">
          <div className="flex gap-2">
            <input
              type="text"
              disabled
              placeholder="Type your health question..."
              className="flex-1 rounded-md border border-border bg-muted/50 px-4 py-2 text-sm text-muted-foreground"
            />
            <button
              disabled
              className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground opacity-50"
            >
              Send
            </button>
          </div>
        </div>
      </div>

      <div className="rounded-md border border-border bg-muted/50 px-4 py-3">
        <p className="text-xs text-muted-foreground">
          AI responses are for informational purposes only. Always consult your healthcare
          provider for medical advice, diagnosis, or treatment.
        </p>
      </div>
    </div>
  );
}
