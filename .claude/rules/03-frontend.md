# MedAssist AI - Frontend Rules

> Next.js 14+ with App Router, TypeScript strict mode, and medical-grade UI standards.

---

## Framework: Next.js 14+ with App Router

- Use the App Router (`app/` directory), NOT the Pages Router (`pages/`)
- Server Components by default; add `"use client"` only when the component needs interactivity, browser APIs, or hooks
- Use `layout.tsx` for shared layouts per route group
- Use `loading.tsx` for Suspense fallbacks
- Use `error.tsx` for error boundaries
- Use `not-found.tsx` for 404 pages

---

## TypeScript Strict Mode

`tsconfig.json` MUST have `"strict": true`. Additional rules:

- **No `any` type** - Use `unknown` and narrow, or define proper types
- **No type assertions (`as`)** unless unavoidable and commented with justification
- **No `@ts-ignore`** - Fix the type error instead
- **All function parameters and return types** must be explicitly typed
- **All component props** must have an interface

```typescript
// CORRECT
interface PatientVitalsProps {
  patientId: string;
  timeRange: TimeRange;
  onAnomalyDetected?: (alert: MonitoringAlert) => void;
}

export function PatientVitals({ patientId, timeRange, onAnomalyDetected }: PatientVitalsProps) {
  // ...
}

// WRONG
export function PatientVitals(props: any) { ... }
```

---

## Styling: Tailwind CSS + shadcn/ui + Radix UI

- **Tailwind CSS 3+** for all styling; no CSS modules, no styled-components, no inline styles
- **shadcn/ui** as the component library; install components via CLI, customize in `components/ui/`
- **Radix UI** primitives for accessible, unstyled building blocks when shadcn/ui lacks a component
- Maintain a consistent design system via `tailwind.config.ts` theme tokens
- Medical-specific color tokens:

```typescript
// tailwind.config.ts
theme: {
  extend: {
    colors: {
      vitals: {
        normal: "#10b981",     // Green - normal range
        warning: "#f59e0b",    // Amber - borderline
        critical: "#ef4444",   // Red - critical
        offline: "#6b7280",    // Gray - device offline
      },
      severity: {
        low: "#3b82f6",
        medium: "#f59e0b",
        high: "#f97316",
        critical: "#ef4444",
      },
    },
  },
}
```

---

## Server State: React Query (TanStack Query)

All server data fetching uses React Query. Never use `useEffect` + `useState` for data fetching.

```typescript
// hooks/useVitals.ts
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";

export function usePatientVitals(patientId: string, timeRange: TimeRange) {
  return useQuery({
    queryKey: ["vitals", patientId, timeRange],
    queryFn: () => api.vitals.getByPatient(patientId, { timeRange }),
    refetchInterval: 30_000, // Refresh every 30s for monitored patients
    staleTime: 10_000,
  });
}

export function useCreateVitalsReading() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: CreateVitalsRequest) => api.vitals.create(data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ["vitals", variables.patientId] });
    },
  });
}
```

---

## Client State: Zustand

Use Zustand for UI state that does not come from the server.

```typescript
// stores/notificationStore.ts
import { create } from "zustand";

interface NotificationState {
  unreadCount: number;
  notifications: Notification[];
  addNotification: (notification: Notification) => void;
  markAsRead: (id: string) => void;
  clearAll: () => void;
}

export const useNotificationStore = create<NotificationState>((set) => ({
  unreadCount: 0,
  notifications: [],
  addNotification: (notification) =>
    set((state) => ({
      notifications: [notification, ...state.notifications],
      unreadCount: state.unreadCount + 1,
    })),
  markAsRead: (id) =>
    set((state) => ({
      notifications: state.notifications.map((n) =>
        n.id === id ? { ...n, read: true } : n
      ),
      unreadCount: Math.max(0, state.unreadCount - 1),
    })),
  clearAll: () => set({ notifications: [], unreadCount: 0 }),
}));
```

---

## Forms: React Hook Form + Zod

All forms use React Hook Form with Zod schemas for validation.

```typescript
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";

const vitalsFormSchema = z.object({
  heartRate: z.number().min(20).max(300),
  bloodPressureSystolic: z.number().min(50).max(300),
  bloodPressureDiastolic: z.number().min(20).max(200),
  temperature: z.number().min(90).max(115),
  oxygenSaturation: z.number().min(0).max(100),
  notes: z.string().max(500).optional(),
});

type VitalsFormData = z.infer<typeof vitalsFormSchema>;

export function VitalsEntryForm({ patientId }: { patientId: string }) {
  const form = useForm<VitalsFormData>({
    resolver: zodResolver(vitalsFormSchema),
  });
  // ...
}
```

---

## Charts: Recharts + D3.js

- **Recharts** for standard vitals charts (line, area, bar)
- **D3.js** only for custom visualizations that Recharts cannot handle
- All charts must be responsive and accessible
- Include proper axis labels, units, and legends

