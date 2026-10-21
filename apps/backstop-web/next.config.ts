import type { NextConfig } from "next";

const pages = process.env.GITHUB_PAGES === "true";
const nextConfig: NextConfig = pages
  ? { output: "export", basePath: "/backstop-studionet", trailingSlash: true }
  : {};

export default nextConfig;
