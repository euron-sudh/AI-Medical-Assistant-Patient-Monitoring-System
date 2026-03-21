export default function PlatformMetricsPage() {
  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Platform Metrics</h1>
        <p className="mt-1 text-muted-foreground">
          Usage statistics and platform analytics across all users and services.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-lg border border-border bg-card p-4 shadow-sm">
          <h4 className="text-sm font-medium text-muted-foreground">Active Users (DAU)</h4>
          <p className="mt-2 text-3xl font-bold text-foreground">--</p>
          <p className="mt-1 text-xs text-muted-foreground">Daily active users</p>
        </div>
        <div className="rounded-lg border border-border bg-card p-4 shadow-sm">
          <h4 className="text-sm font-medium text-muted-foreground">Weekly Active (WAU)</h4>
          <p className="mt-2 text-3xl font-bold text-foreground">--</p>
          <p className="mt-1 text-xs text-muted-foreground">Weekly active users</p>
        </div>
        <div className="rounded-lg border border-border bg-card p-4 shadow-sm">
          <h4 className="text-sm font-medium text-muted-foreground">Monthly Active (MAU)</h4>
          <p className="mt-2 text-3xl font-bold text-foreground">--</p>
          <p className="mt-1 text-xs text-muted-foreground">Monthly active users</p>
        </div>
        <div className="rounded-lg border border-border bg-card p-4 shadow-sm">
          <h4 className="text-sm font-medium text-muted-foreground">Total Users</h4>
          <p className="mt-2 text-3xl font-bold text-foreground">40</p>
          <p className="mt-1 text-xs text-muted-foreground">Registered accounts</p>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <div className="rounded-lg border border-border bg-card shadow-sm">
          <div className="border-b border-border px-6 py-4">
            <h3 className="text-lg font-semibold text-foreground">Feature Adoption</h3>
          </div>
          <div className="p-6">
            <div className="space-y-4">
              {[
                { name: "Appointments", count: 110, color: "bg-blue-500" },
                { name: "Vitals Logging", count: 100, color: "bg-green-500" },
                { name: "AI Chat Sessions", count: 100, color: "bg-purple-500" },
                { name: "Symptom Checks", count: 100, color: "bg-amber-500" },
                { name: "Telemedicine", count: 100, color: "bg-red-500" },
                { name: "Care Plans", count: 100, color: "bg-teal-500" },
              ].map((feature) => (
                <div key={feature.name} className="flex items-center gap-3">
                  <span className="w-32 text-sm text-muted-foreground">{feature.name}</span>
                  <div className="flex-1">
                    <div className="h-2 rounded-full bg-muted">
                      <div
                        className={`h-2 rounded-full ${feature.color}`}
                        style={{ width: `${Math.min((feature.count / 110) * 100, 100)}%` }}
                      />
                    </div>
                  </div>
                  <span className="text-sm font-medium text-foreground">{feature.count}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="rounded-lg border border-border bg-card shadow-sm">
          <div className="border-b border-border px-6 py-4">
            <h3 className="text-lg font-semibold text-foreground">Users by Role</h3>
          </div>
          <div className="p-6">
            <div className="space-y-4">
              {[
                { role: "Patients", count: 20, percentage: 50 },
                { role: "Doctors", count: 10, percentage: 25 },
                { role: "Nurses", count: 5, percentage: 12.5 },
                { role: "Admins", count: 3, percentage: 7.5 },
              ].map((item) => (
                <div key={item.role} className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <span className="text-sm text-foreground">{item.role}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-foreground">{item.count}</span>
                    <span className="text-xs text-muted-foreground">({item.percentage}%)</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div className="rounded-lg border border-border bg-card shadow-sm">
        <div className="border-b border-border px-6 py-4">
          <h3 className="text-lg font-semibold text-foreground">API Performance</h3>
        </div>
        <div className="p-6">
          <div className="grid gap-4 md:grid-cols-3">
            <div>
              <p className="text-sm text-muted-foreground">Avg Response Time</p>
              <p className="mt-1 text-2xl font-bold text-foreground">-- ms</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Error Rate</p>
              <p className="mt-1 text-2xl font-bold text-green-600">-- %</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Uptime</p>
              <p className="mt-1 text-2xl font-bold text-green-600">-- %</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
