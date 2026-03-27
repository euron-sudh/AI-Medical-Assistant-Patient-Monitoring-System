"use client";

import { useEffect, useState } from "react";
import apiClient from "@/lib/api-client";
import LoadingSkeleton from "@/components/shared/LoadingSkeleton";
import EmptyState from "@/components/shared/EmptyState";
import StatusBadge from "@/components/shared/StatusBadge";

interface CarePlanGoal {
  id: string;
  title: string;
  description: string | null;
  target_value: string | null;
  current_value: string | null;
  unit: string | null;
  status: string;
  target_date: string | null;
}

interface CarePlanActivity {
  id: string;
  title: string;
  description: string | null;
  activity_type: string;
  frequency: string | null;
  status: string;
  due_date: string | null;
  completed_at: string | null;
}

interface CarePlan {
  id: string;
  title: string;
  description: string | null;
  status: string;
  start_date: string;
  end_date: string | null;
  ai_recommendations: Record<string, unknown> | null;
  goals: CarePlanGoal[];
  activities: CarePlanActivity[];
  created_at: string;
}

const planStatusBadge: Record<string, string> = {
  draft: "bg-gray-100 text-gray-700",
  active: "bg-green-100 text-green-700",
  completed: "bg-blue-100 text-blue-700",
  cancelled: "bg-red-100 text-red-700",
};

const goalStatusColors: Record<string, string> = {
  not_started: "bg-gray-200",
  in_progress: "bg-blue-500",
  achieved: "bg-green-500",
  missed: "bg-red-500",
};

const activityTypeBadge: Record<string, string> = {
  medication: "bg-purple-100 text-purple-700",
  exercise: "bg-green-100 text-green-700",
  diet: "bg-amber-100 text-amber-700",
  monitoring: "bg-blue-100 text-blue-700",
  appointment: "bg-teal-100 text-teal-700",
  other: "bg-gray-100 text-gray-700",
};

