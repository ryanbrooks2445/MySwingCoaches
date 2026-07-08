import type { Metadata } from "next";
import Link from "next/link";
import { PublicHeader } from "@/components/PublicHeader";
import { SimplifiedSwingReport } from "@/components/SimplifiedSwingReport";
import { Button } from "@/components/ui/Button";
import { EXAMPLE_SIMPLIFIED_REPORT } from "@/lib/example-report";
import { PRICE_PER_ANALYSIS_DISPLAY } from "@/lib/pricing";
import { DISCLAIMER } from "@/lib/utils";

export const metadata: Metadata = {
  title: "Example Swing Analysis — ForeFixed",
  description:
    "See a full anonymized ForeFixed golf swing analysis: one priority, video evidence, feel, drill, and 7-day practice plan.",
};

export default function ExampleReportPage() {
  return (
    <div className="min-h-screen">
      <PublicHeader />
      <main className="mx-auto max-w-3xl px-4 py-8">
        <div className="rounded-xl border border-[var(--color-accent)]/30 bg-emerald-50/60 px-4 py-3 text-sm text-[var(--color-muted)]">
          Anonymized real report example — no account required. This is what you receive after uploading
          your swing.
        </div>

        <header className="mt-8">
          <p className="text-xs font-semibold uppercase tracking-wider text-[var(--color-accent)]">
            Full swing
          </p>
          <h1 className="mt-2 text-3xl font-bold leading-tight tracking-tight">
            Main priority: athletic setup balance
          </h1>
          <p className="mt-2 text-sm text-[var(--color-muted)]">Sample report · anonymized player</p>
        </header>

        <SimplifiedSwingReport report={EXAMPLE_SIMPLIFIED_REPORT} />

        <div className="mt-10 rounded-2xl border border-[var(--color-border)] bg-[var(--color-card)] p-6 text-center">
          <h2 className="text-xl font-semibold">Ready for your own analysis?</h2>
          <p className="mt-2 text-sm text-[var(--color-muted)]">
            Upload one swing and get a personalized plan like this in minutes. {PRICE_PER_ANALYSIS_DISPLAY}{" "}
            per analysis.
          </p>
          <Link href="/signup?redirect=/upload" className="mt-5 inline-block">
            <Button size="lg">Analyze my swing</Button>
          </Link>
        </div>

        <footer className="mt-10 border-t border-[var(--color-border)] pt-6 text-sm text-[var(--color-muted)]">
          {DISCLAIMER}
        </footer>
      </main>
    </div>
  );
}
