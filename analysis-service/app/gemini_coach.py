from __future__ import annotations

import json
import logging

from google import genai
from google.genai import types

from app.config import get_settings
from app.schemas import (
    DISCLAIMER,
    CheckpointFrame,
    CoachingReportSchema,
    DetectedIssue,
    SwingMetrics,
    TopIssue,
)

logger = logging.getLogger(__name__)


def _build_prompt(
    *,
    skill_level: str,
    handedness: str,
    camera_angle: str,
    metrics: SwingMetrics,
    detected_issues: list[DetectedIssue],
    checkpoint_frames: list[CheckpointFrame],
    history_summary: str | None,
) -> str:
    issues_json = [i.model_dump() for i in detected_issues]
    frames_json = [
        {"phase": f.phase, "url": f.url, "confidence": f.confidence}
        for f in checkpoint_frames
    ]
    history = history_summary or "No prior swing history available."

    return f"""You are an experienced golf coach assistant. Analyze ONLY the structured data below.
Do not invent measurements. Use the detected issues as primary evidence; you may refine severity and scoring.

Player context:
- Skill level: {skill_level}
- Handedness: {handedness}
- Camera angle: {camera_angle}

Swing metrics (computed from pose landmarks):
{json.dumps(metrics.model_dump(), indent=2)}

Rules engine detected issues:
{json.dumps(issues_json, indent=2)}

Checkpoint frames (URLs for reference):
{json.dumps(frames_json, indent=2)}

Previous swing history summary:
{history}

Generate a coaching report as JSON matching the required schema.
Scores should reflect metrics and detected issues (0-100).
Include exactly up to 3 top_issues, prioritized by severity.
The disclaimer field MUST be exactly: "{DISCLAIMER}"
Write coach-style, encouraging but direct language."""


def _fallback_report(metrics: SwingMetrics, issues: list[DetectedIssue]) -> CoachingReportSchema:
    base = max(40, 85 - len(issues) * 8)
    top = [
        TopIssue(
            issue=i.issue,
            severity=i.severity,
            why_it_matters=i.why_it_matters,
            fix=i.fix,
            drill=i.drill,
        )
        for i in issues[:3]
    ]
    if not top:
        top = [
            TopIssue(
                issue="Solid baseline swing",
                severity="low",
                why_it_matters="No major faults detected by the rules engine.",
                fix="Continue building consistency with structured practice.",
                drill="Alignment stick gate drill for path and setup.",
            )
        ]

    return CoachingReportSchema(
        overall_score=base,
        setup_score=base,
        backswing_score=base - 2,
        downswing_score=base - 3,
        impact_score=base - 1,
        finish_score=int(metrics.finish_balance),
        main_diagnosis="Rules-based analysis (AI narrative unavailable). Review detected issues below.",
        top_issues=top,
        practice_plan="Focus on one priority issue per range session. 10 slow-motion reps, then 10 full-speed reps.",
        next_upload_focus="Film face-on or down-the-line with full body visible from setup through finish.",
        disclaimer=DISCLAIMER,
    )


def generate_coaching_report(
    *,
    skill_level: str,
    handedness: str,
    camera_angle: str,
    metrics: SwingMetrics,
    detected_issues: list[DetectedIssue],
    checkpoint_frames: list[CheckpointFrame],
    history_summary: str | None,
) -> tuple[CoachingReportSchema, bool]:
    settings = get_settings()
    if not settings.gemini_api_key:
        logger.warning("GEMINI_API_KEY not set; using fallback report")
        return _fallback_report(metrics, detected_issues), False

    prompt = _build_prompt(
        skill_level=skill_level,
        handedness=handedness,
        camera_angle=camera_angle,
        metrics=metrics,
        detected_issues=detected_issues,
        checkpoint_frames=checkpoint_frames,
        history_summary=history_summary,
    )

    try:
        client = genai.Client(api_key=settings.gemini_api_key)
        response = client.models.generate_content(
            model=settings.gemini_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=CoachingReportSchema,
            ),
        )
        text = response.text or "{}"
        report = CoachingReportSchema.model_validate_json(text)
        if DISCLAIMER not in report.disclaimer:
            report.disclaimer = DISCLAIMER
        return report, True
    except Exception as exc:
        logger.exception("Gemini coaching report failed: %s", exc)
        return _fallback_report(metrics, detected_issues), False
