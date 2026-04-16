/** @type {import('next').NextConfig} */
const path = require("path");
const nextConfig = {
  output: "standalone",
  reactStrictMode: true,
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "**",
      },
    ],
  },
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
    NEXT_PUBLIC_SOCKET_URL: process.env.NEXT_PUBLIC_SOCKET_URL,
    NEXT_PUBLIC_DAILY_API_KEY: process.env.NEXT_PUBLIC_DAILY_API_KEY,
    NEXT_PUBLIC_OPENAI_VOICE_API_KEY: process.env.NEXT_PUBLIC_OPENAI_VOICE_API_KEY,
  },
  typescript: {
    // Allow builds to succeed even with TS errors — team is actively fixing types
    ignoreBuildErrors: true,
  },
  eslint: {
    ignoreDuringBuilds: true,
  },
};

module.exports = nextConfig;
