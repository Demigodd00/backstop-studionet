import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "BACKSTOP — Agent policy regression registry",
  description: "On-chain regression suites for agent policy repairs, independently checked by GenLayer validators.",
  icons: { icon: process.env.GITHUB_PAGES === "true" ? "/backstop-studionet/favicon.svg" : "/favicon.svg" },
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
