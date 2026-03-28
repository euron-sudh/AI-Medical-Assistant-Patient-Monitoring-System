"use client";

import { useState, useEffect, useCallback, useRef, useMemo } from "react";
import { useRouter } from "next/navigation";
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  PieChart,
  Pie,
  Cell,
} from "recharts";

/* ==========================================================================
   TYPES
   ========================================================================== */

interface Scene {
  id: string;
  title: string;
  subtitle: string;
  narration: string;
  durationMs: number;
}

type VoiceOption = "alloy" | "nova";

/* ==========================================================================
   TTS SERVICE -- EURI API (OpenAI-compatible)
   ========================================================================== */

const EURI_TTS_URL = "https://api.euron.one/api/v1/euri/audio/speech";
const EURI_API_KEY =
  "euri-1359066cf23e5b59f64abda2da199c73046b7ba3910a018cdbdcb5ae3a13396d";

async function fetchTTSAudio(
  text: string,
  voice: VoiceOption
): Promise<ArrayBuffer | null> {
  try {
    const res = await fetch(EURI_TTS_URL, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${EURI_API_KEY}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ model: "tts-1", voice, input: text }),
    });
    if (!res.ok) {
      console.error(`TTS API error: ${res.status} ${res.statusText}`);
      return null;
    }
    const buf = await res.arrayBuffer();
    if (buf.byteLength === 0) {
      console.error("TTS API returned empty audio buffer");
      return null;
    }
    return buf;
  } catch (err) {
    console.error("TTS API fetch failed:", err);
    return null;
  }
}

/* ==========================================================================
   DEMO SCRIPT -- 11 SCENES
   ========================================================================== */

const SCENES: Scene[] = [
  {
    id: "intro",
    title: "Welcome to MedAssist AI",
    subtitle: "Platform Overview",
    narration:
      "Welcome to MedAssist AI, the enterprise-grade intelligent medical assistant platform designed to elevate the standard of patient care. By unifying AI-powered diagnostics, continuous patient monitoring, and real-time clinical decision support into a single secure platform, MedAssist AI empowers hospitals, telemedicine providers, and health systems to deliver faster, safer, and more personalized care at scale.",
    durationMs: 18000,
  },
  {
    id: "patient-portal",
    title: "Patient Portal",
    subtitle: "Empowering Patients with Transparency",
    narration:
      "The Patient Portal places each individual at the center of their care journey. Patients gain instant access to a personalized health dashboard where they can monitor their vitals in real time, review AI-analyzed medical reports in plain language, manage medication schedules with intelligent reminders, and communicate securely with their care team. Every interaction is protected by end-to-end encryption and full HIPAA compliance, ensuring patient trust from the very first login.",
    durationMs: 22000,
  },
  {
    id: "symptom-analysis",
    title: "AI-Powered Symptom Analysis",
    subtitle: "Reducing Time to Diagnosis",
    narration:
      "Our Symptom Analyst Agent conducts structured, multi-turn clinical interviews that adapt in real time to each patient's responses. Powered by GPT-4o and retrieval-augmented generation grounded in verified medical literature, the agent produces ranked differential diagnoses with calibrated confidence scores, urgency assessments, and specialist recommendations. By cross-referencing patient history, allergies, and active medications, MedAssist AI reduces diagnostic uncertainty and accelerates the path to appropriate care.",
    durationMs: 24000,
  },
  {
    id: "vitals-monitoring",
    title: "Real-Time Vitals Monitoring",
    subtitle: "Predictive Surveillance That Saves Lives",
    narration:
      "The Patient Monitoring Agent delivers continuous, twenty-four-seven vitals surveillance with adaptive baselines that learn each patient's unique physiological patterns. AI-driven anomaly detection identifies deterioration trends thirty to sixty minutes before they become clinically apparent, enabling proactive intervention rather than reactive treatment. Automated escalation chains route critical alerts from bedside nurse to attending physician to on-call specialist, ensuring no alert goes unacknowledged.",
    durationMs: 24000,
  },
  {
    id: "report-analysis",
    title: "Intelligent Report Analysis",
    subtitle: "From Raw Data to Actionable Insight",
    narration:
      "Upload any medical report, from lab panels and imaging studies to pathology results, and the Report Reader Agent, powered by GPT-4o Vision, extracts structured values, identifies abnormalities, and generates both clinician-grade summaries and patient-friendly explanations in seconds. Longitudinal trend analysis automatically compares current results against the patient's historical data, providing the complete clinical context that physicians need to make informed decisions.",
    durationMs: 22000,
  },
  {
    id: "drug-interaction",
    title: "Drug Interaction Safeguards",
    subtitle: "Patient Safety at the Point of Prescribing",
    narration:
      "Every new prescription is instantly analyzed against the patient's full medication profile, documented allergies, and active medical conditions. The Drug Interaction Agent flags potential conflicts with severity classifications and evidence-based citations before they ever reach the patient. When an interaction is detected, the system proactively recommends safer therapeutic alternatives and optimized dosing schedules, strengthening medication safety across the entire care continuum.",
    durationMs: 20000,
  },
  {
    id: "doctor-dashboard",
    title: "Doctor Dashboard",
    subtitle: "A Clinical Command Center",
    narration:
      "The Doctor Dashboard is a unified command center purpose-built for clinical efficiency. Physicians gain real-time visibility into their patient panel through a monitoring wall with color-coded status indicators, live vitals sparklines, and an intelligent alert feed. AI-assisted clinical note generation, priority patient queues ranked by acuity, and evidence-based decision support with source citations ensure that critical situations are identified and addressed without delay.",
    durationMs: 22000,
  },
  {
    id: "telemedicine",
    title: "Integrated Telemedicine",
    subtitle: "High-Quality Virtual Care, Enhanced by AI",
    narration:
      "MedAssist AI integrates high-definition video consultations powered by WebRTC with real-time transcription driven by OpenAI Whisper. During every call, an AI assistant sidebar provides contextual clinical support, while screen sharing enables collaborative review of reports and imaging. After the consultation, the platform automatically generates structured SOAP notes from the conversation transcript, reducing documentation burden and giving physicians more time for patient care.",
    durationMs: 22000,
  },
  {
    id: "admin-compliance",
    title: "Administration and Compliance",
    subtitle: "Enterprise-Grade Security, Built In",
    narration:
      "HIPAA compliance is not an afterthought. It is woven into every layer of the MedAssist AI architecture. Data is encrypted at rest with AES-256 and in transit with TLS 1.3. A comprehensive audit trail records every access to protected health information with immutable, tamper-proof entries retained for the full regulatory period. Role-based access control with four distinct privilege levels, automated compliance reporting, and real-time infrastructure health monitoring provide your compliance and IT teams with complete operational confidence.",
    durationMs: 24000,
  },
  {
    id: "ai-agents",
    title: "AI Agent Architecture",
    subtitle: "Seven Specialists, One Orchestrator",
    narration:
      "At the core of MedAssist AI is a coordinated ecosystem of seven specialized AI agents, each with dedicated tools, persistent memory, and autonomous decision-making capabilities. The Symptom Analyst, Report Reader, Triage, Voice, Drug Interaction, Monitoring, and Follow-Up agents are orchestrated by a central dispatcher powered by GPT-4o function calling, enabling parallel execution and context-aware collaboration that delivers clinically precise, patient-centered outcomes.",
    durationMs: 22000,
  },
  {
    id: "closing",
    title: "Transform Healthcare Today",
    subtitle: "Next Steps",
    narration:
      "MedAssist AI. Seven specialized AI agents. Continuous real-time monitoring. Full HIPAA compliance. One unified platform engineered to transform care delivery at scale. We invite you to experience the future of healthcare firsthand. Contact our team to schedule a personalized live demonstration and discover how MedAssist AI can drive measurable outcomes for your organization.",
    durationMs: 18000,
  },
];

/* ==========================================================================
   SYNTHETIC DATA
   ========================================================================== */

function generateVitalsData(count: number, offset: number = 0) {
  return Array.from({ length: count }, (_, i) => {
    const t = i + offset;
    return {
      time: `${String(8 + Math.floor(t / 6)).padStart(2, "0")}:${String(
        (t * 10) % 60
      ).padStart(2, "0")}`,
      heartRate: 72 + Math.sin(t * 0.3) * 8 + Math.random() * 4,
      systolic: 120 + Math.sin(t * 0.2) * 10 + Math.random() * 5,
      diastolic: 78 + Math.sin(t * 0.25) * 6 + Math.random() * 3,
      spo2: 97.5 + Math.sin(t * 0.15) * 1.2 + Math.random() * 0.5,
      temperature: 36.7 + Math.sin(t * 0.1) * 0.3 + Math.random() * 0.1,
      respiratory: 16 + Math.sin(t * 0.35) * 2 + Math.random() * 1,
    };
  });
}

const VITALS_DATA = generateVitalsData(24);

const LAB_RESULTS = [
  { test: "Hemoglobin", value: 13.8, unit: "g/dL", refMin: 12.0, refMax: 17.5, status: "normal" },
  { test: "WBC Count", value: 11.2, unit: "K/uL", refMin: 4.5, refMax: 11.0, status: "high" },
  { test: "Platelet Count", value: 245, unit: "K/uL", refMin: 150, refMax: 400, status: "normal" },
  { test: "Glucose (Fasting)", value: 142, unit: "mg/dL", refMin: 70, refMax: 100, status: "high" },
  { test: "Creatinine", value: 0.9, unit: "mg/dL", refMin: 0.7, refMax: 1.3, status: "normal" },
  { test: "TSH", value: 0.3, unit: "mIU/L", refMin: 0.4, refMax: 4.0, status: "low" },
  { test: "Total Cholesterol", value: 218, unit: "mg/dL", refMin: 0, refMax: 200, status: "high" },
  { test: "HbA1c", value: 6.8, unit: "%", refMin: 0, refMax: 5.7, status: "high" },
];

const CHAT_MESSAGES = [
  {
    role: "assistant" as const,
    text: "Hello. I am your AI Symptom Analyst. Could you describe the symptoms you are experiencing today?",
  },
  {
    role: "user" as const,
    text: "I have been having persistent headaches for the past 3 days, mostly on the right side. I also feel dizzy when I stand up.",
  },
  {
    role: "assistant" as const,
    text: "Thank you for sharing that. Can you describe the character of the pain? For example, is it throbbing, sharp, or a dull pressure? And on a scale of 1 to 10, how would you rate its severity?",
  },
  {
    role: "user" as const,
    text: "It is a throbbing pain, about 6 out of 10. It tends to get worse in the afternoon.",
  },
  {
    role: "assistant" as const,
    text: "Understood. Based on your reported symptoms, your history of mild hypertension, and your current medications, I have completed my analysis. Here are the findings:",
  },
];

const DIFFERENTIAL_DIAGNOSES = [
  { condition: "Tension-type Headache", confidence: 0.72, urgency: "Low" },
  { condition: "Migraine without Aura", confidence: 0.58, urgency: "Low" },
  { condition: "Hypertension-related Headache", confidence: 0.45, urgency: "Medium" },
  { condition: "Cervicogenic Headache", confidence: 0.31, urgency: "Low" },
];

const MEDICATIONS = [
  { name: "Lisinopril", dosage: "10mg", frequency: "Once daily", status: "Active" },
  { name: "Metformin", dosage: "500mg", frequency: "Twice daily", status: "Active" },
  { name: "Ibuprofen", dosage: "400mg", frequency: "As needed", status: "Active" },
  { name: "Atorvastatin", dosage: "20mg", frequency: "Once daily", status: "Active" },
];

const DRUG_INTERACTIONS = [
  {
    drug1: "Lisinopril",
    drug2: "Ibuprofen",
    severity: "Moderate",
    effect: "NSAIDs may reduce the antihypertensive effect of ACE inhibitors and increase the risk of renal impairment",
  },
  {
    drug1: "Metformin",
    drug2: "Ibuprofen",
    severity: "Mild",
    effect: "NSAIDs may rarely increase the risk of lactic acidosis when combined with metformin",
  },
];

