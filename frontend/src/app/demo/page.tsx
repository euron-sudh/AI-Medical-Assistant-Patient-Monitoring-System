"use client";

import { useState, useEffect, useCallback, useRef, useMemo } from "react";
import { useRouter } from "next/navigation";
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
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

/* ─────────────────────────────────────────────
   TYPES
   ───────────────────────────────────────────── */

interface Scene {
  id: string;
  title: string;
  narration: string;
  durationMs: number;
}

/* ─────────────────────────────────────────────
   DEMO SCRIPT - 11 SCENES
   ───────────────────────────────────────────── */

const SCENES: Scene[] = [
  {
    id: "intro",
    title: "Welcome to MedAssist AI",
    narration:
      "Welcome to MedAssist AI, the intelligent medical assistant platform that transforms patient care with AI-powered monitoring, diagnosis support, and real-time clinical insights. Built for hospitals, telemedicine providers, and health startups, MedAssist AI brings the future of healthcare to your organization today.",
    durationMs: 16000,
  },
  {
    id: "patient-portal",
    title: "Patient Portal",
    narration:
      "Patients access their personalized health dashboard to track vitals, manage medications, view AI-analyzed medical reports, and communicate with their care team. All from one secure, HIPAA-compliant portal. Appointments, medication reminders, and real-time health scores keep patients engaged in their own care journey.",
    durationMs: 21000,
  },
  {
    id: "symptom-analysis",
    title: "AI Symptom Analysis",
    narration:
      "Our AI Symptom Analyst conducts intelligent multi-turn interviews, generating differential diagnoses with confidence scores and urgency assessments. It considers patient history, allergies, and medications for personalized analysis. The system uses GPT-4o with retrieval-augmented generation to ground every recommendation in verified medical literature.",
    durationMs: 22000,
  },
  {
    id: "vitals-monitoring",
    title: "Real-Time Vitals Monitoring",
    narration:
      "The Patient Monitoring Agent provides twenty-four seven real-time vitals surveillance. Adaptive baselines learn each patient's normal ranges. AI-powered anomaly detection triggers alerts thirty to sixty minutes before potential deterioration, with automatic escalation chains from nurse to attending physician to on-call specialist.",
    durationMs: 22000,
  },
  {
    id: "report-analysis",
    title: "Medical Report Analysis",
    narration:
      "Upload any medical report, whether lab results, imaging, or pathology, and our Report Reader Agent extracts values, identifies abnormalities, and generates both clinical summaries for doctors and plain-language explanations for patients. Trend analysis compares results across time for complete clinical context.",
    durationMs: 18000,
  },
  {
    id: "drug-interaction",
    title: "Drug Interaction Checking",
    narration:
      "Real-time drug interaction checking analyzes every prescription against the patient's full medication list, allergies, and conditions, flagging conflicts before they reach the patient. The system suggests safer alternatives and optimized dosing schedules automatically.",
    durationMs: 14000,
  },
  {
    id: "doctor-dashboard",
    title: "Doctor Dashboard",
    narration:
      "Doctors get a powerful command center with real-time monitoring walls, AI-assisted clinical notes, priority patient queues, and intelligent decision support. Every insight is evidence-based with source citations. Color-coded patient cards and alert feeds ensure critical situations are never missed.",
    durationMs: 21000,
  },
  {
    id: "telemedicine",
    title: "Telemedicine",
    narration:
      "Integrated telemedicine features HD video consultations, real-time transcription powered by OpenAI Whisper, and AI-generated SOAP notes after every consultation. Screen sharing enables collaborative report review during calls.",
    durationMs: 13000,
  },
  {
    id: "admin-compliance",
    title: "Admin & Compliance",
    narration:
      "Full HIPAA compliance is built in from the ground up. Encrypted data at rest and in transit, comprehensive audit logging, role-based access control, and automated compliance reporting give your compliance team complete peace of mind. Every access to protected health information is tracked and auditable.",
    durationMs: 18000,
  },
  {
    id: "ai-agents",
    title: "AI Agent Ecosystem",
    narration:
      "Seven specialized AI agents work together through our intelligent orchestrator. The Symptom Analyst, Report Reader, Triage, Voice, Drug Interaction, Monitoring, and Follow-Up agents deliver coordinated, context-aware care. Each agent has its own tools, memory, and decision-making capabilities, collaborating autonomously for optimal patient outcomes.",
    durationMs: 20000,
  },
  {
    id: "closing",
    title: "Transform Healthcare Today",
    narration:
      "MedAssist AI. Seven specialized AI agents. Twenty-four seven monitoring. Full HIPAA compliance. Transforming healthcare with intelligent, agentic AI. Ready to see it in action? Contact us for a live demo and discover how MedAssist AI can revolutionize care delivery at your organization.",
    durationMs: 16000,
  },
];

/* ─────────────────────────────────────────────
   SYNTHETIC DATA
   ───────────────────────────────────────────── */

