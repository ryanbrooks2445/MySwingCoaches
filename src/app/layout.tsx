import type { Metadata } from "next";
import { Space_Grotesk } from "next/font/google";
import "./globals.css";
import { APP_TITLE } from "@/lib/brand";
import { SiteFooter } from "@/components/SiteFooter";

const spaceGrotesk = Space_Grotesk({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-space-grotesk",
  display: "swap",
});

export const metadata: Metadata = {
  title: APP_TITLE,
  description: "Upload your swing. Get a coach-level breakdown in minutes.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={spaceGrotesk.variable}>
      <body className="flex min-h-screen flex-col antialiased">
        <div className="flex-1">{children}</div>
        <SiteFooter />
      </body>
    </html>
  );
}
