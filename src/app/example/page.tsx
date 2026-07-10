import type { Metadata } from "next";
import Link from "next/link";
import { ArrowRight, PlayCircle } from "lucide-react";
import { PublicHeader } from "@/components/PublicHeader";
import { PageHero } from "@/components/PageHero";
import { PublicPageBand } from "@/components/PublicPageBand";
import { Reveal } from "@/components/Reveal";
import { SimplifiedSwingReport } from "@/components/SimplifiedSwingReport";
import { Button } from "@/components/ui/Button";
import { EXAMPLE_SIMPLIFIED_REPORT } from "@/lib/example-report";
import { PRICE_PER_ANALYSIS_DISPLAY } from "@/lib/pricing";
import { DISCLAIMER } from "@/lib/utils";

export const metadata: Metadata = {
  title: "Example Swing Analysis — ForeFixed",
  description:
    "See a full anonymized ForeFixed golf swing analysis: one priority, video evidence, feel, and drill.",
};

export default function ExampleReportPage() {
  return (
    <div className="min-h-screen">
      <PublicHeader />
      <PublicPageBand variant="ink">
        <div className="relative mx-auto max-w-3xl px-4 py-14 sm:py-20">
          <Reveal immediate>
            <PageHero
              eyebrow="See it before you buy"
              title="A real, anonymized report"
              description="This is exactly what lands in your account after an upload — your ordered fix list, evidence from film, and drills for each fix."
              dark
            />
          </Reveal>
        </div>
      </PublicPageBand>

      <main id="main-content" className="mx-auto max-w-3xl px-4 py-10 sm:py-14">
        <Reveal immediate>
          <div className="rounded-2xl border border-[var(--color-emerald)]/30 bg-[var(--color-accent-muted)] px-4 py-3 text-sm text-[var(--color-accent-deep)]">
            <PlayCircle className="mr-2 inline h-4 w-4" />
            Anonymized real report example — no account required.
          </div>
        </Reveal>

        <Reveal immediate>
          <header className="mt-8">
            <p className="text-xs font-semibold uppercase tracking-widest text-[var(--color-accent)]">
              Full swing
            </p>
            <h2 className="mt-2 font-display text-3xl font-bold leading-tight tracking-tight">
              Main priority: athletic setup balance
            </h2>
            <p className="mt-2 text-sm text-[var(--color-muted)]">Sample report · anonymized player</p>
          </header>
        </Reveal>

        <Reveal immediate>
          <div className="mt-8">
            <SimplifiedSwingReport report={EXAMPLE_SIMPLIFIED_REPORT} />
          </div>
        </Reveal>

        <Reveal delay={160}>
          <div className="ring-gradient mt-12 rounded-3xl bg-[var(--color-card)] p-8 text-center shadow-xl">
            <h2 className="font-display text-2xl font-bold">Ready for your own analysis?</h2>
            <p className="mx-auto mt-3 max-w-md text-sm leading-relaxed text-[var(--color-muted)]">
              Upload one swing and get a personalized plan like this in minutes.{" "}
              {PRICE_PER_ANALYSIS_DISPLAY} per analysis.
            </p>
            <Link href="/signup?redirect=/upload" className="mt-6 inline-block">
              <Button size="lg" variant="cta" className="group">
                Analyze my swing
                <ArrowRight className="ml-2 h-4 w-4 transition-transform group-hover:translate-x-1" />
              </Button>
            </Link>
          </div>
        </Reveal>

        <footer className="mt-10 border-t border-[var(--color-border)] pt-6 text-sm text-[var(--color-muted)]">
          {DISCLAIMER}
        </footer>
      </main>
    </div>
  );
}
