"use client";

import { useState } from "react";
import { AnalysisSectionCards } from "@/components/AnalysisSectionCards";
import { ReportMarkdown } from "@/components/ReportMarkdown";
import { Card } from "@/components/ui/Card";
import { tipAccentClass } from "@/lib/analysis-sections";
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
  const confidencePct = Math.round((adv.confidence_score ?? 0) * 100);
  const showFoundationalLink =
    adv.foundational_missing_piece?.trim() &&
    !adv.foundational_missing_piece.toLowerCase().includes("none — maintain") &&
    !isMaintenance;

  return (
    <div className="mt-8 space-y-10">
      {isMaintenance && (
        <div className="relative overflow-hidden rounded-2xl border border-emerald-500/40 bg-gradient-to-r from-emerald-500/20 via-teal-400/10 to-emerald-500/5 px-5 py-4">
          <p className="text-sm font-medium text-emerald-800 dark:text-emerald-200">
            <span className="mr-2" aria-hidden>
              ⭐
            </span>
            Elite baseline on film — this report celebrates what you’re doing and how to protect it.
          </p>
        </div>
      )}

      <Section
        number={1}
        title="Your analysis"
        subtitle={
          isMaintenance
            ? "What’s working, phase by phase — and what to keep owning."
            : "Setup to finish, your unlock, and what changes when you nail it."
        }
        accentClass="bg-gradient-to-br from-sky-500 to-cyan-600"
      >
        <AnalysisSectionCards content={report.pga_analysis} />
      </Section>

      <Section
        number={2}
        title={isMaintenance ? "What to keep doing" : "Your unlock"}
        subtitle={isMaintenance ? "Anchors that protect this pattern" : "The one move that changes everything"}
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
              {isMaintenance ? "Keep owning this" : "Focus here first"}
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
        title={isMaintenance ? "Feels to protect" : "Feels to train"}
        subtitle="Short cues — say these in your pre-shot routine"
        accentClass="bg-gradient-to-br from-violet-500 to-fuchsia-600"
      >
        <ul className="space-y-3">
          {report.tips_and_feels.map((tip, i) => (
            <li
              key={tip}
              className={cn(
                "rounded-xl border-l-4 px-4 py-3.5 text-sm leading-relaxed shadow-sm",
                tipAccentClass(i)
              )}
            >
              <span className="mr-2 inline-flex h-6 w-6 items-center justify-center rounded-full bg-[var(--color-card)] text-xs font-bold text-[var(--color-accent)] shadow-sm">
                {i + 1}
              </span>
              <ReportMarkdown content={tip} className="inline text-[var(--color-foreground)]" />
            </li>
          ))}
        </ul>
      </Section>

      {report.drills.length > 0 && (
        <Section
          number={4}
          title={isMaintenance ? "Stay sharp" : "Drills that unlock it"}
          subtitle="Rep these until the feel sticks"
          accentClass="bg-gradient-to-br from-[var(--color-accent)] to-green-600"
        >
          <div className="space-y-4">
            {report.drills.map((drill, i) => (
              <Card
                key={drill.name}
                className="overflow-hidden border-[var(--color-accent)]/25 bg-gradient-to-br from-[var(--color-accent)]/8 to-transparent"
              >
                <div className="flex items-start gap-3">
                  <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-[var(--color-accent)]/20 text-sm font-bold text-[var(--color-accent)]">
                    {i + 1}
                  </span>
                  <div className="min-w-0 flex-1">
                    <h3 className="font-semibold text-[var(--color-foreground)]">{drill.name}</h3>
                    <p className="mt-2 text-xs font-semibold uppercase tracking-wide text-emerald-600 dark:text-emerald-400">
                      {isMaintenance ? "Why it keeps you sharp" : "Why this unlocks your game"}
                    </p>
                    <ReportMarkdown content={drill.why_it_helps} className="mt-1 text-sm" />
                    <p className="mt-3 text-xs font-semibold uppercase tracking-wide text-sky-600 dark:text-sky-400">
                      How to do it
                    </p>
                    <ReportMarkdown content={drill.how_to_do_it} className="mt-1 text-sm" />
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </Section>
      )}

      <Section
        number={report.drills.length > 0 ? 5 : 4}
        title="Next swing check"
        subtitle="Film this on your next rep"
        accentClass="bg-gradient-to-br from-indigo-500 to-violet-600"
      >
        <div className="rounded-2xl border border-indigo-500/35 bg-gradient-to-r from-indigo-500/15 via-violet-400/10 to-indigo-500/5 px-5 py-4">
          <ReportMarkdown
            content={report.next_swing_check}
            className="text-base font-medium text-[var(--color-foreground)]"
          />
        </div>
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
              {report.drills.length > 0 ? 6 : 5}
            </span>
            Advanced details
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
