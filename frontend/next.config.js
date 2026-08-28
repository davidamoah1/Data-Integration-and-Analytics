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
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || process.env.API_BACKEND_URL || 'https://data-integration-and-analytics.onrender.com';
    const backendUrl = apiUrl && apiUrl.startsWith('http')
      ? apiUrl.replace(/\/$/, '')
      : process.env.NODE_ENV === 'development'
        ? 'http://127.0.0.1:8000'
        : '';

    // When backendUrl is empty (same-origin Vercel), route directly to the
    // Python serverless function at /api/index.py. Vercel preserves the
    // original request path so the ASGI app sees e.g. /analytics/dashboards.
    // When NEXT_PUBLIC_API_URL is set to a Render URL (e.g. https://dataflow-api.onrender.com),
    // all API requests proxy to the Render backend instead.
    const pyFn = '/api/index.py';

    const rootPaths = ['/docs', '/openapi.json', '/health', '/ready'];

    // All API calls are prefixed with /api/ by the client, so we only need
    // a single rewrite to route them to the Python serverless function.
    // Non-/api/ prefixed paths (e.g. /studios, /datasets, /analytics) are
    // served by Next.js page routes without conflict.
    const beforeFileRewrites = [
      // General /api/ prefix (all backend routes)
      { source: '/api/:path*', destination: backendUrl ? `${backendUrl}/api/:path*` : pyFn },
      // Root-level endpoints
      ...rootPaths.map(source => ({
        source,
        destination: backendUrl ? `${backendUrl}${source}` : pyFn,
      })),
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
