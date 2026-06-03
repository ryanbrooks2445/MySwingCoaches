import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "MySwingCoaches — AI Golf Swing Analysis",
  description: "Upload your swing. Get a coach-level breakdown in minutes.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen antialiased">{children}</body>
    </html>
  );
}
