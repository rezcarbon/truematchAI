/** @type {import('next').NextConfig} */
const nextConfig = {
  // Recruiter pages use mock data - skip static generation
  output: 'standalone',
  experimental: {
    dynamicIO: true,
  },
}

module.exports = nextConfig
