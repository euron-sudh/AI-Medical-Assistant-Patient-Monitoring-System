"use client";
type BadgeStatus = "active" | "completed" | "cancelled" | "pending" | "in_progress" | "discontinued" | "on_hold" | "draft" | "reviewed" | "processing" | "missed" | "achieved";
interface StatusBadgeProps { status: string; showDot?: boolean; size?: "sm" | "md"; className?: string; }
const statusStyles: Record<BadgeStatus, { bg: string; dot: string }> = { active: { bg: "bg-green-100 text-green-700", dot: "bg-green-500" }, completed: { bg: "bg-blue-100 text-blue-700", dot: "bg-blue-500" }, cancelled: { bg: "bg-red-100 text-red-700", dot: "bg-red-500" }, pending: { bg: "bg-amber-100 text-amber-700", dot: "bg-amber-500" }, in_progress: { bg: "bg-blue-100 text-blue-700", dot: "bg-blue-500" }, discontinued: { bg: "bg-red-100 text-red-700", dot: "bg-red-500" }, on_hold: { bg: "bg-amber-100 text-amber-700", dot: "bg-amber-500" }, draft: { bg: "bg-gray-100 text-gray-700", dot: "bg-gray-400" }, reviewed: { bg: "bg-green-100 text-green-700", dot: "bg-green-500" }, processing: { bg: "bg-blue-100 text-blue-700", dot: "bg-blue-500" }, missed: { bg: "bg-red-100 text-red-700", dot: "bg-red-500" }, achieved: { bg: "bg-green-100 text-green-700", dot: "bg-green-500" } };
const defaultStyle = { bg: "bg-gray-100 text-gray-700", dot: "bg-gray-400" };
export default function StatusBadge({ status, showDot = true, size = "sm", className = "" }: StatusBadgeProps) {
  const ns = status.toLowerCase().replace(/\s+/g, "_") as BadgeStatus;
  const style = statusStyles[ns] ?? defaultStyle;
  const sc = size === "sm" ? "px-2 py-0.5 text-xs" : "px-3 py-1 text-sm";
  return (<span className={`inline-flex items-center gap-1.5 rounded-full font-medium ${style.bg} ${sc} ${className}`}>{showDot && <span className={`inline-block h-1.5 w-1.5 rounded-full ${style.dot}`} />}{status.replace(/_/g, " ")}</span>);
}
