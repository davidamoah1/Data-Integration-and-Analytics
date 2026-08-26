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

    // When backendUrl is empty (same-origin Vercel), we still need rewrites
    // to route API paths to the Python serverless function via vercel.json.
    // Use empty string as destination prefix so paths stay the same.
    const dest = backendUrl || '';

    const beforeFileRewrites = [
      // Non-/api prefixed backend paths — must be in beforeFiles so Next.js
      // page routes don't intercept them and return HTML.
      { source: '/analytics/:path*', destination: `${dest}/analytics/:path*` },
      { source: '/datasets/:path*', destination: `${dest}/datasets/:path*` },
      { source: '/datasets', destination: `${dest}/datasets/` },
      { source: '/notifications/:path*', destination: `${dest}/notifications/:path*` },
      { source: '/notifications', destination: `${dest}/notifications` },
      { source: '/admin/:path*', destination: `${dest}/admin/:path*` },
      { source: '/ai/:path*', destination: `${dest}/ai/:path*` },
      { source: '/etl/:path*', destination: `${dest}/etl/:path*` },
      { source: '/ml/:path*', destination: `${dest}/ml/:path*` },
      { source: '/monitoring/:path*', destination: `${dest}/monitoring/:path*` },
      { source: '/performance/:path*', destination: `${dest}/performance/:path*` },
      { source: '/platform/:path*', destination: `${dest}/platform/:path*` },
      { source: '/saas/:path*', destination: `${dest}/saas/:path*` },
      { source: '/scheduler/:path*', destination: `${dest}/scheduler/:path*` },
      { source: '/semantic/:path*', destination: `${dest}/semantic/:path*` },
      { source: '/validation/:path*', destination: `${dest}/validation/:path*` },
      { source: '/workflows/:path*', destination: `${dest}/workflows/:path*` },
      { source: '/connectors/:path*', destination: `${dest}/connectors/:path*` },
      { source: '/dashboard-engine/:path*', destination: `${dest}/dashboard-engine/:path*` },
      { source: '/dataset-workflow/:path*', destination: `${dest}/dataset-workflow/:path*` },
      { source: '/departments/:path*', destination: `${dest}/departments/:path*` },
      { source: '/organizations/:path*', destination: `${dest}/organizations/:path*` },
      // General /api/ prefix (backend routes that already use /api/)
      { source: '/api/:path*', destination: `${dest}/api/:path*` },
      // Root-level endpoints
      { source: '/docs', destination: `${dest}/docs` },
      { source: '/openapi.json', destination: `${dest}/openapi.json` },
      { source: '/health', destination: `${dest}/health` },
      { source: '/ready', destination: `${dest}/ready` },
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
