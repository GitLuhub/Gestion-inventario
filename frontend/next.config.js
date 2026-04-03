/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  reactStrictMode: true,
  swcMinify: true,
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  },
  async rewrites() {
    // API_INTERNAL_URL: hostname Docker interno (server-side, dentro del contenedor)
    // NEXT_PUBLIC_API_URL: IP pública (client-side, navegador)
    const destination = process.env.API_INTERNAL_URL
      || process.env.NEXT_PUBLIC_API_URL
      || 'http://localhost:8000'
    return [
      {
        source: '/api/:path*',
        destination: `${destination}/api/:path*`,
      },
    ]
  },
}

module.exports = nextConfig
