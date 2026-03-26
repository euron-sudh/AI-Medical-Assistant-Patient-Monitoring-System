#!/usr/bin/env bash
# =============================================================================
# MedAssist AI — GCP Infrastructure Setup (One-Time)
# Uses pbit82@gmail.com GCP account
# =============================================================================
set -euo pipefail

# ─── Configuration ───────────────────────────────────────────────────────────
PROJECT_ID="${GCP_PROJECT_ID:-medassist-ai-prod}"
REGION="us-central1"
ZONE="us-central1-a"
VM_NAME="medassist-vm"
VM_MACHINE_TYPE="e2-standard-2"
CLOUD_SQL_INSTANCE="medassist-db"
CLOUD_SQL_TIER="db-f1-micro"
STORAGE_BUCKET="${PROJECT_ID}-medassist-reports"
ARTIFACT_REPO="medassist"
DB_PASSWORD="${DB_PASSWORD:-$(openssl rand -base64 24 | tr -d '/+=' | head -c 32)}"
NETWORK="medassist-network"

echo "============================================"
echo "  MedAssist AI — GCP Setup"
echo "  Project: ${PROJECT_ID}"
echo "  Region:  ${REGION}"
echo "============================================"

# ─── Step 1: Create project & enable billing ─────────────────────────────────
echo ""
echo ">>> Step 1: Creating GCP project..."
if gcloud projects describe "${PROJECT_ID}" &>/dev/null; then
    echo "    Project ${PROJECT_ID} already exists, skipping."
else
    gcloud projects create "${PROJECT_ID}" --name="MedAssist AI Production"
    echo "    Project created."
fi

gcloud config set project "${PROJECT_ID}"

echo ""
echo ">>> Linking billing account..."
BILLING_ACCOUNT=$(gcloud billing accounts list --format="value(ACCOUNT_ID)" --filter="open=true" | head -n 1)
if [ -z "${BILLING_ACCOUNT}" ]; then
    echo "ERROR: No active billing account found. Please set up billing at https://console.cloud.google.com/billing"
    echo "Then run: gcloud billing projects link ${PROJECT_ID} --billing-account=YOUR_ACCOUNT_ID"
    exit 1
fi
gcloud billing projects link "${PROJECT_ID}" --billing-account="${BILLING_ACCOUNT}" 2>/dev/null || true
echo "    Billing linked: ${BILLING_ACCOUNT}"

# ─── Step 2: Enable APIs ─────────────────────────────────────────────────────
echo ""
echo ">>> Step 2: Enabling GCP APIs..."
gcloud services enable \
    compute.googleapis.com \
    sqladmin.googleapis.com \
    storage.googleapis.com \
    artifactregistry.googleapis.com \
    secretmanager.googleapis.com \
    cloudbuild.googleapis.com \
    --project="${PROJECT_ID}"
echo "    APIs enabled."

# ─── Step 3: Create VPC network ──────────────────────────────────────────────
echo ""
echo ">>> Step 3: Creating VPC network..."
if gcloud compute networks describe "${NETWORK}" --project="${PROJECT_ID}" &>/dev/null; then
    echo "    Network ${NETWORK} already exists."
else
    gcloud compute networks create "${NETWORK}" \
        --project="${PROJECT_ID}" \
        --subnet-mode=auto
    echo "    Network created."
fi

# Firewall: Allow HTTP
gcloud compute firewall-rules create "${NETWORK}-allow-http" \
    --project="${PROJECT_ID}" \
    --network="${NETWORK}" \
    --allow=tcp:80 \
    --source-ranges=0.0.0.0/0 \
    --target-tags=http-server \
    --description="Allow HTTP traffic" 2>/dev/null || true

# Firewall: Allow SSH
gcloud compute firewall-rules create "${NETWORK}-allow-ssh" \
    --project="${PROJECT_ID}" \
    --network="${NETWORK}" \
    --allow=tcp:22 \
    --source-ranges=0.0.0.0/0 \
    --target-tags=ssh-server \
    --description="Allow SSH" 2>/dev/null || true

# Firewall: Allow internal traffic
gcloud compute firewall-rules create "${NETWORK}-allow-internal" \
    --project="${PROJECT_ID}" \
    --network="${NETWORK}" \
    --allow=tcp,udp,icmp \
    --source-ranges=10.128.0.0/9 \
    --description="Allow internal VPC traffic" 2>/dev/null || true

echo "    Firewall rules configured."

# ─── Step 4: Reserve static IP ───────────────────────────────────────────────
echo ""
echo ">>> Step 4: Reserving static IP..."
if gcloud compute addresses describe "${VM_NAME}-ip" --region="${REGION}" --project="${PROJECT_ID}" &>/dev/null; then
    echo "    Static IP already reserved."
