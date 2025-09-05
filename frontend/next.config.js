/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  transpilePackages: ["@excalidraw/excalidraw"],
  webpack: (config) => {
    // Handle canvas module for Excalidraw
    config.externals = config.externals || {};
    config.externals.canvas = "canvas";
    
    return config;
  },
}