const MONITORED_PATIENTS = [
  { name: "James Wilson", age: 68, room: "ICU-204", status: "critical", hr: 112, bp: "165/98", spo2: 91, news2: 8 },
  { name: "Sarah Chen", age: 45, room: "CCU-112", status: "warning", hr: 98, bp: "148/92", spo2: 94, news2: 5 },
  { name: "Robert Davis", age: 72, room: "ICU-207", status: "stable", hr: 76, bp: "128/82", spo2: 97, news2: 2 },
  { name: "Maria Garcia", age: 56, room: "MED-315", status: "stable", hr: 82, bp: "132/84", spo2: 98, news2: 1 },
  { name: "Thomas Brown", age: 61, room: "ICU-201", status: "warning", hr: 104, bp: "155/95", spo2: 93, news2: 6 },
  { name: "Linda Martinez", age: 39, room: "MED-308", status: "stable", hr: 70, bp: "118/76", spo2: 99, news2: 0 },
];

const AUDIT_LOG_ENTRIES = [
  { time: "14:32:07", user: "Dr. Emily Carter", action: "View Patient Record", resource: "Patient #4821", status: "Success" },
  { time: "14:31:45", user: "Nurse J. Williams", action: "Update Vitals", resource: "Patient #3156", status: "Success" },
  { time: "14:30:22", user: "Dr. M. Thompson", action: "Prescribe Medication", resource: "Patient #4821", status: "Success" },
  { time: "14:29:58", user: "Admin R. Chen", action: "Export Audit Logs", resource: "System", status: "Success" },
  { time: "14:28:33", user: "Dr. Emily Carter", action: "View Lab Results", resource: "Patient #2847", status: "Success" },
  { time: "14:27:11", user: "patient2847@mail.com", action: "Access Denied", resource: "Patient #4821", status: "Denied" },
];

const AGENT_DATA = [
  { name: "Symptom\nAnalyst", model: "GPT-4o", color: "#0EA5E9", description: "Conducts multi-turn clinical interviews and generates ranked differential diagnoses with confidence scoring" },
  { name: "Report\nReader", model: "GPT-4o Vision", color: "#8B5CF6", description: "Parses lab results, imaging, and pathology reports to extract structured values and identify abnormalities" },
  { name: "Triage", model: "GPT-4o-mini", color: "#EF4444", description: "Calculates Emergency Severity Index scores and routes patients to the appropriate level of care" },
  { name: "Voice", model: "Whisper + TTS", color: "#14B8A6", description: "Enables hands-free interaction through real-time speech-to-text and natural voice synthesis" },
  { name: "Drug\nInteraction", model: "GPT-4o-mini", color: "#F97316", description: "Detects medication conflicts, validates dosages, and recommends safer therapeutic alternatives" },
  { name: "Monitoring", model: "GPT-4o-mini", color: "#22C55E", description: "Performs continuous vitals surveillance with adaptive baselines and predictive anomaly detection" },
  { name: "Follow-Up", model: "GPT-4o", color: "#EC4899", description: "Generates personalized care plans, tracks treatment adherence, and schedules intelligent follow-ups" },
];

const SYSTEM_HEALTH = [
  { service: "PostgreSQL 16", status: "Healthy", uptime: "99.99%", latency: "2ms" },
  { service: "Redis 7", status: "Healthy", uptime: "99.99%", latency: "<1ms" },
  { service: "InfluxDB", status: "Healthy", uptime: "99.97%", latency: "5ms" },
  { service: "OpenAI API", status: "Healthy", uptime: "99.95%", latency: "320ms" },
  { service: "Pinecone", status: "Healthy", uptime: "99.98%", latency: "45ms" },
  { service: "Celery Workers", status: "Healthy", uptime: "99.99%", latency: "\u2014" },
];

const PIE_DATA = [
  { name: "Symptom Analysis", value: 35, color: "#0EA5E9" },
  { name: "Report Reading", value: 25, color: "#8B5CF6" },
  { name: "Triage", value: 15, color: "#EF4444" },
  { name: "Drug Checks", value: 12, color: "#F97316" },
  { name: "Monitoring", value: 8, color: "#22C55E" },
  { name: "Other", value: 5, color: "#94A3B8" },
];

/* ==========================================================================
   HOOKS
   ========================================================================== */

function useAnimatedVitals() {
  const [data, setData] = useState(() => generateVitalsData(24));
  const tickRef = useRef(24);

  useEffect(() => {
    const interval = setInterval(() => {
      tickRef.current += 1;
      setData((prev) => {
        const next = [...prev.slice(1), generateVitalsData(1, tickRef.current)[0]];
        return next;
      });
    }, 1500);
    return () => clearInterval(interval);
  }, []);

  return data;
}

/** Returns elapsed seconds since the scene mounted — drives timed reveals. */
function useSceneTimer(sceneId: string) {
  const [elapsed, setElapsed] = useState(0);
  const startRef = useRef(Date.now());

  useEffect(() => {
    startRef.current = Date.now();
    setElapsed(0);
    const iv = setInterval(() => {
      setElapsed((Date.now() - startRef.current) / 1000);
    }, 100);
    return () => clearInterval(iv);
  }, [sceneId]);

  return elapsed;
}

/** Animated counter: counts from 0 to `target` over `durationMs`. */
function useCountUp(target: number, durationMs: number, startDelay: number, elapsed: number) {
  if (elapsed < startDelay) return 0;
  const progress = Math.min((elapsed - startDelay) / (durationMs / 1000), 1);
  return Math.round(target * progress);
}

/* ==========================================================================
   TTS AUDIO HOOK (with pre-fetch, volume, loading, error state)
   ========================================================================== */

function useTTSAudio() {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const objectUrlRef = useRef<string | null>(null);
  const cacheRef = useRef<Map<string, ArrayBuffer>>(new Map());
  const fallbackTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const volumeRef = useRef(1);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [hasError, setHasError] = useState(false);

  const clearFallbackTimer = useCallback(() => {
    if (fallbackTimerRef.current) {
      clearTimeout(fallbackTimerRef.current);
      fallbackTimerRef.current = null;
    }
  }, []);

  const prefetch = useCallback(async (text: string, voice: VoiceOption): Promise<boolean> => {
    const key = `${voice}:${text.slice(0, 60)}`;
    if (cacheRef.current.has(key)) return true;
    const buf = await fetchTTSAudio(text, voice);
    if (buf) {
      cacheRef.current.set(key, buf);
      return true;
    }
    return false;
  }, []);

  const setVolume = useCallback((vol: number) => {
    volumeRef.current = Math.max(0, Math.min(1, vol));
    if (audioRef.current) {
      audioRef.current.volume = volumeRef.current;
    }
  }, []);

  const play = useCallback(
    async (text: string, voice: VoiceOption, onEnd?: () => void) => {
      // Stop any current playback
      clearFallbackTimer();
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current.onended = null;
        audioRef.current.onerror = null;
        audioRef.current = null;
      }
      if (objectUrlRef.current) {
        URL.revokeObjectURL(objectUrlRef.current);
        objectUrlRef.current = null;
      }

      setHasError(false);
      setIsLoading(true);
      setIsSpeaking(false);

      const key = `${voice}:${text.slice(0, 60)}`;
      let buffer = cacheRef.current.get(key) ?? null;
      if (!buffer) {
        buffer = await fetchTTSAudio(text, voice);
        if (buffer) {
          cacheRef.current.set(key, buffer);
        }
      }

      // TTS fetch failed -- show error, use timer fallback for scene advancement
      if (!buffer) {
        setIsLoading(false);
        setHasError(true);
        setIsSpeaking(false);
        const fallbackMs = Math.max(text.length * 65, 4000);
        fallbackTimerRef.current = setTimeout(() => {
          setHasError(false);
          onEnd?.();
        }, fallbackMs);
        return;
      }

      setIsLoading(false);

      const blob = new Blob([buffer], { type: "audio/mpeg" });
      const url = URL.createObjectURL(blob);
      objectUrlRef.current = url;

      const audio = new Audio(url);
      audio.volume = volumeRef.current;
      audio.preload = "auto";
      audioRef.current = audio;

      audio.onended = () => {
        setIsSpeaking(false);
        onEnd?.();
      };

      audio.onerror = () => {
        console.error("Audio playback error");
        setIsSpeaking(false);
        setHasError(true);
        // Fall back to timer-based advancement
        const fallbackMs = Math.max(text.length * 65, 4000);
        fallbackTimerRef.current = setTimeout(() => {
          setHasError(false);
          onEnd?.();
        }, fallbackMs);
      };

      try {
        await audio.play();
        setIsSpeaking(true);
      } catch (playErr) {
        console.error("Audio play() rejected:", playErr);
        setIsSpeaking(false);
        setHasError(true);
        // Timer fallback for auto-advance
        const fallbackMs = Math.max(text.length * 65, 4000);
        fallbackTimerRef.current = setTimeout(() => {
          setHasError(false);
          onEnd?.();
        }, fallbackMs);
      }
    },
    [clearFallbackTimer]
  );

  const pause = useCallback(() => {
    clearFallbackTimer();
    if (audioRef.current) {
      audioRef.current.pause();
    }
    setIsSpeaking(false);
  }, [clearFallbackTimer]);

  const resume = useCallback(() => {
    if (audioRef.current && !audioRef.current.ended) {
      audioRef.current.play().then(() => {
        setIsSpeaking(true);
      }).catch(() => {
        // Already paused or disposed
      });
    }
  }, []);

  const stop = useCallback(() => {
    clearFallbackTimer();
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.onended = null;
      audioRef.current.onerror = null;
      audioRef.current = null;
    }
    if (objectUrlRef.current) {
      URL.revokeObjectURL(objectUrlRef.current);
      objectUrlRef.current = null;
    }
    setIsSpeaking(false);
    setIsLoading(false);
    setHasError(false);
  }, [clearFallbackTimer]);

  useEffect(() => {
    return () => {
      clearFallbackTimer();
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current.onended = null;
        audioRef.current.onerror = null;
        audioRef.current = null;
      }
      if (objectUrlRef.current) URL.revokeObjectURL(objectUrlRef.current);
    };
  }, [clearFallbackTimer]);

  return { play, pause, resume, stop, prefetch, setVolume, isSpeaking, isLoading, hasError };
}

/* ==========================================================================
   CSS KEYFRAMES (injected via style tag)
   ========================================================================== */

const KEYFRAMES = `
@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(24px); }
  to { opacity: 1; transform: translateY(0); }
}
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}
@keyframes scaleIn {
  from { opacity: 0; transform: scale(0.85); }
  to { opacity: 1; transform: scale(1); }
}
@keyframes slideInLeft {
  from { opacity: 0; transform: translateX(-32px); }
  to { opacity: 1; transform: translateX(0); }
}
@keyframes slideInRight {
  from { opacity: 0; transform: translateX(32px); }
  to { opacity: 1; transform: translateX(0); }
}
@keyframes slideInDown {
  from { opacity: 0; transform: translateY(-20px); }
  to { opacity: 1; transform: translateY(0); }
}
@keyframes pulseGlow {
  0%, 100% { box-shadow: 0 0 0 0 rgba(14, 165, 233, 0.4); }
  50% { box-shadow: 0 0 24px 8px rgba(14, 165, 233, 0.15); }
}
@keyframes drawLine {
  from { stroke-dashoffset: 1000; }
  to { stroke-dashoffset: 0; }
}
@keyframes typewriter {
  from { width: 0; }
  to { width: 100%; }
}
@keyframes float {
  0%, 100% { transform: translateY(0px); }
  50% { transform: translateY(-8px); }
}
@keyframes waveform1 { 0%,100%{height:8px} 50%{height:20px} }
@keyframes waveform2 { 0%,100%{height:14px} 50%{height:6px} }
@keyframes waveform3 { 0%,100%{height:10px} 50%{height:24px} }
@keyframes ripple {
  0% { transform: scale(0.8); opacity: 1; }
  100% { transform: scale(2.4); opacity: 0; }
}
@keyframes orbitalSpin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
@keyframes particleDrift {
  0% { transform: translateY(0) translateX(0); opacity: 0; }
  10% { opacity: 0.6; }
  90% { opacity: 0.6; }
  100% { transform: translateY(-100vh) translateX(40px); opacity: 0; }
}
`;

