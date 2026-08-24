const withPWA = require('@ducanh2912/next-pwa').default({
  dest: 'public',
  cacheOnFrontEndNav: true,
  aggressiveFrontEndNavCaching: true,
  reloadOnOnline: true,
  disable: process.env.NODE_ENV === 'development',
  workboxOptions: {
    disableDevLogs: true,
  },
});

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  poweredByHeader: false,
  skipTrailingSlashRedirect: true,
  output: process.env.NODE_ENV === 'production' ? 'standalone' : undefined,
  // @ducanh2912/next-pwa injects webpack config; Turbopack (default in Next 16)
  // is not compatible with it. Build/dev scripts explicitly pass --webpack,
  // so this empty key just silences the Turbopack/webpack conflict warning.
  turbopack: {},
  experimental: {
    optimizePackageImports: ['lucide-react'],
    workerThreads: false,
    cpus: 1,
  },
  async rewrites() {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || '';
    const backendUrl = apiUrl && apiUrl.startsWith('http')
      ? apiUrl.replace(/\/$/, '')
      : process.env.NODE_ENV === 'development'
        ? 'http://127.0.0.1:8000'
        : '';
    if (!backendUrl) return [];

    const beforeFileRewrites = [
      // Specific backend paths that don't use /api/ prefix on the backend
      { source: '/api/datasets', destination: `${backendUrl}/datasets/` },
      { source: '/api/datasets/:path*', destination: `${backendUrl}/datasets/:path*` },
      { source: '/api/analytics/:path*', destination: `${backendUrl}/analytics/:path*` },
      { source: '/api/ai/:path*', destination: `${backendUrl}/ai/:path*` },
      { source: '/api/etl/:path*', destination: `${backendUrl}/etl/:path*` },
      { source: '/api/semantic/:path*', destination: `${backendUrl}/semantic/:path*` },
      { source: '/api/validation/:path*', destination: `${backendUrl}/validation/:path*` },
      { source: '/api/dataset-workflow/:path*', destination: `${backendUrl}/dataset-workflow/:path*` },
      { source: '/api/ecosystem/:path*', destination: `${backendUrl}/ecosystem/:path*` },
      { source: '/api/saas/:path*', destination: `${backendUrl}/saas/:path*` },
      { source: '/api/studios/:path*', destination: `${backendUrl}/studios/:path*` },
      { source: '/api/workflow/:path*', destination: `${backendUrl}/workflow/:path*` },
      { source: '/api/reports/:path*', destination: `${backendUrl}/reports/:path*` },
      // General /api/ prefix (backend routes that already use /api/)
      { source: '/api/:path*', destination: `${backendUrl}/api/:path*` },
    ];

    const afterFileRewrites = [];

    return {
      beforeFiles: beforeFileRewrites,
      afterFiles: afterFileRewrites,
      fallback: [],
    };
  },
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          { key: 'X-Content-Type-Options', value: 'nosniff' },
          { key: 'X-Frame-Options', value: 'DENY' },
          { key: 'X-XSS-Protection', value: '1; mode=block' },
          { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
        ],
      },
      {
        source: '/sw.js',
        headers: [
          { key: 'Content-Type', value: 'application/javascript; charset=utf-8' },
          { key: 'Cache-Control', value: 'no-cache, no-store, must-revalidate' },
          { key: 'Service-Worker-Allowed', value: '/' },
        ],
      },
      {
        source: '/manifest.json',
        headers: [
          { key: 'Content-Type', value: 'application/manifest+json' },
        ],
      },
    ];
  },
};

module.exports = withPWA(nextConfig);
