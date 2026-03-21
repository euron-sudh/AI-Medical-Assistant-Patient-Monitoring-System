# Operations Rules for MedAssist AI

## Environments

| Environment | Purpose | URL |
|-------------|---------|-----|
| **dev** | Local development | `localhost` (Flask :5000, Next.js :3000) |
| **staging** | Pre-production validation | `staging.medassist.example.com` |
| **prod** | Live healthcare environment | `app.medassist.example.com` |

**CRITICAL: Never share databases between environments. Each environment has fully isolated data stores.**

## Docker Compose Services

All local development runs via Docker Compose with these services:

| Service | Image / Build | Port | Notes |
|---------|--------------|------|-------|
| `flask-backend` | Build from `./backend` | 5000 | Flask 3+ API server |
| `next-frontend` | Build from `./frontend` | 3000 | Next.js 14+ app |
| `postgres` | `postgres:16` | 5432 | Primary relational DB |
| `redis` | `redis:7` | 6379 | Cache, sessions, pub/sub |
| `influxdb` | `influxdb:2` | 8086 | Time-series vitals data |
| `elasticsearch` | `elasticsearch:8` | 9200 | Search and log indexing |
| `minio` | `minio/minio` | 9000 | S3-compatible object storage |
| `celery-worker` | Build from `./backend` | -- | Async task processing |

Run locally:
```bash
docker compose up --build
```

## AWS Production Architecture

- **Orchestration**: Amazon EKS (Kubernetes)
- **Database**: Amazon RDS PostgreSQL 16 (Multi-AZ, encrypted at rest)
- **Cache**: Amazon ElastiCache Redis 7 (cluster mode)
- **Object Storage**: Amazon S3 (medical records, reports, audio/video recordings)
- **CDN**: Amazon CloudFront (frontend assets, static content)
- **API Gateway**: Kong or Nginx (rate limiting, auth, routing)
- **Time-Series**: InfluxDB on EKS (patient vitals)
- **Search**: Elasticsearch on EKS (medical knowledge base, logs)

## CI/CD Pipeline

GitHub Actions is the CI/CD platform. Pipeline stages:

1. **Lint & Type Check** -- ruff, mypy, eslint, tsc
2. **Unit Tests** -- pytest, jest
3. **Integration Tests** -- against Docker Compose services
4. **Security Scan** -- Trivy (containers), Bandit (Python), SAST
5. **Build & Push** -- Docker images to ECR
6. **Deploy Staging** -- automatic on `main` merge
7. **Deploy Prod** -- manual approval required

## Infrastructure as Code

All infrastructure is managed with **Terraform**.

- Terraform state stored in S3 with DynamoDB locking.
- All changes go through PR review before `terraform apply`.
- Never modify infrastructure manually in the AWS console.
- Use workspaces or directory structure to separate staging/prod.

## Health Checks

Every service exposes a **`GET /health`** endpoint returning:

```json
{
  "status": "healthy",
  "service": "flask-backend",
  "version": "1.2.3",
  "timestamp": "2026-03-16T12:00:00Z",
  "dependencies": {
    "postgres": "healthy",
    "redis": "healthy",
    "influxdb": "healthy"
  }
}
```

- Kubernetes liveness and readiness probes point to `/health`.
- Unhealthy dependency should degrade gracefully, not crash the service.

## Database Migrations

- Use **Alembic** for all PostgreSQL schema changes.
- Every migration must have a corresponding downgrade path.
- Never modify a migration that has been applied to staging or prod.
- Run migrations as a separate Kubernetes Job before deployment.

```bash
flask db upgrade    # Apply migrations
flask db downgrade  # Rollback one step
```

## Secrets Management

- **AWS Secrets Manager** for production secrets (DB credentials, API keys, encryption keys).
- **HashiCorp Vault** as an alternative for on-prem or hybrid deployments.
- Never commit secrets to git. Use `.env` files locally (git-ignored).
- Rotate secrets on a regular schedule. OpenAI API keys rotate quarterly.

## Scaling Rules

- **Backend is stateless.** No in-memory session state. All state lives in PostgreSQL, Redis, or S3.
- Scale Flask backend horizontally via EKS HPA (Horizontal Pod Autoscaler).
- Celery workers scale independently based on queue depth.
- Use Redis for session storage and distributed locking.
- Frontend is statically exported where possible; CDN handles scale.
