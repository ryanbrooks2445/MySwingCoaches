import type { KeyFrameUrl, PhaseFrame, SwingReport } from "@/lib/types";

export function confidenceLabel(confidence: number | undefined): "High" | "Limited" | "Not visible" {
  if (confidence === undefined || confidence < 0.4) return "Not visible";
  if (confidence < 0.6) return "Limited";
  return "High";
}

export function confidenceBadgeClass(label: ReturnType<typeof confidenceLabel>): string {
  switch (label) {
    case "High":
      return "bg-emerald-100 text-emerald-800";
    case "Limited":
      return "bg-amber-100 text-amber-800";
    case "Not visible":
      return "bg-slate-100 text-slate-600";
    default: {
      const _exhaustive: never = label;
      return _exhaustive;
    }
  }
}

export function mergeFramesWithPhaseMap(
  frames: KeyFrameUrl[],
  phaseMap: PhaseFrame[] | undefined
): Array<KeyFrameUrl & { person_visible?: boolean; notes?: string }> {
  if (!phaseMap?.length) return frames;
  const byPhase = new Map(phaseMap.map((p) => [p.phase, p]));
  return frames.map((frame) => {
    const meta = byPhase.get(frame.phase);
    return {
      ...frame,
      confidence: meta?.confidence ?? frame.confidence,
      person_visible: meta?.person_visible,
      notes: meta?.notes,
    };
  });
}

export function limitationBanners(phaseMap: PhaseFrame[] | undefined): string[] {
  if (!phaseMap?.length) return [];
  const notes: string[] = [];
  const impact = phaseMap.find(
    (p) => p.phase === "impact" || p.phase === "impact_window_estimate"
  );
  if (
    impact &&
    (impact.phase === "impact_window_estimate" ||
      (impact.confidence ?? 0) < 0.5 ||
      impact.person_visible === false)
  ) {
    notes.push("Impact frame was not clearly visible, so impact feedback is limited.");
  }
  const finish = phaseMap.find((p) => p.phase === "finish" || p.phase === "early_follow_through");
  if (
    finish &&
    (finish.person_visible === false || (finish.confidence ?? 0) < 0.4)
  ) {
    notes.push("Finish was not clearly visible on this upload.");
  }
  return notes;
}

export type ProgressState = "first_upload" | "improved" | "same_priority" | "new_priority";

export function compareToPriorReport(
  current: SwingReport,
  prior: SwingReport | null
): {
  state: ProgressState;
  priorMainFix: string | null;
  priorCreatedAt: string | null;
  priorFrames: KeyFrameUrl[];
} | null {
  if (!prior) {
    return {
      state: "first_upload",
      priorMainFix: null,
      priorCreatedAt: null,
      priorFrames: [],
    };
  }

  const currentFix =
    current.coaching_content?.main_fix ??
    current.coaching_content?.advanced_details?.foundational_missing_piece ??
    current.main_diagnosis ??
    "";
  const priorFix =
    prior.coaching_content?.main_fix ??
    prior.coaching_content?.advanced_details?.foundational_missing_piece ??
    prior.main_diagnosis ??
    "";

  const normalize = (s: string) => s.toLowerCase().replace(/\s+/g, " ").trim();
  const same = normalize(currentFix).slice(0, 80) === normalize(priorFix).slice(0, 80);

  let state: ProgressState = "new_priority";
  if (same) state = "same_priority";
  else if (
    normalize(currentFix).includes("keep") ||
    normalize(currentFix).includes("maintain") ||
    normalize(priorFix).includes("setup") && !normalize(currentFix).includes("setup")
  ) {
    state = "improved";
  }

  return {
    state,
    priorMainFix: priorFix || null,
    priorCreatedAt: prior.created_at,
    priorFrames: prior.key_frame_urls ?? [],
  };
}
