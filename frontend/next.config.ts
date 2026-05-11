import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Enables standalone output for Docker — produces a minimal
  // self-contained server in .next/standalone
  output: "standalone",
};

export default nextConfig;
