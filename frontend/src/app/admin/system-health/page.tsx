export default function SystemHealthPage() {
  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-foreground">System Health</h1>
        <p className="mt-1 text-muted-foreground">
          Monitor the health and status of all infrastructure components.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {[
          { name: "PostgreSQL", status: "Unknown", description: "Primary relational database" },
          { name: "Redis", status: "Unknown", description: "Cache, sessions, pub/sub" },
          { name: "InfluxDB", status: "Unknown", description: "Time-series vitals data" },
          { name: "Elasticsearch", status: "Unknown", description: "Full-text search" },
          { name: "OpenAI API", status: "Unknown", description: "AI model inference" },
          { name: "Celery Workers", status: "Unknown", description: "Background task processing" },
          { name: "MinIO / S3", status: "Unknown", description: "File and document storage" },
          { name: "Pinecone", status: "Unknown", description: "Vector similarity search" },
        ].map((service) => (
          <div key={service.name} className="rounded-lg border border-border bg-card p-4 shadow-sm">
            <div className="flex items-center justify-between">
              <span className="font-medium text-foreground">{service.name}</span>
              <span className="inline-flex items-center rounded-full bg-gray-100 px-2.5 py-0.5 text-xs font-medium text-gray-600">
                {service.status}
              </span>
            </div>
            <p className="mt-1 text-xs text-muted-foreground">{service.description}</p>
          </div>
        ))}
      </div>

      <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-foreground">Health Check History</h2>
        <p className="mt-2 text-sm text-muted-foreground">
          Historical uptime and health check data will be displayed here with Prometheus metrics
          and Grafana-style visualizations.
        </p>
        <div className="mt-4">
          <span className="inline-flex items-center rounded-full bg-amber-100 px-3 py-1 text-xs font-medium text-amber-800">
            Coming Soon
          </span>
        </div>
      </div>
    </div>
  );
}
