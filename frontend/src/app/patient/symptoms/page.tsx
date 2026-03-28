"use client";

import { useState, useEffect, useRef, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { Send, Stethoscope, Bot, User, AlertTriangle, TestTube2, ArrowRight } from "lucide-react";
import { ApiKeyModal } from "@/components/shared/api-key-modal";
import SpecialtySelector from "@/components/shared/SpecialtySelector";
import apiClient from "@/lib/api-client";

const JOURNEY_STORAGE_STEP = "medassist_journey_step";
const JOURNEY_STORAGE_SPECIALTY = "medassist_specialty";

interface Message { role: "user" | "assistant"; content: string; }

interface SessionResult {
  urgency_score?: number;
  differential_diagnosis?: Array<{ condition: string; confidence: number }>;
  recommended_action?: string;
  recommended_specialist?: string;
  recommended_tests?: string[];
}

function SymptomsPageContent() {
  const searchParams = useSearchParams();
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
  const [showSpecialtyPicker, setShowSpecialtyPicker] = useState(false);
  const [selectedSpecialty, setSelectedSpecialty] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => { setHasApiKey(true); loadPastSessions(); }, []);

  const specialtyParam = searchParams.get("specialty");
  const resumeParam = searchParams.get("resume");

  useEffect(() => { if (specialtyParam) { setSelectedSpecialty(specialtyParam); localStorage.setItem(JOURNEY_STORAGE_SPECIALTY, specialtyParam); localStorage.setItem(JOURNEY_STORAGE_STEP, "1"); } }, [specialtyParam]);

  useEffect(() => {
    if (!resumeParam) return;
    let cancelled = false;
    const loadSession = async () => {
      try {
        const res = await apiClient.get(`/symptoms/session/${resumeParam}`);
        const data = res.data as Record<string, unknown>;
        if (cancelled || !data?.id) return;
        setSessionId(String(data.id));
        setSessionResult(null);
        setError(null);
        const log = data.conversation_log;
        const parsed: Message[] = [];
        if (Array.isArray(log)) {
          for (const entry of log) {
            if (entry && typeof entry === "object" && "role" in entry && "content" in entry) {
              const role = (entry as { role: string }).role;
              const content = String((entry as { content: unknown }).content ?? "");
              if (role === "user" || role === "assistant") parsed.push({ role, content });
            }
          }
        }
        if (parsed.length === 0) parsed.push({ role: "assistant", content: "Welcome back. Continue describing your symptoms, or ask a follow-up question." });
        setMessages(parsed);
        const analysis = data.ai_analysis as Record<string, unknown> | null | undefined;
        if (analysis && typeof analysis === "object") {
          setSessionResult({ urgency_score: analysis.urgency_score as number | undefined, differential_diagnosis: analysis.differential_diagnosis as SessionResult["differential_diagnosis"] | undefined, recommended_action: analysis.recommended_action as string | undefined, recommended_specialist: analysis.recommended_specialist as string | undefined, recommended_tests: analysis.recommended_tests as string[] | undefined });
        }
      } catch { if (!cancelled) setError("Could not resume this session. Start a new check or try again."); }
    };
    void loadSession();
    return () => { cancelled = true; };
  }, [resumeParam]);

  useEffect(() => { messagesEndRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages]);

  const loadPastSessions = async () => {
    try {
      const userStr = localStorage.getItem("user");
      if (!userStr) return;
      const user = JSON.parse(userStr);
      const res = await apiClient.get(`/symptoms/history/${user.id}`);
      const sessions = res.data?.sessions ?? res.data ?? [];
      setPastSessions(Array.isArray(sessions) ? sessions : []);
    } catch { /* History not available */ } finally { setLoadingHistory(false); }
  };

  const handleSpecialtySelect = (specialtyId: string) => {
    setSelectedSpecialty(specialtyId);
    setShowSpecialtyPicker(false);
    localStorage.setItem(JOURNEY_STORAGE_SPECIALTY, specialtyId);
    localStorage.setItem(JOURNEY_STORAGE_STEP, "1");
  };

  const startSession = async () => {
    
    // API key is pre-configured on backend
    setIsLoading(true); setError(null); setSessionResult(null); setMessages([]);
    try {
      const res = await apiClient.post("/symptoms/session", {});
      const id = res.data?.session_id ?? res.data?.id;
      setSessionId(id);
      const specialtyLabel = selectedSpecialty ? selectedSpecialty.replace(/_/g, " ").replace(/\b\w/g, (c: string) => c.toUpperCase()) : null;
      setMessages([{ role: "assistant", content: specialtyLabel ? `Hello! I am the MedAssist Symptom Analyst, focused on ${specialtyLabel}. Please describe your symptoms in detail.` : "Hello! I am the MedAssist Symptom Analyst. Please describe your symptoms in detail. What are you experiencing?" }]);
    } catch (err: unknown) {
      const msg = extractErrorMessage(err, "Failed to start symptom session.");
      setError(msg);
    } finally { setIsLoading(false); }
  };

  const sendMessage = async () => {
    if (!input.trim() || isLoading || !sessionId) return;
    
    // API key is pre-configured on backend
    const userMessage: Message = { role: "user", content: input.trim() };
    setMessages((prev) => [...prev, userMessage]);
    setInput(""); setIsLoading(true); setError(null);
    try {
      const res = await apiClient.post(`/symptoms/session/${sessionId}/message`, { message: userMessage.content });
      const data = res.data;
      const aiContent = data?.response ?? data?.message ?? data?.ai_response ?? "No response received.";
      setMessages((prev) => [...prev, { role: "assistant", content: aiContent }]);
      if (data?.urgency_score || data?.differential_diagnosis || data?.analysis) {
        setSessionResult({ urgency_score: data.urgency_score ?? data.analysis?.urgency_score, differential_diagnosis: data.differential_diagnosis ?? data.analysis?.differential_diagnosis, recommended_action: data.recommended_action ?? data.analysis?.recommended_action, recommended_specialist: data.recommended_specialist ?? data.analysis?.recommended_specialist, recommended_tests: data.recommended_tests ?? data.analysis?.recommended_tests });
      }
    } catch (err: unknown) { setError(extractErrorMessage(err, "Failed to send message.")); }
    finally { setIsLoading(false); }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(); } };
  const resetSession = () => { setSessionId(null); setMessages([]); setSessionResult(null); setError(null); loadPastSessions(); };
  const urgencyColor = (score: number) => { if (score <= 3) return "text-green-600 bg-green-100"; if (score <= 6) return "text-amber-600 bg-amber-100"; return "text-red-600 bg-red-100"; };

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Symptom Checker</h1>
          <p className="mt-1 text-muted-foreground">Describe your symptoms and get AI-powered analysis and recommendations.</p>
          {selectedSpecialty && (
            <div className="mt-2 flex items-center gap-2">
              <Stethoscope className="h-4 w-4 text-primary" />
              <span className="text-sm font-medium text-primary">{selectedSpecialty.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())}</span>
              <button type="button" onClick={() => { setSelectedSpecialty(null); setShowSpecialtyPicker(true); }} className="text-xs text-muted-foreground underline hover:text-foreground">Change</button>
            </div>
          )}
        </div>
        <button onClick={() => setShowKeyModal(true)} className="flex items-center gap-2 rounded-md border border-input px-3 py-1.5 text-sm font-medium hover:bg-muted">
          <span className={`inline-block h-2 w-2 rounded-full ${hasApiKey ? "bg-green-500" : "bg-red-500"}`} />
          {hasApiKey ? "AI Connected" : "Set API Key"}
        </button>
      </div>

      {showSpecialtyPicker && !sessionId && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-foreground">Select a Specialty</h2>
            <button type="button" onClick={() => setShowSpecialtyPicker(false)} className="text-sm text-muted-foreground hover:text-foreground">Skip</button>
          </div>
          <SpecialtySelector onSelect={handleSpecialtySelect} />
        </div>
      )}

      {!sessionId && !showSpecialtyPicker ? (
        <div className="grid gap-6 md:grid-cols-2">
          <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary/10 text-primary"><Stethoscope className="h-5 w-5" /></div>
              <div><p className="text-sm font-medium text-muted-foreground">Start New Check</p><p className="text-xl font-bold text-foreground">AI Symptom Analysis</p></div>
            </div>
            {!selectedSpecialty && (
              <button type="button" onClick={() => setShowSpecialtyPicker(true)} className="mt-4 flex w-full items-center justify-between rounded-md border border-dashed border-primary/40 bg-primary/5 px-4 py-3 text-sm font-medium text-primary hover:bg-primary/10">
                <span>Choose a specialty first (recommended)</span><ArrowRight className="h-4 w-4" />
              </button>
            )}
            <p className="mt-4 text-sm text-muted-foreground">Start a new symptom check session. Our AI assistant will guide you through questions to help identify possible conditions.</p>
            <button onClick={startSession} disabled={isLoading} className="mt-4 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50">{isLoading ? "Starting..." : "Start New Check"}</button>
          </div>
          <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-blue-100 text-blue-600"><span className="text-lg font-bold">H</span></div>
              <div><p className="text-sm font-medium text-muted-foreground">Session History</p><p className="text-xl font-bold text-foreground">Past Checks</p></div>
            </div>
            <div className="mt-4">
              {loadingHistory ? <p className="text-sm text-muted-foreground">Loading history...</p> : pastSessions.length === 0 ? <p className="text-sm text-muted-foreground italic">No past sessions found.</p> : (
                <div className="space-y-2 max-h-64 overflow-y-auto">
                  {pastSessions.slice(0, 10).map((session, idx) => (
                    <div key={(session.id as string) ?? idx} className="rounded-md border border-border p-3 text-sm">
                      <div className="flex items-center justify-between">
                        <span className="font-medium text-foreground">{(session.chief_complaint as string) ?? (session.initial_complaint as string) ?? "Symptom Check"}</span>
                        {typeof session.urgency_score === "number" && <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${urgencyColor(session.urgency_score)}`}>Urgency: {session.urgency_score}/10</span>}
                      </div>
                      <p className="mt-1 text-xs text-muted-foreground">{session.created_at ? new Date(session.created_at as string).toLocaleDateString() : ""} - Status: {(session.status as string) ?? "unknown"}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      ) : sessionId ? (
        <div className="flex flex-col" style={{ height: "calc(100vh - 16rem)" }}>
          <div className="mb-3 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-sm text-muted-foreground">Session: {sessionId.slice(0, 8)}...</span>
              {selectedSpecialty && <span className="rounded-full bg-primary/10 px-2.5 py-0.5 text-xs font-medium text-primary">{selectedSpecialty.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())}</span>}
            </div>
            <button onClick={resetSession} className="rounded-md border border-input px-3 py-1 text-sm hover:bg-muted">End Session</button>
          </div>

          <div className="flex-1 overflow-y-auto rounded-lg border border-border bg-card p-4">
            {messages.map((msg, i) => (
              <div key={i} className={`mb-4 flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                <div className={`flex max-w-[80%] gap-2 ${msg.role === "user" ? "flex-row-reverse" : "flex-row"}`}>
                  <div className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${msg.role === "user" ? "bg-primary text-primary-foreground" : "bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300"}`}>
                    {msg.role === "user" ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
                  </div>
                  <div className={`rounded-2xl px-4 py-3 text-sm shadow-sm ${msg.role === "user" ? "rounded-tr-sm bg-primary text-primary-foreground" : "rounded-tl-sm bg-muted text-foreground"}`}>
                    <p className="whitespace-pre-wrap">{msg.content}</p>
                  </div>
                </div>
              </div>
            ))}
            {isLoading && (
              <div className="mb-4 flex justify-start">
                <div className="flex gap-2">
                  <div className="flex h-8 w-8 items-center justify-center rounded-full bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300"><Bot className="h-4 w-4" /></div>
                  <div className="rounded-2xl rounded-tl-sm bg-muted px-4 py-3 text-sm text-muted-foreground shadow-sm">
                    <span className="inline-flex gap-1"><span className="animate-bounce">.</span><span className="animate-bounce" style={{ animationDelay: "0.1s" }}>.</span><span className="animate-bounce" style={{ animationDelay: "0.2s" }}>.</span></span> Analyzing...
                  </div>
                </div>
              </div>
            )}
            {error && <div className="mb-4 flex items-center gap-2 rounded-md bg-destructive/10 px-4 py-3 text-sm text-destructive"><AlertTriangle className="h-4 w-4 shrink-0" />{error}</div>}
            <div ref={messagesEndRef} />
          </div>

          {sessionResult && (
            <div className="mt-3 rounded-lg border border-border bg-card p-4">
              <h3 className="text-sm font-semibold text-foreground">Analysis Results</h3>
              <div className="mt-2 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                {sessionResult.urgency_score != null && (
                  <div className="rounded-md border p-3">
                    <p className="text-xs text-muted-foreground">Urgency Score</p>
                    <p className={`mt-1 text-lg font-bold ${sessionResult.urgency_score <= 3 ? "text-green-600" : sessionResult.urgency_score <= 6 ? "text-amber-600" : "text-red-600"}`}>{sessionResult.urgency_score}/10</p>
                  </div>
                )}
                {sessionResult.recommended_action && <div className="rounded-md border p-3"><p className="text-xs text-muted-foreground">Recommended Action</p><p className="mt-1 text-sm font-medium text-foreground">{sessionResult.recommended_action}</p></div>}
                {sessionResult.recommended_specialist && <div className="rounded-md border p-3"><p className="text-xs text-muted-foreground">Specialist</p><p className="mt-1 text-sm font-medium text-foreground">{sessionResult.recommended_specialist}</p></div>}
              </div>
              {sessionResult.recommended_tests && sessionResult.recommended_tests.length > 0 && (
                <div className="mt-3 rounded-md border border-blue-200 bg-blue-50 p-3 dark:border-blue-900 dark:bg-blue-950/30">
                  <div className="flex items-center gap-2 mb-2"><TestTube2 className="h-4 w-4 text-blue-600" /><p className="text-xs font-semibold text-blue-700 dark:text-blue-300">Recommended Tests</p></div>
                  <ul className="space-y-1">
                    {sessionResult.recommended_tests.map((test, i) => <li key={i} className="flex items-center gap-2 text-sm text-blue-800 dark:text-blue-200"><span className="h-1.5 w-1.5 shrink-0 rounded-full bg-blue-500" />{test}</li>)}
                  </ul>
                </div>
              )}
              {sessionResult.differential_diagnosis && sessionResult.differential_diagnosis.length > 0 && (
                <div className="mt-3">
                  <p className="text-xs font-medium text-muted-foreground">Possible Conditions</p>
                  <div className="mt-1 space-y-1">
                    {sessionResult.differential_diagnosis.map((d, i) => <div key={i} className="flex items-center justify-between rounded-md bg-muted px-3 py-2 text-sm"><span className="text-foreground">{d.condition}</span><span className="text-xs text-muted-foreground">{Math.round(d.confidence * 100)}% confidence</span></div>)}
                  </div>
                </div>
              )}
            </div>
          )}

          <div className="mt-3 flex gap-2">
            <input type="text" value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={handleKeyDown} placeholder="Describe your symptoms..." disabled={isLoading} className="flex-1 rounded-full border border-input bg-background px-5 py-2.5 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring disabled:opacity-50" />
            <button onClick={sendMessage} disabled={!input.trim() || isLoading} className="flex h-10 w-10 items-center justify-center rounded-full bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50"><Send className="h-4 w-4" /></button>
          </div>
        </div>
      ) : null}

      <div className="rounded-md border border-border bg-muted/50 px-4 py-3">
        <p className="text-xs text-muted-foreground">AI-generated symptom analysis is for informational purposes only and is not a substitute for professional medical advice. If you are experiencing a medical emergency, call 911 immediately.</p>
      </div>

      <ApiKeyModal isOpen={showKeyModal} onClose={() => setShowKeyModal(false)} onSave={() => setHasApiKey(true)} />
    </div>
  );
}

export default function SymptomsPage() {
  return (
    <Suspense fallback={<div className="flex min-h-[240px] items-center justify-center rounded-lg border border-border bg-card"><p className="text-sm text-muted-foreground">Loading...</p></div>}>
      <SymptomsPageContent />
    </Suspense>
  );
}

function extractErrorMessage(err: unknown, fallback: string): string {
  if (err && typeof err === "object" && "response" in err && err.response && typeof err.response === "object" && "data" in err.response) {
    const data = (err.response as { data: Record<string, unknown> }).data;
    if (data?.error && typeof data.error === "object" && "message" in (data.error as Record<string, unknown>)) return (data.error as { message: string }).message;
    if (typeof data?.message === "string") return data.message;
    if (typeof data?.error === "string") return data.error;
  }
  return fallback;
}
