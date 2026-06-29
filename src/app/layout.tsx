import type { Metadata } from "next";
import "./globals.css";
import { APP_TITLE } from "@/lib/brand";
import { SiteFooter } from "@/components/SiteFooter";

export const metadata: Metadata = {
  title: APP_TITLE,
  description: "Upload your swing. Get a coach-level breakdown in minutes.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="flex min-h-screen flex-col antialiased">
        <div className="flex-1">{children}</div>
        <SiteFooter />
      </body>
    </html>
  );
}
