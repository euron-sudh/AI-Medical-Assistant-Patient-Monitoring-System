# Simple single-stage Dockerfile for Render free tier
FROM node:22-alpine

WORKDIR /app

# Copy package files
COPY package.json package-lock.json* ./

# Install all dependencies (including dev for build)
RUN npm install

# Copy source code
COPY . .

# Set build-time env
ENV NEXT_TELEMETRY_DISABLED=1

# Build the app
RUN npm run build

# Production settings
ENV NODE_ENV=production
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

EXPOSE 3000

# Start with next start (not standalone)
CMD ["npm", "start"]
