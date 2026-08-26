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

    // When backendUrl is empty (same-origin Vercel), route directly to the
    // Python serverless function at /api/index.py. Vercel preserves the
    // original request path so the ASGI app sees e.g. /analytics/dashboards.
    const pyFn = '/api/index.py';

    // Build rewrite entries for a given destination prefix
    const apiPaths = [
      '/analytics/:path*',
      '/datasets/:path*',
      '/datasets',
      '/notifications/:path*',
      '/notifications',
      '/admin/:path*',
      '/ai/:path*',
      '/etl/:path*',
      '/ml/:path*',
      '/monitoring/:path*',
      '/performance/:path*',
      '/platform/:path*',
      '/saas/:path*',
      '/scheduler/:path*',
      '/semantic/:path*',
      '/validation/:path*',
      '/workflows/:path*',
      '/connectors/:path*',
      '/dashboard-engine/:path*',
      '/dataset-workflow/:path*',
      '/departments/:path*',
      '/organizations/:path*',
    ];
    const rootPaths = ['/docs', '/openapi.json', '/health', '/ready'];

    const beforeFileRewrites = [
      // Non-/api prefixed backend paths
      ...apiPaths.map(source => ({
        source,
        destination: backendUrl ? `${backendUrl}${source}` : pyFn,
      })),
      // General /api/ prefix (backend routes that already use /api/)
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
