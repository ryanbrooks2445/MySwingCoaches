import Link from "next/link";
import { CheckCircle2, Sparkles } from "lucide-react";
import { APP_NAME } from "@/lib/brand";
import { PublicHeader } from "@/components/PublicHeader";

const defaultBenefits = [
  "Fixes ranked in priority order — root cause first",
  "Evidence tied to checkpoints in your own video",
  "A feel and drill for every fix on your list",
  "Reports ready in 2–5 minutes",
];

interface AuthLayoutProps {
  children: React.ReactNode;
  asideTitle?: string;
  asideDescription?: string;
  benefits?: string[];
  asideFooter?: React.ReactNode;
}

export function AuthLayout({
  children,
  asideTitle = "Coach-style analysis, on your schedule",
  asideDescription = "Upload one swing and get a prioritized plan you can take straight to the range.",
  benefits = defaultBenefits,
  asideFooter,
}: AuthLayoutProps) {
  return (
    <div className="min-h-screen bg-[var(--color-background)]">
      <PublicHeader />
      <div className="mx-auto grid max-w-6xl lg:min-h-[calc(100vh-4.5rem)] lg:grid-cols-2">
        <div id="main-content" className="flex items-center justify-center px-4 py-12 lg:py-16">
          {children}
        </div>

        <aside className="relative overflow-hidden border-t border-[var(--color-border)] bg-[var(--color-ink)] px-6 py-12 text-white lg:border-l lg:border-t-0 lg:py-16">
          <div aria-hidden className="pointer-events-none absolute inset-0">
            <div
              className="blob absolute -right-16 top-8 h-72 w-72 animate-float-slow"
              style={{ background: "radial-gradient(circle, rgba(16,185,129,0.45), transparent 70%)" }}
            />
            <div
              className="blob absolute bottom-0 left-1/4 h-64 w-64 animate-drift"
              style={{ background: "radial-gradient(circle, rgba(245,158,11,0.3), transparent 70%)" }}
            />
          </div>

          <div className="relative">
            <Link href="/" className="font-display text-lg font-semibold tracking-tight text-white">
              {APP_NAME}
            </Link>

            <p className="mt-8 inline-flex items-center gap-2 rounded-full border border-white/15 bg-white/5 px-4 py-1.5 text-xs font-medium uppercase tracking-widest text-[var(--color-lime)]">
              <Sparkles className="h-3.5 w-3.5" />
              Evidence-based AI swing analysis
            </p>

            <h2 className="mt-6 font-display text-3xl font-bold leading-tight tracking-tight sm:text-4xl">
              {asideTitle}
            </h2>
            <p className="mt-4 leading-relaxed text-white/70">{asideDescription}</p>

            <ul className="mt-10 space-y-4">
              {benefits.map((item) => (
                <li key={item} className="flex gap-3 text-sm text-white/80">
                  <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0 text-[var(--color-lime)]" />
                  <span>{item}</span>
                </li>
              ))}
            </ul>

            {asideFooter && <div className="mt-10">{asideFooter}</div>}
          </div>
        </aside>
      </div>
    </div>
  );
}
