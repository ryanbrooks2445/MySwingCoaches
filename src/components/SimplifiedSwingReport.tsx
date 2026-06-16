"use client";

import { useState } from "react";
import { ReportMarkdown } from "@/components/ReportMarkdown";
import { Card } from "@/components/ui/Card";
import type { SimplifiedSwingReport as SimplifiedReport } from "@/lib/types";
import { cn } from "@/lib/utils";

interface SimplifiedSwingReportProps {
  report: SimplifiedReport;
}

function Section({
  number,
  title,
  subtitle,
  children,
  className,
  accentClass,
}: {
  number: number;
  title: string;
  subtitle?: string;
  children: React.ReactNode;
  className?: string;
  accentClass?: string;
}) {
  return (
    <section className={cn("space-y-4", className)}>
      <div className="flex items-start gap-3">
        <span
          className={cn(
            "flex h-9 w-9 shrink-0 items-center justify-center rounded-xl text-sm font-bold text-white shadow-sm",
            accentClass ?? "bg-[var(--color-accent)]"
          )}
        >
          {number}
        </span>
        <div>
          <h2 className="text-lg font-semibold tracking-tight sm:text-xl">{title}</h2>
          {subtitle && <p className="mt-0.5 text-sm text-[var(--color-muted)]">{subtitle}</p>}
        </div>
      </div>
      {children}
    </section>
  );
}

