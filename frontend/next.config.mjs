import createNextIntlPlugin from 'next-intl/plugin';

const withNextIntl = createNextIntlPlugin('./src/i18n/request.ts');

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: process.env.BUILD_TARGET === 'electron' ? 'export' : 'standalone',
  images: {
    unoptimized: process.env.BUILD_TARGET === 'electron',
  },
  experimental: {
    optimizePackageImports: ['lucide-react', 'reactflow'],
  },
  async rewrites() {
    if (process.env.BUILD_TARGET === 'electron') return [];
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    return [
      {
        source: '/api-proxy/:path*',
        destination: `${apiUrl}/api/:path*`,
      },
    ];
  },
};

export default withNextIntl(nextConfig);
