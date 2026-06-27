"use client";

import { CoachVerdictCard } from "@/components/CoachVerdictCard";
import { DrillVideoEmbed } from "@/components/DrillVideoEmbed";
import { FeelBlueprintReport } from "@/components/FeelBlueprintReport";
import { ReportMarkdown } from "@/components/ReportMarkdown";
import { Card } from "@/components/ui/Card";
import { DRILL_CATALOG } from "@/lib/drill-videos";
import {
  confidenceBadgeClass,
  confidenceLabel,
  limitationBanners,
  mergeFramesWithPhaseMap,
} from "@/lib/phase-frames";
import type { FeelBlueprintDiagnostic, KeyFrameUrl, PhaseFrame, SimplifiedSwingReport as SimplifiedReport } from "@/lib/types";
import { cn } from "@/lib/utils";
import { useState } from "react";

interface SimplifiedSwingReportProps {
  report: SimplifiedReport;
  feelBlueprint?: FeelBlueprintDiagnostic | null;
  frames?: KeyFrameUrl[];
  phaseMap?: PhaseFrame[];
  drillVideoUrl?: string | null;
  drillVideoTitle?: string | null;
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

function resolveDrillVideo(drillName: string | undefined): { url: string; title: string } | null {
  if (!drillName) return null;
  const slug = drillName.toLowerCase().replace(/\s+/g, "_");
  const entry = DRILL_CATALOG[slug];
  if (entry) return { url: entry.embedUrl, title: entry.title };
  return null;
}

export function SimplifiedSwingReport({
  report,
  feelBlueprint,
  frames = [],
  phaseMap,
  drillVideoUrl,
  drillVideoTitle,
}: SimplifiedSwingReportProps) {
  const [advancedOpen, setAdvancedOpen] = useState(false);
  const adv = report.advanced_details;
  const isMaintenance = adv.report_mode === "maintenance";
  const showFoundationalLink = Boolean(adv.foundational_missing_piece?.trim());
  const primaryDrill = report.drills[0];
  const primaryFeel = report.tips_and_feels[0];
  const mergedFrames = mergeFramesWithPhaseMap(frames, phaseMap);
  const banners = limitationBanners(phaseMap);
  const drillFromCatalog = resolveDrillVideo(primaryDrill?.name);
  const embedUrl = drillVideoUrl ?? drillFromCatalog?.url;
  const embedTitle = drillVideoTitle ?? drillFromCatalog?.title;

  const plan = report.practice_plan?.length
    ? report.practice_plan
    : [
        "Day 1-2: rehearsal swings only.",
        primaryDrill
          ? "Day 3-4: 15-20 half-speed balls with the drill feel."
          : "Day 3-4: 15-20 half-speed balls with the main feel.",
        "Day 5-6: blend the feel into normal swings.",
        "Day 7: upload the recommended angle.",
      ];

  const hasQuickVerdict = /quick coach verdict/i.test(report.pga_analysis);
  const showCoachLetter = Boolean(feelBlueprint) && !report.coach_verdict && !hasQuickVerdict;
  const sectionOffset = showCoachLetter ? 1 : 0;

  return (
    <div className="mt-8 space-y-8">
      {banners.length > 0 && (
        <div className="space-y-2">
          {banners.map((banner) => (
            <div
              key={banner}
              className="rounded-xl border border-amber-500/30 bg-amber-50 px-4 py-3 text-sm text-amber-900"
            >
              {banner}
            </div>
          ))}
        </div>
      )}

      {report.coach_verdict && <CoachVerdictCard verdict={report.coach_verdict} />}

      {showCoachLetter && feelBlueprint && (
        <Section
          number={1}
          title="Your Coach Letter"
          subtitle="Full PGA read on your swing"
          accentClass="bg-emerald-700"
        >
          <FeelBlueprintReport feel={feelBlueprint} />
        </Section>
      )}

      {report.pga_analysis.trim() && (
        <Section
          number={1 + sectionOffset}
          title="Full Swing Analysis"
          subtitle="What your coach saw on film"
          accentClass="bg-emerald-700"
        >
          <Card>
            <ReportMarkdown content={report.pga_analysis} className="leading-relaxed" variant="phases" />
          </Card>
        </Section>
      )}

      <Section
        number={2 + sectionOffset}
        title={isMaintenance ? "Main Priority" : "Main Swing Priority"}
        subtitle="The one thing to change first"
        accentClass={isMaintenance ? "bg-emerald-600" : "bg-amber-600"}
      >
        <div
          className={cn(
            "rounded-lg border shadow-sm",
            isMaintenance ? "border-teal-500/40" : "border-amber-500/45"
          )}
        >
          <div
            className={cn(
              "rounded-lg px-5 py-5",
              isMaintenance ? "bg-emerald-50" : "bg-amber-50"
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
        {!isMaintenance && adv.secondary_fix?.trim() && (
          <Card className="mt-3 border-sky-500/25 bg-sky-50/50">
            <p className="text-xs font-semibold uppercase tracking-wider text-sky-700">
              Secondary focus
            </p>
            <ReportMarkdown content={adv.secondary_fix} className="mt-2 text-sm" />
          </Card>
        )}
      </Section>

      <Section
        number={3 + sectionOffset}
        title="Evidence On Film"
        subtitle="What the camera could verify"
        accentClass="bg-sky-600"
      >
        <Card>
          <ul className="list-disc space-y-2 pl-5 text-sm text-[var(--color-muted)] marker:text-[var(--color-accent)]">
            {adv.evidence_metrics.slice(0, 4).map((evidence) => (
              <li key={evidence}>{evidence}</li>
            ))}
          </ul>
          {mergedFrames.length > 0 && (
            <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-3">
              {mergedFrames
                .filter((frame) => frame.person_visible !== false || (frame.confidence ?? 0) >= 0.35)
                .slice(0, 8)
                .map((frame) => {
                  const label = confidenceLabel(frame.confidence);
                  const dimmed = frame.person_visible === false || label === "Not visible";
                  return (
                    <figure
                      key={frame.phase}
                      className={cn(
                        "overflow-hidden rounded-lg border border-[var(--color-border)]",
                        dimmed && "opacity-50"
                      )}
                    >
                      {frame.url ? (
                        // eslint-disable-next-line @next/next/no-img-element
                        <img
                          src={frame.url}
                          alt={`${frame.phase.replaceAll("_", " ")} swing frame`}
                          className="aspect-[4/3] w-full bg-black object-contain"
                        />
                      ) : null}
                      <figcaption className="flex flex-wrap items-center gap-1 px-2 py-1.5 text-xs text-[var(--color-muted)]">
                        <span className="capitalize">{frame.phase.replaceAll("_", " ")}</span>
                        <span
                          className={cn(
                            "rounded px-1.5 py-0.5 text-[10px] font-semibold uppercase",
                            confidenceBadgeClass(label)
                          )}
                        >
                          {label}
                        </span>
                      </figcaption>
                    </figure>
                  );
                })}
            </div>
          )}
        </Card>
      </Section>

      <Section
        number={4 + sectionOffset}
        title="One Feel"
        subtitle="Use one thought before each rep"
        accentClass="bg-violet-600"
      >
        <Card>
          <ReportMarkdown
            content={primaryFeel || report.main_fix}
            className="text-base font-medium text-[var(--color-foreground)]"
          />
        </Card>
      </Section>

      <Section
        number={5 + sectionOffset}
        title={isMaintenance ? "Pattern Drill" : "Priority Drill"}
        subtitle={isMaintenance ? "Reinforce the pattern you want to keep" : "One drill until the move sticks"}
        accentClass="bg-[var(--color-accent)]"
      >
        <Card className="overflow-hidden border-[var(--color-accent)]/25">
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
            content={
              primaryDrill?.how_to_do_it ??
              "Make slow rehearsal swings, then hit 15-20 balls at 60% speed with the main feel."
            }
            className="mt-1 text-sm"
          />
          {embedUrl && (
            <DrillVideoEmbed videoUrl={embedUrl} title={embedTitle ?? undefined} className="mt-4" />
          )}
        </Card>
      </Section>

      <Section
        number={6 + sectionOffset}
        title="7-Day Practice Plan"
        subtitle="Simple reps, then prove it on video"
        accentClass="bg-indigo-600"
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
        number={7 + sectionOffset}
        title="Next Upload Goal"
        subtitle="Film this on your next rep"
        accentClass="bg-indigo-600"
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
              {8 + sectionOffset}
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
          </Card>
        )}
      </section>
    </div>
  );
}
