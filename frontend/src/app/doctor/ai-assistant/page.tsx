"use client";

import { useState, useEffect, useRef } from "react";
import { ApiKeyModal } from "@/components/shared/api-key-modal";
import apiClient from "@/lib/api-client";

interface Message {
  role: "user" | "assistant";
  content: string;
}

export default function AIAssistantPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasApiKey, setHasApiKey] = useState(false);
  const [showKeyModal, setShowKeyModal] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const key = localStorage.getItem("euriApiKey");
    setHasApiKey(!!key && key.startsWith("euri-"));
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return;

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
      const response = await apiClient.post(
        "/chat/message",
        {
          message: userMessage.content,
          history: messages.slice(-10),
          context: "doctor_clinical_assistant",
        },
        {
          headers: { "X-Euri-Api-Key": euriKey },
        }
      );

      const aiMessage: Message = {
        role: "assistant",
        content: response.data.response,
      };
      setMessages((prev) => [...prev, aiMessage]);
    } catch (err: unknown) {
      const errData =
        err &&
        typeof err === "object" &&
        "response" in err &&
        err.response &&
        typeof err.response === "object" &&
        "data" in err.response
          ? (err.response as { data: { error?: { message?: string } } }).data
          : null;
      const msg =
        errData?.error?.message ?? "Failed to get AI response. Check your API key.";
      setError(msg);
      if (msg.includes("API key") || msg.includes("Invalid")) {
        setShowKeyModal(true);
      }
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

  const clearChat = () => {
    setMessages([]);
    setError(null);
  };

  return (
    <div className="flex h-[calc(100vh-8rem)] flex-col space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">AI Clinical Assistant</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            AI-powered clinical decision support for diagnosis, treatment planning, and medical queries.
          </p>
        </div>
        <div className="flex items-center gap-2">
          {messages.length > 0 && (
            <button
              onClick={clearChat}
              className="rounded-md border border-input px-3 py-1.5 text-xs font-medium hover:bg-muted"
            >
              Clear Chat
            </button>
          )}
          <button
            onClick={() => setShowKeyModal(true)}
            className="flex items-center gap-2 rounded-md border border-input px-3 py-1.5 text-xs font-medium hover:bg-muted"
          >
            <span
              className={`inline-block h-2 w-2 rounded-full ${
                hasApiKey ? "bg-green-500" : "bg-red-500"
              }`}
            />
            {hasApiKey ? "AI Connected" : "Set API Key"}
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto rounded-lg border border-border bg-card p-4">
        {messages.length === 0 && (
          <div className="flex h-full flex-col items-center justify-center text-center">
            <div className="flex h-16 w-16 items-center justify-center rounded-full bg-emerald-100">
              <span className="text-2xl font-bold text-emerald-700">Dx</span>
            </div>
            <h3 className="mt-4 text-lg font-semibold text-foreground">
              Clinical Decision Support
            </h3>
            <p className="mt-2 max-w-md text-sm text-muted-foreground">
              Ask about differential diagnoses, treatment protocols, drug interactions, lab result
              interpretation, or clinical guidelines. Responses include evidence-based references.
            </p>
            {!hasApiKey && (
              <button
                onClick={() => setShowKeyModal(true)}
                className="mt-4 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
              >
                Set EURI API Key to Start
              </button>
            )}
            <div className="mt-6 grid grid-cols-1 gap-2 sm:grid-cols-2">
              {[
                "Differential diagnosis for persistent chest pain with normal ECG",
                "First-line treatment for newly diagnosed Type 2 diabetes",
                "Drug interactions between warfarin and amiodarone",
                "Interpret CBC: WBC 15.2, Hgb 10.1, Plt 450",
                "NEWS2 scoring criteria and clinical escalation",
                "Guidelines for managing acute hypertensive crisis",
              ].map((q) => (
                <button
                  key={q}
                  onClick={() => setInput(q)}
                  className="rounded-md border border-border px-3 py-2 text-left text-xs text-muted-foreground hover:bg-muted"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

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
                <span className="animate-bounce" style={{ animationDelay: "0.1s" }}>.</span>
                <span className="animate-bounce" style={{ animationDelay: "0.2s" }}>.</span>
              </span>
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

      <div className="flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={
            hasApiKey
              ? "Ask a clinical question..."
              : "Set API key first..."
          }
          disabled={!hasApiKey || isLoading}
          className="flex-1 rounded-md border border-input bg-background px-4 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring disabled:opacity-50"
        />
        <button
          onClick={sendMessage}
          disabled={!input.trim() || isLoading || !hasApiKey}
          className="rounded-md bg-primary px-6 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
        >
          Send
        </button>
      </div>

      <div className="rounded-md border border-border bg-muted/50 px-4 py-2">
        <p className="text-xs text-muted-foreground">
          AI responses are for clinical decision support only. Always apply your professional
          judgment and verify recommendations against current clinical guidelines and patient context.
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
