import type {
  DiagnosticCheckpointGrade,
  KeyFrameUrl,
  PhaseFrame,
  SimplifiedSwingReport,
} from "@/lib/types";

const NOT_VISIBLE_RE = /not visible/i;

export function isVisibleEvidenceLine(line: string): boolean {
  const text = line.trim();
  if (!text) return false;
  if (NOT_VISIBLE_RE.test(text) && text.split(/\s+/).length <= 5) return false;
  if (/^[\w\s]+:\s*not visible\.?$/i.test(text)) return false;
  return true;
}

export function filterVisibleEvidence(lines: string[]): string[] {
  return lines.filter(isVisibleEvidenceLine);
}

export function filterVisibleCheckpoints(
  checkpoints: DiagnosticCheckpointGrade[] | undefined
): DiagnosticCheckpointGrade[] {
  if (!checkpoints?.length) return [];
  return checkpoints.filter((item) => {
    if (item.grade === "not_visible") return false;
    const observation = (item.observation ?? "").trim();
    if (!observation) return false;
    if (NOT_VISIBLE_RE.test(observation) && observation.split(/\s+/).length <= 3) return false;
    return true;
  });
}

export function hasUsablePhaseCapture(
  _frames: KeyFrameUrl[],
  phaseMap: PhaseFrame[] | undefined
): boolean {
  if (!phaseMap?.length) return false;
  return phaseMap.some(
    (phase) =>
      phase.person_visible !== false && (phase.confidence ?? 0) >= 0.35
  );
}

export function usableSwingFrames(
  frames: KeyFrameUrl[],
  phaseMap: PhaseFrame[] | undefined
): Array<KeyFrameUrl & { person_visible?: boolean; notes?: string }> {
  const merged = phaseMap?.length
    ? frames.map((frame) => {
        const meta = phaseMap.find((p) => p.phase === frame.phase);
        return {
          ...frame,
          confidence: meta?.confidence ?? frame.confidence,
          person_visible: meta?.person_visible,
          notes: meta?.notes,
        };
      })
    : frames;

  return merged.filter(
    (frame) =>
      frame.url &&
      frame.person_visible !== false &&
      (frame.confidence ?? 0) >= 0.35
  );
}

export function resolveBestFix(report: SimplifiedSwingReport): string {
  return (
    report.coach_verdict?.best_fix?.trim() ||
    report.main_fix.trim()
  );
}

export function resolveOneFeel(tips: string[], bestFix: string): string | null {
  const fixNorm = bestFix.trim().toLowerCase().replace(/\s+/g, " ");
  if (!fixNorm || fixNorm === "—") {
    return tips.find((tip) => tip.trim())?.trim() ?? null;
  }
  for (const tip of tips) {
    const trimmed = tip.trim();
    if (!trimmed) continue;
    const tipNorm = trimmed.toLowerCase().replace(/\s+/g, " ");
    if (tipNorm === fixNorm) continue;
    if (fixNorm.includes(tipNorm) || tipNorm.includes(fixNorm)) continue;
    return trimmed;
  }
  return null;
}

export function extractAnalysisSection(analysis: string, heading: string): string {
  const lines = analysis.replace(/\r\n/g, "\n").split("\n");
  const target = heading.toLowerCase();
  let capture = false;
  const collected: string[] = [];

  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed) {
      if (capture && collected.length) break;
      continue;
    }
    if (trimmed.toLowerCase() === target) {
      capture = true;
      continue;
    }
    if (capture) {
      if (/^[A-Za-z][^:\n]{0,48}$/.test(trimmed) && !trimmed.includes("·")) {
        break;
      }
      collected.push(trimmed);
    }
  }

  return collected.join(" ").trim();
}

function normalizeCompare(text: string): string {
  return text.toLowerCase().replace(/\s+/g, " ").trim();
}

function isDuplicateText(a: string, b: string): boolean {
  const left = normalizeCompare(a);
  const right = normalizeCompare(b);
  if (!left || !right) return false;
  if (left === right) return true;
  const shorter = left.length <= right.length ? left : right;
  const longer = left.length > right.length ? left : right;
  return longer.includes(shorter) && shorter.length >= 24;
}

export function dedupePracticePlan(plan: string[], bestFix: string): string[] {
  if (!bestFix.trim() || bestFix.trim() === "—") return plan.filter((item) => item.trim());
  return plan.filter((item) => item.trim() && !isDuplicateText(item, bestFix));
}

export function cameraVerifiedSummary(
  report: SimplifiedSwingReport,
  bestFix?: string
): {
  flaw: string | null;
  impact: string | null;
  working: string | null;
} {
  const adv = report.advanced_details;
  const fixText = bestFix ?? resolveBestFix(report);
  const missingPiece = extractAnalysisSection(report.pga_analysis, "The missing piece");
  let flaw =
    report.coach_verdict?.main_issue?.trim() ||
    missingPiece ||
    adv.foundational_missing_piece?.trim() ||
    adv.root_cause?.trim() ||
    null;
  let impact =
    adv.symptom?.trim() ||
    adv.chain_reaction?.trim() ||
    adv.why_it_caused_the_miss?.trim() ||
    null;
  let working =
    report.coach_verdict?.biggest_positive?.trim() ||
    extractAnalysisSection(report.pga_analysis, "What's working") ||
    null;

  if (flaw && isDuplicateText(flaw, fixText)) flaw = null;
  if (impact && isDuplicateText(impact, fixText)) impact = null;
  if (working && isDuplicateText(working, fixText)) working = null;

  return {
    flaw: flaw && !NOT_VISIBLE_RE.test(flaw) ? flaw : null,
    impact: impact && impact !== "—" && !impact.toLowerCase().startsWith("n/a") ? impact : null,
    working: working && !NOT_VISIBLE_RE.test(working) ? working : null,
  };
}

export function goodVsWorkBlocks(analysis: string): {
  working: string[];
  work: string[];
} {
  const workingText = extractAnalysisSection(analysis, "What's working");
  const missingText = extractAnalysisSection(analysis, "The missing piece");
  const setupText = extractAnalysisSection(analysis, "Setup to finish");

  const working = splitIntoBullets(workingText);
  const work = [
    ...splitIntoBullets(missingText),
    ...splitPhaseNarrative(setupText).filter((line) => /constraint|issue|miss|bent|inside|steep/i.test(line)),
  ];

  return {
    working: dedupeLines(working),
    work: dedupeLines(work),
  };
}

function splitIntoBullets(text: string): string[] {
  if (!text.trim()) return [];
  return text
    .split(/(?<=[.!?])\s+/)
    .map((part) => part.trim())
    .filter((part) => part.length > 12);
}

function splitPhaseNarrative(text: string): string[] {
  if (!text.trim()) return [];
  return text
    .split(/\s*(?=(?:Setup|Takeaway|Backswing|Transition|Downswing|Impact|Finish)\s*·)/i)
    .map((part) => part.trim())
    .filter((part) => part.length > 12);
}

function dedupeLines(lines: string[]): string[] {
  const seen = new Set<string>();
  const out: string[] = [];
  for (const line of lines) {
    const key = line.toLowerCase();
    if (seen.has(key)) continue;
    seen.add(key);
    out.push(line);
  }
  return out;
}
