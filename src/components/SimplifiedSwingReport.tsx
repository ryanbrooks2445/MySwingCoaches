"use client";

import { DrillVideoEmbed } from "@/components/DrillVideoEmbed";
import { PrioritizedFeelsHero } from "@/components/PrioritizedFeelsHero";
import { ReportMarkdown } from "@/components/ReportMarkdown";
import { Card } from "@/components/ui/Card";
import {
  cameraVerifiedSummary,
  filterVisibleCheckpoints,
  filterVisibleEvidence,
  goodVsWorkBlocks,
  hasUsablePhaseCapture,
  resolveBestFix,
  resolveOneFeel,
  usableSwingFrames,
} from "@/lib/report-display";
import { formatPhaseLabel } from "@/lib/status-labels";
import type { KeyFrameUrl, PhaseFrame, SimplifiedSwingReport as SimplifiedReport } from "@/lib/types";

interface SimplifiedSwingReportProps {
  report: SimplifiedReport;
  frames?: KeyFrameUrl[];
  phaseMap?: PhaseFrame[];
  drillVideoUrl?: string | null;
  drillVideoTitle?: string | null;
}

function BlockHeader({ emoji, title }: { emoji: string; title: string }) {
  return (
    <h2 className="flex items-center gap-2 text-lg font-semibold tracking-tight text-[var(--color-foreground)] sm:text-xl">
      <span aria-hidden>{emoji}</span>
      <span>{title}</span>
    </h2>
  );
}

function LabelRow({ label, content }: { label: string; content: string }) {
  return (
    <div>
      <p className="text-xs font-semibold uppercase tracking-wider text-[var(--color-muted)]">{label}</p>
      <ReportMarkdown content={content} className="mt-1 text-sm leading-relaxed text-[var(--color-foreground)]" />
    </div>
  );
}