else
    gcloud compute addresses create "${VM_NAME}-ip" \
        --region="${REGION}" \
        --project="${PROJECT_ID}"
    echo "    Static IP reserved."
fi
STATIC_IP=$(gcloud compute addresses describe "${VM_NAME}-ip" --region="${REGION}" --project="${PROJECT_ID}" --format="value(address)")
echo "    IP Address: ${STATIC_IP}"

# ─── Step 5: Create Cloud SQL PostgreSQL ──────────────────────────────────────
echo ""
echo ">>> Step 5: Creating Cloud SQL PostgreSQL instance..."
if gcloud sql instances describe "${CLOUD_SQL_INSTANCE}" --project="${PROJECT_ID}" &>/dev/null; then
    echo "    Cloud SQL instance already exists."
else
    gcloud sql instances create "${CLOUD_SQL_INSTANCE}" \
        --project="${PROJECT_ID}" \
        --database-version=POSTGRES_16 \
        --edition=ENTERPRISE \
        --tier="${CLOUD_SQL_TIER}" \
        --region="${REGION}" \
        --storage-type=SSD \
        --storage-size=10GB \
        --storage-auto-increase \
        --backup-start-time=03:00 \
        --availability-type=zonal \
        --assign-ip \
        --authorized-networks="0.0.0.0/0" \
        --database-flags=max_connections=100
    echo "    Cloud SQL instance created."
fi

# Create database
gcloud sql databases create medassist \
    --instance="${CLOUD_SQL_INSTANCE}" \
    --project="${PROJECT_ID}" 2>/dev/null || true

# Set user password
gcloud sql users set-password postgres \
    --instance="${CLOUD_SQL_INSTANCE}" \
    --project="${PROJECT_ID}" \
    --password="${DB_PASSWORD}" 2>/dev/null || true

# Create medassist user
gcloud sql users create medassist \
    --instance="${CLOUD_SQL_INSTANCE}" \
    --project="${PROJECT_ID}" \
    --password="${DB_PASSWORD}" 2>/dev/null || true

CLOUD_SQL_IP=$(gcloud sql instances describe "${CLOUD_SQL_INSTANCE}" --project="${PROJECT_ID}" --format="value(ipAddresses[0].ipAddress)")
echo "    Cloud SQL IP: ${CLOUD_SQL_IP}"

# ─── Step 6: Create Cloud Storage bucket ─────────────────────────────────────
echo ""
echo ">>> Step 6: Creating Cloud Storage bucket..."
if gsutil ls -b "gs://${STORAGE_BUCKET}" &>/dev/null; then
    echo "    Bucket already exists."
else
    gsutil mb -l "${REGION}" -c STANDARD "gs://${STORAGE_BUCKET}"
    gsutil uniformbucketlevelaccess set on "gs://${STORAGE_BUCKET}"
    echo "    Bucket created: gs://${STORAGE_BUCKET}"
fi

# Create HMAC key for S3-compatible access
echo "    Creating HMAC key for S3 compatibility..."
SA_EMAIL=$(gcloud iam service-accounts list --project="${PROJECT_ID}" --format="value(email)" --filter="displayName:Compute Engine default" | head -1)
if [ -z "${SA_EMAIL}" ]; then
    SA_EMAIL="${PROJECT_ID}@appspot.gserviceaccount.com"
fi
HMAC_OUTPUT=$(gsutil hmac create "${SA_EMAIL}" 2>/dev/null || echo "HMAC_EXISTS")
if [ "${HMAC_OUTPUT}" != "HMAC_EXISTS" ]; then
    HMAC_ACCESS_KEY=$(echo "${HMAC_OUTPUT}" | grep "Access ID:" | awk '{print $3}')
    HMAC_SECRET_KEY=$(echo "${HMAC_OUTPUT}" | grep "Secret:" | awk '{print $2}')
    echo "    HMAC Access Key: ${HMAC_ACCESS_KEY}"
    echo "    HMAC Secret Key: (saved — see output below)"
else
    echo "    HMAC key already exists. Check GCP console for keys."
    HMAC_ACCESS_KEY="CHECK_GCP_CONSOLE"
    HMAC_SECRET_KEY="CHECK_GCP_CONSOLE"
fi

# ─── Step 7: Create Artifact Registry ────────────────────────────────────────
echo ""
echo ">>> Step 7: Creating Artifact Registry..."
if gcloud artifacts repositories describe "${ARTIFACT_REPO}" --location="${REGION}" --project="${PROJECT_ID}" &>/dev/null; then
    echo "    Artifact Registry already exists."
