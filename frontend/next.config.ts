import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  images: {
    domains: [
      'cdn.futwiz.com',
      'sortitoutsidospaces.b-cdn.net',
      'b.fssta.com',
      'ui-avatars.com',
      // Add other image domains from your cache
    ],
  },
  // Enable CORS
  async headers() {
    return [
      {
        source: '/api/:path*',
        headers: [
          { key: 'Access-Control-Allow-Origin', value: '*' },
        ],
      },
    ];
  },
  typescript: {
    ignoreBuildErrors: true,
  },
  eslint: {
    ignoreDuringBuilds: true,
  }
};



export default nextConfig;