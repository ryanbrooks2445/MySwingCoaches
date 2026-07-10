import type { ReportStatus } from "@/lib/types";

const REPORT_STATUS_LABELS: Record<ReportStatus, string> = {
  awaiting_payment: "Awaiting payment",
  processing: "Processing",
  ready: "Ready",
  failed: "Failed",
};

const VIDEO_STATUS_LABELS: Record<string, string> = {
  uploaded: "Uploaded",
  processing: "Processing",
  ready: "Ready",
  failed: "Failed",
};

/** Human-readable label for swing report or video status strings. */
export function formatSwingStatus(status: string): string {
  if (status in REPORT_STATUS_LABELS) {
    return REPORT_STATUS_LABELS[status as ReportStatus];
  }
  return VIDEO_STATUS_LABELS[status] ?? status.replaceAll("_", " ");
}

const PHASE_LABELS: Record<string, string> = {
  address: "Address / stance",
  setup: "Setup",
  takeaway: "Takeaway",
  top: "Top",
  transition: "Transition",
  downswing: "Downswing",
  impact: "Impact",
  impact_window_estimate: "Impact (estimate)",
  early_follow_through: "Early follow-through",
  follow_through: "Follow-through",
  finish: "Finish",
  backswing: "Backswing",
  backstroke: "Backstroke",
  forward: "Forward stroke",
};

/** Human-readable label for swing phase keyframe captions. */
export function formatPhaseLabel(phase: string): string {
  if (phase in PHASE_LABELS) return PHASE_LABELS[phase];
  return phase.replaceAll("_", " ");
}
