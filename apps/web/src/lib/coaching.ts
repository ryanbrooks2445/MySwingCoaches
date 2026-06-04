import type { CoachingContent, SwingReport } from "@/lib/types";

/** Parse 3-part blueprint from report (new or legacy gemini_raw). */
export function parseCoachingContent(report: SwingReport): CoachingContent | null {
  if (report.coaching_content?.diagnostic) {
    return report.coaching_content;
  }
  const raw = report.gemini_raw as CoachingContent | null | undefined;
  if (raw?.diagnostic && raw?.blueprint && raw?.roadmap) {
    return raw;
  }
  return null;
}

export function getReportFocusLabel(report: SwingReport): string | null {
  const content = parseCoachingContent(report);
  if (content?.roadmap?.weekly_focus) {
    return content.roadmap.weekly_focus.replace(/\*\*/g, "");
  }
  if (content?.diagnostic?.headline) {
    return content.diagnostic.headline;
  }
  return report.main_diagnosis;
}
