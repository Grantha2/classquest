/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // pdf-parse is a CommonJS lib that should only run on the server.
  experimental: {
    serverComponentsExternalPackages: ["pdf-parse"],
  },
  // react-leaflet ships ESM that Next needs to transpile.
  transpilePackages: ["react-leaflet", "@react-leaflet/core"],
};

export default nextConfig;
