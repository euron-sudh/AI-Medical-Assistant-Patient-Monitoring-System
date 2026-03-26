#!/usr/bin/env bash
# =============================================================================
# MedAssist AI — Build & Deploy to GCP
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "${SCRIPT_DIR}")"

# Load GCP outputs if available
if [ -f "${PROJECT_ROOT}/.gcp-outputs" ]; then
    source "${PROJECT_ROOT}/.gcp-outputs"
fi

# Configuration (override via env or .gcp-outputs)
PROJECT_ID="${GCP_PROJECT_ID:-medassist-ai-prod}"
REGION="${GCP_REGION:-us-central1}"
ZONE="${GCP_ZONE:-us-central1-a}"
VM_NAME="${VM_NAME:-medassist-vm}"
REGISTRY_URL="${REGISTRY_URL:-${REGION}-docker.pkg.dev/${PROJECT_ID}/medassist}"
IMAGE_TAG="${IMAGE_TAG:-$(git -C "${PROJECT_ROOT}" rev-parse --short HEAD 2>/dev/null || echo 'latest')}"
VM_IP="${VM_IP:-}"

echo "============================================"
echo "  MedAssist AI — Deploy"
echo "  Tag: ${IMAGE_TAG}"
echo "============================================"

# ─── Step 1: Authenticate Docker with Artifact Registry ──────────────────────
echo ""
echo ">>> Step 1: Authenticating Docker with Artifact Registry..."
gcloud auth configure-docker "${REGION}-docker.pkg.dev" --quiet

# ─── Step 2: Build Docker images ─────────────────────────────────────────────
echo ""
echo ">>> Step 2: Building Docker images..."

# Determine API URL
if [ -n "${VM_IP}" ]; then
    API_URL="http://${VM_IP}/api/v1"
    SOCKET_URL="http://${VM_IP}"
else
    API_URL="${NEXT_PUBLIC_API_URL:-http://localhost/api/v1}"
    SOCKET_URL="${NEXT_PUBLIC_SOCKET_URL:-http://localhost}"
fi

echo "    Building backend..."
docker build \
    -t "${REGISTRY_URL}/backend:${IMAGE_TAG}" \
    -t "${REGISTRY_URL}/backend:latest" \
    -f "${PROJECT_ROOT}/backend/Dockerfile.prod" \
    "${PROJECT_ROOT}/backend"

echo "    Building frontend..."
docker build \
    -t "${REGISTRY_URL}/frontend:${IMAGE_TAG}" \
    -t "${REGISTRY_URL}/frontend:latest" \
    -f "${PROJECT_ROOT}/frontend/Dockerfile.prod" \
    --build-arg "NEXT_PUBLIC_API_URL=${API_URL}" \
    --build-arg "NEXT_PUBLIC_SOCKET_URL=${SOCKET_URL}" \
    "${PROJECT_ROOT}/frontend"

echo "    Images built."

# ─── Step 3: Push images ─────────────────────────────────────────────────────
echo ""
echo ">>> Step 3: Pushing images to Artifact Registry..."
docker push "${REGISTRY_URL}/backend:${IMAGE_TAG}"
docker push "${REGISTRY_URL}/backend:latest"
docker push "${REGISTRY_URL}/frontend:${IMAGE_TAG}"
docker push "${REGISTRY_URL}/frontend:latest"
echo "    Images pushed."

# ─── Step 4: Deploy to VM ────────────────────────────────────────────────────
echo ""
echo ">>> Step 4: Deploying to VM..."

# Copy production files to VM
echo "    Uploading config files..."
gcloud compute scp \
    "${PROJECT_ROOT}/docker-compose.prod.yml" \
    "${VM_NAME}:/opt/medassist/docker-compose.prod.yml" \
    --zone="${ZONE}" --project="${PROJECT_ID}"

gcloud compute scp \
    "${PROJECT_ROOT}/.env.prod" \
    "${VM_NAME}:/opt/medassist/.env.prod" \
    --zone="${ZONE}" --project="${PROJECT_ID}"

gcloud compute scp --recurse \
    "${PROJECT_ROOT}/nginx" \
    "${VM_NAME}:/opt/medassist/" \
    --zone="${ZONE}" --project="${PROJECT_ID}"

# Pull and restart on VM
echo "    Pulling images and restarting services..."
gcloud compute ssh "${VM_NAME}" --zone="${ZONE}" --project="${PROJECT_ID}" --command="
    cd /opt/medassist

    # Configure Docker auth
    gcloud auth configure-docker ${REGION}-docker.pkg.dev --quiet 2>/dev/null || true

    # Set registry URL for compose
    export REGISTRY_URL='${REGISTRY_URL}'
    export IMAGE_TAG='${IMAGE_TAG}'

    # Pull latest images
    docker compose -f docker-compose.prod.yml pull

    # Restart services (zero-downtime for nginx)
    docker compose -f docker-compose.prod.yml up -d --remove-orphans

    # Cleanup old images
    docker image prune -f

    # Show status
    echo ''
    echo 'Container status:'
    docker compose -f docker-compose.prod.yml ps
"

# ─── Step 5: Health check ────────────────────────────────────────────────────
echo ""
echo ">>> Step 5: Running health check..."
sleep 10

if [ -n "${VM_IP}" ]; then
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://${VM_IP}/health" --max-time 10 2>/dev/null || echo "000")
    if [ "${HTTP_CODE}" = "200" ]; then
        echo "    Health check PASSED (HTTP ${HTTP_CODE})"
    else
        echo "    Health check returned HTTP ${HTTP_CODE} — services may still be starting."
        echo "    Try: curl http://${VM_IP}/health"
    fi
    echo ""
    echo "============================================"
    echo "  DEPLOYMENT COMPLETE"
    echo "  App URL: http://${VM_IP}"
    echo "  API URL: http://${VM_IP}/api/v1/health/"
    echo "============================================"
else
    echo "    VM_IP not set — check manually after deployment."
fi