/* ==========================================================================
   HELPER: timed visibility class
   ========================================================================== */

function vis(elapsed: number, showAfter: number): string {
  return elapsed >= showAfter ? "opacity-100" : "opacity-0 pointer-events-none";
}

function anim(elapsed: number, showAfter: number, animation: string, duration = "0.7s"): React.CSSProperties {
  if (elapsed < showAfter) return { opacity: 0 };
  return {
    animation: `${animation} ${duration} ease-out both`,
  };
}

/* ==========================================================================
   MAIN DEMO COMPONENT
   ========================================================================== */

export default function DemoPage() {
  const router = useRouter();
  const [started, setStarted] = useState(false);
  const [currentScene, setCurrentScene] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [progress, setProgress] = useState(0);
  const [sceneProgress, setSceneProgress] = useState(0);
  const [transitioning, setTransitioning] = useState(false);
  const [voice, setVoice] = useState<VoiceOption>("alloy");
  const [autoAdvance, setAutoAdvance] = useState(true);
  const [narrationEnabled, setNarrationEnabled] = useState(true);
  const [isPaused, setIsPaused] = useState(false);
  const [muted, setMuted] = useState(false);
  const [volume, setVolume] = useState(1);
  const [isLoadingAudio, setIsLoadingAudio] = useState(false);

  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const progressRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const sceneStartRef = useRef<number>(0);

  const tts = useTTSAudio();

  const totalDuration = useMemo(
    () => SCENES.reduce((sum, s) => sum + s.durationMs, 0),
    []
  );
  const cumulativeDurations = useMemo(() => {
    const result: number[] = [];
    let sum = 0;
    for (const s of SCENES) {
      result.push(sum);
      sum += s.durationMs;
    }
    return result;
  }, []);

  const animatedVitals = useAnimatedVitals();

  /* -- Scene advancement -- */
  const advanceScene = useCallback(() => {
    setTransitioning(true);
    setTimeout(() => {
      setCurrentScene((prev) => {
        const next = prev + 1;
        if (next >= SCENES.length) {
          setPlaying(false);
          setTransitioning(false);
          return prev;
        }
        return next;
      });
      setTimeout(() => setTransitioning(false), 50);
    }, 500);
  }, []);

  /* -- Play scene -- */
  const playScene = useCallback(
    (index: number) => {
      if (index >= SCENES.length) {
        setPlaying(false);
        return;
      }
      const scene = SCENES[index];
      sceneStartRef.current = Date.now();

      // Pre-fetch next scene audio in background
      if (index + 1 < SCENES.length) {
        tts.prefetch(SCENES[index + 1].narration, voice);
      }

      if (narrationEnabled) {
        // Set current volume before playing (handles mute state)
        tts.setVolume(muted ? 0 : volume);
        tts.play(scene.narration, voice, () => {
          if (autoAdvance) {
            timerRef.current = setTimeout(() => advanceScene(), 1200);
          }
        });
      } else if (autoAdvance) {
        timerRef.current = setTimeout(() => advanceScene(), scene.durationMs);
      }
    },
    [tts, voice, advanceScene, autoAdvance, narrationEnabled, muted, volume]
  );

  /* -- Effect: play current scene when it changes -- */
  useEffect(() => {
    if (playing && !isPaused) {
      playScene(currentScene);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentScene, playing]);

  /* -- Global progress ticker -- */
  useEffect(() => {
    if (!playing || isPaused) {
      if (progressRef.current) clearInterval(progressRef.current);
      return;
    }
    progressRef.current = setInterval(() => {
      const elapsed = cumulativeDurations[currentScene] + (Date.now() - sceneStartRef.current);
      setProgress(Math.min((elapsed / totalDuration) * 100, 100));
      const sceneDur = SCENES[currentScene]?.durationMs ?? 1;
      const sceneElapsed = Date.now() - sceneStartRef.current;
      setSceneProgress(Math.min((sceneElapsed / sceneDur) * 100, 100));
    }, 80);
    return () => {
      if (progressRef.current) clearInterval(progressRef.current);
    };
  }, [playing, isPaused, currentScene, cumulativeDurations, totalDuration]);

  /* -- Controls -- */
  const handleStart = useCallback(async () => {
    if (narrationEnabled) {
      // Pre-fetch first scene audio BEFORE starting -- user has clicked so autoplay is allowed
      setIsLoadingAudio(true);
      await tts.prefetch(SCENES[0].narration, voice);
      // Also kick off prefetch for scene 2 in background
      if (SCENES.length > 1) {
        tts.prefetch(SCENES[1].narration, voice);
      }
      setIsLoadingAudio(false);
    }
    setStarted(true);
    setPlaying(true);
    setIsPaused(false);
    setCurrentScene(0);
    setProgress(0);
  }, [narrationEnabled, tts, voice]);

  const togglePlayPause = useCallback(() => {
    if (isPaused) {
      setIsPaused(false);
      setPlaying(true);
      tts.resume();
    } else {
      setIsPaused(true);
      tts.pause();
      if (timerRef.current) clearTimeout(timerRef.current);
    }
  }, [isPaused, tts]);

  const goToScene = useCallback(
    (index: number) => {
      tts.stop();
      if (timerRef.current) clearTimeout(timerRef.current);
      setCurrentScene(index);
      setIsPaused(false);
      setPlaying(true);
    },
    [tts]
  );

  const skipNext = useCallback(() => {
    if (currentScene < SCENES.length - 1) {
      tts.stop();
      if (timerRef.current) clearTimeout(timerRef.current);
      advanceScene();
    }
  }, [currentScene, advanceScene, tts]);

  const skipPrev = useCallback(() => {
    if (currentScene > 0) goToScene(currentScene - 1);
  }, [currentScene, goToScene]);

  const handleClose = useCallback(() => {
    tts.stop();
    if (timerRef.current) clearTimeout(timerRef.current);
    router.push("/login");
  }, [router, tts]);

  const toggleMute = useCallback(() => {
    setMuted((m) => {
      if (!m) {
        tts.setVolume(0);
      } else {
        tts.setVolume(volume);
      }
      return !m;
    });
  }, [tts, volume]);

  const handleVolumeChange = useCallback((newVol: number) => {
    setVolume(newVol);
    if (!muted) {
      tts.setVolume(newVol);
    }
    if (newVol === 0) {
      setMuted(true);
    } else if (muted) {
      setMuted(false);
    }
  }, [tts, muted]);

  /* -- Keyboard shortcuts -- */
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") handleClose();
      if (e.key === " " && started) { e.preventDefault(); togglePlayPause(); }
      if (e.key === "ArrowRight" && started) skipNext();
      if (e.key === "ArrowLeft" && started) skipPrev();
      if (e.key === "m" && started) toggleMute();
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [handleClose, togglePlayPause, skipNext, skipPrev, toggleMute, started]);

  /* -- Cleanup -- */
  useEffect(() => {
    return () => {
      tts.stop();
      if (timerRef.current) clearTimeout(timerRef.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const scene = SCENES[currentScene];
  const isLastScene = currentScene === SCENES.length - 1 && !playing;

  // Format time
  const formatTime = (ms: number) => {
    const totalSec = Math.floor(ms / 1000);
    const m = Math.floor(totalSec / 60);
    const s = totalSec % 60;
    return `${m}:${String(s).padStart(2, "0")}`;
  };
  const elapsedMs = (progress / 100) * totalDuration;

  /* =======================================================================
     RENDER: Start overlay
     ======================================================================= */
  if (!started) {
    return (
      <>
        <style dangerouslySetInnerHTML={{ __html: KEYFRAMES }} />
        <div className="fixed inset-0 z-50 flex items-center justify-center overflow-hidden bg-gradient-to-br from-slate-950 via-blue-950 to-slate-950">
          {/* Animated particles */}
          <div className="pointer-events-none absolute inset-0">
            {Array.from({ length: 30 }).map((_, i) => (
              <div
                key={i}
                className="absolute rounded-full bg-sky-400/20"
                style={{
                  width: 2 + Math.random() * 4,
                  height: 2 + Math.random() * 4,
                  left: `${Math.random() * 100}%`,
                  bottom: `-${Math.random() * 10}%`,
                  animation: `particleDrift ${8 + Math.random() * 12}s linear infinite`,
                  animationDelay: `${Math.random() * 10}s`,
                }}
              />
            ))}
          </div>

          <button
            onClick={handleClose}
            className="absolute right-6 top-6 z-10 rounded-full bg-white/10 p-2.5 text-white/60 backdrop-blur-sm transition hover:bg-white/20 hover:text-white"
            aria-label="Close demo"
          >
            <XIcon />
          </button>

          <div className="relative z-10 flex max-w-2xl flex-col items-center px-6 text-center">
            {/* Logo */}
            <div style={{ animation: "scaleIn 1s ease-out both" }} className="mb-8 flex items-center gap-4">
              <div className="relative flex h-20 w-20 items-center justify-center rounded-3xl bg-gradient-to-br from-sky-400 to-blue-600 shadow-2xl shadow-sky-500/30" style={{ animation: "pulseGlow 3s ease-in-out infinite" }}>
                <PulseIcon className="h-11 w-11 text-white" />
              </div>
              <div className="text-left">
                <h1 className="text-5xl font-bold tracking-tight text-white">MedAssist AI</h1>
                <p className="text-base font-medium text-sky-300/90">Intelligent Medical Assistant Platform</p>
              </div>
            </div>

            <p style={{ animation: "fadeInUp 0.8s ease-out 0.3s both" }} className="mb-8 max-w-lg text-lg leading-relaxed text-blue-200/70">
              Experience how seven specialized AI agents work in concert to elevate patient care through real-time monitoring, intelligent diagnostics, and clinical decision support.
            </p>

            {/* Voice & settings */}
            <div style={{ animation: "fadeInUp 0.8s ease-out 0.5s both" }} className="mb-8 flex flex-wrap items-center justify-center gap-3">
              <div className="flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 backdrop-blur-sm">
                <SpeakerIcon className="h-4 w-4 text-sky-300/70" />
                <span className="text-xs font-medium text-blue-200/60">Voice:</span>
                <button
                  onClick={() => setVoice("alloy")}
                  className={`rounded-lg px-3 py-1 text-xs font-semibold transition-all ${voice === "alloy" ? "bg-sky-500/30 text-sky-200 shadow-sm shadow-sky-500/20" : "text-blue-200/40 hover:text-blue-200/70"}`}
                >
                  Alloy
                </button>
                <button
                  onClick={() => setVoice("nova")}
                  className={`rounded-lg px-3 py-1 text-xs font-semibold transition-all ${voice === "nova" ? "bg-sky-500/30 text-sky-200 shadow-sm shadow-sky-500/20" : "text-blue-200/40 hover:text-blue-200/70"}`}
                >
                  Nova
                </button>
              </div>

              <label className="flex cursor-pointer items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 backdrop-blur-sm">
                <input type="checkbox" checked={narrationEnabled} onChange={(e) => setNarrationEnabled(e.target.checked)} className="h-3.5 w-3.5 rounded border-white/30 bg-white/10 text-sky-500 focus:ring-sky-500" />
                <span className="text-xs font-medium text-blue-200/60">AI Narration</span>
              </label>

              <label className="flex cursor-pointer items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 backdrop-blur-sm">
                <input type="checkbox" checked={autoAdvance} onChange={(e) => setAutoAdvance(e.target.checked)} className="h-3.5 w-3.5 rounded border-white/30 bg-white/10 text-sky-500 focus:ring-sky-500" />
                <span className="text-xs font-medium text-blue-200/60">Auto-advance</span>
              </label>
            </div>

            <button
              onClick={handleStart}
              disabled={isLoadingAudio}
              style={{ animation: "fadeInUp 0.8s ease-out 0.7s both" }}
              className="group relative inline-flex items-center gap-3 rounded-2xl bg-gradient-to-r from-sky-500 to-blue-600 px-12 py-4.5 text-lg font-bold text-white shadow-2xl shadow-sky-500/25 transition-all hover:scale-[1.03] hover:shadow-sky-500/40 active:scale-[0.98] disabled:opacity-80 disabled:cursor-wait disabled:hover:scale-100"
            >
              <div className="absolute -inset-1 rounded-2xl bg-gradient-to-r from-sky-400 to-blue-500 opacity-0 blur-lg transition-opacity group-hover:opacity-30" />
              {isLoadingAudio ? (
                <>
                  <div className="relative h-6 w-6 animate-spin rounded-full border-2 border-white/30 border-t-white" />
                  <span className="relative">Loading Voice...</span>
                </>
              ) : (
                <>
                  <PlayTriangleIcon className="relative h-6 w-6" />
                  <span className="relative">Begin Product Demo</span>
                </>
              )}
            </button>

            <p style={{ animation: "fadeIn 1s ease-out 1s both" }} className="mt-8 text-sm text-blue-300/40">
              ~3.5 minutes &middot; AI voice narration &middot; Space to pause &middot; Arrow keys to navigate &middot; ESC to exit
            </p>
          </div>

          {/* Background glow orbs */}
          <div className="pointer-events-none absolute inset-0 overflow-hidden">
            <div className="absolute -left-40 -top-40 h-[500px] w-[500px] rounded-full bg-sky-500/8 blur-3xl" />
            <div className="absolute -bottom-40 -right-40 h-[500px] w-[500px] rounded-full bg-blue-600/8 blur-3xl" />
            <div className="absolute left-1/2 top-1/4 h-80 w-80 -translate-x-1/2 rounded-full bg-cyan-400/5 blur-3xl" />
          </div>
        </div>
      </>
    );
  }

  /* =======================================================================
     RENDER: Demo player
     ======================================================================= */
  return (
    <>
      <style dangerouslySetInnerHTML={{ __html: KEYFRAMES }} />
      <div className="fixed inset-0 z-50 flex flex-col bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
        {/* ---- Top progress bar ---- */}
        <div className="h-1 w-full bg-white/5">
          <div
            className="h-full bg-gradient-to-r from-sky-400 via-blue-500 to-purple-500 transition-all duration-200"
            style={{ width: `${progress}%` }}
          />
        </div>

        {/* ---- Main content area with crossfade ---- */}
        <div className="relative flex-1 overflow-hidden">
          <div
            className={`absolute inset-0 transition-all duration-500 ${
              transitioning ? "scale-[0.98] opacity-0 blur-sm" : "scale-100 opacity-100 blur-0"
            }`}
          >
            <div className="flex h-full flex-col">
              {/* Scene title overlay */}
              <div className="pointer-events-none absolute left-0 right-0 top-0 z-10 flex flex-col items-center pt-4 md:pt-6">
                <h2 className="text-lg font-bold tracking-wide text-white/90 md:text-xl">{scene?.title}</h2>
                {scene?.subtitle && (
                  <p className="mt-0.5 text-xs font-medium tracking-widest text-sky-400/70 uppercase">{scene.subtitle}</p>
                )}
              </div>

              {/* Scene content */}
              <div className="flex-1 overflow-hidden px-4 pt-16 pb-2 md:px-8 md:pt-20">
                {scene && (
                  <SceneRenderer
                    sceneId={scene.id}
                    animatedVitals={animatedVitals}
                  />
                )}
              </div>
            </div>
          </div>
        </div>

        {/* ---- Narration bar with waveform / loading / error / subtitles ---- */}
        <div className="border-t border-white/[0.06] bg-black/40 backdrop-blur-sm px-4 py-2.5 md:px-8">
          <div className="mx-auto flex max-w-4xl items-start gap-3">
            {/* Voice status indicator */}
            <div className="mt-1 flex items-end gap-[3px]" aria-hidden>
              {tts.isLoading ? (
                /* Loading spinner */
                <div className="flex items-center gap-1">
                  <div className="h-4 w-4 animate-spin rounded-full border-2 border-sky-400/30 border-t-sky-400" />
                </div>
              ) : tts.hasError ? (
                /* Error indicator */
                <div className="flex items-center gap-1" title="Voice narration unavailable">
                  <svg className="h-4 w-4 text-red-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <circle cx="12" cy="12" r="10" />
                    <line x1="15" y1="9" x2="9" y2="15" />
                    <line x1="9" y1="9" x2="15" y2="15" />
                  </svg>
                </div>
              ) : (
                /* Waveform bars */
                [1, 2, 3, 1, 2].map((variant, i) => (
                  <div
                    key={i}
                    className={`w-[3px] rounded-full transition-colors ${tts.isSpeaking && !muted ? "bg-sky-400" : "bg-white/20"}`}
                    style={{
                      height: tts.isSpeaking && !muted ? undefined : "6px",
                      animation: tts.isSpeaking && !muted ? `waveform${variant} 0.${4 + i}s ease-in-out infinite` : "none",
                    }}
                  />
                ))
              )}
            </div>
            {/* Status label + narration text (subtitles) */}
            <div className="min-h-[2.5rem] flex-1 text-center">
              {tts.isLoading && (
                <p className="mb-0.5 text-[11px] font-medium text-sky-400/80 animate-pulse">Loading voice...</p>
              )}
              {tts.hasError && (
                <p className="mb-0.5 text-[11px] font-medium text-red-400/80">Voice unavailable -- reading subtitles</p>
              )}
              <p className="text-[13px] leading-relaxed text-blue-100/70 md:text-sm">
                {scene?.narration}
              </p>
            </div>
          </div>
        </div>

        {/* ---- Scene progress (thin) ---- */}
        <div className="h-0.5 w-full bg-white/5">
          <div className="h-full bg-sky-500/40 transition-all duration-200" style={{ width: `${sceneProgress}%` }} />
        </div>

        {/* ---- Player controls bar ---- */}
        <div className="flex items-center justify-between border-t border-white/[0.06] bg-black/60 backdrop-blur-md px-3 py-2 md:px-6">
          {/* Left: scene info */}
          <div className="flex items-center gap-3">
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-gradient-to-br from-sky-400 to-blue-600">
              <PulseIcon className="h-4 w-4 text-white" />
            </div>
            <div className="hidden md:block">
              <p className="text-xs font-semibold text-white/80">Scene {currentScene + 1} / {SCENES.length}</p>
              <p className="text-[10px] text-blue-200/40">{formatTime(elapsedMs)} / {formatTime(totalDuration)}</p>
            </div>
          </div>

          {/* Center: transport controls */}
          <div className="flex items-center gap-2">
            <button onClick={skipPrev} disabled={currentScene === 0} className="rounded-lg p-2 text-white/60 transition hover:bg-white/10 hover:text-white disabled:opacity-30 disabled:pointer-events-none" aria-label="Previous scene">
              <SkipBackIcon />
            </button>
            <button onClick={togglePlayPause} className="flex h-10 w-10 items-center justify-center rounded-full bg-white/10 text-white transition hover:bg-white/20 active:scale-95" aria-label={isPaused ? "Play" : "Pause"}>
              {isPaused ? <PlayTriangleIcon className="h-5 w-5 ml-0.5" /> : <PauseIcon />}
            </button>
            <button onClick={skipNext} disabled={currentScene >= SCENES.length - 1} className="rounded-lg p-2 text-white/60 transition hover:bg-white/10 hover:text-white disabled:opacity-30 disabled:pointer-events-none" aria-label="Next scene">
              <SkipForwardIcon />
            </button>
          </div>

          {/* Right: extra controls */}
          <div className="flex items-center gap-1.5">
            {/* Scene dots (clickable) */}
            <div className="hidden items-center gap-1 mr-2 md:flex">
              {SCENES.map((s, i) => (
                <button
                  key={s.id}
                  onClick={() => goToScene(i)}
                  className={`group relative h-2 rounded-full transition-all ${
                    i === currentScene ? "w-5 bg-sky-400" : i < currentScene ? "w-2 bg-sky-500/40 hover:bg-sky-500/60" : "w-2 bg-white/15 hover:bg-white/30"
                  }`}
                  aria-label={`Go to ${s.title}`}
                >
                  <span className="pointer-events-none absolute -top-7 left-1/2 -translate-x-1/2 whitespace-nowrap rounded bg-slate-800 px-2 py-0.5 text-[10px] text-white opacity-0 shadow-lg transition group-hover:opacity-100">{s.title}</span>
                </button>
              ))}
            </div>

            {/* Volume control with slider */}
            <div className="flex items-center gap-1.5 group">
              <button onClick={toggleMute} className={`rounded-lg p-2 transition hover:bg-white/10 ${muted ? "text-red-400/70" : "text-white/50 hover:text-white/80"}`} aria-label={muted ? "Unmute" : "Mute"}>
                {muted || volume === 0 ? <MuteIcon /> : <SpeakerIcon className="h-4 w-4" />}
              </button>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={muted ? 0 : volume}
                onChange={(e) => handleVolumeChange(parseFloat(e.target.value))}
                className="hidden h-1 w-16 cursor-pointer appearance-none rounded-full bg-white/20 accent-sky-400 md:block [&::-webkit-slider-thumb]:h-3 [&::-webkit-slider-thumb]:w-3 [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-sky-400"
                aria-label="Volume"
              />
            </div>

            {/* Voice selector */}
            <div className="hidden items-center gap-0.5 rounded-lg bg-white/5 p-0.5 md:flex">
              <button onClick={() => setVoice("alloy")} className={`rounded-md px-2 py-1 text-[10px] font-semibold transition ${voice === "alloy" ? "bg-sky-500/30 text-sky-200" : "text-white/30 hover:text-white/60"}`}>Alloy</button>
              <button onClick={() => setVoice("nova")} className={`rounded-md px-2 py-1 text-[10px] font-semibold transition ${voice === "nova" ? "bg-sky-500/30 text-sky-200" : "text-white/30 hover:text-white/60"}`}>Nova</button>
            </div>

            {/* Exit */}
            <button onClick={handleClose} className="rounded-lg p-2 text-white/40 transition hover:bg-white/10 hover:text-white/80" aria-label="Exit demo">
              <XIcon />
            </button>
          </div>
        </div>

        {/* ---- End screen overlay ---- */}
        {isLastScene && (
          <div className="absolute inset-0 z-20 flex items-center justify-center bg-slate-950/85 backdrop-blur-md">
            <div className="flex flex-col items-center gap-6 text-center" style={{ animation: "scaleIn 0.6s ease-out both" }}>
              <div className="relative flex h-24 w-24 items-center justify-center rounded-3xl bg-gradient-to-br from-sky-400 to-blue-600 shadow-2xl shadow-sky-500/30" style={{ animation: "pulseGlow 3s ease-in-out infinite" }}>
                <PulseIcon className="h-14 w-14 text-white" />
              </div>
              <h2 className="text-4xl font-bold tracking-tight text-white">Thank You for Watching</h2>
              <p className="max-w-md text-lg text-blue-200/60">Ready to transform care delivery at your organization?</p>
              <div className="flex gap-4">
                <button onClick={() => { setCurrentScene(0); setProgress(0); setPlaying(true); setIsPaused(false); }} className="rounded-xl border border-white/10 bg-white/5 px-8 py-3.5 font-semibold text-white backdrop-blur-sm transition hover:bg-white/10">Replay Demo</button>
                <button onClick={handleClose} className="rounded-xl bg-gradient-to-r from-sky-500 to-blue-600 px-8 py-3.5 font-semibold text-white shadow-xl shadow-sky-500/25 transition hover:scale-[1.03]">Get Started</button>
              </div>
              <p className="mt-2 text-sm text-blue-300/40">hello@medassist.ai &middot; +1 (888) 555-0199</p>
            </div>
          </div>
        )}
      </div>
    </>
  );
}

/* ==========================================================================
   SCENE RENDERER
   ========================================================================== */

interface SceneRendererProps {
  sceneId: string;
  animatedVitals: ReturnType<typeof generateVitalsData>;
}

function SceneRenderer({ sceneId, animatedVitals }: SceneRendererProps) {
  const t = useSceneTimer(sceneId);

  switch (sceneId) {
    case "intro":
      return <IntroScene t={t} />;
    case "patient-portal":
      return <PatientPortalScene t={t} />;
    case "symptom-analysis":
      return <SymptomAnalysisScene t={t} />;
    case "vitals-monitoring":
      return <VitalsMonitoringScene vitals={animatedVitals} t={t} />;
    case "report-analysis":
      return <ReportAnalysisScene t={t} />;
    case "drug-interaction":
      return <DrugInteractionScene t={t} />;
    case "doctor-dashboard":
      return <DoctorDashboardScene t={t} />;
    case "telemedicine":
      return <TelemedicineScene t={t} />;
    case "admin-compliance":
      return <AdminComplianceScene t={t} />;
    case "ai-agents":
      return <AIAgentsScene t={t} />;
    case "closing":
      return <ClosingScene t={t} />;
    default:
      return null;
  }
}

/* ==========================================================================
   SCENE 1: INTRO -- Cinematic entrance with animated counters
   ========================================================================== */

function IntroScene({ t }: { t: number }) {
  const agents = useCountUp(7, 2000, 2.5, t);
  const patients = useCountUp(10000, 2500, 3.0, t);
  const uptime = useCountUp(999, 2000, 3.5, t);

  return (
    <div className="flex h-full flex-col items-center justify-center gap-6">
      {/* Animated particles background */}
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        {Array.from({ length: 20 }).map((_, i) => (
          <div
            key={i}
            className="absolute rounded-full bg-sky-400/10"
            style={{
              width: 2 + Math.random() * 3,
              height: 2 + Math.random() * 3,
              left: `${Math.random() * 100}%`,
              bottom: `-5%`,
              animation: `particleDrift ${10 + Math.random() * 15}s linear infinite`,
              animationDelay: `${Math.random() * 8}s`,
            }}
          />
        ))}
      </div>

      {/* Logo */}
      <div style={anim(t, 0.3, "scaleIn", "1s")} className="flex items-center gap-5">
        <div
          className="relative flex h-28 w-28 items-center justify-center rounded-3xl bg-gradient-to-br from-sky-400 to-blue-600 shadow-2xl shadow-sky-500/30"
          style={{ animation: t > 1 ? "pulseGlow 3s ease-in-out infinite" : "none" }}
        >
          <PulseIcon className="h-16 w-16 text-white" />
          {/* Ripple */}
          {t > 1.5 && (
            <div className="absolute inset-0 rounded-3xl border-2 border-sky-400/30" style={{ animation: "ripple 2s ease-out infinite" }} />
          )}
        </div>
        <div>
          <h1 className="text-5xl font-bold tracking-tight text-white md:text-7xl">MedAssist AI</h1>
          <p className="mt-1 text-lg font-medium text-sky-300/80 md:text-xl">Intelligent Medical Assistant Platform</p>
        </div>
      </div>

      {/* Stats counters */}
      <div style={anim(t, 2.0, "fadeInUp", "0.8s")} className="mt-4 grid grid-cols-2 gap-4 md:grid-cols-4">
        {[
          { label: "Patients Served", value: patients > 0 ? `${(patients / 1000).toFixed(1)}K+` : "0" },
          { label: "Specialized AI Agents", value: String(agents) },
          { label: "System Uptime", value: uptime > 0 ? `${(uptime / 10).toFixed(1)}%` : "0%" },
          { label: "Regulatory Compliance", value: t > 4 ? "HIPAA" : "---" },
        ].map((stat, i) => (
          <div
            key={stat.label}
            className="flex flex-col items-center rounded-2xl border border-white/10 bg-white/[0.03] px-6 py-5 backdrop-blur-sm"
            style={anim(t, 2.5 + i * 0.3, "fadeInUp", "0.6s")}
          >
            <span className="text-3xl font-bold tabular-nums text-sky-400">{stat.value}</span>
            <span className="mt-1.5 text-center text-xs font-medium text-blue-200/50">{stat.label}</span>
          </div>
        ))}
      </div>

      {/* Tagline */}
      <p style={anim(t, 5, "fadeIn", "1s")} className="mt-4 max-w-2xl text-center text-base text-blue-200/40 md:text-lg">
        Engineered for hospitals, telemedicine providers, and health systems worldwide -- delivering measurable improvements in clinical outcomes, operational efficiency, and patient engagement.
      </p>
    </div>
  );
}

/* ==========================================================================
   SCENE 2: PATIENT PORTAL
   ========================================================================== */

function PatientPortalScene({ t }: { t: number }) {
  return (
    <div className="mx-auto h-full max-w-6xl space-y-3 overflow-y-auto pb-4">
      {/* Quick stat cards */}
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        {[
          { label: "Heart Rate", value: "72 bpm", trend: "+2", color: "text-red-400", icon: <HeartIcon /> },
          { label: "Blood Pressure", value: "120/78", trend: "-3", color: "text-blue-400", icon: <DropletIcon /> },
          { label: "SpO2", value: "98%", trend: "0", color: "text-cyan-400", icon: <WindIcon /> },
          { label: "Health Score", value: "87/100", trend: "+5", color: "text-green-400", icon: <ShieldIcon /> },
        ].map((card, i) => (
          <div key={card.label} style={anim(t, 1 + i * 0.4, "fadeInUp", "0.5s")} className="rounded-xl border border-white/10 bg-white/[0.03] p-3 backdrop-blur-sm">
            <div className="flex items-center justify-between">
              <span className="text-xs text-blue-200/60">{card.label}</span>
              <span className={card.color}>{card.icon}</span>
            </div>
            <p className="mt-1 text-xl font-bold text-white">{card.value}</p>
            <p className={`text-xs ${parseFloat(card.trend) > 0 ? "text-green-400" : parseFloat(card.trend) < 0 ? "text-red-400" : "text-blue-200/50"}`}>
              {parseFloat(card.trend) > 0 ? "+" : ""}{card.trend} from last week
            </p>
          </div>
        ))}
      </div>

      <div className="grid gap-3 md:grid-cols-3">
        {/* Upcoming Appointments */}
        <div style={anim(t, 3, "slideInLeft", "0.6s")} className="rounded-xl border border-white/10 bg-white/[0.03] p-4 backdrop-blur-sm">
          <h3 className="mb-3 text-sm font-semibold text-white">Upcoming Appointments</h3>
          <div className="space-y-2">
            {[
              { dr: "Dr. Emily Carter", time: "Mar 22, 10:00 AM", type: "Follow-up", mode: "Telemedicine" },
              { dr: "Dr. M. Thompson", time: "Mar 28, 2:30 PM", type: "Cardiology", mode: "In-Person" },
            ].map((a, i) => (
              <div key={i} style={anim(t, 3.5 + i * 0.5, "fadeInUp", "0.4s")} className="rounded-lg bg-white/5 p-3">
                <p className="text-sm font-medium text-white">{a.dr}</p>
                <p className="text-xs text-blue-200/60">{a.time} &middot; {a.type}</p>
                <span className={`mt-1 inline-block rounded-full px-2 py-0.5 text-xs ${a.mode === "Telemedicine" ? "bg-sky-500/20 text-sky-300" : "bg-emerald-500/20 text-emerald-300"}`}>
                  {a.mode}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Medication Reminders */}
        <div style={anim(t, 3.5, "fadeInUp", "0.6s")} className="rounded-xl border border-white/10 bg-white/[0.03] p-4 backdrop-blur-sm">
          <h3 className="mb-3 text-sm font-semibold text-white">Active Medications</h3>
          <div className="space-y-2">
            {MEDICATIONS.map((m, i) => (
              <div key={i} style={anim(t, 4 + i * 0.35, "fadeInUp", "0.4s")} className="flex items-center justify-between rounded-lg bg-white/5 p-3">
                <div>
                  <p className="text-sm font-medium text-white">{m.name}</p>
                  <p className="text-xs text-blue-200/60">{m.dosage} &middot; {m.frequency}</p>
                </div>
                <span className="rounded-full bg-green-500/20 px-2 py-0.5 text-xs text-green-300">{m.status}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Vitals Mini Chart */}
        <div style={anim(t, 4, "slideInRight", "0.6s")} className="rounded-xl border border-white/10 bg-white/[0.03] p-4 backdrop-blur-sm">
          <h3 className="mb-3 text-sm font-semibold text-white">Heart Rate -- Last 24h</h3>
          <ResponsiveContainer width="100%" height={180}>
            <AreaChart data={VITALS_DATA}>
              <defs>
                <linearGradient id="hrGradP" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#EF4444" stopOpacity={0.3} />
                  <stop offset="100%" stopColor="#EF4444" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
              <XAxis dataKey="time" tick={{ fontSize: 9, fill: "rgba(255,255,255,0.3)" }} />
              <YAxis domain={[55, 95]} tick={{ fontSize: 9, fill: "rgba(255,255,255,0.3)" }} />
              <Area type="monotone" dataKey="heartRate" stroke="#EF4444" fill="url(#hrGradP)" strokeWidth={2} dot={false} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}

/* ==========================================================================
   SCENE 3: SYMPTOM ANALYSIS
   ========================================================================== */

function SymptomAnalysisScene({ t }: { t: number }) {
  const visibleMessages = Math.min(Math.floor(t / 2.5) + 1, CHAT_MESSAGES.length);
  const showDiagnosis = t > 10;
  const showRecommendation = t > 14;

  return (
    <div className="mx-auto grid h-full max-w-6xl gap-4 overflow-y-auto pb-4 md:grid-cols-2">
      {/* Chat */}
      <div style={anim(t, 0.5, "slideInLeft", "0.6s")} className="rounded-xl border border-white/10 bg-white/[0.03] p-4 backdrop-blur-sm">
        <div className="mb-3 flex items-center gap-2">
          <div className="h-2 w-2 animate-pulse rounded-full bg-green-400" />
          <h3 className="text-sm font-semibold text-white">AI Symptom Analyst</h3>
          <span className="rounded-full bg-sky-500/15 px-2 py-0.5 text-[10px] text-sky-300">GPT-4o</span>
        </div>
        <div className="space-y-3">
          {CHAT_MESSAGES.slice(0, visibleMessages).map((msg, i) => (
            <div key={i} style={anim(t, 0.5 + i * 2.5, "fadeInUp", "0.5s")} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
              <div className={`max-w-[85%] rounded-2xl px-4 py-2.5 text-sm ${msg.role === "user" ? "bg-sky-600/80 text-white" : "bg-white/10 text-blue-100/90"}`}>
                {msg.text}
              </div>
            </div>
          ))}
          {/* Typing indicator */}
          {visibleMessages < CHAT_MESSAGES.length && (
            <div className="flex justify-start">
              <div className="flex gap-1 rounded-2xl bg-white/10 px-4 py-3">
                <div className="h-2 w-2 animate-bounce rounded-full bg-sky-400/60" style={{ animationDelay: "0ms" }} />
                <div className="h-2 w-2 animate-bounce rounded-full bg-sky-400/60" style={{ animationDelay: "150ms" }} />
                <div className="h-2 w-2 animate-bounce rounded-full bg-sky-400/60" style={{ animationDelay: "300ms" }} />
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Diagnosis Results */}
      <div className="space-y-4">
        <div style={anim(t, 10, "slideInRight", "0.6s")} className={`rounded-xl border border-white/10 bg-white/[0.03] p-4 backdrop-blur-sm transition-opacity duration-500 ${showDiagnosis ? "opacity-100" : "opacity-0"}`}>
          <h3 className="mb-3 text-sm font-semibold text-white">Differential Diagnosis</h3>
          <div className="space-y-2.5">
            {DIFFERENTIAL_DIAGNOSES.map((d, i) => (
              <div key={i} style={anim(t, 10.5 + i * 0.6, "fadeInUp", "0.5s")} className="rounded-lg bg-white/5 p-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-white">{d.condition}</span>
                  <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${d.urgency === "Medium" ? "bg-amber-500/20 text-amber-300" : "bg-green-500/20 text-green-300"}`}>{d.urgency}</span>
                </div>
                <div className="mt-2">
                  <div className="h-2 w-full rounded-full bg-white/10 overflow-hidden">
                    <div
                      className="h-2 rounded-full bg-gradient-to-r from-sky-400 to-blue-500 transition-all duration-1000"
                      style={{ width: t > 11 + i * 0.6 ? `${d.confidence * 100}%` : "0%" }}
                    />
                  </div>
                  <p className="mt-1 text-xs text-blue-200/60">Confidence: {(d.confidence * 100).toFixed(0)}%</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div style={anim(t, 14, "fadeInUp", "0.6s")} className={`rounded-xl border border-amber-500/30 bg-amber-500/10 p-4 transition-opacity duration-500 ${showRecommendation ? "opacity-100" : "opacity-0"}`}>
          <p className="text-sm font-medium text-amber-300">Recommended Action</p>
          <p className="mt-1 text-sm text-amber-200/80">
            Schedule a follow-up with your primary care physician within 7 days. Monitor blood pressure daily. Seek immediate attention if headache becomes severe or vision changes occur.
          </p>
        </div>
      </div>
    </div>
  );
}

/* ==========================================================================
   SCENE 4: VITALS MONITORING
   ========================================================================== */

function VitalsMonitoringScene({ vitals, t }: { vitals: ReturnType<typeof generateVitalsData>; t: number }) {
  const showAlert = t > 8;

  return (
    <div className="mx-auto h-full max-w-6xl space-y-3 overflow-y-auto pb-4">
      {/* Alert notification */}
      {showAlert && (
        <div style={anim(t, 8, "slideInDown", "0.5s")} className="rounded-xl border border-red-500/40 bg-red-500/15 p-3 backdrop-blur-sm">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-red-500/30">
              <AlertTriangleIcon className="h-5 w-5 text-red-400" />
            </div>
            <div className="flex-1">
              <p className="text-sm font-semibold text-red-300">CRITICAL ALERT -- Room ICU-204</p>
              <p className="text-xs text-red-200/70">SpO2 dropped to 91% for patient James Wilson. NEWS2 score: 8. Auto-escalating to attending physician.</p>
            </div>
            <button className="shrink-0 rounded-lg bg-red-500/30 px-3 py-1.5 text-xs font-medium text-red-200 transition hover:bg-red-500/40">Acknowledge</button>
          </div>
        </div>
      )}

      {/* Vitals grid */}
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        {[
          { label: "Heart Rate", value: Math.round(vitals[vitals.length - 1]?.heartRate ?? 72), unit: "bpm", color: "#EF4444", min: 40, max: 120, normal: [60, 100] as [number, number] },
          { label: "SpO2", value: +(vitals[vitals.length - 1]?.spo2 ?? 97.5).toFixed(1), unit: "%", color: "#06B6D4", min: 80, max: 100, normal: [95, 100] as [number, number] },
          { label: "Temperature", value: +(vitals[vitals.length - 1]?.temperature ?? 36.7).toFixed(1), unit: "\u00B0C", color: "#F97316", min: 35, max: 40, normal: [36.1, 37.2] as [number, number] },
          { label: "Respiratory", value: Math.round(vitals[vitals.length - 1]?.respiratory ?? 16), unit: "/min", color: "#22C55E", min: 8, max: 30, normal: [12, 20] as [number, number] },
        ].map((v, i) => (
          <div key={v.label} style={anim(t, 1 + i * 0.3, "scaleIn", "0.5s")} className="rounded-xl border border-white/10 bg-white/[0.03] p-3 text-center backdrop-blur-sm">
            <p className="text-xs text-blue-200/60">{v.label}</p>
            <p className="mt-1 text-2xl font-bold tabular-nums" style={{ color: v.color }}>{v.value}</p>
            <p className="text-xs text-blue-200/50">{v.unit}</p>
            <div className="mx-auto mt-2 h-1.5 w-full max-w-[100px] overflow-hidden rounded-full bg-white/10">
              <div className="h-full rounded-full transition-all duration-500" style={{
                width: `${((v.value as number - (v.min ?? 0)) / ((v.max ?? 100) - (v.min ?? 0))) * 100}%`,
                backgroundColor: v.normal && ((v.value as number) < v.normal[0] || (v.value as number) > v.normal[1]) ? "#F97316" : v.color,
              }} />
            </div>
          </div>
        ))}
      </div>

      {/* Live charts */}
      <div className="grid gap-3 md:grid-cols-2">
        <div style={anim(t, 3, "slideInLeft", "0.6s")} className="rounded-xl border border-white/10 bg-white/[0.03] p-4 backdrop-blur-sm">
          <h3 className="mb-2 text-sm font-semibold text-white">Heart Rate (Live)</h3>
          <ResponsiveContainer width="100%" height={140}>
            <LineChart data={vitals}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
              <XAxis dataKey="time" tick={{ fontSize: 8, fill: "rgba(255,255,255,0.25)" }} />
              <YAxis domain={[55, 95]} tick={{ fontSize: 8, fill: "rgba(255,255,255,0.25)" }} />
              <ReferenceLine y={100} stroke="rgba(239,68,68,0.3)" strokeDasharray="3 3" />
              <ReferenceLine y={60} stroke="rgba(239,68,68,0.3)" strokeDasharray="3 3" />
              <Line type="monotone" dataKey="heartRate" stroke="#EF4444" strokeWidth={2} dot={false} isAnimationActive={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
        <div style={anim(t, 3.5, "slideInRight", "0.6s")} className="rounded-xl border border-white/10 bg-white/[0.03] p-4 backdrop-blur-sm">
          <h3 className="mb-2 text-sm font-semibold text-white">Oxygen Saturation (Live)</h3>
          <ResponsiveContainer width="100%" height={140}>
            <AreaChart data={vitals}>
              <defs>
                <linearGradient id="spo2GradV" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#06B6D4" stopOpacity={0.3} />
                  <stop offset="100%" stopColor="#06B6D4" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
              <XAxis dataKey="time" tick={{ fontSize: 8, fill: "rgba(255,255,255,0.25)" }} />
              <YAxis domain={[92, 100]} tick={{ fontSize: 8, fill: "rgba(255,255,255,0.25)" }} />
              <ReferenceLine y={95} stroke="rgba(239,68,68,0.3)" strokeDasharray="3 3" />
              <Area type="monotone" dataKey="spo2" stroke="#06B6D4" fill="url(#spo2GradV)" strokeWidth={2} dot={false} isAnimationActive={false} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* NEWS2 Score */}
      <div style={anim(t, 5, "fadeInUp", "0.6s")} className="flex items-center gap-4 rounded-xl border border-white/10 bg-white/[0.03] p-4 backdrop-blur-sm">
        <div className="text-center">
          <p className="text-xs text-blue-200/60">NEWS2 Score</p>
          <p className="text-3xl font-bold text-amber-400">5</p>
        </div>
        <div className="h-12 w-px bg-white/10" />
        <div>
          <p className="text-sm font-medium text-amber-300">Medium Clinical Risk</p>
          <p className="text-xs text-blue-200/60">Increased monitoring frequency recommended. Urgent clinical review by ward-based physician.</p>
        </div>
      </div>
    </div>
  );
}

/* ==========================================================================
   SCENE 5: REPORT ANALYSIS
   ========================================================================== */

function ReportAnalysisScene({ t }: { t: number }) {
  const visibleRows = Math.min(Math.floor((t - 1.5) / 0.8), LAB_RESULTS.length);

  return (
    <div className="mx-auto grid h-full max-w-6xl gap-4 overflow-y-auto pb-4 md:grid-cols-5">
      {/* Lab Values Table */}
      <div style={anim(t, 0.5, "slideInLeft", "0.6s")} className="rounded-xl border border-white/10 bg-white/[0.03] p-4 backdrop-blur-sm md:col-span-3">
        <h3 className="mb-3 text-sm font-semibold text-white">Lab Results -- Complete Blood Panel</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-white/10 text-left text-xs text-blue-200/60">
                <th className="pb-2 pr-4">Test</th>
                <th className="pb-2 pr-4">Value</th>
                <th className="pb-2 pr-4">Unit</th>
                <th className="pb-2 pr-4">Reference</th>
                <th className="pb-2">Status</th>
              </tr>
            </thead>
            <tbody>
              {LAB_RESULTS.slice(0, Math.max(0, visibleRows)).map((lab, i) => (
                <tr key={i} className="border-b border-white/5" style={anim(t, 1.5 + i * 0.8, "fadeInUp", "0.4s")}>
                  <td className="py-2 pr-4 text-white">{lab.test}</td>
                  <td className={`py-2 pr-4 font-mono font-medium ${lab.status === "normal" ? "text-green-400" : lab.status === "high" ? "text-red-400" : "text-amber-400"}`}>
                    {lab.value}
                  </td>
                  <td className="py-2 pr-4 text-blue-200/60">{lab.unit}</td>
                  <td className="py-2 pr-4 text-blue-200/60">{lab.refMin} - {lab.refMax}</td>
                  <td className="py-2">
                    <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                      lab.status === "normal" ? "bg-green-500/20 text-green-300" : lab.status === "high" ? "bg-red-500/20 text-red-300" : "bg-amber-500/20 text-amber-300"
                    } ${lab.status !== "normal" ? "animate-pulse" : ""}`}>
                      {lab.status === "normal" ? "Normal" : lab.status === "high" ? "High" : "Low"}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* AI Summary */}
      <div className="space-y-4 md:col-span-2">
        <div style={anim(t, 8, "slideInRight", "0.6s")} className={`rounded-xl border border-sky-500/30 bg-sky-500/10 p-4 backdrop-blur-sm transition-opacity duration-700 ${t > 8 ? "opacity-100" : "opacity-0"}`}>
          <div className="mb-2 flex items-center gap-2">
            <SparklesIcon className="h-4 w-4 text-sky-400" />
            <h3 className="text-sm font-semibold text-sky-300">AI-Generated Summary</h3>
          </div>
          <p className="text-sm leading-relaxed text-sky-100/80">
            Analysis identified <strong className="text-white">4 values outside normal range</strong>.
            Elevated fasting glucose (142 mg/dL) and HbA1c (6.8%) indicate pre-diabetic to early diabetic range,
            warranting endocrinology consultation. Mildly elevated WBC may suggest infection or inflammation.
            TSH is slightly below reference, and total cholesterol is borderline elevated.
          </p>
        </div>

        <div style={anim(t, 12, "fadeInUp", "0.6s")} className={`rounded-xl border border-white/10 bg-white/[0.03] p-4 backdrop-blur-sm transition-opacity duration-700 ${t > 12 ? "opacity-100" : "opacity-0"}`}>
          <h3 className="mb-2 text-sm font-semibold text-white">Recommended Follow-up</h3>
          <ul className="space-y-1.5 text-sm text-blue-200/70">
            {["Repeat fasting glucose in 2 weeks", "Thyroid panel follow-up (Free T3, Free T4)", "LDL/HDL cholesterol breakdown", "Schedule endocrinology consultation"].map((item, i) => (
              <li key={i} style={anim(t, 12.5 + i * 0.5, "fadeInUp", "0.3s")} className="flex items-start gap-2">
                <span className={`mt-1 block h-1.5 w-1.5 rounded-full ${i < 2 ? "bg-amber-400" : "bg-sky-400"}`} />
                {item}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}

/* ==========================================================================
   SCENE 6: DRUG INTERACTION
   ========================================================================== */

function DrugInteractionScene({ t }: { t: number }) {
  return (
    <div className="mx-auto h-full max-w-5xl space-y-4 overflow-y-auto pb-4">
      {/* Current Medications */}
      <div style={anim(t, 0.5, "fadeInUp", "0.6s")} className="rounded-xl border border-white/10 bg-white/[0.03] p-4 backdrop-blur-sm">
        <h3 className="mb-3 text-sm font-semibold text-white">Active Medications</h3>
        <div className="grid gap-2 md:grid-cols-2">
          {MEDICATIONS.map((m, i) => (
            <div key={i} style={anim(t, 1 + i * 0.4, "fadeInUp", "0.4s")} className="flex items-center justify-between rounded-lg bg-white/5 p-3">
              <div>
                <p className="text-sm font-medium text-white">{m.name}</p>
                <p className="text-xs text-blue-200/60">{m.dosage} &middot; {m.frequency}</p>
              </div>
              <span className="rounded-full bg-green-500/20 px-2 py-0.5 text-xs text-green-300">{m.status}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Interactions */}
      <div className="space-y-3">
        {DRUG_INTERACTIONS.map((inter, i) => (
          <div
            key={i}
            style={anim(t, 5 + i * 1.5, "slideInLeft", "0.6s")}
            className={`rounded-xl border p-4 backdrop-blur-sm ${inter.severity === "Moderate" ? "border-amber-500/30 bg-amber-500/10" : "border-yellow-500/20 bg-yellow-500/5"}`}
          >
            <div className="flex items-center gap-3">
              <AlertTriangleIcon className={`h-5 w-5 shrink-0 ${inter.severity === "Moderate" ? "text-amber-400" : "text-yellow-400"}`} />
              <div>
                <p className="text-sm font-semibold text-white">
                  {inter.drug1} + {inter.drug2}
                  <span className={`ml-2 rounded-full px-2 py-0.5 text-xs ${inter.severity === "Moderate" ? "bg-amber-500/30 text-amber-300" : "bg-yellow-500/30 text-yellow-300"}`}>{inter.severity}</span>
                </p>
                <p className="mt-1 text-sm text-blue-200/70">{inter.effect}</p>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* AI Recommendation */}
      <div style={anim(t, 10, "fadeInUp", "0.7s")} className={`rounded-xl border border-sky-500/30 bg-sky-500/10 p-4 backdrop-blur-sm transition-opacity duration-700 ${t > 10 ? "opacity-100" : "opacity-0"}`}>
        <div className="flex items-center gap-2">
          <SparklesIcon className="h-4 w-4 text-sky-400" />
          <p className="text-sm font-medium text-sky-300">AI Recommendation</p>
        </div>
        <p className="mt-1 text-sm text-sky-100/80">
          Consider replacing Ibuprofen with Acetaminophen to eliminate the NSAID-ACE inhibitor interaction risk. Alternative: topical diclofenac for localized pain relief with significantly lower systemic interaction potential.
        </p>
      </div>
    </div>
  );
}

/* ==========================================================================
   SCENE 7: DOCTOR DASHBOARD
   ========================================================================== */

function DoctorDashboardScene({ t }: { t: number }) {
  return (
    <div className="mx-auto h-full max-w-6xl space-y-3 overflow-y-auto pb-4">
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {MONITORED_PATIENTS.map((p, i) => {
          const statusColor = p.status === "critical" ? "border-red-500/50 bg-red-500/10" : p.status === "warning" ? "border-amber-500/40 bg-amber-500/10" : "border-green-500/30 bg-green-500/5";
          const statusBadge = p.status === "critical" ? "bg-red-500/30 text-red-300" : p.status === "warning" ? "bg-amber-500/30 text-amber-300" : "bg-green-500/30 text-green-300";
          return (
            <div key={i} style={anim(t, 1 + i * 0.5, "scaleIn", "0.5s")} className={`rounded-xl border p-3 backdrop-blur-sm ${statusColor}`}>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-white">{p.name}</p>
                  <p className="text-xs text-blue-200/60">{p.room} &middot; Age {p.age}</p>
                </div>
                <span className={`rounded-full px-2 py-0.5 text-xs font-medium capitalize ${statusBadge}`}>{p.status}</span>
              </div>
              <div className="mt-2 grid grid-cols-4 gap-2 text-center">
                <div><p className="text-xs text-blue-200/50">HR</p><p className={`text-sm font-mono font-semibold ${p.hr > 100 ? "text-red-400" : "text-green-400"}`}>{p.hr}</p></div>
                <div><p className="text-xs text-blue-200/50">BP</p><p className="text-sm font-mono font-semibold text-blue-300">{p.bp}</p></div>
                <div><p className="text-xs text-blue-200/50">SpO2</p><p className={`text-sm font-mono font-semibold ${p.spo2 < 95 ? "text-amber-400" : "text-green-400"}`}>{p.spo2}%</p></div>
                <div><p className="text-xs text-blue-200/50">NEWS2</p><p className={`text-sm font-mono font-semibold ${p.news2 >= 7 ? "text-red-400" : p.news2 >= 5 ? "text-amber-400" : "text-green-400"}`}>{p.news2}</p></div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Alert feed */}
      <div style={anim(t, 5, "fadeInUp", "0.6s")} className="rounded-xl border border-white/10 bg-white/[0.03] p-4 backdrop-blur-sm">
        <h3 className="mb-3 text-sm font-semibold text-white">Active Alert Feed</h3>
        <div className="space-y-2">
          {[
            { time: "2 min ago", msg: "SpO2 dropped to 91% -- James Wilson (ICU-204)", sev: "critical" },
            { time: "18 min ago", msg: "HR elevated to 104 bpm -- Thomas Brown (ICU-201)", sev: "warning" },
            { time: "45 min ago", msg: "BP 148/92 -- Sarah Chen (CCU-112)", sev: "warning" },
          ].map((a, i) => (
            <div key={i} style={anim(t, 6 + i * 0.8, "slideInLeft", "0.4s")} className={`flex items-center justify-between rounded-lg p-3 ${a.sev === "critical" ? "bg-red-500/10" : "bg-amber-500/10"}`}>
              <div className="flex items-center gap-3">
                <div className={`h-2 w-2 rounded-full ${a.sev === "critical" ? "animate-pulse bg-red-400" : "bg-amber-400"}`} />
                <div><p className="text-sm text-white">{a.msg}</p><p className="text-xs text-blue-200/50">{a.time}</p></div>
              </div>
              <button className="shrink-0 rounded-lg bg-white/10 px-3 py-1 text-xs text-white transition hover:bg-white/20">Acknowledge</button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

/* ==========================================================================
   SCENE 8: TELEMEDICINE
   ========================================================================== */

function TelemedicineScene({ t }: { t: number }) {
  return (
    <div className="mx-auto h-full max-w-5xl overflow-y-auto pb-4">
      <div style={anim(t, 0.5, "scaleIn", "0.7s")} className="overflow-hidden rounded-xl border border-white/10">
        {/* Video grid */}
        <div className="grid grid-cols-3 gap-px bg-black/50">
          {/* Main video */}
          <div className="col-span-2 flex aspect-[16/10] flex-col items-center justify-center bg-gradient-to-br from-slate-800 to-slate-700 p-8 relative">
            <div style={anim(t, 1, "scaleIn", "0.5s")} className="flex h-20 w-20 items-center justify-center rounded-full bg-sky-600/30">
              <UserIcon className="h-10 w-10 text-sky-400" />
            </div>
            <p className="mt-3 text-sm font-medium text-white">Dr. Emily Carter</p>
            <p className="text-xs text-blue-200/60">Internal Medicine</p>
            <div className="mt-4 flex items-center gap-2">
              <div className="h-2 w-2 animate-pulse rounded-full bg-green-400" />
              <span className="text-xs text-green-300">HD Video Active</span>
            </div>
            {/* Duration badge */}
            {t > 3 && (
              <div style={anim(t, 3, "fadeIn", "0.5s")} className="absolute top-3 left-3 rounded-lg bg-black/50 px-2 py-1 text-xs text-white/60 backdrop-blur-sm">
                {Math.floor(t - 3)}:{String(Math.floor(((t - 3) % 1) * 60)).padStart(2, "0")}
              </div>
            )}
          </div>
          {/* Self view + AI sidebar */}
          <div className="flex flex-col gap-px">
            <div style={anim(t, 1.5, "fadeIn", "0.5s")} className="flex flex-1 flex-col items-center justify-center bg-gradient-to-br from-slate-700 to-slate-600 p-4">
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-emerald-600/30">
                <UserIcon className="h-6 w-6 text-emerald-400" />
              </div>
              <p className="mt-2 text-xs text-white">You</p>
            </div>
            <div style={anim(t, 3, "slideInRight", "0.6s")} className="flex-1 bg-slate-800 p-3">
              <div className="flex items-center gap-1.5">
                <SparklesIcon className="h-3 w-3 text-sky-400" />
                <p className="text-xs font-semibold text-sky-300">AI Assistant</p>
              </div>
              <p className="mt-1 text-xs text-blue-200/70">Live transcription active...</p>
              <div className="mt-2 space-y-1.5">
                <div style={anim(t, 5, "fadeIn", "0.5s")} className="rounded bg-white/5 p-2">
                  <p className="text-xs italic text-blue-200/50">&quot;...Your blood pressure readings have been improving since we adjusted the Lisinopril dosage...&quot;</p>
                </div>
                {t > 8 && (
                  <div style={anim(t, 8, "fadeIn", "0.5s")} className="rounded bg-white/5 p-2">
                    <p className="text-[10px] font-semibold text-sky-300/70">SOAP Notes</p>
                    <p className="text-xs italic text-blue-200/50">&quot;S: Patient reports improved energy. O: BP 120/78...&quot;</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
        {/* Call controls */}
        <div style={anim(t, 2, "fadeInUp", "0.5s")} className="flex items-center justify-center gap-3 bg-black/60 p-3">
          {["Mic", "Camera", "Share", "Notes", "Chat"].map((ctrl) => (
            <button key={ctrl} className="flex flex-col items-center gap-1 rounded-lg bg-white/10 px-4 py-2 text-xs text-white transition hover:bg-white/20">{ctrl}</button>
          ))}
          <button className="flex flex-col items-center gap-1 rounded-lg bg-red-600 px-4 py-2 text-xs text-white transition hover:bg-red-700">End Call</button>
        </div>
      </div>
    </div>
  );
}

/* ==========================================================================
   SCENE 9: ADMIN & COMPLIANCE
   ========================================================================== */

function AdminComplianceScene({ t }: { t: number }) {
  return (
    <div className="mx-auto h-full max-w-6xl space-y-3 overflow-y-auto pb-4">
      <div className="grid gap-3 md:grid-cols-2">
        {/* System Health */}
        <div style={anim(t, 0.5, "slideInLeft", "0.6s")} className="rounded-xl border border-white/10 bg-white/[0.03] p-4 backdrop-blur-sm">
          <h3 className="mb-3 text-sm font-semibold text-white">Infrastructure Health</h3>
          <div className="space-y-2">
            {SYSTEM_HEALTH.map((s, i) => (
              <div key={i} style={anim(t, 1 + i * 0.4, "fadeInUp", "0.3s")} className="flex items-center justify-between rounded-lg bg-white/5 p-2.5">
                <div className="flex items-center gap-2">
                  <div className="h-2 w-2 rounded-full bg-green-400" style={{ animation: t > 1.5 + i * 0.4 ? "pulseGlow 2s ease-in-out infinite" : "none" }} />
                  <span className="text-sm text-white">{s.service}</span>
                </div>
                <div className="flex items-center gap-4 text-xs text-blue-200/60">
                  <span>{s.uptime}</span>
                  <span>{s.latency}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Audit Log */}
        <div style={anim(t, 1, "slideInRight", "0.6s")} className="rounded-xl border border-white/10 bg-white/[0.03] p-4 backdrop-blur-sm">
          <h3 className="mb-3 text-sm font-semibold text-white">HIPAA Audit Log</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-white/10 text-left text-blue-200/50">
                  <th className="pb-2 pr-3">Time</th>
                  <th className="pb-2 pr-3">User</th>
                  <th className="pb-2 pr-3">Action</th>
                  <th className="pb-2">Status</th>
                </tr>
              </thead>
              <tbody>
                {AUDIT_LOG_ENTRIES.map((log, i) => (
                  <tr key={i} className="border-b border-white/5" style={anim(t, 2 + i * 0.6, "fadeInUp", "0.3s")}>
                    <td className="py-1.5 pr-3 font-mono text-blue-200/60">{log.time}</td>
                    <td className="py-1.5 pr-3 text-white">{log.user}</td>
                    <td className="py-1.5 pr-3 text-blue-200/70">{log.action}</td>
                    <td className="py-1.5">
                      <span className={`rounded-full px-2 py-0.5 text-xs ${log.status === "Success" ? "bg-green-500/20 text-green-300" : "bg-red-500/20 text-red-300"}`}>{log.status}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Compliance stats */}
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        {[
          { label: "Encryption", value: "AES-256", sub: "At rest and in transit" },
          { label: "Audit Retention", value: "6+ Years", sub: "HIPAA compliant" },
          { label: "Access Control", value: "RBAC", sub: "4 distinct privilege levels" },
          { label: "PHI De-identification", value: "Active", sub: "Applied before all AI calls" },
        ].map((stat, i) => (
          <div key={stat.label} style={anim(t, 7 + i * 0.4, "scaleIn", "0.5s")} className="rounded-xl border border-white/10 bg-white/[0.03] p-3 text-center backdrop-blur-sm">
            <p className="text-xs text-blue-200/60">{stat.label}</p>
            <p className="mt-1 text-lg font-bold text-sky-400">{stat.value}</p>
            <p className="text-xs text-blue-200/50">{stat.sub}</p>
          </div>
        ))}
      </div>

      {/* AI Usage pie chart */}
      <div style={anim(t, 10, "fadeInUp", "0.7s")} className={`rounded-xl border border-white/10 bg-white/[0.03] p-4 backdrop-blur-sm transition-opacity duration-700 ${t > 10 ? "opacity-100" : "opacity-0"}`}>
        <h3 className="mb-2 text-sm font-semibold text-white">AI Agent Usage Distribution</h3>
        <div className="flex items-center justify-center">
          <ResponsiveContainer width="100%" height={160}>
            <PieChart>
              <Pie data={PIE_DATA} cx="50%" cy="50%" innerRadius={40} outerRadius={70} dataKey="value" stroke="none">
                {PIE_DATA.map((entry, i) => (<Cell key={i} fill={entry.color} />))}
              </Pie>
              <Tooltip contentStyle={{ background: "rgba(15,23,42,0.9)", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 8, fontSize: 12 }} itemStyle={{ color: "white" }} />
            </PieChart>
          </ResponsiveContainer>
        </div>
        <div className="mt-2 flex flex-wrap justify-center gap-3">
          {PIE_DATA.map((entry, i) => (
            <div key={i} className="flex items-center gap-1.5 text-xs text-blue-200/60">
              <div className="h-2 w-2 rounded-full" style={{ backgroundColor: entry.color }} />
              {entry.name}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

/* ==========================================================================
   SCENE 10: AI AGENTS -- Circular layout with light-up effect
   ========================================================================== */

function AIAgentsScene({ t }: { t: number }) {
  // Each agent lights up at a different time
  const agentActiveTimes = [3, 5, 7, 9, 11, 13, 15];

  return (
    <div className="mx-auto h-full max-w-5xl space-y-5 overflow-y-auto pb-4">
      {/* Orchestrator */}
      <div style={anim(t, 0.5, "scaleIn", "0.7s")} className="flex flex-col items-center">
        <div className="rounded-2xl border border-sky-500/40 bg-gradient-to-br from-sky-500/20 to-blue-500/20 px-8 py-4 text-center backdrop-blur-sm" style={{ animation: t > 1 ? "pulseGlow 3s ease-in-out infinite" : "none" }}>
          <p className="text-sm font-bold text-sky-300">Agent Orchestrator</p>
          <p className="text-xs text-blue-200/60">GPT-4o with function calling</p>
          <p className="mt-1 text-xs text-blue-200/50">Central dispatcher routing tasks to specialist agents</p>
        </div>
        <div className="h-6 w-px bg-sky-500/30" />
        <div className="h-3 w-3 rounded-full border-2 border-sky-500/50" style={{ animation: t > 2 ? "pulseGlow 2s ease-in-out infinite" : "none" }} />
        <div className="h-4 w-px bg-sky-500/30" />
      </div>

      {/* Agent grid */}
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {AGENT_DATA.map((agent, i) => {
          const isActive = t > agentActiveTimes[i];
          return (
            <div
              key={i}
              style={anim(t, 2 + i * 0.4, "scaleIn", "0.5s")}
              className={`rounded-xl border p-4 backdrop-blur-sm transition-all duration-700 ${
                isActive ? "border-white/20 bg-white/[0.06]" : "border-white/[0.06] bg-white/[0.02]"
              }`}
            >
              <div className="mb-2 flex h-10 w-10 items-center justify-center rounded-lg transition-all duration-700" style={{ backgroundColor: isActive ? `${agent.color}30` : `${agent.color}10` }}>
                <div className="h-5 w-5 rounded-full transition-all duration-700" style={{
                  backgroundColor: agent.color,
                  opacity: isActive ? 1 : 0.3,
                  boxShadow: isActive ? `0 0 12px ${agent.color}60` : "none",
                }} />
              </div>
              <p className={`whitespace-pre-line text-sm font-semibold transition-colors duration-700 ${isActive ? "text-white" : "text-white/40"}`}>{agent.name}</p>
              <p className="mt-0.5 text-xs text-blue-200/50">{agent.model}</p>
              <p className={`mt-2 text-xs leading-relaxed transition-colors duration-700 ${isActive ? "text-blue-200/70" : "text-blue-200/30"}`}>{agent.description}</p>
            </div>
          );
        })}
      </div>

      {/* Shared memory */}
      <div style={anim(t, 16, "fadeInUp", "0.7s")} className={`rounded-xl border border-white/10 bg-white/[0.03] p-4 text-center backdrop-blur-sm transition-opacity duration-700 ${t > 16 ? "opacity-100" : "opacity-0"}`}>
        <p className="text-sm font-semibold text-white">Shared Context &amp; Memory Store</p>
        <p className="mt-1 text-xs text-blue-200/60">Redis (short-term context) + Pinecone (long-term medical knowledge embeddings)</p>
        <div className="mt-3 flex justify-center gap-6">
          <div className="text-center"><p className="text-2xl font-bold text-sky-400">3,072</p><p className="text-xs text-blue-200/50">Embedding dimensions</p></div>
          <div className="text-center"><p className="text-2xl font-bold text-purple-400">50K+</p><p className="text-xs text-blue-200/50">Medical knowledge vectors</p></div>
          <div className="text-center"><p className="text-2xl font-bold text-emerald-400">&lt;45ms</p><p className="text-xs text-blue-200/50">Retrieval latency</p></div>
        </div>
      </div>
    </div>
  );
}

/* ==========================================================================
   SCENE 11: CLOSING
   ========================================================================== */

function ClosingScene({ t }: { t: number }) {
  return (
    <div className="flex h-full flex-col items-center justify-center gap-6">
      {/* Particles */}
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        {Array.from({ length: 15 }).map((_, i) => (
          <div key={i} className="absolute rounded-full bg-sky-400/15" style={{ width: 3, height: 3, left: `${Math.random() * 100}%`, bottom: "-5%", animation: `particleDrift ${10 + Math.random() * 12}s linear infinite`, animationDelay: `${Math.random() * 6}s` }} />
        ))}
      </div>

      <div style={anim(t, 0.3, "scaleIn", "0.8s")} className="flex items-center gap-4">
        <div className="relative flex h-20 w-20 items-center justify-center rounded-3xl bg-gradient-to-br from-sky-400 to-blue-600 shadow-2xl shadow-sky-500/30" style={{ animation: t > 1 ? "pulseGlow 3s ease-in-out infinite" : "none" }}>
          <PulseIcon className="h-12 w-12 text-white" />
        </div>
        <h1 className="text-4xl font-bold tracking-tight text-white md:text-5xl">MedAssist AI</h1>
      </div>

      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        {[
          { value: "7", label: "Specialized AI Agents" },
          { value: "24/7", label: "Continuous Monitoring" },
          { value: "<2s", label: "Triage Response Time" },
          { value: "100%", label: "HIPAA Compliant" },
        ].map((stat, i) => (
          <div key={stat.label} style={anim(t, 2 + i * 0.4, "fadeInUp", "0.5s")} className="flex flex-col items-center rounded-2xl border border-white/10 bg-white/[0.03] px-6 py-5 backdrop-blur-sm">
            <span className="text-3xl font-bold text-sky-400">{stat.value}</span>
            <span className="mt-1 text-center text-sm text-blue-200/70">{stat.label}</span>
          </div>
        ))}
      </div>

      <p style={anim(t, 5, "fadeIn", "0.8s")} className="max-w-xl text-center text-lg text-blue-200/50">
        One unified platform engineered to transform care delivery at scale.<br />Experience the future of healthcare firsthand.
      </p>

      <div style={anim(t, 7, "fadeInUp", "0.6s")} className="flex flex-col items-center gap-4 sm:flex-row">
        <button className="rounded-xl bg-gradient-to-r from-sky-500 to-blue-600 px-10 py-3.5 text-lg font-bold text-white shadow-xl shadow-sky-500/25 transition-all hover:scale-[1.03] hover:shadow-sky-500/40">
          Schedule a Live Demo
        </button>
        <button className="rounded-xl border border-white/10 bg-white/5 px-8 py-3.5 text-lg font-semibold text-white/80 backdrop-blur-sm transition hover:bg-white/10">
          Contact Us
        </button>
      </div>

      <p style={anim(t, 9, "fadeIn", "0.8s")} className="text-sm text-blue-300/30">hello@medassist.ai &middot; +1 (888) 555-0199</p>
    </div>
  );
}

/* ==========================================================================
   SVG ICONS (inline, no external dependencies)
   ========================================================================== */

function PulseIcon({ className = "h-6 w-6" }: { className?: string }) {
  return (<svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M22 12h-4l-3 9L9 3l-3 9H2" /></svg>);
}

function XIcon() {
  return (<svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" /></svg>);
}

function PlayTriangleIcon({ className = "h-6 w-6" }: { className?: string }) {
  return (<svg className={className} viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z" /></svg>);
}

function PauseIcon() {
  return (<svg className="h-5 w-5" viewBox="0 0 24 24" fill="currentColor"><rect x="6" y="4" width="4" height="16" rx="1" /><rect x="14" y="4" width="4" height="16" rx="1" /></svg>);
}

function SkipBackIcon() {
  return (<svg className="h-4 w-4" viewBox="0 0 24 24" fill="currentColor"><path d="M19 20L9 12l10-8v16zM5 4h2v16H5V4z" /></svg>);
}

function SkipForwardIcon() {
  return (<svg className="h-4 w-4" viewBox="0 0 24 24" fill="currentColor"><path d="M5 4l10 8-10 8V4zm12 0h2v16h-2V4z" /></svg>);
}

function MuteIcon() {
  return (<svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" /><line x1="23" y1="9" x2="17" y2="15" /><line x1="17" y1="9" x2="23" y2="15" /></svg>);
}

function AlertTriangleIcon({ className = "h-5 w-5" }: { className?: string }) {
  return (<svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" /><line x1="12" y1="9" x2="12" y2="13" /><line x1="12" y1="17" x2="12.01" y2="17" /></svg>);
}

function SparklesIcon({ className = "h-4 w-4" }: { className?: string }) {
  return (<svg className={className} viewBox="0 0 24 24" fill="currentColor"><path d="M9.937 15.5A2 2 0 0 0 8.5 14.063l-6.135-1.582a.5.5 0 0 1 0-.962L8.5 9.936A2 2 0 0 0 9.937 8.5l1.582-6.135a.5.5 0 0 1 .963 0L14.063 8.5A2 2 0 0 0 15.5 9.937l6.135 1.581a.5.5 0 0 1 0 .964L15.5 14.063a2 2 0 0 0-1.437 1.437l-1.582 6.135a.5.5 0 0 1-.963 0z" /></svg>);
}

function SpeakerIcon({ className = "h-4 w-4" }: { className?: string }) {
  return (<svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" /><path d="M15.54 8.46a5 5 0 0 1 0 7.07" /><path d="M19.07 4.93a10 10 0 0 1 0 14.14" /></svg>);
}

function HeartIcon() {
  return (<svg className="h-4 w-4" viewBox="0 0 24 24" fill="currentColor"><path d="M20.84 4.61a5.5 5.5 0 00-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 00-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 000-7.78z" /></svg>);
}

function DropletIcon() {
  return (<svg className="h-4 w-4" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2.69l5.66 5.66a8 8 0 11-11.31 0z" /></svg>);
}

function WindIcon() {
  return (<svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M9.59 4.59A2 2 0 1111 8H2m10.59 11.41A2 2 0 1014 16H2m15.73-8.27A2.5 2.5 0 1119.5 12H2" /></svg>);
}

function ShieldIcon() {
  return (<svg className="h-4 w-4" viewBox="0 0 24 24" fill="currentColor"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" /></svg>);
}

function UserIcon({ className = "h-6 w-6" }: { className?: string }) {
  return (<svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2" /><circle cx="12" cy="7" r="4" /></svg>);
}
