from __future__ import annotations

import re

from app.schemas import CoachingReportSchema, SwingMode


class ReportQualityError(ValueError):
    """Raised when a generated report is not safe to show as a completed analysis."""


_GENERIC_MAIN_FIXES = (
    "focus on one athletic feel",
    "feel balanced at address",
    "feel smooth through the ball",
    "own the pattern",
)

_OVERPRAISE_TERMS = (
    "dominate the course",
    "scratch golfer",
    "tour-ready",
    "tour caliber",
    "tour-caliber",
    "elite consistency",
    "perfect",
    "textbook",
)


def _blob(report: CoachingReportSchema) -> str:
    parts = [
        report.personalized_greeting,
        report.pga_analysis,
        report.main_fix,
        report.next_swing_check,
        report.advanced_details.root_cause,
        report.advanced_details.foundational_missing_piece,
        report.advanced_details.chain_reaction,
        " ".join(report.tips_and_feels),
        " ".join(report.advanced_details.evidence_metrics),
    ]
    return " ".join(part for part in parts if part).lower()


def _high_score_context(player_context: str | None) -> bool:
    text = (player_context or "").lower()
    if not text:
        return False
    score_matches = re.findall(r"(?:9[- ]?hole score|average score|shoots?|score)[:\s]+(\d{2,3})", text)
    return any(int(score) >= 50 for score in score_matches)


def audit_report_quality(
    report: CoachingReportSchema,
    *,
    swing_mode: SwingMode,
    player_context: str | None = None,
) -> None:
    adv = report.advanced_details
    text = _blob(report)

    if adv.confidence_score <= 0 or "non-golf video uploaded" in text:
        raise ReportQualityError("Uploaded video could not be verified as a usable golf swing.")

    if any(term in report.main_fix.lower() for term in _GENERIC_MAIN_FIXES):
        raise ReportQualityError("Generated report used a generic main fix.")

    if _high_score_context(player_context) and any(term in text for term in _OVERPRAISE_TERMS):
        raise ReportQualityError("Generated report overpraised a high-score golfer.")

    if adv.report_mode == "maintenance":
        if _high_score_context(player_context):
            raise ReportQualityError("Generated maintenance report for high-score golfer context.")
        if len(adv.diagnostic_checkpoints) < 4:
            raise ReportQualityError("Maintenance report lacked enough checkpoint evidence.")
        return

    min_checkpoints = 3 if swing_mode == "full_swing" else 2
    if len(adv.diagnostic_checkpoints) < min_checkpoints:
        raise ReportQualityError("Development report lacked required checkpoint evidence.")

    if len([item for item in adv.evidence_metrics if item.strip()]) < 2:
        raise ReportQualityError("Development report lacked required visible evidence.")

    if len((adv.root_cause or "").strip()) < 8:
        raise ReportQualityError("Development report lacked a clear root cause.")

    if len((adv.foundational_missing_piece or "").strip()) < 8:
        raise ReportQualityError("Development report lacked a foundational missing piece.")

    if len((adv.chain_reaction or "").strip()) < 20:
        raise ReportQualityError("Development report lacked a cause-and-effect chain.")