export function SimplifiedSwingReport({ report }: SimplifiedSwingReportProps) {
  const [advancedOpen, setAdvancedOpen] = useState(false);
  const adv = report.advanced_details;
  const isMaintenance = adv.report_mode === "maintenance";
  const showFoundationalLink = Boolean(adv.foundational_missing_piece?.trim());
  const confidencePct = Math.round((adv.confidence_score ?? 0) * 100);
  const primaryDrill = report.drills[0];
  const feels = report.tips_and_feels.slice(0, 3);
  const plan = [
    "Day 1-2: rehearsal swings only.",
    primaryDrill
      ? "Day 3-4: 15-20 half-speed balls with the drill feel."
      : "Day 3-4: 15-20 half-speed balls with the main feel.",
    "Day 5-6: blend the feel into normal swings.",
    "Day 7: upload the recommended angle.",
  ];

  return (
    <div className="mt-8 space-y-8">
      <Section
        number={1}
        title="Coach Summary"
        accentClass="bg-gradient-to-br from-sky-500 to-cyan-600"
      >
        <Card>
          <ReportMarkdown content={report.pga_analysis} className="leading-relaxed" />
        </Card>
      </Section>

      <Section
        number={2}
        title="Main Swing Leak"
        subtitle="The one thing to fix first"
        accentClass={
          isMaintenance
            ? "bg-gradient-to-br from-teal-500 to-emerald-600"
            : "bg-gradient-to-br from-amber-500 to-orange-600"
        }
      >
        <div
          className={cn(
            "rounded-2xl border p-[1px] shadow-sm",
            isMaintenance ? "border-teal-500/40" : "border-amber-500/45"
          )}
        >
          <div
            className={cn(
              "rounded-[calc(1rem-1px)] bg-gradient-to-br px-5 py-5",
              isMaintenance
                ? "from-teal-500/15 via-emerald-400/5 to-[var(--color-card)]"
                : "from-amber-500/20 via-orange-400/10 to-[var(--color-card)]"
            )}
          >
            <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-[var(--color-muted)]">
              {isMaintenance ? "Keep owning this" : "Primary fix"}
            </p>
            <ReportMarkdown
              content={report.main_fix}
              className="text-base leading-relaxed text-[var(--color-foreground)]"
            />
          </div>
        </div>
      </Section>

      <Section
        number={3}
        title="What To Feel"
        subtitle="Keep this to one pre-shot thought"
        accentClass="bg-gradient-to-br from-violet-500 to-fuchsia-600"
      >
        <ul className="space-y-3">
          {feels.map((tip, i) => (
            <li
              key={tip}
              className="rounded-xl border border-[var(--color-border)] bg-[var(--color-card)] px-4 py-3.5 text-sm leading-relaxed shadow-sm"
            >
              <span className="mr-2 inline-flex h-6 w-6 items-center justify-center rounded-full bg-[var(--color-card)] text-xs font-bold text-[var(--color-accent)] shadow-sm">
                {i + 1}
              </span>
              <ReportMarkdown content={tip} className="inline text-[var(--color-foreground)]" />
            </li>
          ))}
        </ul>
      </Section>

      <Section
        number={4}
        title="Fix-It Drill"
        subtitle="One drill until the move sticks"
        accentClass="bg-gradient-to-br from-[var(--color-accent)] to-green-600"
      >
        <Card className="overflow-hidden border-[var(--color-accent)]/25 bg-gradient-to-br from-[var(--color-accent)]/8 to-transparent">
          <h3 className="font-semibold text-[var(--color-foreground)]">
            {primaryDrill?.name ?? "Main Feel Rehearsal"}
          </h3>
          {primaryDrill?.why_it_helps && (
            <ReportMarkdown content={primaryDrill.why_it_helps} className="mt-2 text-sm" />
          )}
          <p className="mt-3 text-xs font-semibold uppercase tracking-wide text-sky-600 dark:text-sky-400">
            How to do it
          </p>
          <ReportMarkdown
            content={primaryDrill?.how_to_do_it ?? "Make slow rehearsal swings, then hit 15-20 balls at 60% speed with the main feel."}
            className="mt-1 text-sm"
          />
        </Card>
      </Section>

      <Section
        number={5}
        title="7-Day Practice Plan"
        subtitle="Simple reps, then prove it on video"
        accentClass="bg-gradient-to-br from-indigo-500 to-violet-600"
      >
        <Card>
          <ul className="space-y-3 text-sm leading-relaxed">
            {plan.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </Card>
      </Section>

      <Section
        number={6}
        title="Next Upload Goal"
        subtitle="Film this on your next rep"
        accentClass="bg-gradient-to-br from-indigo-500 to-violet-600"
      >
        <Card>
          <ReportMarkdown
            content={report.next_swing_check}
            className="text-base font-medium text-[var(--color-foreground)]"
          />
        </Card>
      </Section>

      <section>
        <button
          type="button"
          onClick={() => setAdvancedOpen((o) => !o)}
          className="flex w-full items-center justify-between rounded-xl border border-[var(--color-border)] bg-[var(--color-card)] px-4 py-3 text-left text-sm font-medium transition-colors hover:bg-[var(--color-border)]/20"
          aria-expanded={advancedOpen}
        >
            <span className="flex items-center gap-3">
              <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-[var(--color-border)] text-sm text-[var(--color-muted)]">
                7
              </span>
            Advanced Evidence
            {adv.report_mode && (
              <span className="text-xs font-normal text-[var(--color-muted)]">({adv.report_mode})</span>
            )}
          </span>
          <span className="text-[var(--color-muted)]">{advancedOpen ? "Hide" : "Show"}</span>
        </button>

        {advancedOpen && (
          <Card className="mt-3 space-y-4 text-sm">
            {showFoundationalLink && (
              <div>
                <p className="text-xs font-medium uppercase text-[var(--color-accent)]">
                  Foundational athletic link
                </p>
                <ReportMarkdown content={adv.foundational_missing_piece!} className="mt-1" />
              </div>
            )}
            {adv.profile_constraints_applied?.trim() && (
              <div>
                <p className="text-xs font-medium uppercase text-[var(--color-muted)]">
                  Adapted for your body
                </p>
                <ReportMarkdown content={adv.profile_constraints_applied} className="mt-1" />
              </div>
            )}
            {adv.diagnostic_checkpoints && adv.diagnostic_checkpoints.length > 0 && (
              <div>
                <p className="text-xs font-medium uppercase text-[var(--color-muted)]">
                  Checkpoint map (coach view)
                </p>
                <ul className="mt-2 space-y-2 text-[var(--color-muted)]">
                  {adv.diagnostic_checkpoints.map((c) => (
                    <li key={c.checkpoint} className="border-l-2 border-[var(--color-border)] pl-3">
                      <span className="font-medium text-[var(--color-foreground)]">{c.checkpoint}</span>
                      <p className="mt-0.5 text-sm">{c.observation}</p>
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {!isMaintenance && adv.root_cause?.trim() && (
              <div>
                <p className="text-xs font-medium uppercase text-[var(--color-muted)]">Root cause</p>
                <ReportMarkdown content={adv.root_cause} className="mt-1" />
              </div>
            )}
            {!isMaintenance && adv.symptom?.trim() && adv.symptom.toLowerCase() !== "n/a" && (
              <div>
                <p className="text-xs font-medium uppercase text-[var(--color-muted)]">Symptom</p>
                <ReportMarkdown content={adv.symptom} className="mt-1" />
              </div>
            )}
            {adv.evidence_metrics.length > 0 && (
              <div>
                <p className="text-xs font-medium uppercase text-[var(--color-muted)]">
                  Evidence on film
                </p>
                <ul className="mt-2 list-disc space-y-1 pl-5 text-[var(--color-muted)]">
                  {adv.evidence_metrics.map((m) => (
                    <li key={m}>{m}</li>
                  ))}
                </ul>
              </div>
            )}
            {!isMaintenance && adv.secondary_fix?.trim() && (
              <div>
                <p className="text-xs font-medium uppercase text-[var(--color-muted)]">
                  Secondary fix
                </p>
                <ReportMarkdown content={adv.secondary_fix} className="mt-1" />
              </div>
            )}
            {!isMaintenance && adv.optional_fix?.trim() && (
              <div>
                <p className="text-xs font-medium uppercase text-[var(--color-muted)]">
                  Optional fix
                </p>
                <ReportMarkdown content={adv.optional_fix} className="mt-1" />
              </div>
            )}
            {!isMaintenance && adv.chain_reaction?.trim() && adv.chain_reaction !== "—" && (
              <div>
                <p className="text-xs font-medium uppercase text-[var(--color-muted)]">
                  Chain reaction
                </p>
                <ReportMarkdown content={adv.chain_reaction} className="mt-1" />
              </div>
            )}
            {!isMaintenance &&
              adv.why_it_caused_the_miss?.trim() &&
              !adv.why_it_caused_the_miss.toLowerCase().startsWith("n/a") && (
                <div>
                  <p className="text-xs font-medium uppercase text-[var(--color-muted)]">
                    Why it caused the miss
                  </p>
                  <ReportMarkdown content={adv.why_it_caused_the_miss} className="mt-1" />
                </div>
              )}
            {adv.next_checkpoint?.trim() && (
              <div>
                <p className="text-xs font-medium uppercase text-[var(--color-muted)]">
                  Next checkpoint
                </p>
                <ReportMarkdown content={adv.next_checkpoint} className="mt-1" />
              </div>
            )}
            <p className="text-xs text-[var(--color-muted)]">Confidence: {confidencePct}%</p>
          </Card>
        )}
      </section>
    </div>
  );
}
