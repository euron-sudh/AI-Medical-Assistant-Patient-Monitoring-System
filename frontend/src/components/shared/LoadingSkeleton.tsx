"use client";
interface LoadingSkeletonProps { rows?: number; variant?: "card" | "table" | "text"; className?: string; }
function SkeletonPulse({ className = "" }: { className?: string }) { return <div className={`animate-pulse rounded-md bg-muted ${className}`} />; }
export default function LoadingSkeleton({ rows = 3, variant = "card", className = "" }: LoadingSkeletonProps) {
  if (variant === "text") return (<div className={`space-y-2 ${className}`}>{[...Array(rows)].map((_, i) => (<SkeletonPulse key={i} className={`h-4 ${i === rows - 1 ? "w-2/3" : "w-full"}`} />))}</div>);
  return (<div className={`space-y-4 ${className}`}>{[...Array(rows)].map((_, i) => (<div key={i} className="rounded-lg border border-border bg-card p-6 shadow-sm"><div className="flex items-center gap-4"><SkeletonPulse className="h-10 w-10 rounded-full" /><div className="flex-1 space-y-2"><SkeletonPulse className="h-4 w-1/3" /><SkeletonPulse className="h-3 w-1/2" /></div><SkeletonPulse className="h-6 w-16 rounded-full" /></div></div>))}</div>);
}