export function SimplifiedSwingReport({
  report,
  frames = [],
  phaseMap,
  drillVideoUrl,
  drillVideoTitle,
}: SimplifiedSwingReportProps) {
  const adv = report.advanced_details;
  const primaryDrill = report.drills[0];
  const bestFix = resolveBestFix(report);
  const primaryFeel = resolveOneFeel(report.tips_and_feels, bestFix);
  const camera = cameraVerifiedSummary(report, bestFix);
  const visibleEvidence = filterVisibleEvidence(adv.evidence_metrics ?? []);
  const visibleCheckpoints = filterVisibleCheckpoints(adv.diagnostic_checkpoints);
  const showPhaseCapture = hasUsablePhaseCapture(frames, phaseMap);
  const swingFrames = showPhaseCapture ? usableSwingFrames(frames, phaseMap) : [];
  const { working, work } = goodVsWorkBlocks(report.pga_analysis);
  const showCameraVerified = Boolean(
    camera.flaw || camera.impact || camera.working || visibleEvidence.length > 0
  );
  const showStructuredCamera =
    Boolean(camera.flaw || camera.impact || camera.working);
  const showEvidenceLines = visibleEvidence.length > 0 && !showStructuredCamera;

  const showGoodVsWork =
    !showCameraVerified && (working.length > 0 || work.length > 0);
  const showPhaseCheckpoints = showPhaseCapture && visibleCheckpoints.length > 0;
  const hasPriorityHero = (report.priority_fixes?.length ?? 0) >= 2;

  return (
    <div className="mt-8 space-y-8">
      {hasPriorityHero && (
        <PrioritizedFeelsHero
          priorities={report.priority_fixes!}
          drillVideoUrl={drillVideoUrl}
          drillVideoTitle={drillVideoTitle}
        />
      )}

      {!hasPriorityHero && bestFix && bestFix !== "—" && (
        <section className="overflow-hidden rounded-2xl border border-amber-500/35 bg-gradient-to-br from-amber-50 via-white to-orange-50 shadow-sm">
          <div className="px-5 py-5 sm:px-6">
            <BlockHeader emoji="🎯" title="The Best Fix" />
            <ReportMarkdown
              content={bestFix}
              className="mt-3 text-base leading-relaxed text-[var(--color-foreground)]"
            />
          </div>
        </section>
      )}

      {showCameraVerified && (
        <section className="space-y-4">
          <BlockHeader emoji="🎥" title="What the Camera Verified" />
          <Card className="space-y-4">
            {camera.flaw && <LabelRow label="The Flaw" content={camera.flaw} />}
            {camera.impact && <LabelRow label="The Impact" content={camera.impact} />}
            {camera.working && <LabelRow label="What's Working" content={camera.working} />}
            {showEvidenceLines &&
              visibleEvidence.map((line) => (
                <LabelRow key={line} label="On film" content={line} />
              ))}
            {swingFrames.length > 0 && (
              <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
                {swingFrames.slice(0, 6).map((frame) => (
                  <figure
                    key={frame.phase}
                    className="overflow-hidden rounded-lg border border-[var(--color-border)]"
                  >
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img
                      src={frame.url!}
                      alt={`${formatPhaseLabel(frame.phase)} swing frame`}
                      className="aspect-[4/3] w-full bg-black object-contain"
                    />
                    <figcaption className="px-2 py-1.5 text-xs text-[var(--color-muted)]">
                      {formatPhaseLabel(frame.phase)}
                    </figcaption>
                  </figure>
                ))}
              </div>
            )}
          </Card>
        </section>
      )}

      {showGoodVsWork && (
        <section className="space-y-4">
          <BlockHeader emoji="📋" title="The Good vs. The Work" />
          <div className="grid gap-4 sm:grid-cols-2">
            <Card className="border-emerald-500/25 bg-emerald-50/40">
              <p className="text-xs font-semibold uppercase tracking-wider text-emerald-800">The Good</p>
              <ul className="mt-3 space-y-2 text-sm leading-relaxed text-[var(--color-foreground)]">
                {working.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </Card>
            <Card className="border-amber-500/25 bg-amber-50/40">
              <p className="text-xs font-semibold uppercase tracking-wider text-amber-800">The Work</p>
              <ul className="mt-3 space-y-2 text-sm leading-relaxed text-[var(--color-foreground)]">
                {work.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </Card>
          </div>
        </section>
      )}

      {primaryFeel && !hasPriorityHero && (
        <section className="space-y-3">
          <BlockHeader emoji="💡" title="One Feel" />
          <Card>
            <ReportMarkdown
              content={primaryFeel}
              className="text-base font-medium text-[var(--color-foreground)]"
            />
          </Card>
        </section>
      )}

      {primaryDrill && !hasPriorityHero && (
        <section className="space-y-3">
          <BlockHeader
            emoji="🛠️"
            title={`Priority Drill${primaryDrill.name ? `: ${primaryDrill.name}` : ""}`}
          />
          <Card className="border-[var(--color-accent)]/25">
            {primaryDrill.why_it_helps && (
              <>
                <p className="text-xs font-semibold uppercase tracking-wider text-[var(--color-muted)]">Goal</p>
                <ReportMarkdown content={primaryDrill.why_it_helps} className="mt-1 text-sm" />
              </>
            )}
            {primaryDrill.how_to_do_it && (
              <>
                <p className="mt-4 text-xs font-semibold uppercase tracking-wider text-[var(--color-muted)]">
                  How to do it
                </p>
                <ReportMarkdown content={primaryDrill.how_to_do_it} className="mt-1 text-sm" />
              </>
            )}
            {drillVideoUrl && (
              <DrillVideoEmbed
                videoUrl={drillVideoUrl}
                title={drillVideoTitle ?? undefined}
                className="mt-4"
              />
            )}
          </Card>
        </section>
      )}

      {report.next_swing_check.trim() && (
        <section className="space-y-3">
          <BlockHeader emoji="📹" title="Next Upload Goal" />
          <Card>
            <ReportMarkdown
              content={report.next_swing_check}
              className="text-base font-medium text-[var(--color-foreground)]"
            />
          </Card>
        </section>
      )}

      {showPhaseCheckpoints && (
        <details className="rounded-xl border border-[var(--color-border)] bg-[var(--color-card)]">
          <summary className="cursor-pointer px-4 py-3 text-sm font-medium text-[var(--color-muted)]">
            Phase checkpoints
          </summary>
          <ul className="space-y-2 border-t border-[var(--color-border)] px-4 py-3 text-sm text-[var(--color-muted)]">
            {visibleCheckpoints.map((checkpoint) => (
              <li key={checkpoint.checkpoint} className="border-l-2 border-[var(--color-border)] pl-3">
                <span className="font-medium text-[var(--color-foreground)]">{checkpoint.checkpoint}</span>
                {checkpoint.observation && <p className="mt-0.5">{checkpoint.observation}</p>}
              </li>
            ))}
          </ul>
        </details>
      )}
    </div>
  );
}