else
    gcloud artifacts repositories create "${ARTIFACT_REPO}" \
        --project="${PROJECT_ID}" \
        --repository-format=docker \
        --location="${REGION}" \
        --description="MedAssist AI Docker images"
    echo "    Artifact Registry created."
fi

REGISTRY_URL="${REGION}-docker.pkg.dev/${PROJECT_ID}/${ARTIFACT_REPO}"
echo "    Registry URL: ${REGISTRY_URL}"

# ─── Step 8: Create Compute Engine VM ─────────────────────────────────────────
echo ""
echo ">>> Step 8: Creating Compute Engine VM..."
if gcloud compute instances describe "${VM_NAME}" --zone="${ZONE}" --project="${PROJECT_ID}" &>/dev/null; then
    echo "    VM already exists."
else
    gcloud compute instances create "${VM_NAME}" \
        --project="${PROJECT_ID}" \
        --zone="${ZONE}" \
        --machine-type="${VM_MACHINE_TYPE}" \
        --network="${NETWORK}" \
        --address="${VM_NAME}-ip" \
        --tags=http-server,ssh-server \
        --image-family=ubuntu-2204-lts \
        --image-project=ubuntu-os-cloud \
        --boot-disk-size=30GB \
        --boot-disk-type=pd-ssd \
        --scopes=cloud-platform \
        --metadata=startup-script='#!/bin/bash
# Install Docker
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com | sh
    usermod -aG docker $(whoami)
fi

# Install Docker Compose plugin
if ! docker compose version &> /dev/null; then
    apt-get update && apt-get install -y docker-compose-plugin
fi

# Create app directory
mkdir -p /opt/medassist
chown -R $(whoami):$(whoami) /opt/medassist

# Configure Docker auth for Artifact Registry
gcloud auth configure-docker '${REGION}'-docker.pkg.dev --quiet
'
    echo "    VM created."
fi

# Wait for VM to be ready
echo "    Waiting for VM to be ready..."
sleep 15

# ─── Step 9: Configure Docker auth on VM ─────────────────────────────────────
echo ""
echo ">>> Step 9: Configuring Docker on VM..."
gcloud compute ssh "${VM_NAME}" --zone="${ZONE}" --project="${PROJECT_ID}" --command="
    # Wait for startup script
    while ! command -v docker &> /dev/null; do echo 'Waiting for Docker...'; sleep 5; done
    sudo usermod -aG docker \$(whoami) || true
    # Auth for Artifact Registry
    gcloud auth configure-docker ${REGION}-docker.pkg.dev --quiet 2>/dev/null || true
    mkdir -p /opt/medassist
    echo 'Docker ready!'
" || echo "    SSH may need a moment — try again if it fails."

# ─── Output Summary ──────────────────────────────────────────────────────────
echo ""
echo "============================================"
echo "  GCP SETUP COMPLETE"
echo "============================================"
echo ""
echo "  VM Static IP:      ${STATIC_IP}"
echo "  Cloud SQL IP:      ${CLOUD_SQL_IP}"
echo "  Database Password: ${DB_PASSWORD}"
echo "  Storage Bucket:    gs://${STORAGE_BUCKET}"
echo "  Registry URL:      ${REGISTRY_URL}"
echo "  HMAC Access Key:   ${HMAC_ACCESS_KEY:-CHECK_CONSOLE}"
echo "  HMAC Secret Key:   ${HMAC_SECRET_KEY:-CHECK_CONSOLE}"
echo ""
echo "  Access your app at: http://${STATIC_IP}"
echo ""
echo "  Next steps:"
echo "  1. Copy the above values to .env.prod"
echo "  2. Run: make deploy"
echo "============================================"

# Save outputs to a file for reference
cat > "$(dirname "$0")/../.gcp-outputs" <<ENVEOF
GCP_PROJECT_ID=${PROJECT_ID}
GCP_REGION=${REGION}
GCP_ZONE=${ZONE}
VM_NAME=${VM_NAME}
VM_IP=${STATIC_IP}
CLOUD_SQL_IP=${CLOUD_SQL_IP}
DB_PASSWORD=${DB_PASSWORD}
STORAGE_BUCKET=${STORAGE_BUCKET}
REGISTRY_URL=${REGISTRY_URL}
HMAC_ACCESS_KEY=${HMAC_ACCESS_KEY:-CHECK_CONSOLE}
HMAC_SECRET_KEY=${HMAC_SECRET_KEY:-CHECK_CONSOLE}
ENVEOF
echo "  Outputs saved to .gcp-outputs"
