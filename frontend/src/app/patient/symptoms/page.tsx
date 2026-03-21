"use client";

import { useState, useEffect, useRef } from "react";
import { ApiKeyModal } from "@/components/shared/api-key-modal";
import apiClient from "@/lib/api-client";

interface Message {
  role: "user" | "assistant";
  content: string;
}

interface SessionResult {
  urgency_score?: number;
  differential_diagnosis?: Array<{
    condition: string;
    confidence: number;
  }>;
  recommended_action?: string;
  recommended_specialist?: string;
}

export default function SymptomsPage() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasApiKey, setHasApiKey] = useState(false);
  const [showKeyModal, setShowKeyModal] = useState(false);
  const [sessionResult, setSessionResult] = useState<SessionResult | null>(null);
  const [pastSessions, setPastSessions] = useState<Array<Record<string, unknown>>>([]);
  const [loadingHistory, setLoadingHistory] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const key = localStorage.getItem("euriApiKey");
    setHasApiKey(!!key && key.startsWith("euri-"));
    loadPastSessions();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const loadPastSessions = async () => {
    try {
      const userStr = localStorage.getItem("user");
      if (!userStr) return;
      const user = JSON.parse(userStr);
      const res = await apiClient.get(`/symptoms/history/${user.id}`);
      const sessions = res.data?.sessions ?? res.data ?? [];
      setPastSessions(Array.isArray(sessions) ? sessions : []);
    } catch {
      // History not available is fine
    } finally {
      setLoadingHistory(false);
    }
  };

  const startSession = async () => {
    const euriKey = localStorage.getItem("euriApiKey") ?? "";
    if (!euriKey) {
      setShowKeyModal(true);
      return;
    }

    setIsLoading(true);
    setError(null);
    setSessionResult(null);
    setMessages([]);

    try {
      const res = await apiClient.post(
        "/symptoms/session",
        {},
        { headers: { "X-Euri-Api-Key": euriKey } }
      );
      const id = res.data?.session_id ?? res.data?.id;
      setSessionId(id);
      setMessages([
        {
          role: "assistant",
          content:
            "Hello! I'm the MedAssist Symptom Analyst. Please describe your symptoms in detail. What are you experiencing?",
        },
      ]);
    } catch (err: unknown) {
      const msg = extractErrorMessage(err, "Failed to start symptom session.");
      setError(msg);
      if (msg.includes("API key") || msg.includes("Invalid")) {
        setShowKeyModal(true);
      }
    } finally {
      setIsLoading(false);
    }
  };

  const sendMessage = async () => {
    if (!input.trim() || isLoading || !sessionId) return;

    const euriKey = localStorage.getItem("euriApiKey") ?? "";
    if (!euriKey) {
      setShowKeyModal(true);
      return;
    }

    const userMessage: Message = { role: "user", content: input.trim() };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);
    setError(null);

    try {
      const res = await apiClient.post(
        `/symptoms/session/${sessionId}/message`,
        { message: userMessage.content },
        { headers: { "X-Euri-Api-Key": euriKey } }
      );

      const data = res.data;
      const aiContent =
        data?.response ?? data?.message ?? data?.ai_response ?? "No response received.";

      setMessages((prev) => [...prev, { role: "assistant", content: aiContent }]);

      // Check if the session returned analysis results
      if (data?.urgency_score || data?.differential_diagnosis || data?.analysis) {
        setSessionResult({
          urgency_score: data.urgency_score ?? data.analysis?.urgency_score,
          differential_diagnosis:
            data.differential_diagnosis ?? data.analysis?.differential_diagnosis,
          recommended_action:
            data.recommended_action ?? data.analysis?.recommended_action,
          recommended_specialist:
            data.recommended_specialist ?? data.analysis?.recommended_specialist,
        });
      }
    } catch (err: unknown) {
      const msg = extractErrorMessage(err, "Failed to send message.");
      setError(msg);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const resetSession = () => {
    setSessionId(null);
    setMessages([]);
    setSessionResult(null);
    setError(null);
    loadPastSessions();
  };

  const urgencyColor = (score: number) => {
    if (score <= 3) return "text-green-600 bg-green-100";
    if (score <= 6) return "text-amber-600 bg-amber-100";
    return "text-red-600 bg-red-100";
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Symptom Checker</h1>
          <p className="mt-1 text-muted-foreground">
            Describe your symptoms and get AI-powered analysis and recommendations.
          </p>
        </div>
        <button
          onClick={() => setShowKeyModal(true)}
          className="flex items-center gap-2 rounded-md border border-input px-3 py-1.5 text-sm font-medium hover:bg-muted"
        >
          <span
            className={`inline-block h-2 w-2 rounded-full ${
              hasApiKey ? "bg-green-500" : "bg-red-500"
            }`}
          />
          {hasApiKey ? "AI Connected" : "Set API Key"}
        </button>
      </div>

      {!sessionId ? (
        <div className="grid gap-6 md:grid-cols-2">
          {/* Start New Check */}
          <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary/10 text-primary">
                <span className="text-lg font-bold">S</span>
              </div>
              <div>
                <p className="text-sm font-medium text-muted-foreground">Start New Check</p>
                <p className="text-xl font-bold text-foreground">AI Symptom Analysis</p>
              </div>
            </div>
            <p className="mt-4 text-sm text-muted-foreground">
              Start a new symptom check session. Our AI assistant will guide you through a
              series of questions to help identify possible conditions.
            </p>
            <button
              onClick={startSession}
              disabled={isLoading}
              className="mt-4 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
            >
              {isLoading ? "Starting..." : "Start New Check"}
            </button>
            {!hasApiKey && (
              <p className="mt-2 text-xs text-amber-600">
                Set your EURI API key first to use AI features.
              </p>
            )}
          </div>

          {/* Past Sessions */}
          <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-blue-100 text-blue-600">
                <span className="text-lg font-bold">H</span>
              </div>
              <div>
                <p className="text-sm font-medium text-muted-foreground">Session History</p>
                <p className="text-xl font-bold text-foreground">Past Checks</p>
              </div>
            </div>
            <div className="mt-4">
              {loadingHistory ? (
                <p className="text-sm text-muted-foreground">Loading history...</p>
              ) : pastSessions.length === 0 ? (
                <p className="text-sm text-muted-foreground italic">No past sessions found.</p>
              ) : (
                <div className="space-y-2 max-h-64 overflow-y-auto">
                  {pastSessions.slice(0, 10).map((session, idx) => (
                    <div
                      key={(session.id as string) ?? idx}
                      className="rounded-md border border-border p-3 text-sm"
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-medium text-foreground">
                          {(session.chief_complaint as string) ??
                            (session.initial_complaint as string) ??
                            "Symptom Check"}
                        </span>
                        {typeof session.urgency_score === "number" && (
                          <span
                            className={`rounded-full px-2 py-0.5 text-xs font-medium ${urgencyColor(
                              session.urgency_score
                            )}`}
                          >
                            Urgency: {session.urgency_score}/10
                          </span>
                        )}
                      </div>
                      <p className="mt-1 text-xs text-muted-foreground">
                        {session.created_at
                          ? new Date(session.created_at as string).toLocaleDateString()
                          : ""}
                        {" - "}
                        Status: {(session.status as string) ?? "unknown"}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      ) : (
        /* Active Session - Chat Interface */
        <div className="flex flex-col" style={{ height: "calc(100vh - 16rem)" }}>
          <div className="mb-3 flex items-center justify-between">
            <span className="text-sm text-muted-foreground">
              Session: {sessionId.slice(0, 8)}...
            </span>
            <button
              onClick={resetSession}
              className="rounded-md border border-input px-3 py-1 text-sm hover:bg-muted"
            >
              End Session
            </button>
          </div>

          <div className="flex-1 overflow-y-auto rounded-lg border border-border bg-card p-4">
            {messages.map((msg, i) => (
              <div
                key={i}
                className={`mb-4 flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
              >
                <div
                  className={`max-w-[80%] rounded-lg px-4 py-3 text-sm ${
                    msg.role === "user"
                      ? "bg-primary text-primary-foreground"
                      : "bg-muted text-foreground"
                  }`}
                >
                  <p className="whitespace-pre-wrap">{msg.content}</p>
                </div>
              </div>
            ))}

            {isLoading && (
              <div className="mb-4 flex justify-start">
                <div className="rounded-lg bg-muted px-4 py-3 text-sm text-muted-foreground">
                  <span className="inline-flex gap-1">
                    <span className="animate-bounce">.</span>
                    <span className="animate-bounce" style={{ animationDelay: "0.1s" }}>
                      .
                    </span>
                    <span className="animate-bounce" style={{ animationDelay: "0.2s" }}>
                      .
                    </span>
                  </span>{" "}
                  Analyzing...
                </div>
              </div>
            )}

            {error && (
              <div className="mb-4 rounded-md bg-destructive/10 px-4 py-3 text-sm text-destructive">
                {error}
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Session Result Panel */}
          {sessionResult && (
            <div className="mt-3 rounded-lg border border-border bg-card p-4">
              <h3 className="text-sm font-semibold text-foreground">Analysis Results</h3>
              <div className="mt-2 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                {sessionResult.urgency_score != null && (
                  <div className="rounded-md border p-3">
                    <p className="text-xs text-muted-foreground">Urgency Score</p>
                    <p
                      className={`mt-1 text-lg font-bold ${
                        sessionResult.urgency_score <= 3
                          ? "text-green-600"
                          : sessionResult.urgency_score <= 6
                          ? "text-amber-600"
                          : "text-red-600"
                      }`}
                    >
                      {sessionResult.urgency_score}/10
                    </p>
                  </div>
                )}
                {sessionResult.recommended_action && (
                  <div className="rounded-md border p-3">
                    <p className="text-xs text-muted-foreground">Recommended Action</p>
                    <p className="mt-1 text-sm font-medium text-foreground">
                      {sessionResult.recommended_action}
                    </p>
                  </div>
                )}
                {sessionResult.recommended_specialist && (
                  <div className="rounded-md border p-3">
                    <p className="text-xs text-muted-foreground">Specialist</p>
                    <p className="mt-1 text-sm font-medium text-foreground">
                      {sessionResult.recommended_specialist}
                    </p>
                  </div>
                )}
              </div>
              {sessionResult.differential_diagnosis &&
                sessionResult.differential_diagnosis.length > 0 && (
                  <div className="mt-3">
                    <p className="text-xs font-medium text-muted-foreground">
                      Possible Conditions
                    </p>
                    <div className="mt-1 space-y-1">
                      {sessionResult.differential_diagnosis.map((d, i) => (
                        <div
                          key={i}
                          className="flex items-center justify-between rounded-md bg-muted px-3 py-2 text-sm"
                        >
                          <span className="text-foreground">{d.condition}</span>
                          <span className="text-xs text-muted-foreground">
                            {Math.round(d.confidence * 100)}% confidence
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
            </div>
          )}

          {/* Input */}
          <div className="mt-3 flex gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Describe your symptoms..."
              disabled={isLoading}
              className="flex-1 rounded-md border border-input bg-background px-4 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring disabled:opacity-50"
            />
            <button
              onClick={sendMessage}
              disabled={!input.trim() || isLoading}
              className="rounded-md bg-primary px-6 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
            >
              Send
            </button>
          </div>
        </div>
      )}

      <div className="rounded-md border border-border bg-muted/50 px-4 py-3">
        <p className="text-xs text-muted-foreground">
          AI-generated symptom analysis is for informational purposes only and is not a
          substitute for professional medical advice. If you are experiencing a medical
          emergency, call 911 immediately.
        </p>
      </div>

      <ApiKeyModal
        isOpen={showKeyModal}
        onClose={() => setShowKeyModal(false)}
        onSave={(key) => setHasApiKey(!!key && key.startsWith("euri-"))}
      />
    </div>
  );
}

function extractErrorMessage(err: unknown, fallback: string): string {
  if (
    err &&
    typeof err === "object" &&
    "response" in err &&
    err.response &&
    typeof err.response === "object" &&
    "data" in err.response
  ) {
    const data = (err.response as { data: Record<string, unknown> }).data;
    if (data?.error && typeof data.error === "object" && "message" in (data.error as Record<string, unknown>)) {
      return (data.error as { message: string }).message;
    }
    if (typeof data?.message === "string") return data.message;
    if (typeof data?.error === "string") return data.error;
  }
  return fallback;
}