```typescript
// components/charts/vitals-line-chart.tsx
interface VitalsLineChartProps {
  readings: VitalsReading[];
  metric: "heartRate" | "bloodPressure" | "temperature" | "oxygenSaturation";
  normalRange: { min: number; max: number };
  height?: number;
}

export function VitalsLineChart({ readings, metric, normalRange, height = 300 }: VitalsLineChartProps) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={readings}>
        <ReferenceArea y1={normalRange.min} y2={normalRange.max} fill="#10b981" fillOpacity={0.1} />
        <Line type="monotone" dataKey={metric} stroke="#3b82f6" dot={false} />
        <XAxis dataKey="timestamp" tickFormatter={formatTime} />
        <YAxis domain={["auto", "auto"]} />
        <Tooltip content={<VitalsTooltip />} />
      </LineChart>
    </ResponsiveContainer>
  );
}
```

---

## Real-Time Updates: Socket.IO Client

```typescript
// lib/socket.ts
import { io, Socket } from "socket.io-client";

let socket: Socket | null = null;

export function getSocket(token: string): Socket {
  if (!socket) {
    socket = io(process.env.NEXT_PUBLIC_WS_URL!, {
      auth: { token },
      transports: ["websocket"],
    });
  }
  return socket;
}

// hooks/useWebSocket.ts
export function useVitalsSocket(patientId: string, onUpdate: (reading: VitalsReading) => void) {
  const { data: session } = useSession();

  useEffect(() => {
    if (!session?.accessToken) return;

    const socket = getSocket(session.accessToken);
    socket.emit("subscribe_vitals", { patient_id: patientId });

    socket.on("vitals_update", (data: VitalsReading) => {
      if (data.patientId === patientId) {
        onUpdate(data);
      }
    });

    return () => {
      socket.emit("unsubscribe_vitals", { patient_id: patientId });
      socket.off("vitals_update");
    };
  }, [patientId, session?.accessToken, onUpdate]);
}
```

---

## Voice: Web Speech API

```typescript
// hooks/useVoice.ts
export function useVoiceInput() {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState("");
  const recognitionRef = useRef<SpeechRecognition | null>(null);

  const startListening = useCallback(() => {
    const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = "en-US";
    recognitionRef.current = recognition;
    // ... handlers
    recognition.start();
    setIsListening(true);
  }, []);

  return { isListening, transcript, startListening, stopListening };
}
```

---

## Video: Daily.co SDK

All telemedicine video calls use the Daily.co SDK via WebRTC.

```typescript
// hooks/useTelemedicine.ts
import DailyIframe, { DailyCall } from "@daily-co/daily-js";

export function useTelemedicineCall(roomUrl: string) {
  const callRef = useRef<DailyCall | null>(null);

  const joinCall = useCallback(async () => {
    const call = DailyIframe.createCallObject();
    await call.join({ url: roomUrl });
    callRef.current = call;
  }, [roomUrl]);

  const leaveCall = useCallback(async () => {
    await callRef.current?.leave();
    callRef.current?.destroy();
    callRef.current = null;
  }, []);

  return { joinCall, leaveCall, callRef };
}
```

---

## PDF: react-pdf

Use react-pdf for rendering medical reports and lab results inline.

---

## Notifications: react-hot-toast + Web Push API

- **react-hot-toast** for in-app toast notifications (vitals alerts, appointment reminders, system messages)
- **Web Push API** for browser push notifications when the app is in the background
- Critical medical alerts (e.g., abnormal vitals) must use both toast and push notifications to ensure delivery

---

## Internationalization: next-intl

- **next-intl** for all user-facing text; no hardcoded strings in components
- Use message keys organized by feature area (e.g., `vitals.heartRate`, `appointments.upcoming`)
- Default locale is `en`; support additional locales as configured per hospital deployment

---

## Authentication: NextAuth.js

```typescript
// lib/auth.ts
import NextAuth from "next-auth";
import CredentialsProvider from "next-auth/providers/credentials";

export const { handlers, signIn, signOut, auth } = NextAuth({
  providers: [
    CredentialsProvider({
      async authorize(credentials) {
        const res = await fetch(`${API_URL}/api/v1/auth/login`, {
          method: "POST",
          body: JSON.stringify(credentials),
          headers: { "Content-Type": "application/json" },
        });
        if (!res.ok) return null;
        return res.json();
      },
    }),
  ],
  callbacks: {
    async jwt({ token, user }) {
      if (user) {
        token.accessToken = user.accessToken;
        token.role = user.role;
      }
      return token;
    },
    async session({ session, token }) {
      session.accessToken = token.accessToken as string;
      session.user.role = token.role as UserRole;
      return session;
    },
  },
});
```

---

## Directory Structure - Route Groups

