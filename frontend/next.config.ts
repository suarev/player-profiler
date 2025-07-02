import type { NextConfig } from "next";

/** @type {import('next').NextConfig} */
const nextConfig = {
  eslint: {
    // Warning: This allows production builds to successfully complete even if
    // your project has ESLint errors.
    ignoreDuringBuilds: true,
  },
  images: {
    domains: ['cdn.futwiz.com', 'ui-avatars.com', 'b.fssta.com', 'sortitoutsidospaces.b-cdn.net'],
  },
}

module.exports = nextConfig