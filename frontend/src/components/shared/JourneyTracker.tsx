"use client";

import { Check, Sparkles, Stethoscope, MessageSquare, TestTube2, Upload, Brain, UserCheck } from "lucide-react";
import type { LucideIcon } from "lucide-react";

const JOURNEY_STEPS: { label: string; icon: LucideIcon; description: string }[] = [
  { label: "Specialty Selection", icon: Stethoscope, description: "Choose a medical specialty for your consultation" },
  { label: "Symptom Analysis", icon: MessageSquare, description: "Describe your symptoms to the AI assistant" },
  { label: "Test Recommendations", icon: TestTube2, description: "AI recommends relevant diagnostic tests" },
  { label: "Report Upload", icon: Upload, description: "Upload test results and medical reports" },
  { label: "AI Analysis", icon: Brain, description: "AI analyzes your reports and provides insights" },
  { label: "Doctor Referral", icon: UserCheck, description: "Get referred to the appropriate specialist" },
];

interface JourneyTrackerProps { currentStep: number; loading?: boolean; }

export default function JourneyTracker({ currentStep, loading }: JourneyTrackerProps) {
  const safeStep = Math.min(Math.max(currentStep, 0), JOURNEY_STEPS.length - 1);
  return (
    <section className="rounded-xl border border-border bg-card p-4 shadow-sm sm:p-6" aria-label="Patient journey progress">
      <div className="mb-4 flex items-center gap-2">
        <Sparkles className="h-5 w-5 text-primary" aria-hidden />
        <h2 className="text-base font-semibold text-foreground">Patient Journey Tracker</h2>
        <span className="ml-auto text-xs text-muted-foreground">Step {safeStep + 1} of {JOURNEY_STEPS.length}</span>
      </div>
      {loading ? <JourneySkeleton /> : (
        <>
          <div className="mb-5"><div className="h-2 w-full rounded-full bg-muted"><div className="h-2 rounded-full bg-emerald-500 transition-all duration-500 ease-out" style={{ width: `${(safeStep / (JOURNEY_STEPS.length - 1)) * 100}%` }} /></div></div>
          <div className="overflow-x-auto pb-2">
            <ol className="flex min-w-[720px] items-start sm:min-w-0">
              {JOURNEY_STEPS.map((step, index) => {
                const isDone = index < safeStep;
                const isCurrent = index === safeStep;
                const isFuture = index > safeStep;
                const lineDone = index > 0 && index <= safeStep;
                const Icon = step.icon;
                return (
                  <li key={step.label} className="flex min-w-0 flex-1 items-start">
                    {index > 0 && <div className={`mx-1 mt-[18px] h-0.5 flex-1 transition-colors duration-300 ${lineDone ? "bg-emerald-500" : "bg-border"}`} aria-hidden />}
                    <div className="flex w-[64px] shrink-0 flex-col items-center sm:w-auto sm:min-w-[90px] sm:flex-1">
                      <div className={`flex h-9 w-9 items-center justify-center rounded-full border-2 transition-all duration-300 ${isDone ? "border-emerald-500 bg-emerald-500 text-white" : isCurrent ? "border-primary bg-primary text-primary-foreground ring-2 ring-primary/30 ring-offset-2 ring-offset-card" : "border-muted-foreground/30 bg-muted text-muted-foreground"}`}>
                        {isDone ? <Check className="h-4 w-4" strokeWidth={3} /> : <Icon className="h-4 w-4" />}
                      </div>
                      <span className={`mt-2 text-center text-[10px] font-semibold leading-tight sm:text-xs ${isFuture ? "text-muted-foreground" : isCurrent ? "text-primary" : "text-foreground"}`}>{step.label}</span>
                      <span className="mt-0.5 hidden text-center text-[9px] leading-tight text-muted-foreground sm:block">{step.description}</span>
                    </div>
                  </li>
                );
              })}
            </ol>
          </div>
          <div className="mt-3 rounded-md bg-primary/5 px-3 py-2 sm:hidden">
            <p className="text-xs font-medium text-primary">Current: {JOURNEY_STEPS[safeStep].label}</p>
            <p className="text-[10px] text-muted-foreground">{JOURNEY_STEPS[safeStep].description}</p>
          </div>
        </>
      )}
    </section>
  );
}

function JourneySkeleton() {
  return (
    <div className="space-y-4">
      <div className="h-2 w-full animate-pulse rounded-full bg-muted" />
      <div className="flex animate-pulse gap-2">
        {JOURNEY_STEPS.map((s) => (<div key={s.label} className="flex flex-1 flex-col items-center gap-2"><div className="h-9 w-9 rounded-full bg-muted" /><div className="h-3 w-full max-w-[72px] rounded bg-muted" /></div>))}
      </div>
    </div>
  );
}