export default function CarePlanPage() {
  const [carePlans, setCarePlans] = useState<CarePlan[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedPlanId, setExpandedPlanId] = useState<string | null>(null);

  useEffect(() => {
    fetchCarePlans();
  }, []);

  const fetchCarePlans = async () => {
    try {
      const userStr = localStorage.getItem("user");
      if (!userStr) {
        setError("User not found. Please log in again.");
        setLoading(false);
        return;
      }
      const user = JSON.parse(userStr);
      const patientId = user.id ?? user.patient_id;

      const res = await apiClient.get(`/care-plans/${patientId}`);
      const data = res.data?.care_plans ?? res.data;
      setCarePlans(Array.isArray(data) ? data : []);

      // Auto-expand first active plan
      const plans = Array.isArray(data) ? data : [];
      const activePlan = plans.find((p: CarePlan) => p.status === "active");
      if (activePlan) setExpandedPlanId(activePlan.id);
    } catch (err: unknown) {
      const status =
        err && typeof err === "object" && "response" in err
          ? (err as { response?: { status?: number } }).response?.status
          : undefined;
      if (status === 404) {
        setCarePlans([]);
      } else {
        setError("Failed to load care plans.");
      }
    } finally {
      setLoading(false);
    }
  };

  const activePlans = carePlans.filter((p) => p.status === "active");
  const allGoals = carePlans.flatMap((p) => p.goals ?? []);
  const inProgressGoals = allGoals.filter((g) => g.status === "in_progress");
  const achievedGoals = allGoals.filter((g) => g.status === "achieved");
  const adherenceRate =
    allGoals.length > 0
      ? Math.round((achievedGoals.length / allGoals.length) * 100)
      : null;

  const getProgress = (goal: CarePlanGoal): number | null => {
    if (!goal.target_value || !goal.current_value) return null;
    const target = parseFloat(goal.target_value);
    const current = parseFloat(goal.current_value);
    if (isNaN(target) || isNaN(current) || target === 0) return null;
    return Math.min(100, Math.round((current / target) * 100));
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Care Plan</h1>
        <p className="mt-1 text-muted-foreground">
          View your personalized care plans, goals, and track your progress.
        </p>
      </div>

      {/* Summary Cards */}
      <div className="grid gap-6 md:grid-cols-3">
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <p className="text-sm font-medium text-muted-foreground">Active Plans</p>
          <p className="mt-2 text-3xl font-bold text-foreground">{activePlans.length}</p>
        </div>
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <p className="text-sm font-medium text-muted-foreground">Goals in Progress</p>
          <p className="mt-2 text-3xl font-bold text-foreground">{inProgressGoals.length}</p>
        </div>
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <p className="text-sm font-medium text-muted-foreground">Adherence Rate</p>
          <p className="mt-2 text-3xl font-bold text-foreground">
            {adherenceRate != null ? `${adherenceRate}%` : "N/A"}
          </p>
        </div>
      </div>

      {loading ? (
        <div className="rounded-lg border border-border bg-card p-12 text-center">
          <p className="text-sm text-muted-foreground">Loading care plans...</p>
        </div>
      ) : error ? (
        <div className="rounded-lg border border-border bg-card p-12 text-center">
          <p className="text-sm text-destructive">{error}</p>
        </div>
      ) : carePlans.length === 0 ? (
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-foreground">Your Care Plans</h2>
          <p className="mt-2 text-sm text-muted-foreground">
            No active care plans. Your doctor will create personalized care plans with goals,
            medication schedules, lifestyle recommendations, and follow-up appointments.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {carePlans.map((plan) => (
            <div
              key={plan.id}
              className="rounded-lg border border-border bg-card shadow-sm"
            >
              {/* Plan Header */}
              <button
                onClick={() =>
                  setExpandedPlanId(expandedPlanId === plan.id ? null : plan.id)
                }
                className="flex w-full items-center justify-between px-6 py-4 text-left hover:bg-muted/30 transition-colors"
              >
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="text-sm font-semibold text-foreground">{plan.title}</h3>
                    <span
                      className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${
                        planStatusBadge[plan.status] ?? "bg-gray-100 text-gray-700"
                      }`}
                    >
                      {plan.status}
                    </span>
                  </div>
                  <p className="mt-0.5 text-xs text-muted-foreground">
                    Started {new Date(plan.start_date).toLocaleDateString()}
                    {plan.end_date &&
                      ` - Target end: ${new Date(plan.end_date).toLocaleDateString()}`}
                  </p>
                </div>
                <span className="text-muted-foreground">
                  {expandedPlanId === plan.id ? "\u25B2" : "\u25BC"}
                </span>
              </button>

              {/* Expanded Content */}
              {expandedPlanId === plan.id && (
                <div className="border-t border-border px-6 py-4 space-y-5">
                  {plan.description && (
                    <p className="text-sm text-muted-foreground">{plan.description}</p>
                  )}

                  {/* Goals */}
                  {plan.goals && plan.goals.length > 0 && (
                    <div>
                      <h4 className="text-sm font-semibold text-foreground mb-2">Goals</h4>
                      <div className="space-y-3">
                        {plan.goals.map((goal) => {
                          const progress = getProgress(goal);
                          return (
                            <div
                              key={goal.id}
                              className="rounded-md border border-border p-3"
                            >
                              <div className="flex items-start justify-between">
                                <div>
                                  <p className="text-sm font-medium text-foreground">
                                    {goal.title}
                                  </p>
                                  {goal.description && (
                                    <p className="mt-0.5 text-xs text-muted-foreground">
                                      {goal.description}
                                    </p>
                                  )}
                                </div>
                                <span
                                  className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${
                                    goal.status === "achieved"
                                      ? "bg-green-100 text-green-700"
                                      : goal.status === "in_progress"
                                      ? "bg-blue-100 text-blue-700"
                                      : goal.status === "missed"
                                      ? "bg-red-100 text-red-700"
                                      : "bg-gray-100 text-gray-700"
                                  }`}
                                >
                                  {goal.status.replace("_", " ")}
                                </span>
                              </div>

                              {/* Progress Bar */}
                              {(goal.target_value || goal.current_value) && (
                                <div className="mt-2">
                                  <div className="flex justify-between text-xs text-muted-foreground mb-1">
                                    <span>
                                      Current: {goal.current_value ?? "0"}
                                      {goal.unit ? ` ${goal.unit}` : ""}
                                    </span>
                                    <span>
                                      Target: {goal.target_value ?? "--"}
                                      {goal.unit ? ` ${goal.unit}` : ""}
                                    </span>
                                  </div>
                                  <div className="h-2 w-full rounded-full bg-muted">
                                    <div
                                      className={`h-2 rounded-full transition-all ${
                                        goalStatusColors[goal.status] ?? "bg-blue-500"
                                      }`}
                                      style={{ width: `${progress ?? 0}%` }}
                                    />
                                  </div>
                                  {progress != null && (
                                    <p className="mt-0.5 text-xs text-muted-foreground text-right">
                                      {progress}%
                                    </p>
                                  )}
                                </div>
                              )}

                              {goal.target_date && (
                                <p className="mt-1 text-xs text-muted-foreground">
                                  Target date:{" "}
                                  {new Date(goal.target_date).toLocaleDateString()}
                                </p>
                              )}
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}

                  {/* Activities */}
                  {plan.activities && plan.activities.length > 0 && (
                    <div>
                      <h4 className="text-sm font-semibold text-foreground mb-2">
                        Activities
                      </h4>
                      <div className="space-y-2">
                        {plan.activities.map((activity) => (
                          <div
                            key={activity.id}
                            className="flex items-center justify-between rounded-md bg-muted/50 px-3 py-2"
                          >
                            <div className="flex items-center gap-2">
                              <span
                                className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${
                                  activityTypeBadge[activity.activity_type] ??
                                  activityTypeBadge.other
                                }`}
                              >
                                {activity.activity_type}
                              </span>
                              <span className="text-sm text-foreground">{activity.title}</span>
                            </div>
                            <div className="flex items-center gap-2">
                              {activity.frequency && (
                                <span className="text-xs text-muted-foreground">
                                  {activity.frequency}
                                </span>
                              )}
                              {activity.status === "completed" ? (
                                <span className="inline-block h-4 w-4 rounded-full bg-green-500 text-center text-xs text-white leading-4">
                                  &#10003;
                                </span>
                              ) : (
                                <span className="inline-block h-4 w-4 rounded-full border-2 border-muted-foreground" />
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* AI Recommendations */}
                  {plan.ai_recommendations && (
                    <div>
                      <h4 className="text-sm font-semibold text-foreground mb-2">
                        AI Recommendations
                      </h4>
                      <div className="rounded-md bg-primary/5 border border-primary/20 p-3">
                        <pre className="text-xs text-foreground whitespace-pre-wrap">
                          {typeof plan.ai_recommendations === "string"
                            ? plan.ai_recommendations
                            : JSON.stringify(plan.ai_recommendations, null, 2)}
                        </pre>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
