import type { Metadata } from "next";
import Script from "next/script";
import { Space_Grotesk } from "next/font/google";
import "./globals.css";
import { APP_NAME, APP_TITLE } from "@/lib/brand";
import { SiteFooter } from "@/components/SiteFooter";

const spaceGrotesk = Space_Grotesk({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-space-grotesk",
  display: "swap",
});

const siteUrl = "https://forefixed.com";
const description =
  "Upload your golf swing. Get a coach-level breakdown with prioritized fixes, evidence from your film, and drills — in minutes.";

export const metadata: Metadata = {
  metadataBase: new URL(siteUrl),
  title: {
    default: APP_TITLE,
    template: `%s — ${APP_NAME}`,
  },
  description,
  applicationName: APP_NAME,
  openGraph: {
    type: "website",
    locale: "en_US",
    url: siteUrl,
    siteName: APP_NAME,
    title: APP_TITLE,
    description,
    images: [
      {
        url: "/marketing/swing-analysis-still.png",
        width: 1200,
        height: 630,
        alt: `${APP_NAME} swing analysis`,
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: APP_TITLE,
    description,
    images: ["/marketing/swing-analysis-still.png"],
  },
  icons: {
    icon: [{ url: "/icon", type: "image/png" }],
    apple: [{ url: "/apple-icon", type: "image/png" }],
  },
};

const plausibleDomain = process.env.NEXT_PUBLIC_PLAUSIBLE_DOMAIN?.trim();

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={spaceGrotesk.variable}>
      <body className="flex min-h-screen flex-col antialiased">
        <a
          href="#main-content"
          className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded-lg focus:bg-[var(--color-ink)] focus:px-4 focus:py-2 focus:text-sm focus:font-medium focus:text-white"
        >
          Skip to content
        </a>
        <div className="flex-1">{children}</div>
        <SiteFooter />
        {plausibleDomain ? (
          <Script
            defer
            data-domain={plausibleDomain}
            src="https://plausible.io/js/script.tagged-events.js"
            strategy="afterInteractive"
          />
        ) : null}
      </body>
    </html>
  );
}