```
app/
├── (auth)/                    # Public auth pages (no sidebar/nav)
│   ├── login/page.tsx
│   ├── register/page.tsx
│   └── forgot-password/page.tsx
├── (patient)/                 # Patient Portal (patient role)
│   ├── layout.tsx             # Patient sidebar + nav
│   ├── dashboard/page.tsx
│   ├── vitals/page.tsx
│   ├── reports/page.tsx
│   ├── medications/page.tsx
│   ├── appointments/page.tsx
│   ├── chat/page.tsx
│   └── telemedicine/[sessionId]/page.tsx
├── (doctor)/                  # Doctor Dashboard (doctor, nurse roles)
│   ├── layout.tsx             # Doctor sidebar + nav
│   ├── dashboard/page.tsx
│   ├── patients/
│   │   ├── page.tsx           # Patient list
│   │   └── [patientId]/page.tsx  # Patient detail
│   ├── appointments/page.tsx
│   ├── telemedicine/[sessionId]/page.tsx
│   └── analytics/page.tsx
└── (admin)/                   # Admin Panel (admin role)
    ├── layout.tsx             # Admin sidebar + nav
    ├── dashboard/page.tsx
    ├── users/page.tsx
    ├── devices/page.tsx
    ├── audit-logs/page.tsx
    └── settings/page.tsx
```

---

## Component Patterns

### Server Components (Default)

```typescript
// app/(patient)/vitals/page.tsx - Server Component
import { auth } from "@/lib/auth";
import { VitalsOverview } from "@/components/vitals/vitals-overview";

export default async function VitalsPage() {
  const session = await auth();
  if (!session) redirect("/login");

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">My Vitals</h1>
      <VitalsOverview patientId={session.user.id} />
    </div>
  );
}
```

### Client Components (Interactive)

```typescript
// components/vitals/vitals-overview.tsx
"use client";

import { usePatientVitals } from "@/hooks/useVitals";
import { useVitalsSocket } from "@/hooks/useWebSocket";
import { VitalsLineChart } from "@/components/charts/vitals-line-chart";

interface VitalsOverviewProps {
  patientId: string;
}

export function VitalsOverview({ patientId }: VitalsOverviewProps) {
  const [timeRange, setTimeRange] = useState<TimeRange>("24h");
  const { data: vitals, isLoading } = usePatientVitals(patientId, timeRange);

  useVitalsSocket(patientId, (newReading) => {
    queryClient.setQueryData(["vitals", patientId, timeRange], (old) => [newReading, ...old]);
  });

  if (isLoading) return <VitalsSkeleton />;

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      <VitalsLineChart readings={vitals} metric="heartRate" normalRange={{ min: 60, max: 100 }} />
      <VitalsLineChart readings={vitals} metric="oxygenSaturation" normalRange={{ min: 95, max: 100 }} />
    </div>
  );
}
```

---

## Accessibility (WCAG 2.1 AA)

- All interactive elements must be keyboard-navigable
- All images must have alt text; medical images include descriptive alt text
- Color is never the sole indicator of status (always pair with icon/text)
- Focus traps on modals and dialogs
- Announce dynamic content changes with `aria-live` regions
- Minimum contrast ratio: 4.5:1 for text, 3:1 for large text
- Critical alerts use `role="alert"` for screen reader announcement

---

## File Naming Conventions

| Type              | Convention            | Example                        |
|-------------------|-----------------------|--------------------------------|
| Component file    | kebab-case.tsx        | `vitals-line-chart.tsx`        |
| Page file         | `page.tsx`            | `app/(patient)/vitals/page.tsx`|
| Layout file       | `layout.tsx`          | `app/(doctor)/layout.tsx`      |
| Hook file         | camelCase.ts          | `usePatientVitals.ts`          |
| Utility file      | camelCase.ts          | `formatVitals.ts`              |
| Store file        | camelCase.ts          | `notificationStore.ts`         |
| Type file         | camelCase.ts          | `apiTypes.ts`                  |
| Test file         | kebab-case.test.tsx   | `vitals-line-chart.test.tsx`   |
| Constant file     | camelCase.ts          | `vitalRanges.ts`               |

---

## Testing: Jest + React Testing Library + Cypress

- **Jest + RTL** for unit and component tests
- **Cypress** for end-to-end tests
- Test files co-located next to source or in `__tests__/`
- Minimum 80% coverage for components
- E2E tests for critical flows: login, vitals entry, symptom chat, telemedicine join

```typescript
// components/vitals/__tests__/vitals-line-chart.test.tsx
import { render, screen } from "@testing-library/react";
import { VitalsLineChart } from "../vitals-line-chart";

describe("VitalsLineChart", () => {
  it("renders chart with readings", () => {
    render(
      <VitalsLineChart
        readings={mockReadings}
        metric="heartRate"
        normalRange={{ min: 60, max: 100 }}
      />
    );
    expect(screen.getByRole("img", { name: /heart rate chart/i })).toBeInTheDocument();
  });

  it("highlights anomalous readings", () => {
    const anomalousReadings = [{ ...mockReadings[0], heartRate: 180 }];
    render(
      <VitalsLineChart readings={anomalousReadings} metric="heartRate" normalRange={{ min: 60, max: 100 }} />
    );
    // Assert anomaly indicator is present
  });
});
```