function generateVitalsData(count: number, offset: number = 0) {
  return Array.from({ length: count }, (_, i) => {
    const t = i + offset;
    return {
      time: `${String(8 + Math.floor(t / 6)).padStart(2, "0")}:${String((t * 10) % 60).padStart(2, "0")}`,
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
  { role: "assistant" as const, text: "Hello! I'm your AI Symptom Analyst. What symptoms are you experiencing today?" },
  { role: "user" as const, text: "I've been having persistent headaches for the past 3 days, mostly on the right side. Also feeling a bit dizzy when I stand up." },
  { role: "assistant" as const, text: "I'd like to understand more about your headache. Can you describe the pain? Is it throbbing, sharp, or a dull pressure? And on a scale of 1-10, how severe is it?" },
  { role: "user" as const, text: "It's a throbbing pain, about 6 out of 10. Gets worse in the afternoon." },
  { role: "assistant" as const, text: "Thank you. Given your symptoms, history of mild hypertension, and current medications, I've completed my analysis. Here are the results:" },
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
  { drug1: "Lisinopril", drug2: "Ibuprofen", severity: "Moderate", effect: "NSAIDs may reduce antihypertensive effect and increase risk of renal impairment" },
  { drug1: "Metformin", drug2: "Ibuprofen", severity: "Mild", effect: "NSAIDs may rarely increase the risk of lactic acidosis with metformin" },
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
  { name: "Symptom\nAnalyst", model: "GPT-4o", color: "#0EA5E9", description: "Multi-turn symptom interviews & differential diagnosis" },
  { name: "Report\nReader", model: "GPT-4o Vision", color: "#8B5CF6", description: "Medical report parsing & abnormality detection" },
  { name: "Triage", model: "GPT-4o-mini", color: "#EF4444", description: "Emergency severity scoring & priority routing" },
  { name: "Voice", model: "Whisper + TTS", color: "#14B8A6", description: "Speech-to-text, transcription & voice interaction" },
  { name: "Drug\nInteraction", model: "GPT-4o-mini", color: "#F97316", description: "Medication conflict detection & alternatives" },
  { name: "Monitoring", model: "GPT-4o-mini", color: "#22C55E", description: "Vitals anomaly detection & early warning" },
  { name: "Follow-Up", model: "GPT-4o", color: "#EC4899", description: "Care plan generation & adherence tracking" },
];

const SYSTEM_HEALTH = [
  { service: "PostgreSQL 16", status: "Healthy", uptime: "99.99%", latency: "2ms" },
  { service: "Redis 7", status: "Healthy", uptime: "99.99%", latency: "<1ms" },
  { service: "InfluxDB", status: "Healthy", uptime: "99.97%", latency: "5ms" },
  { service: "OpenAI API", status: "Healthy", uptime: "99.95%", latency: "320ms" },
  { service: "Pinecone", status: "Healthy", uptime: "99.98%", latency: "45ms" },
  { service: "Celery Workers", status: "Healthy", uptime: "99.99%", latency: "—" },
];

const PIE_DATA = [
  { name: "Symptom Analysis", value: 35, color: "#0EA5E9" },
  { name: "Report Reading", value: 25, color: "#8B5CF6" },
  { name: "Triage", value: 15, color: "#EF4444" },
  { name: "Drug Checks", value: 12, color: "#F97316" },
  { name: "Monitoring", value: 8, color: "#22C55E" },
  { name: "Other", value: 5, color: "#94A3B8" },
];

/* ─────────────────────────────────────────────
   ANIMATED VITALS HOOK
   ───────────────────────────────────────────── */

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

/* ─────────────────────────────────────────────
   MAIN DEMO COMPONENT
   ───────────────────────────────────────────── */

export default function DemoPage() {
  const router = useRouter();
  const [started, setStarted] = useState(false);
  const [currentScene, setCurrentScene] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [caption, setCaption] = useState("");
  const [progress, setProgress] = useState(0);
  const [sceneProgress, setSceneProgress] = useState(0);
  const [transitioning, setTransitioning] = useState(false);
  const [showAlert, setShowAlert] = useState(false);

  const utteranceRef = useRef<SpeechSynthesisUtterance | null>(null);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const progressRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const sceneStartRef = useRef<number>(0);

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

  /* ── Speech synthesis helper ── */
  const speak = useCallback(
    (text: string, onEnd?: () => void) => {
      if (typeof window === "undefined") return;
      window.speechSynthesis.cancel();

      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 0.95;
      utterance.pitch = 1.0;
      utterance.volume = 1.0;

      // Try to pick a good English voice
      const voices = window.speechSynthesis.getVoices();
      const preferred = voices.find(
        (v) =>
          v.lang.startsWith("en") &&
          (v.name.includes("Female") ||
            v.name.includes("Samantha") ||
            v.name.includes("Google UK English Female") ||
            v.name.includes("Microsoft Zira") ||
            v.name.includes("Karen") ||
            v.name.includes("Moira") ||
            v.name.includes("Victoria"))
      );
      const fallback = voices.find((v) => v.lang.startsWith("en"));
      if (preferred) utterance.voice = preferred;
      else if (fallback) utterance.voice = fallback;

      utterance.onboundary = (event) => {
        if (event.name === "word") {
          const spoken = text.slice(0, event.charIndex + event.charLength);
          setCaption(spoken);
        }
      };

      utterance.onend = () => {
        setCaption(text);
        onEnd?.();
      };

      utteranceRef.current = utterance;
      window.speechSynthesis.speak(utterance);
    },
    []
  );

  /* ── Scene advancement ── */
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
      setTransitioning(false);
    }, 600);
  }, []);

  /* ── Play scene ── */
  const playScene = useCallback(
    (index: number) => {
      if (index >= SCENES.length) {
        setPlaying(false);
        return;
      }
      const scene = SCENES[index];
      setCaption("");
      setShowAlert(false);
      sceneStartRef.current = Date.now();

      speak(scene.narration, () => {
        // After narration ends, wait a beat then advance
        timerRef.current = setTimeout(() => {
          advanceScene();
        }, 1200);
      });

      // Show alert notification mid-scene for vitals monitoring
      if (scene.id === "vitals-monitoring") {
        setTimeout(() => setShowAlert(true), 8000);
      }
    },
    [speak, advanceScene]
  );

  /* ── Effect: play current scene when it changes ── */
  useEffect(() => {
    if (playing) {
      playScene(currentScene);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentScene, playing]);

  /* ── Global progress ticker ── */
  useEffect(() => {
    if (!playing) {
      if (progressRef.current) clearInterval(progressRef.current);
      return;
    }
    progressRef.current = setInterval(() => {
      const elapsed = cumulativeDurations[currentScene] + (Date.now() - sceneStartRef.current);
      setProgress(Math.min((elapsed / totalDuration) * 100, 100));
      const sceneDur = SCENES[currentScene]?.durationMs ?? 1;
      const sceneElapsed = Date.now() - sceneStartRef.current;
      setSceneProgress(Math.min((sceneElapsed / sceneDur) * 100, 100));
    }, 100);
    return () => {
      if (progressRef.current) clearInterval(progressRef.current);
    };
  }, [playing, currentScene, cumulativeDurations, totalDuration]);

  /* ── Controls ── */
  const handleStart = useCallback(() => {
    setStarted(true);
    setPlaying(true);
    setCurrentScene(0);
    setProgress(0);
    // Voices might not be loaded yet, warm them up
    window.speechSynthesis.getVoices();
  }, []);

  const togglePlayPause = useCallback(() => {
    if (playing) {
      window.speechSynthesis.pause();
      setPlaying(false);
      if (timerRef.current) clearTimeout(timerRef.current);
    } else {
      window.speechSynthesis.resume();
      setPlaying(true);
    }
  }, [playing]);

  const skipScene = useCallback(() => {
    window.speechSynthesis.cancel();
    if (timerRef.current) clearTimeout(timerRef.current);
    advanceScene();
  }, [advanceScene]);

  const handleClose = useCallback(() => {
    window.speechSynthesis.cancel();
    if (timerRef.current) clearTimeout(timerRef.current);
    router.push("/login");
  }, [router]);

  /* ── Keyboard shortcuts ── */
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") handleClose();
      if (e.key === " " && started) {
        e.preventDefault();
        togglePlayPause();
      }
      if (e.key === "ArrowRight" && started) skipScene();
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [handleClose, togglePlayPause, skipScene, started]);

  /* ── Cleanup ── */
  useEffect(() => {
    return () => {
      window.speechSynthesis.cancel();
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, []);

  const scene = SCENES[currentScene];
  const isLastScene = currentScene === SCENES.length - 1 && !playing;

  /* ─────────────────────────────────────────────
     RENDER: Start overlay
     ───────────────────────────────────────────── */
  if (!started) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-gradient-to-br from-slate-900 via-blue-950 to-slate-900">
        <button
          onClick={handleClose}
          className="absolute right-6 top-6 rounded-full bg-white/10 p-2 text-white/70 transition hover:bg-white/20 hover:text-white"
          aria-label="Close demo"
        >
          <XIcon />
        </button>

        <div className="flex max-w-2xl flex-col items-center px-6 text-center">
          {/* Logo */}
          <div className="mb-8 flex items-center gap-3">
            <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-sky-400 to-blue-600 shadow-lg shadow-sky-500/30">
              <PulseIcon className="h-9 w-9 text-white" />
            </div>
            <div className="text-left">
              <h1 className="text-4xl font-bold text-white">MedAssist AI</h1>
              <p className="text-sm font-medium text-sky-300">Intelligent Medical Assistant Platform</p>
            </div>
          </div>

          <p className="mb-10 max-w-lg text-lg text-blue-200/80">
            Experience how seven specialized AI agents work together to transform patient
            care with real-time monitoring, intelligent diagnosis, and clinical decision support.
          </p>

          <button
            onClick={handleStart}
            className="group relative inline-flex items-center gap-3 rounded-xl bg-gradient-to-r from-sky-500 to-blue-600 px-10 py-4 text-lg font-semibold text-white shadow-xl shadow-sky-500/25 transition-all hover:scale-105 hover:shadow-sky-500/40"
          >
            <PlayTriangleIcon className="h-6 w-6 transition-transform group-hover:scale-110" />
            Start Product Demo
          </button>

          <p className="mt-6 text-sm text-blue-300/60">
            Duration: ~3 minutes &middot; Audio narration &middot; Press ESC to exit
          </p>
        </div>

        {/* Background decorations */}
        <div className="pointer-events-none absolute inset-0 overflow-hidden">
          <div className="absolute -left-40 -top-40 h-96 w-96 rounded-full bg-sky-500/10 blur-3xl" />
          <div className="absolute -bottom-40 -right-40 h-96 w-96 rounded-full bg-blue-500/10 blur-3xl" />
          <div className="absolute left-1/2 top-1/3 h-64 w-64 -translate-x-1/2 rounded-full bg-cyan-500/5 blur-3xl" />
        </div>
      </div>
    );
  }

  /* ─────────────────────────────────────────────
     RENDER: Demo player
     ───────────────────────────────────────────── */
  return (
    <div className="fixed inset-0 z-50 flex flex-col bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      {/* Top bar */}
      <div className="flex items-center justify-between border-b border-white/10 bg-black/30 px-6 py-3">
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-sky-400 to-blue-600">
            <PulseIcon className="h-5 w-5 text-white" />
          </div>
          <span className="text-sm font-semibold text-white">MedAssist AI Demo</span>
          <span className="rounded-full bg-sky-500/20 px-2.5 py-0.5 text-xs font-medium text-sky-300">
            {currentScene + 1} / {SCENES.length}
          </span>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={togglePlayPause}
            className="rounded-lg bg-white/10 px-3 py-1.5 text-sm text-white transition hover:bg-white/20"
          >
            {playing ? "Pause" : "Resume"}
          </button>
          <button
            onClick={skipScene}
            className="rounded-lg bg-white/10 px-3 py-1.5 text-sm text-white transition hover:bg-white/20"
            disabled={currentScene >= SCENES.length - 1 && !playing}
          >
            Skip
          </button>
          <button
            onClick={handleClose}
            className="rounded-lg bg-white/10 p-1.5 text-white/70 transition hover:bg-white/20 hover:text-white"
            aria-label="Close demo"
          >
            <XIcon />
          </button>
        </div>
      </div>

      {/* Scene title */}
      <div className="flex items-center justify-center bg-black/20 py-2">
        <h2 className="text-lg font-bold text-white">{scene?.title}</h2>
      </div>

      {/* Main content area */}
      <div
        className={`flex-1 overflow-hidden transition-opacity duration-500 ${
          transitioning ? "opacity-0" : "opacity-100"
        }`}
      >
        <div className="h-full overflow-y-auto px-4 py-4 scrollbar-thin md:px-8">
          {scene && <SceneRenderer sceneId={scene.id} animatedVitals={animatedVitals} showAlert={showAlert} />}
        </div>
      </div>

      {/* Caption bar */}
      <div className="border-t border-white/10 bg-black/40 px-6 py-3">
        <p className="min-h-[3rem] text-center text-sm leading-relaxed text-blue-100/90 md:text-base">
          {caption || scene?.narration.slice(0, 0)}
        </p>
      </div>

      {/* Progress bar */}
      <div className="h-1.5 w-full bg-white/10">
        <div
          className="h-full bg-gradient-to-r from-sky-400 to-blue-500 transition-all duration-200"
          style={{ width: `${progress}%` }}
        />
      </div>

      {/* End screen overlay */}
      {isLastScene && (
        <div className="absolute inset-0 flex items-center justify-center bg-slate-900/80 backdrop-blur-sm">
          <div className="flex flex-col items-center gap-6 text-center">
            <div className="flex h-20 w-20 items-center justify-center rounded-2xl bg-gradient-to-br from-sky-400 to-blue-600 shadow-xl shadow-sky-500/30">
              <PulseIcon className="h-11 w-11 text-white" />
            </div>
            <h2 className="text-3xl font-bold text-white">Thank You for Watching</h2>
            <p className="max-w-md text-blue-200/80">
              Ready to transform care delivery at your organization?
            </p>
            <div className="flex gap-4">
              <button
                onClick={() => {
                  setCurrentScene(0);
                  setProgress(0);
                  setPlaying(true);
                  setCaption("");
                }}
                className="rounded-xl bg-white/10 px-6 py-3 font-semibold text-white transition hover:bg-white/20"
              >
                Replay Demo
              </button>
              <button
                onClick={handleClose}
                className="rounded-xl bg-gradient-to-r from-sky-500 to-blue-600 px-6 py-3 font-semibold text-white shadow-lg shadow-sky-500/25 transition hover:scale-105"
              >
                Back to Login
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

/* ─────────────────────────────────────────────
   SCENE RENDERER
   ───────────────────────────────────────────── */

interface SceneRendererProps {
  sceneId: string;
  animatedVitals: ReturnType<typeof generateVitalsData>;
  showAlert: boolean;
}

function SceneRenderer({ sceneId, animatedVitals, showAlert }: SceneRendererProps) {
  switch (sceneId) {
    case "intro":
      return <IntroScene />;
    case "patient-portal":
      return <PatientPortalScene />;
    case "symptom-analysis":
      return <SymptomAnalysisScene />;
    case "vitals-monitoring":
      return <VitalsMonitoringScene vitals={animatedVitals} showAlert={showAlert} />;
    case "report-analysis":
      return <ReportAnalysisScene />;
    case "drug-interaction":
      return <DrugInteractionScene />;
    case "doctor-dashboard":
      return <DoctorDashboardScene />;
    case "telemedicine":
      return <TelemedicineScene />;
    case "admin-compliance":
      return <AdminComplianceScene />;
    case "ai-agents":
      return <AIAgentsScene />;
    case "closing":
      return <ClosingScene />;
    default:
      return null;
  }
}

/* ─────────────────────────────────────────────
   SCENE 1: INTRO
   ───────────────────────────────────────────── */

function IntroScene() {
  return (
    <div className="flex h-full flex-col items-center justify-center gap-8">
      <div className="animate-in fade-in zoom-in-95 duration-1000 flex items-center gap-4">
        <div className="flex h-24 w-24 items-center justify-center rounded-3xl bg-gradient-to-br from-sky-400 to-blue-600 shadow-2xl shadow-sky-500/30">
          <PulseIcon className="h-14 w-14 text-white" />
        </div>
        <div>
          <h1 className="text-5xl font-bold text-white md:text-6xl">MedAssist AI</h1>
          <p className="mt-1 text-xl font-medium text-sky-300">Intelligent Medical Assistant Platform</p>
        </div>
      </div>

      <div className="animate-in fade-in slide-in-from-bottom-4 duration-1000 delay-500 mt-4 grid grid-cols-2 gap-4 md:grid-cols-4">
        {[
          { label: "AI Agents", value: "7", icon: "brain" },
          { label: "Monitoring", value: "24/7", icon: "pulse" },
          { label: "Response Time", value: "<2s", icon: "zap" },
          { label: "Compliance", value: "HIPAA", icon: "shield" },
        ].map((stat) => (
          <div
            key={stat.label}
            className="flex flex-col items-center rounded-2xl border border-white/10 bg-white/5 px-6 py-5 backdrop-blur"
          >
            <span className="text-3xl font-bold text-sky-400">{stat.value}</span>
            <span className="mt-1 text-sm text-blue-200/70">{stat.label}</span>
          </div>
        ))}
      </div>

      <p className="animate-in fade-in duration-1000 delay-1000 max-w-2xl text-center text-lg text-blue-200/60">
        Transforming healthcare with agentic AI for hospitals, telemedicine providers, and health startups worldwide.
      </p>
    </div>
  );
}

/* ─────────────────────────────────────────────
   SCENE 2: PATIENT PORTAL
   ───────────────────────────────────────────── */

function PatientPortalScene() {
  return (
    <div className="mx-auto max-w-6xl space-y-4">
      {/* Quick stat cards */}
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <StatCard label="Heart Rate" value="72 bpm" trend="+2" color="text-red-400" icon={<HeartIcon />} />
        <StatCard label="Blood Pressure" value="120/78" trend="-3" color="text-blue-400" icon={<DropletIcon />} />
        <StatCard label="SpO2" value="98%" trend="0" color="text-cyan-400" icon={<WindIcon />} />
        <StatCard label="Health Score" value="87/100" trend="+5" color="text-green-400" icon={<ShieldIcon />} />
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        {/* Upcoming Appointments */}
        <div className="rounded-xl border border-white/10 bg-white/5 p-4">
          <h3 className="mb-3 text-sm font-semibold text-white">Upcoming Appointments</h3>
          <div className="space-y-2">
            {[
              { dr: "Dr. Emily Carter", time: "Mar 22, 10:00 AM", type: "Follow-up", mode: "Telemedicine" },
              { dr: "Dr. M. Thompson", time: "Mar 28, 2:30 PM", type: "Cardiology", mode: "In-Person" },
            ].map((a, i) => (
              <div key={i} className="rounded-lg bg-white/5 p-3">
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
        <div className="rounded-xl border border-white/10 bg-white/5 p-4">
          <h3 className="mb-3 text-sm font-semibold text-white">Medication Reminders</h3>
          <div className="space-y-2">
            {MEDICATIONS.map((m, i) => (
              <div key={i} className="flex items-center justify-between rounded-lg bg-white/5 p-3">
                <div>
                  <p className="text-sm font-medium text-white">{m.name}</p>
                  <p className="text-xs text-blue-200/60">{m.dosage} &middot; {m.frequency}</p>
                </div>
                <span className="rounded-full bg-green-500/20 px-2 py-0.5 text-xs text-green-300">
                  {m.status}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Vitals Mini Chart */}
        <div className="rounded-xl border border-white/10 bg-white/5 p-4">
          <h3 className="mb-3 text-sm font-semibold text-white">Heart Rate - Last 24h</h3>
          <ResponsiveContainer width="100%" height={180}>
            <AreaChart data={VITALS_DATA}>
              <defs>
                <linearGradient id="hrGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#EF4444" stopOpacity={0.3} />
                  <stop offset="100%" stopColor="#EF4444" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
              <XAxis dataKey="time" tick={{ fontSize: 10, fill: "rgba(255,255,255,0.4)" }} />
              <YAxis domain={[55, 95]} tick={{ fontSize: 10, fill: "rgba(255,255,255,0.4)" }} />
              <Area type="monotone" dataKey="heartRate" stroke="#EF4444" fill="url(#hrGrad)" strokeWidth={2} dot={false} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}

/* ─────────────────────────────────────────────
   SCENE 3: SYMPTOM ANALYSIS
   ───────────────────────────────────────────── */

function SymptomAnalysisScene() {
  const [visibleMessages, setVisibleMessages] = useState(1);

  useEffect(() => {
    const timers: ReturnType<typeof setTimeout>[] = [];
    for (let i = 1; i < CHAT_MESSAGES.length; i++) {
      timers.push(setTimeout(() => setVisibleMessages(i + 1), i * 2800));
    }
    return () => timers.forEach(clearTimeout);
  }, []);

  return (
    <div className="mx-auto grid max-w-6xl gap-4 md:grid-cols-2">
      {/* Chat */}
      <div className="rounded-xl border border-white/10 bg-white/5 p-4">
        <div className="mb-3 flex items-center gap-2">
          <div className="h-2 w-2 animate-pulse rounded-full bg-green-400" />
          <h3 className="text-sm font-semibold text-white">AI Symptom Analyst</h3>
        </div>
        <div className="space-y-3 overflow-hidden">
          {CHAT_MESSAGES.slice(0, visibleMessages).map((msg, i) => (
            <div
              key={i}
              className={`animate-in fade-in slide-in-from-bottom-2 duration-500 flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`max-w-[85%] rounded-2xl px-4 py-2.5 text-sm ${
                  msg.role === "user"
                    ? "bg-sky-600 text-white"
                    : "bg-white/10 text-blue-100"
                }`}
              >
                {msg.text}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Diagnosis Results */}
      <div className="space-y-4">
        <div className="rounded-xl border border-white/10 bg-white/5 p-4">
          <h3 className="mb-3 text-sm font-semibold text-white">Differential Diagnosis</h3>
          <div className="space-y-2">
            {DIFFERENTIAL_DIAGNOSES.map((d, i) => (
              <div key={i} className="rounded-lg bg-white/5 p-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-white">{d.condition}</span>
                  <span
                    className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                      d.urgency === "Medium"
                        ? "bg-amber-500/20 text-amber-300"
                        : "bg-green-500/20 text-green-300"
                    }`}
                  >
                    {d.urgency}
                  </span>
                </div>
                <div className="mt-2">
                  <div className="h-2 w-full rounded-full bg-white/10">
                    <div
                      className="h-2 rounded-full bg-gradient-to-r from-sky-400 to-blue-500"
                      style={{ width: `${d.confidence * 100}%` }}
                    />
                  </div>
                  <p className="mt-1 text-xs text-blue-200/60">Confidence: {(d.confidence * 100).toFixed(0)}%</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 p-4">
          <p className="text-sm font-medium text-amber-300">Recommended Action</p>
          <p className="mt-1 text-sm text-amber-200/80">
            Schedule a follow-up with your primary care physician within 7 days.
            Monitor blood pressure daily. Seek immediate care if headache becomes severe or vision changes occur.
          </p>
        </div>
      </div>
    </div>
  );
}

/* ─────────────────────────────────────────────
   SCENE 4: VITALS MONITORING (Animated)
   ───────────────────────────────────────────── */

function VitalsMonitoringScene({
  vitals,
  showAlert,
}: {
  vitals: ReturnType<typeof generateVitalsData>;
  showAlert: boolean;
}) {
  return (
    <div className="mx-auto max-w-6xl space-y-4">
      {/* Alert notification */}
      {showAlert && (
        <div className="animate-in fade-in slide-in-from-top-4 duration-500 rounded-xl border border-red-500/40 bg-red-500/15 p-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-red-500/30">
              <AlertTriangleIcon className="h-5 w-5 text-red-400" />
            </div>
            <div>
              <p className="text-sm font-semibold text-red-300">CRITICAL ALERT - Room ICU-204</p>
              <p className="text-xs text-red-200/70">SpO2 dropped to 91% for patient James Wilson. NEWS2 score: 8. Escalating to attending physician.</p>
            </div>
            <div className="ml-auto flex gap-2">
              <button className="rounded-lg bg-red-500/30 px-3 py-1.5 text-xs font-medium text-red-200 transition hover:bg-red-500/40">
                Acknowledge
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Vitals grid */}
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <VitalGauge label="Heart Rate" value={Math.round(vitals[vitals.length - 1]?.heartRate ?? 72)} unit="bpm" color="#EF4444" min={40} max={120} normal={[60, 100]} />
        <VitalGauge label="SpO2" value={+(vitals[vitals.length - 1]?.spo2 ?? 97.5).toFixed(1)} unit="%" color="#06B6D4" min={80} max={100} normal={[95, 100]} />
        <VitalGauge label="Blood Pressure" value={`${Math.round(vitals[vitals.length - 1]?.systolic ?? 120)}/${Math.round(vitals[vitals.length - 1]?.diastolic ?? 78)}`} unit="mmHg" color="#3B82F6" />
        <VitalGauge label="Temperature" value={+(vitals[vitals.length - 1]?.temperature ?? 36.7).toFixed(1)} unit="C" color="#F97316" min={35} max={40} normal={[36.1, 37.2]} />
      </div>

      {/* Live charts */}
      <div className="grid gap-4 md:grid-cols-2">
        <div className="rounded-xl border border-white/10 bg-white/5 p-4">
          <h3 className="mb-2 text-sm font-semibold text-white">Heart Rate (Live)</h3>
          <ResponsiveContainer width="100%" height={160}>
            <LineChart data={vitals}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
              <XAxis dataKey="time" tick={{ fontSize: 9, fill: "rgba(255,255,255,0.3)" }} />
              <YAxis domain={[55, 95]} tick={{ fontSize: 9, fill: "rgba(255,255,255,0.3)" }} />
              <ReferenceLine y={100} stroke="rgba(239,68,68,0.4)" strokeDasharray="3 3" />
              <ReferenceLine y={60} stroke="rgba(239,68,68,0.4)" strokeDasharray="3 3" />
              <Line type="monotone" dataKey="heartRate" stroke="#EF4444" strokeWidth={2} dot={false} isAnimationActive={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
        <div className="rounded-xl border border-white/10 bg-white/5 p-4">
          <h3 className="mb-2 text-sm font-semibold text-white">Oxygen Saturation (Live)</h3>
          <ResponsiveContainer width="100%" height={160}>
            <AreaChart data={vitals}>
              <defs>
                <linearGradient id="spo2Grad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#06B6D4" stopOpacity={0.3} />
                  <stop offset="100%" stopColor="#06B6D4" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
              <XAxis dataKey="time" tick={{ fontSize: 9, fill: "rgba(255,255,255,0.3)" }} />
              <YAxis domain={[92, 100]} tick={{ fontSize: 9, fill: "rgba(255,255,255,0.3)" }} />
              <ReferenceLine y={95} stroke="rgba(239,68,68,0.4)" strokeDasharray="3 3" />
              <Area type="monotone" dataKey="spo2" stroke="#06B6D4" fill="url(#spo2Grad)" strokeWidth={2} dot={false} isAnimationActive={false} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* NEWS2 Score */}
      <div className="flex items-center gap-4 rounded-xl border border-white/10 bg-white/5 p-4">
        <div className="text-center">
          <p className="text-xs text-blue-200/60">NEWS2 Score</p>
          <p className="text-3xl font-bold text-amber-400">5</p>
        </div>
        <div className="h-12 w-px bg-white/10" />
        <div>
          <p className="text-sm font-medium text-amber-300">Medium Clinical Risk</p>
          <p className="text-xs text-blue-200/60">Increased frequency of monitoring. Urgent clinical review by ward-based doctor.</p>
        </div>
      </div>
    </div>
  );
}

/* ─────────────────────────────────────────────
   SCENE 5: REPORT ANALYSIS
   ───────────────────────────────────────────── */

function ReportAnalysisScene() {
  return (
    <div className="mx-auto grid max-w-6xl gap-4 md:grid-cols-5">
      {/* Lab Values Table */}
      <div className="rounded-xl border border-white/10 bg-white/5 p-4 md:col-span-3">
        <h3 className="mb-3 text-sm font-semibold text-white">Lab Results - Complete Blood Panel</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-white/10 text-left text-xs text-blue-200/60">
                <th className="pb-2 pr-4">Test</th>
                <th className="pb-2 pr-4">Value</th>
                <th className="pb-2 pr-4">Unit</th>
                <th className="pb-2 pr-4">Reference Range</th>
                <th className="pb-2">Status</th>
              </tr>
            </thead>
            <tbody>
              {LAB_RESULTS.map((lab, i) => (
                <tr key={i} className="border-b border-white/5">
                  <td className="py-2 pr-4 text-white">{lab.test}</td>
                  <td className={`py-2 pr-4 font-mono font-medium ${lab.status === "normal" ? "text-green-400" : lab.status === "high" ? "text-red-400" : "text-amber-400"}`}>
                    {lab.value}
                  </td>
                  <td className="py-2 pr-4 text-blue-200/60">{lab.unit}</td>
                  <td className="py-2 pr-4 text-blue-200/60">{lab.refMin} - {lab.refMax}</td>
                  <td className="py-2">
                    <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                      lab.status === "normal" ? "bg-green-500/20 text-green-300" : lab.status === "high" ? "bg-red-500/20 text-red-300" : "bg-amber-500/20 text-amber-300"
                    }`}>
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
        <div className="rounded-xl border border-sky-500/30 bg-sky-500/10 p-4">
          <div className="mb-2 flex items-center gap-2">
            <SparklesIcon className="h-4 w-4 text-sky-400" />
            <h3 className="text-sm font-semibold text-sky-300">AI Summary</h3>
          </div>
          <p className="text-sm leading-relaxed text-sky-100/80">
            Your lab results show <strong className="text-white">4 values outside normal range</strong>. Elevated fasting glucose (142 mg/dL) and HbA1c (6.8%)
            suggest pre-diabetic to early diabetic range. WBC is mildly elevated, which may indicate infection or inflammation. TSH is slightly low.
            Total cholesterol is borderline high.
          </p>
        </div>

        <div className="rounded-xl border border-white/10 bg-white/5 p-4">
          <h3 className="mb-2 text-sm font-semibold text-white">Recommended Follow-up</h3>
          <ul className="space-y-1.5 text-sm text-blue-200/70">
            <li className="flex items-start gap-2"><span className="mt-1 block h-1.5 w-1.5 rounded-full bg-amber-400" />Repeat fasting glucose in 2 weeks</li>
            <li className="flex items-start gap-2"><span className="mt-1 block h-1.5 w-1.5 rounded-full bg-amber-400" />Thyroid panel follow-up (Free T3, Free T4)</li>
            <li className="flex items-start gap-2"><span className="mt-1 block h-1.5 w-1.5 rounded-full bg-sky-400" />LDL/HDL cholesterol breakdown</li>
            <li className="flex items-start gap-2"><span className="mt-1 block h-1.5 w-1.5 rounded-full bg-sky-400" />Schedule endocrinology consultation</li>
          </ul>
        </div>
      </div>
    </div>
  );
}

/* ─────────────────────────────────────────────
   SCENE 6: DRUG INTERACTION
   ───────────────────────────────────────────── */

function DrugInteractionScene() {
  return (
    <div className="mx-auto max-w-5xl space-y-4">
      {/* Current Medications */}
      <div className="rounded-xl border border-white/10 bg-white/5 p-4">
        <h3 className="mb-3 text-sm font-semibold text-white">Active Medications</h3>
        <div className="grid gap-2 md:grid-cols-2">
          {MEDICATIONS.map((m, i) => (
            <div key={i} className="flex items-center justify-between rounded-lg bg-white/5 p-3">
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
            className={`rounded-xl border p-4 ${
              inter.severity === "Moderate"
                ? "border-amber-500/30 bg-amber-500/10"
                : "border-yellow-500/20 bg-yellow-500/5"
            }`}
          >
            <div className="flex items-center gap-3">
              <AlertTriangleIcon className={`h-5 w-5 ${inter.severity === "Moderate" ? "text-amber-400" : "text-yellow-400"}`} />
              <div>
                <p className="text-sm font-semibold text-white">
                  {inter.drug1} + {inter.drug2}
                  <span className={`ml-2 rounded-full px-2 py-0.5 text-xs ${inter.severity === "Moderate" ? "bg-amber-500/30 text-amber-300" : "bg-yellow-500/30 text-yellow-300"}`}>
                    {inter.severity}
                  </span>
                </p>
                <p className="mt-1 text-sm text-blue-200/70">{inter.effect}</p>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="rounded-xl border border-sky-500/30 bg-sky-500/10 p-4">
        <div className="flex items-center gap-2">
          <SparklesIcon className="h-4 w-4 text-sky-400" />
          <p className="text-sm font-medium text-sky-300">AI Recommendation</p>
        </div>
        <p className="mt-1 text-sm text-sky-100/80">
          Consider replacing Ibuprofen with Acetaminophen to avoid NSAID-ACE inhibitor interaction. Discuss with prescribing physician.
          Alternative: Topical diclofenac for localized pain (lower systemic interaction risk).
        </p>
      </div>
    </div>
  );
}

/* ─────────────────────────────────────────────
   SCENE 7: DOCTOR DASHBOARD
   ───────────────────────────────────────────── */

function DoctorDashboardScene() {
  return (
    <div className="mx-auto max-w-6xl space-y-4">
      {/* Patient monitoring wall */}
      <h3 className="text-sm font-semibold text-white">Patient Monitoring Wall</h3>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {MONITORED_PATIENTS.map((p, i) => {
          const statusColor = p.status === "critical" ? "border-red-500/50 bg-red-500/10" : p.status === "warning" ? "border-amber-500/40 bg-amber-500/10" : "border-green-500/30 bg-green-500/5";
          const statusBadge = p.status === "critical" ? "bg-red-500/30 text-red-300" : p.status === "warning" ? "bg-amber-500/30 text-amber-300" : "bg-green-500/30 text-green-300";
          return (
            <div key={i} className={`rounded-xl border p-3 ${statusColor}`}>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-white">{p.name}</p>
                  <p className="text-xs text-blue-200/60">{p.room} &middot; Age {p.age}</p>
                </div>
                <span className={`rounded-full px-2 py-0.5 text-xs font-medium capitalize ${statusBadge}`}>
                  {p.status}
                </span>
              </div>
              <div className="mt-2 grid grid-cols-4 gap-2 text-center">
                <div>
                  <p className="text-xs text-blue-200/50">HR</p>
                  <p className={`text-sm font-mono font-semibold ${p.hr > 100 ? "text-red-400" : "text-green-400"}`}>{p.hr}</p>
                </div>
                <div>
                  <p className="text-xs text-blue-200/50">BP</p>
                  <p className="text-sm font-mono font-semibold text-blue-300">{p.bp}</p>
                </div>
                <div>
                  <p className="text-xs text-blue-200/50">SpO2</p>
                  <p className={`text-sm font-mono font-semibold ${p.spo2 < 95 ? "text-amber-400" : "text-green-400"}`}>{p.spo2}%</p>
                </div>
                <div>
                  <p className="text-xs text-blue-200/50">NEWS2</p>
                  <p className={`text-sm font-mono font-semibold ${p.news2 >= 7 ? "text-red-400" : p.news2 >= 5 ? "text-amber-400" : "text-green-400"}`}>{p.news2}</p>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Alert feed */}
      <div className="rounded-xl border border-white/10 bg-white/5 p-4">
        <h3 className="mb-3 text-sm font-semibold text-white">Recent Alerts</h3>
        <div className="space-y-2">
          {[
            { time: "2 min ago", msg: "SpO2 dropped to 91% - James Wilson (ICU-204)", sev: "critical" },
            { time: "18 min ago", msg: "HR elevated to 104 bpm - Thomas Brown (ICU-201)", sev: "warning" },
            { time: "45 min ago", msg: "BP 148/92 - Sarah Chen (CCU-112)", sev: "warning" },
          ].map((a, i) => (
            <div key={i} className={`flex items-center justify-between rounded-lg p-3 ${a.sev === "critical" ? "bg-red-500/10" : "bg-amber-500/10"}`}>
              <div className="flex items-center gap-3">
                <div className={`h-2 w-2 rounded-full ${a.sev === "critical" ? "animate-pulse bg-red-400" : "bg-amber-400"}`} />
                <div>
                  <p className="text-sm text-white">{a.msg}</p>
                  <p className="text-xs text-blue-200/50">{a.time}</p>
                </div>
              </div>
              <button className="rounded-lg bg-white/10 px-3 py-1 text-xs text-white transition hover:bg-white/20">
                Acknowledge
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

/* ─────────────────────────────────────────────
   SCENE 8: TELEMEDICINE
   ───────────────────────────────────────────── */

function TelemedicineScene() {
  return (
    <div className="mx-auto max-w-5xl">
      <div className="overflow-hidden rounded-xl border border-white/10">
        {/* Video grid */}
        <div className="grid grid-cols-3 gap-px bg-black/50">
          {/* Main video */}
          <div className="col-span-2 flex aspect-video flex-col items-center justify-center bg-gradient-to-br from-slate-800 to-slate-700 p-8">
            <div className="flex h-20 w-20 items-center justify-center rounded-full bg-sky-600/30">
              <UserIcon className="h-10 w-10 text-sky-400" />
            </div>
            <p className="mt-3 text-sm font-medium text-white">Dr. Emily Carter</p>
            <p className="text-xs text-blue-200/60">Internal Medicine</p>
            <div className="mt-4 flex items-center gap-2">
              <div className="h-2 w-2 animate-pulse rounded-full bg-green-400" />
              <span className="text-xs text-green-300">HD Video Active</span>
            </div>
          </div>
          {/* Self view + AI sidebar */}
          <div className="flex flex-col gap-px">
            <div className="flex flex-1 flex-col items-center justify-center bg-gradient-to-br from-slate-700 to-slate-600 p-4">
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-emerald-600/30">
                <UserIcon className="h-6 w-6 text-emerald-400" />
              </div>
              <p className="mt-2 text-xs text-white">You</p>
            </div>
            <div className="flex-1 bg-slate-800 p-3">
              <p className="text-xs font-semibold text-sky-300">AI Assistant</p>
              <p className="mt-1 text-xs text-blue-200/70">Live transcription active...</p>
              <div className="mt-2 rounded bg-white/5 p-2">
                <p className="text-xs italic text-blue-200/50">
                  &quot;...Your blood pressure readings have been improving since we adjusted the Lisinopril dosage last month...&quot;
                </p>
              </div>
            </div>
          </div>
        </div>
        {/* Call controls */}
        <div className="flex items-center justify-center gap-4 bg-black/60 p-4">
          {["Mic", "Camera", "Share", "Notes", "Chat"].map((ctrl) => (
            <button key={ctrl} className="flex flex-col items-center gap-1 rounded-lg bg-white/10 px-4 py-2 text-xs text-white transition hover:bg-white/20">
              {ctrl}
            </button>
          ))}
          <button className="flex flex-col items-center gap-1 rounded-lg bg-red-600 px-4 py-2 text-xs text-white transition hover:bg-red-700">
            End Call
          </button>
        </div>
      </div>
    </div>
  );
}

/* ─────────────────────────────────────────────
   SCENE 9: ADMIN & COMPLIANCE
   ───────────────────────────────────────────── */

function AdminComplianceScene() {
  return (
    <div className="mx-auto max-w-6xl space-y-4">
      <div className="grid gap-4 md:grid-cols-2">
        {/* System Health */}
        <div className="rounded-xl border border-white/10 bg-white/5 p-4">
          <h3 className="mb-3 text-sm font-semibold text-white">System Health</h3>
          <div className="space-y-2">
            {SYSTEM_HEALTH.map((s, i) => (
              <div key={i} className="flex items-center justify-between rounded-lg bg-white/5 p-2.5">
                <div className="flex items-center gap-2">
                  <div className="h-2 w-2 rounded-full bg-green-400" />
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
        <div className="rounded-xl border border-white/10 bg-white/5 p-4">
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
                  <tr key={i} className="border-b border-white/5">
                    <td className="py-1.5 pr-3 font-mono text-blue-200/60">{log.time}</td>
                    <td className="py-1.5 pr-3 text-white">{log.user}</td>
                    <td className="py-1.5 pr-3 text-blue-200/70">{log.action}</td>
                    <td className="py-1.5">
                      <span className={`rounded-full px-2 py-0.5 text-xs ${log.status === "Success" ? "bg-green-500/20 text-green-300" : "bg-red-500/20 text-red-300"}`}>
                        {log.status}
                      </span>
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
        <MiniStat label="Encryption" value="AES-256" sub="At rest & in transit" />
        <MiniStat label="Audit Retention" value="6+ Years" sub="HIPAA compliant" />
        <MiniStat label="Access Control" value="RBAC" sub="4 role levels" />
        <MiniStat label="PHI De-identification" value="Active" sub="Before all AI calls" />
      </div>

      {/* AI Usage pie chart */}
      <div className="rounded-xl border border-white/10 bg-white/5 p-4">
        <h3 className="mb-2 text-sm font-semibold text-white">AI Agent Usage Distribution (This Month)</h3>
        <div className="flex items-center justify-center">
          <ResponsiveContainer width="100%" height={180}>
            <PieChart>
              <Pie data={PIE_DATA} cx="50%" cy="50%" innerRadius={45} outerRadius={75} dataKey="value" stroke="none">
                {PIE_DATA.map((entry, i) => (
                  <Cell key={i} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{ background: "rgba(15,23,42,0.9)", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 8, fontSize: 12 }}
                itemStyle={{ color: "white" }}
              />
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

/* ─────────────────────────────────────────────
   SCENE 10: AI AGENTS
   ───────────────────────────────────────────── */

function AIAgentsScene() {
  return (
    <div className="mx-auto max-w-5xl space-y-6">
      {/* Orchestrator */}
      <div className="flex flex-col items-center">
        <div className="rounded-2xl border border-sky-500/40 bg-gradient-to-br from-sky-500/20 to-blue-500/20 px-8 py-4 text-center">
          <p className="text-sm font-bold text-sky-300">Agent Orchestrator</p>
          <p className="text-xs text-blue-200/60">GPT-4o with function calling</p>
          <p className="mt-1 text-xs text-blue-200/50">Routes tasks to specialized agents</p>
        </div>
        <div className="h-8 w-px bg-sky-500/30" />
        <div className="h-3 w-3 rounded-full border-2 border-sky-500/50 bg-transparent" />
        <div className="h-4 w-px bg-sky-500/30" />
      </div>

      {/* Agent grid */}
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {AGENT_DATA.map((agent, i) => (
          <div
            key={i}
            className="group rounded-xl border border-white/10 bg-white/5 p-4 transition-colors hover:bg-white/10"
          >
            <div className="mb-2 flex h-10 w-10 items-center justify-center rounded-lg" style={{ backgroundColor: `${agent.color}20` }}>
              <div className="h-5 w-5 rounded-full" style={{ backgroundColor: agent.color }} />
            </div>
            <p className="whitespace-pre-line text-sm font-semibold text-white">{agent.name}</p>
            <p className="mt-0.5 text-xs text-blue-200/50">{agent.model}</p>
            <p className="mt-2 text-xs leading-relaxed text-blue-200/70">{agent.description}</p>
          </div>
        ))}
      </div>

      {/* Shared memory */}
      <div className="rounded-xl border border-white/10 bg-white/5 p-4 text-center">
        <p className="text-sm font-semibold text-white">Shared Context &amp; Memory Store</p>
        <p className="mt-1 text-xs text-blue-200/60">Redis (short-term context) + Pinecone (long-term medical knowledge)</p>
        <div className="mt-3 flex justify-center gap-6">
          <div className="text-center">
            <p className="text-2xl font-bold text-sky-400">3,072</p>
            <p className="text-xs text-blue-200/50">Embedding dimensions</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-purple-400">50K+</p>
            <p className="text-xs text-blue-200/50">Medical knowledge vectors</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-emerald-400">&lt;45ms</p>
            <p className="text-xs text-blue-200/50">Retrieval latency</p>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ─────────────────────────────────────────────
   SCENE 11: CLOSING
   ───────────────────────────────────────────── */

function ClosingScene() {
  return (
    <div className="flex h-full flex-col items-center justify-center gap-8">
      <div className="flex items-center gap-4">
        <div className="flex h-20 w-20 items-center justify-center rounded-3xl bg-gradient-to-br from-sky-400 to-blue-600 shadow-2xl shadow-sky-500/30">
          <PulseIcon className="h-12 w-12 text-white" />
        </div>
        <h1 className="text-4xl font-bold text-white md:text-5xl">MedAssist AI</h1>
      </div>

      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        {[
          { value: "7", label: "Specialized AI Agents" },
          { value: "24/7", label: "Real-Time Monitoring" },
          { value: "<2s", label: "Triage Response" },
          { value: "100%", label: "HIPAA Compliant" },
        ].map((stat, i) => (
          <div key={i} className="flex flex-col items-center rounded-2xl border border-white/10 bg-white/5 px-6 py-5">
            <span className="text-3xl font-bold text-sky-400">{stat.value}</span>
            <span className="mt-1 text-center text-sm text-blue-200/70">{stat.label}</span>
          </div>
        ))}
      </div>

      <p className="max-w-xl text-center text-lg text-blue-200/70">
        Transforming healthcare with intelligent, agentic AI.
        <br />
        Ready to see it in action?
      </p>

      <div className="rounded-xl bg-gradient-to-r from-sky-500 to-blue-600 px-8 py-3 text-lg font-semibold text-white shadow-xl shadow-sky-500/25">
        Contact Us for a Live Demo
      </div>
    </div>
  );
}

/* ─────────────────────────────────────────────
   REUSABLE UI COMPONENTS
   ───────────────────────────────────────────── */

function StatCard({
  label,
  value,
  trend,
  color,
  icon,
}: {
  label: string;
  value: string;
  trend: string;
  color: string;
  icon: React.ReactNode;
}) {
  const trendNum = parseFloat(trend);
  return (
    <div className="rounded-xl border border-white/10 bg-white/5 p-3">
      <div className="flex items-center justify-between">
        <span className="text-xs text-blue-200/60">{label}</span>
        <span className={color}>{icon}</span>
      </div>
      <p className="mt-1 text-xl font-bold text-white">{value}</p>
      <p className={`text-xs ${trendNum > 0 ? "text-green-400" : trendNum < 0 ? "text-red-400" : "text-blue-200/50"}`}>
        {trendNum > 0 ? "+" : ""}{trend} from last week
      </p>
    </div>
  );
}

function VitalGauge({
  label,
  value,
  unit,
  color,
  min,
  max,
  normal,
}: {
  label: string;
  value: number | string;
  unit: string;
  color: string;
  min?: number;
  max?: number;
  normal?: [number, number];
}) {
  return (
    <div className="rounded-xl border border-white/10 bg-white/5 p-3 text-center">
      <p className="text-xs text-blue-200/60">{label}</p>
      <p className="mt-1 text-2xl font-bold" style={{ color }}>
        {typeof value === "number" ? value : value}
      </p>
      <p className="text-xs text-blue-200/50">{unit}</p>
      {min !== undefined && max !== undefined && typeof value === "number" && (
        <div className="mx-auto mt-2 h-1.5 w-full max-w-[120px] overflow-hidden rounded-full bg-white/10">
          <div
            className="h-full rounded-full"
            style={{
              width: `${((value - min) / (max - min)) * 100}%`,
              backgroundColor: normal && (value < normal[0] || value > normal[1]) ? "#F97316" : color,
            }}
          />
        </div>
      )}
    </div>
  );
}

function MiniStat({ label, value, sub }: { label: string; value: string; sub: string }) {
  return (
    <div className="rounded-xl border border-white/10 bg-white/5 p-3 text-center">
      <p className="text-xs text-blue-200/60">{label}</p>
      <p className="mt-1 text-lg font-bold text-sky-400">{value}</p>
      <p className="text-xs text-blue-200/50">{sub}</p>
    </div>
  );
}

/* ─────────────────────────────────────────────
   SVG ICONS (inline, no external dep)
   ───────────────────────────────────────────── */

function PulseIcon({ className = "h-6 w-6" }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
    </svg>
  );
}

function XIcon() {
  return (
    <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
    </svg>
  );
}

function PlayTriangleIcon({ className = "h-6 w-6" }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M8 5v14l11-7z" />
    </svg>
  );
}

function AlertTriangleIcon({ className = "h-5 w-5" }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" /><line x1="12" y1="9" x2="12" y2="13" /><line x1="12" y1="17" x2="12.01" y2="17" />
    </svg>
  );
}

function SparklesIcon({ className = "h-4 w-4" }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M9.937 15.5A2 2 0 0 0 8.5 14.063l-6.135-1.582a.5.5 0 0 1 0-.962L8.5 9.936A2 2 0 0 0 9.937 8.5l1.582-6.135a.5.5 0 0 1 .963 0L14.063 8.5A2 2 0 0 0 15.5 9.937l6.135 1.581a.5.5 0 0 1 0 .964L15.5 14.063a2 2 0 0 0-1.437 1.437l-1.582 6.135a.5.5 0 0 1-.963 0z" />
    </svg>
  );
}

function HeartIcon() {
  return (
    <svg className="h-4 w-4" viewBox="0 0 24 24" fill="currentColor">
      <path d="M20.84 4.61a5.5 5.5 0 00-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 00-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 000-7.78z" />
    </svg>
  );
}

function DropletIcon() {
  return (
    <svg className="h-4 w-4" viewBox="0 0 24 24" fill="currentColor">
      <path d="M12 2.69l5.66 5.66a8 8 0 11-11.31 0z" />
    </svg>
  );
}

function WindIcon() {
  return (
    <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M9.59 4.59A2 2 0 1111 8H2m10.59 11.41A2 2 0 1014 16H2m15.73-8.27A2.5 2.5 0 1119.5 12H2" />
    </svg>
  );
}

function ShieldIcon() {
  return (
    <svg className="h-4 w-4" viewBox="0 0 24 24" fill="currentColor">
      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
    </svg>
  );
}

function UserIcon({ className = "h-6 w-6" }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2" /><circle cx="12" cy="7" r="4" />
    </svg>
  );
}
