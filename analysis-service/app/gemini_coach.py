from __future__ import annotations

import json
import logging
import re
from collections.abc import Callable
from pathlib import Path

import numpy as np
from google import genai
from google.genai import types

from app.config import get_settings
from app.gemini_report_schema import (
    DIAGNOSTIC_RESPONSE_JSON_SCHEMA,
    GEMINI_COACHING_SCHEMA,
    GEMINI_RESPONSE_JSON_SCHEMA,
    GeminiReportOut,
)
from app.report_converter import (
    apply_film_first_report,
    gemini_out_to_coaching_report,
    parse_gemini_json,
    coach_verdict_from_analysis,
)
from app.report_audit import ReportQualityError, audit_report_quality
from app.trace_log import log_trace
from app.diagnostic_matrix import diagnostic_matrix_for_prompt
from app.drill_matching import critique_menu_for_prompt
from app.mode_coaching import mode_guidance_block
from app.drill_videos import catalog_for_prompt
from app.gemini_video import (
    build_keyframe_parts,
    build_phase_evidence_packet,
    delete_uploaded_file,
    upload_video,
)
from app.phase_detector import PhaseDetectionResult
from app.schemas import (
    AccountabilityPlan,
    AdvancedDetails,
    BlueprintStep,
    CoachingReportSchema,
    DISCLAIMER,
    DrillSummary,
    KinestheticBlueprint,
    MilestoneBlock,
    SwingMode,
)

logger = logging.getLogger(__name__)

FOREFIX_ELITE_BIOMECHANICS_SYSTEM = """You are ForeFix's elite PGA biomechanics coach: a tour-level swing analyst, motor-learning coach, and visual evidence auditor.

Operate like a coach who has the player's video open frame-by-frame. Your job is to extract dense, specific mechanical truth from the visual evidence, not to write generic golf tips.

NON-NEGOTIABLE VISUAL CHECKPOINTS:
- Camera/read quality: identify face-on vs down-the-line vs unclear, and state which claims are limited by that angle.
- Address posture: evaluate spine tilt, hip hinge, knee flex, weight balance, distance from ball, hand position, shoulder/hip alignment, and whether the body has room to rotate.
- Visual lines: assess head line, spine line, pelvis/hip line, shoulder line, knee line, lead-arm structure, shaft line, hand path, clubhead path, swing plane, low-point window, and balance/pressure shift.
- Takeaway and backswing: describe clubhead relative to hands, shaft pitch, wrist set, trail elbow fold, shoulder turn, hip turn, depth, width, arm structure, and clubface angle relative to lead forearm/shaft.
- Top and transition: identify whether the club is laid off/across/neutral, whether the lead arm collapses, how pressure shifts, and whether the lower body starts before the arms.
- Downswing clearing: evaluate lead-hip clearing, pelvis rotation, chest rotation, trail elbow position, shaft shallowing/steepening, hand path, head level, early extension, and whether the player creates space through impact.
- Impact window: note shaft lean, face/path relationship, release pattern, low point, handle location, head stability, lead-side bracing, and what is estimated rather than directly visible.
- Finish: balance, rotation completion, recoil, and whether the finish confirms or contradicts the earlier sequence.

QUALITY BAR:
- Be exhaustive within the requested schema. Prefer concrete visible evidence over labels.
- Do not say "good posture", "solid swing", "needs consistency", or similar filler unless you immediately attach the exact visible reason.
- If a phase is visible, include enough detail that another coach could picture the frame without seeing it.
- If a detail is not visible, mark it as not visible instead of guessing.
- Separate evidence from coaching conclusions unless the current call explicitly asks for diagnosis or coaching."""


OBSERVATION_SYSTEM = FOREFIX_ELITE_BIOMECHANICS_SYSTEM + """

For this call, you are in VIDEO OBSERVATION MODE. Your ONLY job is to describe what you see in this golf swing video.

DO NOT diagnose. DO NOT suggest fixes. DO NOT pick a report mode.
DO NOT use words like "fault", "issue", "problem", "fix", or "should".

Describe ONLY what is physically visible, phase by phase. Be dense and specific:

For each phase (Setup, Takeaway, Backswing, Transition, Downswing, Impact, Finish):
- club: shaft/clubface/clubhead/hand-path details, including face angle where visible
- body: posture, lines, rotation, clearing, pressure shift, arm structure, head movement, balance
- not_visible: exact visual limitations from camera angle, blur, framing, or phase confidence

Return JSON only:
{
  "observations": {
    "setup": { "club": "...", "body": "...", "not_visible": "..." },
    "takeaway": { "club": "...", "body": "...", "not_visible": "..." },
    "backswing": { "club": "...", "body": "...", "not_visible": "..." },
    "transition": { "club": "...", "body": "...", "not_visible": "..." },
    "downswing": { "club": "...", "body": "...", "not_visible": "..." },
    "impact": { "club": "...", "body": "...", "not_visible": "..." },
    "finish": { "club": "...", "body": "...", "not_visible": "..." }
  },
  "camera_angle": "face-on | down-the-line | behind | unclear",
  "video_usability": "good | acceptable | poor",
  "usability_note": "..."
}"""


COACHING_SYSTEM = FOREFIX_ELITE_BIOMECHANICS_SYSTEM + """

For this call, you are writing the paid ForeFix coaching output.
Use locked video evidence as the authority. Write like an elite coach who is both precise and useful: specific cause-effect chain, no filler, no vague encouragement, no invented ball flight.
Maximize information density. Every sentence should either name what was visible, explain why it matters biomechanically, or give a concrete feel/drill/checkpoint.
Do not expose hidden reasoning. Provide the final evidence-backed assessment only."""


DIAGNOSTIC_SYSTEM = FOREFIX_ELITE_BIOMECHANICS_SYSTEM + """

For this call, you are a strict diagnostic grading engine.
Grade only from supplied observations and player profile. Prefer the earliest visible cause over downstream symptoms, but never invent a cause that is absent from the observations.
Return JSON only."""


_CALL3_USER_FACING_RULES = """USER-FACING COPY RULES — FILM FIRST:
- Call 1 observations in locked context are the source of truth for what happened on film.
- Do NOT invent mechanics, ball flight, or fixes not supported by those observations.
- The server builds the phase-by-phase film walkthrough — do NOT write long analysis prose.
- Keep analysis to one optional sentence or leave it empty; elaborate in the evidence array instead.
- Each evidence[] entry must expand one Call 1 phase observation in plain language (club + body + camera limits).
- main_fix must cite the earliest Constraint phase from locked grades and name what the film showed.
- secondary_fix must cite a second visible issue from film, not generic golf advice.

RATING CALIBRATION:
- 2+ Constraint phases OR 3+ Compensating phases → overall rating ≤ 6.5/10
- Obvious lead arm bend/collapse at top OR poor weight transfer → rating ≤ 6.5/10 even if tempo looks athletic
- A 7/10+ requires almost all visible checkpoints clean with at most one minor compensation

MANDATORY CALL-OUTS (if present in locked Call 2 grades):
- Lead arm bend/collapse at top MUST appear in flaw2/flaw3 or secondary_fix
- Poor weight load/transfer MUST appear in user-facing text even if path is the primary fix

DEVELOPMENT vs MAINTENANCE:
- DEVELOPMENT: main_fix targets foundational_missing_piece from locked grades
- MAINTENANCE: main_fix preserves what film shows is already working — no invented flaws"""


def _build_call3_prompt(
    *,
    swing_mode: SwingMode,
    history_summary: str | None,
    player_name: str | None,
    swing_number: int | None,
    player_context: str | None,
    player_age: int | None = None,
    years_playing: int | None = None,
    physical_limitations: str | None = None,
) -> str:
    """Call 3 coaching prompt — text only; locked Call 1 + Call 2 evidence is prepended separately."""
    name = (player_name or "there").split()[0]
    swing_line = f"Swing #{swing_number}" if swing_number else "First swing on file"
    profile_block = (player_context or "").strip() or "No intake profile provided."
    history_block = (
        f"PRIOR SWING HISTORY (continuity — reference when relevant):\n{history_summary.strip()}"
        if history_summary and history_summary.strip()
        else "PRIOR SWING HISTORY: None — treat as first analysis."
    )
    physical_block = _format_physical_boundaries_block(
        age=player_age,
        years_playing=years_playing,
        physical_limitations=physical_limitations,
    )
    physical_section = f"\n\n{physical_block}" if physical_block else ""

    return f"""You are ForeFixed's head coach writing the final paid coaching report.

IMPORTANT: Locked Call 1 observations and Call 2 grades are prepended above as authoritative evidence.
- Do NOT re-watch or re-interpret video — you have no video in this call.
- Do NOT contradict, re-grade, or override locked evidence.
- Write coaching output ONLY from that locked context plus the golfer profile below.

GOLFER:
- Name: {name}
- {swing_line}
- Profile: {profile_block}
{history_block}
{physical_section}

{mode_guidance_block(swing_mode)}

{_CALL3_USER_FACING_RULES}

DRILL & DIAGNOSIS COVERAGE (pick drills matching locked foundational_missing_piece — do not invent new diagnosis):
{critique_menu_for_prompt(swing_mode)}

AVAILABLE DRILLS (use pipe format name|why|how for drill1, drill2, drill3):
{catalog_for_prompt(swing_mode)}

OUTPUT — Return JSON only matching the coaching schema:
- greeting: short personalized opener
- rating, categories: calibrated from locked grades
- analysis: leave empty or one sentence — phase walkthrough is built from Call 1 on the server
- main_fix: one priority tied to the earliest Constraint on film (quote what you saw)
- pri1 through pri5: ranked coaching priorities — root cause first, downstream chain after
  Pipe format per field (10 parts): rank|phase|title|issue|why_first|body_feel1;;body_feel2|space_feel1;;space_feel2|drill_name|drill_why|drill_how
  - rank 1 MUST be the earliest Constraint phase (usually Setup or Takeaway)
  - Include at least pri1, pri2, pri3 when film shows a chain of compensations
  - Each priority needs 2+ body feels OR 2+ space feels (use ;; between multiple feels)
  - phase must be one of: Setup, Takeaway, Backswing, Transition, Downswing, Impact
  - title names the fix; issue quotes what film showed; why_first explains rank in the chain
- tips: 2-4 feel cues tied to visible issues only (supplement pri fields, do not repeat verbatim)
- drill1, drill2, drill3: each "name|why|how" matched to main_fix
- next_check: camera angle that would clarify the biggest not_visible phase
- mode: copy locked report_mode
- missing, root, secondary, symptom, chain: from locked grading only
- evidence: 5-8 strings — each elaborates one Call 1 phase (Setup through Finish) in plain language
- checkpoints: 7 distinct strings, one per phase, using exact phase-prefixed pipe format
  "Setup: [biomechanical detail] | optimal|compensation|constraint|not_visible | visible observation"
  Use lowercase grades and write "compensation" for Call 2 Compensating grades.
  Include Setup, Takeaway, Backswing, Transition, Downswing, Impact, Finish.
  ABSOLUTE REQUIREMENT: checkpoints must contain a minimum of 3 distinct string items.
  ABSOLUTE REQUIREMENT: checkpoints must include strings that begin with these exact case-sensitive prefixes:
  - "Setup: [biomechanical detail]"
  - "Backswing: [biomechanical detail]"
  - "Impact: [biomechanical detail]"
  Replace [biomechanical detail] with the specific body/club detail for that phase, but keep the exact phase prefix and colon.
- letter_open, strengths, flaws, fixes: keep brief and film-specific; skip generic coach letter filler
- confidence: from locked grading

Do NOT write generic coaching essays. If it is not on film, do not say it."""


def _build_prompt(
    *,
    swing_mode: SwingMode,
    history_summary: str | None,
    player_name: str | None,
    swing_number: int | None,
    player_context: str | None,
    player_age: int | None = None,
    years_playing: int | None = None,
    physical_limitations: str | None = None,
) -> str:
    return _build_call3_prompt(
        swing_mode=swing_mode,
        history_summary=history_summary,
        player_name=player_name,
        swing_number=swing_number,
        player_context=player_context,
        player_age=player_age,
        years_playing=years_playing,
        physical_limitations=physical_limitations,
    )


def _format_physical_boundaries_block(
    *,
    age: int | None,
    years_playing: int | None,
    physical_limitations: str | None,
) -> str:
    if age is None and years_playing is None and not (physical_limitations or "").strip():
        return ""

    age_line = str(age) if age is not None else "Not provided"
    years_line = str(years_playing) if years_playing is not None else "Not provided"
    limits = (physical_limitations or "").strip() or "None reported"

    return f"""[PILLAR 1 — HUMAN BLUEPRINT / PHYSICAL BOUNDARIES]
Apply these BEFORE grading video checkpoints. Never prescribe moves that violate them.

- Age: {age_line}
- Years playing: {years_line} (beginner → foundations; 20+ years → micro-adjustments, protect confidence)
- Physical constraints & injuries: {limits}
- Infer mobility tiers from constraints + video: T-spine rotation, hip IR/ER, core stability.
- Adapt cues for pain workarounds (back, knees, wrist, shoulder)."""


def _build_revision_prompt(quality_error: ReportQualityError) -> str:
    return (
        "Revise the report. Your previous draft failed launch-quality audit: "
        f"{quality_error}. Follow the PHASE EVIDENCE PACKET strictly. "
        "Do not claim finish, impact, or path details for phases marked NOT USABLE or low confidence. "
        "If impact is impact_window_estimate, include limitation language. "
        "Do not repeat a generic posture/setup diagnosis unless address frame confidence >= 0.6 "
        "and setup clearly beats path, face, head, arms, sequencing, and impact. "
        "secondary_fix must differ from foundational_missing_piece and be at least 8 characters. "
        "Each diagnostic_checkpoint label MUST start with one of: "
        "Setup:, Takeaway:, Backswing:, Transition:, Downswing:, Impact:, Finish:. "
        "Coach letter fields (letter_open, strength1-3, flaw1-3, ceiling_now, ceiling_unlock, fix1-3) "
        "must be fully populated with specific video evidence. "
        "Do NOT use banned filler phrases: the key is, from start to finish, textbook, model swing. "
        "Return complete JSON only."
    )


def _impact_limited(phase_map: list[dict] | None) -> bool:
    if not phase_map:
        return False
    for entry in phase_map:
        phase = str(entry.get("phase", ""))
        if phase not in {"impact", "impact_window_estimate"}:
            continue
        confidence = float(entry.get("confidence", 0) or 0)
        return phase == "impact_window_estimate" or confidence < 0.5
    return False


def _apply_phase_limitations(
    report: CoachingReportSchema,
    phase_map: list[dict] | None,
) -> CoachingReportSchema:
    if not _impact_limited(phase_map):
        return report
    note = "Camera note: the impact window is estimated, so contact feedback is limited."
    combined = " ".join(
        [
            report.pga_analysis,
            report.main_fix,
            report.next_swing_check,
            " ".join(report.tips_and_feels),
        ]
    ).lower()
    if "impact window" in combined or "contact feedback is limited" in combined:
        return report
    return report.model_copy(update={"pga_analysis": f"{report.pga_analysis}\n\n{note}"})


def _audit_with_revisions(
    client: genai.Client,
    model: str,
    content_parts: list[types.Part],
    *,
    swing_mode: SwingMode,
    player_context: str | None,
    history_summary: str | None,
    phase_map: list[dict] | None,
    max_revisions: int,
    trace_id: str | None,
    report_id: str | None,
    user_id: str | None,
    locked_observation: GeminiReportOut | None = None,
    locked_grading: GeminiReportOut | None = None,
    raw_attempts: list[dict] | None = None,
) -> CoachingReportSchema:
    """Call 3 — text-only coaching report with quality audit and optional revision loop."""
    report = _call_gemini(
        client,
        model,
        content_parts,
        swing_mode,
        trace_id=trace_id,
        report_id=report_id,
        user_id=user_id,
        raw_attempts=raw_attempts,
    )
    revision_parts_base = list(content_parts)

    for revision in range(max_revisions + 1):
        if locked_observation is not None and locked_grading is not None:
            report = apply_film_first_report(report, locked_observation, locked_grading)
        report = _apply_phase_limitations(report, phase_map)
        try:
            audit_report_quality(
                report,
                swing_mode=swing_mode,
                player_context=player_context,
                history_summary=history_summary,
                phase_map=phase_map,
            )
            return report
        except ReportQualityError as quality_error:
            if revision >= max_revisions:
                raise
            logger.warning(
                "Gemini report failed quality audit (attempt %s/%s); requesting revision: %s",
                revision + 1,
                max_revisions + 1,
                quality_error,
            )
            revision_parts = [
                *revision_parts_base,
                types.Part.from_text(text=_build_revision_prompt(quality_error)),
            ]
            report = _call_gemini(
                client,
                model,
                revision_parts,
                swing_mode,
                trace_id=trace_id,
                report_id=report_id,
                user_id=user_id,
                raw_attempts=raw_attempts,
            )

    raise ReportQualityError("Report failed quality audit after all revision attempts.")


def _is_observer_only_report(report: CoachingReportSchema) -> bool:
    return report.advanced_details.root_cause == "Observation-only output"


def _is_retryable_model_error(exc: Exception) -> bool:
    msg = str(exc)
    return any(
        token in msg
        for token in (
            "429",
            "RESOURCE_EXHAUSTED",
            "NOT_FOUND",
            "404",
            "quota",
            "INVALID_ARGUMENT",
            "503",
            "UNAVAILABLE",
            "temporarily unavailable",
            "high demand",
            "too many states",
        )
    )


def _models_to_try(primary: str, fallback: str) -> list[str]:
    models: list[str] = []
    for model in (primary, fallback):
        if model and model not in models:
            models.append(model)
    return models


def _fallback_report(
    reason: str | None = None,
    player_name: str | None = None,
    swing_mode: SwingMode = "full_swing",
) -> CoachingReportSchema:
    note = reason or "Try again in a few minutes."
    name = (player_name or "there").split()[0]
    mode_labels = {
        "full_swing": ("swing", "ball position, tempo, sequencing, and impact"),
        "chipping": ("chip", "landing spot, hinge, low point, and strike"),
        "putting": ("putting stroke", "setup, stroke path, tempo, and face at impact"),
    }
    mode_label, checkpoint_hint = mode_labels.get(swing_mode, mode_labels["full_swing"])
    next_check = f"Film one {mode_label} face-on with full body in frame and good light."
    default_checkpoint = {"full_swing": "address", "chipping": "setup", "putting": "address"}[
        swing_mode
    ]
    report = CoachingReportSchema(
        personalized_greeting=(
            f"{name}, your commitment to getting better is elite — let's get you a full read on the next upload."
        ),
        pga_analysis=(
            "What's working\n"
            "You showed up with real intent — that alone separates serious athletes from casual golfers.\n\n"
            "Setup to finish\n"
            f"We couldn't read enough detail on film for a full checkpoint breakdown. {note} "
            "Re-upload face-on or down-the-line with full body in frame and good light.\n\n"
            "The missing piece\n"
            f"A clear video unlocks the full setup-to-finish story — {checkpoint_hint}.\n\n"
            "What changes when you unlock it\n"
            "You'll get a phase-by-phase breakdown naming what's working and the one foundational link to unlock."
        ),
        main_fix=(
            "Re-film one clean rep: stable camera, full body visible — that unlocks your personalized breakthrough plan."
        ),
        tips_and_feels=[
            "Feel athletic balance — weight on the balls of your feet at address.",
            "Feel a smooth takeaway without rushing the transition.",
        ],
        drills=[
            DrillSummary(
                name="Film check",
                why_it_helps="We need a clear view of setup and impact to coach you accurately.",
                how_to_do_it="Tripod or propped phone, face-on, one slow-motion swing.",
            ),
        ],
        next_swing_check=next_check,
        advanced_details=AdvancedDetails(
            report_mode="development",
            foundational_missing_piece="Video quality or framing blocked full matrix pass.",
            profile_constraints_applied="Re-upload for profile-aware chain analysis.",
            diagnostic_checkpoints=[],
            root_cause="Video quality or framing blocked analysis.",
            symptom="Report unavailable",
            evidence_metrics=["Re-upload required"],
            secondary_fix="",
            optional_fix="",
            chain_reaction="—",
            why_it_caused_the_miss="—",
            confidence_score=0.0,
            next_checkpoint=default_checkpoint,
        ),
        feel_blueprint=None,
        priority_fixes=[],
        blueprint=KinestheticBlueprint(
            headline="Film again",
            intro="One clear video unlocks your plan.",
            steps=[
                BlueprintStep(
                    title="Setup film",
                    step_type="setup",
                    adjustment="Full body in frame.",
                    feel="Steady camera.",
                    video_slug="setup_posture",
                ),
                BlueprintStep(
                    title="One rep",
                    step_type="visual_cue",
                    action="Single slow swing on video.",
                    feel="Balance through finish.",
                    video_slug="slow_motion_reps",
                ),
            ],
        ),
        roadmap=AccountabilityPlan(
            weekly_focus="Re-upload",
            milestones=[
                MilestoneBlock(days="Today", title="Film", detail="One swing on video."),
                MilestoneBlock(days="Next", title="Upload", detail="Open your new report."),
                MilestoneBlock(days="Range", title="Train", detail="Apply your main fix."),
            ],
            day_7_test="New upload received.",
        ),
        next_upload_focus=next_check,
        disclaimer=DISCLAIMER,
    )
    return _normalize_report(report)


def _normalize_report(report: CoachingReportSchema) -> CoachingReportSchema:
    if not report.next_upload_focus.strip():
        report = report.model_copy(update={"next_upload_focus": report.next_swing_check})
    return report


_NARRATIVE_SECTION_TITLES = (
    "Quick coach verdict",
    "Full coach-style analysis",
    "Main swing fault",
    "Secondary swing fault",
    "What you do well",
    "Setup/grip notes",
    "Swing path notes",
    "Head movement notes",
    "Arm/hand structure",
    "Impact-window notes",
    "Drill",
    "Feel",
    "Practice plan",
    "Confidence/visibility limitations",
)


def _parse_narrative_json(text: str) -> dict:
    cleaned = (text or "").strip()
    if cleaned.startswith("```"):
        import re

        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    data = json.loads(cleaned or "{}")
    if not isinstance(data, dict):
        raise ValueError("Narrative response is not a JSON object")
    return data


def _narrative_has_sections(text: str) -> bool:
    lower = (text or "").lower()
    return all(title.lower() in lower for title in _NARRATIVE_SECTION_TITLES)


def _sanitize_user_text(text: str) -> str:
    return (
        (text or "")
        .replace("The key feel", "The main feel")
        .replace("the key feel", "the main feel")
        .replace("The key is", "The priority is")
        .replace("the key is", "the priority is")
    )


def _narrative_analysis_text(value: object) -> str:
    if isinstance(value, str):
        return _sanitize_user_text(value.strip())
    if isinstance(value, dict):
        parts: list[str] = []
        for title in _NARRATIVE_SECTION_TITLES:
            body = value.get(title)
            if isinstance(body, str) and body.strip():
                parts.append(f"{title}\n\n{_sanitize_user_text(body.strip())}")
        return "\n\n".join(parts)
    return ""


def _apply_narrative_response(
    report: CoachingReportSchema,
    narrative: dict,
) -> CoachingReportSchema:
    analysis = _narrative_analysis_text(narrative.get("analysis"))
    if not analysis:
        raise ValueError("Narrative response did not include analysis")
    if not _narrative_has_sections(analysis):
        raise ValueError("Narrative response did not include all required sections")

    drills = list(report.drills)
    drill_name = str(narrative.get("drill_name") or "").strip()
    drill_why = str(narrative.get("drill_why") or "").strip()
    drill_how = str(narrative.get("drill_how") or "").strip()
    if drill_name and drill_why and drill_how:
        drills = [DrillSummary(name=drill_name, why_it_helps=drill_why, how_to_do_it=drill_how), *drills[1:]]

    tips = narrative.get("tips")
    tips_and_feels = [str(t).strip() for t in tips if str(t).strip()] if isinstance(tips, list) else report.tips_and_feels
    if len(tips_and_feels) < 2:
        tips_and_feels = report.tips_and_feels

    advanced = report.advanced_details
    secondary = str(narrative.get("secondary_fix") or "").strip()
    if secondary:
        advanced = advanced.model_copy(update={"secondary_fix": secondary})

    updates = {
        "pga_analysis": analysis,
        "main_fix": _sanitize_user_text(str(narrative.get("main_fix") or report.main_fix).strip())
        or report.main_fix,
        "tips_and_feels": tips_and_feels[:4],
        "drills": drills[:3],
        "next_swing_check": str(narrative.get("next_check") or report.next_swing_check).strip()
        or report.next_swing_check,
        "advanced_details": advanced,
        "coach_verdict": coach_verdict_from_analysis(
            analysis,
            fallback_main_fix=str(narrative.get("main_fix") or report.main_fix),
            fallback_issue=report.advanced_details.foundational_missing_piece or report.advanced_details.root_cause,
            existing=report.coach_verdict,
        ),
    }
    return _normalize_report(report.model_copy(update=updates))


_SETUP_PRIMARY_TERMS = (
    "setup",
    "address",
    "posture",
    "heel",
    "balance",
    "hinge",
    "stance",
    "seated",
)

_DYNAMIC_TERMS = (
    "takeaway",
    "inside",
    "deep",
    "path",
    "clubface",
    "face",
    "hook",
    "slice",
    "release",
    "transition",
    "impact",
    "in-to-out",
    "out-to-in",
    "over-the-top",
)


def _contains_any(text: str, terms: tuple[str, ...]) -> bool:
    lower = text.lower()
    return any(term in lower for term in terms)


def _dynamic_priority_guard(report: CoachingReportSchema) -> CoachingReportSchema:
    """Prefer the highest-value dynamic action when setup is only the upstream context."""
    adv = report.advanced_details
    primary_text = " ".join(
        [
            adv.foundational_missing_piece or "",
            adv.root_cause or "",
            report.main_fix or "",
        ]
    )
    if not _contains_any(primary_text, _SETUP_PRIMARY_TERMS):
        return report

    evidence_blob = " ".join(
        [
            adv.secondary_fix or "",
            adv.symptom or "",
            adv.chain_reaction or "",
            adv.why_it_caused_the_miss or "",
            " ".join(adv.evidence_metrics or []),
            " ".join(
                f"{item.checkpoint} {item.observation}"
                for item in adv.diagnostic_checkpoints
            ),
        ]
    )
    dynamic_hits = sum(1 for term in _DYNAMIC_TERMS if term in evidence_blob.lower())
    if dynamic_hits < 3:
        return report

    secondary = (adv.secondary_fix or "").strip()
    if secondary and not _contains_any(secondary, _SETUP_PRIMARY_TERMS):
        dynamic_priority = secondary
    elif _contains_any(evidence_blob, ("takeaway", "inside", "deep")):
        dynamic_priority = "Inside takeaway and deep club position"
    elif _contains_any(evidence_blob, ("clubface", "face", "release", "hook", "slice")):
        dynamic_priority = "Swing path and clubface timing"
    else:
        dynamic_priority = "Dynamic swing path and face control"

    setup_context = adv.root_cause or adv.foundational_missing_piece or "Setup pattern"
    new_main_fix = (
        f"Make {dynamic_priority.lower()} the first change. Keep the clubhead more in front of your hands going back, "
        "then let your body turn through without a last-second face flip. Treat the setup as supporting context, "
        "not the only fix."
    )
    new_adv = adv.model_copy(
        update={
            "foundational_missing_piece": dynamic_priority,
            "root_cause": dynamic_priority,
            "secondary_fix": f"Setup context: {setup_context}",
        }
    )
    return report.model_copy(update={"main_fix": new_main_fix, "advanced_details": new_adv})


def _preanalyzed_evidence_block(report: CoachingReportSchema) -> str:
    try:
        payload = json.loads(report.pga_analysis or "{}")
    except json.JSONDecodeError:
        payload = {}
    if not isinstance(payload, dict) or "observations" not in payload:
        return ""

    diagnostic_payload = payload.get("diagnostic")
    diagnostic = diagnostic_payload if isinstance(diagnostic_payload, dict) else {
        "grades": payload.get("grades", {}),
        "report_mode": payload.get("report_mode", report.advanced_details.report_mode),
        "foundational_missing_piece": payload.get(
            "foundational_missing_piece",
            report.advanced_details.foundational_missing_piece,
        ),
        "secondary_fix": payload.get("secondary_fix", report.advanced_details.secondary_fix),
        "miss_pattern_match": payload.get("miss_pattern_match"),
        "miss_conflict_note": payload.get("miss_conflict_note"),
        "confidence": payload.get("confidence", report.advanced_details.confidence_score),
    }
    observations = {
        "observations": payload.get("observations", {}),
        "camera_angle": payload.get("camera_angle", "unclear"),
        "video_usability": payload.get("video_usability", "poor"),
        "usability_note": payload.get("usability_note", ""),
    }
    report_mode = diagnostic.get("report_mode") or report.advanced_details.report_mode
    foundational = diagnostic.get("foundational_missing_piece") or report.advanced_details.foundational_missing_piece
    return (
        "PRE-ANALYZED EVIDENCE (DO NOT OVERRIDE):\n"
        "The following observations and grades were determined before this call.\n"
        "You MUST build your analysis from this evidence. Do not contradict it.\n\n"
        "OBSERVATIONS:\n"
        f"{json.dumps(observations, ensure_ascii=False, indent=2)}\n\n"
        "GRADES:\n"
        f"{json.dumps(diagnostic, ensure_ascii=False, indent=2)}\n\n"
        f"report_mode is already set to: {report_mode or report.advanced_details.report_mode}\n"
        f"foundational_missing_piece is already set to: {foundational or report.advanced_details.foundational_missing_piece}\n\n"
        "Your job is to write the coaching output only. Do not re-diagnose.\n"
        "Do not change report_mode. Do not introduce flaws not present in the grades above.\n\n"
    )


def _build_narrative_prompt(report: CoachingReportSchema) -> str:
    evidence_block = _preanalyzed_evidence_block(report)
    return (
        evidence_block
        +
        "SECOND PASS — FINAL COACH NARRATIVE.\n"
        "You already produced structured diagnosis JSON. Now write the final report like Gemini direct video upload at its best.\n"
        "Use the actual video, verified stills, phase evidence, and this structured diagnosis as grounding.\n"
        "Lead with the practical coach verdict first: overall rating out of 10, biggest positive, main issue, and one best fix.\n"
        "Calibrate the overall rating from checkpoint grades and flaw count — multiple constraints means 6.0 or lower, not 7+.\n"
        "Use concise, decisive coach language before the deeper breakdown. Do not invent visible details.\n"
        "If a detail is uncertain, say so in Confidence/visibility limitations.\n"
        "Posture/setup may be main only when the evidence clearly supports it over path, face, head, arms, sequencing, and impact.\n"
        "If the structured diagnosis says setup is context and the main_fix/foundational_missing_piece names a dynamic issue, "
        "keep the final main fault and main_fix on that dynamic issue. Do not pull the report back to a posture-only lesson.\n\n"
        "Return JSON only with keys:\n"
        "analysis, main_fix, secondary_fix, tips (array), drill_name, drill_why, drill_how, next_check.\n\n"
        "analysis MUST be 350-800 words when video is usable and MUST include these exact section titles:\n"
        + "\n".join(_NARRATIVE_SECTION_TITLES)
        + "\n\nStructured diagnosis JSON:\n"
        + json.dumps(report.model_dump(), ensure_ascii=False)
    )


def _call_narrative_gemini(
    client: genai.Client,
    model: str,
    content_parts: list[types.Part],
    report: CoachingReportSchema,
    *,
    trace_id: str | None = None,
    report_id: str | None = None,
    user_id: str | None = None,
    raw_attempts: list[dict] | None = None,
) -> CoachingReportSchema:
    settings = get_settings()
    log_trace(
        "gemini_narrative_request_sent",
        trace_id=trace_id,
        user_id=user_id,
        report_id=report_id,
        status="sent",
        mode="narrative_json",
        model=model,
    )
    response = client.models.generate_content(
        model=model,
        contents=[
            types.Content(
                role="user",
                parts=[
                    *content_parts,
                    types.Part.from_text(text=_build_narrative_prompt(report)),
                ],
            )
        ],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            system_instruction=COACHING_SYSTEM,
            temperature=settings.gemini_temperature,
            top_p=settings.gemini_top_p,
            max_output_tokens=settings.gemini_max_output_tokens,
            media_resolution=types.MediaResolution.MEDIA_RESOLUTION_HIGH,
            thinking_config=types.ThinkingConfig(thinking_budget=-1),
        ),
    )
    text = response.text or "{}"
    raw_record: dict | None = None
    if raw_attempts is not None:
        raw_record = {"kind": "narrative", "model": model, "raw_text": text}
        raw_attempts.append(raw_record)
    parsed = _parse_narrative_json(text)
    if raw_record is not None:
        raw_record["parsed_json"] = parsed
    updated = _apply_narrative_response(report, parsed)
    if raw_record is not None:
        raw_record["converted_report"] = {
            "pga_analysis": updated.pga_analysis,
            "main_fix": updated.main_fix,
            "advanced_details": updated.advanced_details.model_dump(),
        }
    log_trace(
        "gemini_narrative_response_received",
        trace_id=trace_id,
        user_id=user_id,
        report_id=report_id,
        status="ok",
        model=model,
    )
    return updated


def _profile_value(player_context: str | None, labels: tuple[str, ...], fallback: object = None) -> str:
    if fallback not in (None, ""):
        return str(fallback)
    text = player_context or ""
    for label in labels:
        match = re.search(rf"{re.escape(label)}\s*:\s*([^.\n]+)", text, flags=re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return "Not provided"


def _build_locked_context(observation: GeminiReportOut, grading: GeminiReportOut) -> str:
    """Serialise Call 1 + Call 2 outputs as locked context text for Call 3 (no video)."""
    obs_payload = {
        "camera_angle": observation.camera_angle,
        "usability_note": observation.usability_note,
        "observations": observation.observations.model_dump() if observation.observations else {},
    }
    grade_payload = {
        "grades": grading.grades.model_dump() if grading.grades else {},
        "report_mode": grading.report_mode or "development",
        "foundational_missing_piece": grading.foundational_missing_piece,
        "secondary_fix": grading.secondary_fix,
        "miss_pattern_match": grading.miss_pattern_match or "low",
        "miss_conflict_note": grading.miss_conflict_note,
        "confidence": grading.confidence,
    }
    return (
        "=== LOCKED EVIDENCE — OBSERVATION AND GRADING PASSES (DO NOT CONTRADICT) ===\n\n"
        "[CALL 1 — VIDEO OBSERVATION]\n"
        + json.dumps(obs_payload, indent=2)
        + "\n\n[CALL 2 — GRADED CHECKPOINTS]\n"
        + json.dumps(grade_payload, indent=2)
        + "\n\n=== END LOCKED EVIDENCE ===\n\n"
        "Coaching rules for Call 3:\n"
        "- Reflect all Call 2 grades in diagnostic_checkpoints and evidence_metrics.\n"
        "- Use foundational_missing_piece as the primary fix target.\n"
        "- If report_mode is 'maintenance', write preservation-focused coaching.\n"
        "- Do NOT invent observations absent from Call 1. Honour not_visible limitations.\n"
    )


def _call_json_with_retry(
    api_call_fn: "Callable[[], GeminiReportOut]",
    *,
    label: str = "call",
    max_retries: int = 1,
) -> GeminiReportOut:
    """Make a Gemini API call and parse JSON. Retries once on parse failure."""
    last_exc: Exception | None = None
    for attempt in range(max_retries + 1):
        try:
            return api_call_fn()
        except (json.JSONDecodeError, ValueError) as exc:
            last_exc = exc
            if attempt < max_retries:
                logger.warning(
                    "JSON parse error on %s (attempt %d/%d), retrying: %s",
                    label,
                    attempt + 1,
                    max_retries + 1,
                    exc,
                )
    raise last_exc or ValueError(f"{label} failed after {max_retries + 1} attempt(s)")


def _call_observation_gemini(
    client: genai.Client,
    model: str,
    visual_parts: list[types.Part],
    *,
    trace_id: str | None = None,
    report_id: str | None = None,
    user_id: str | None = None,
    raw_attempts: list[dict] | None = None,
) -> GeminiReportOut:
    """Call 1 — video + phase evidence → raw per-phase observations + video_usability."""
    settings = get_settings()
    log_trace(
        "gemini_observation_request_sent",
        trace_id=trace_id,
        user_id=user_id,
        report_id=report_id,
        status="sent",
        model=model,
    )
    response = client.models.generate_content(
        model=model,
        contents=[types.Content(role="user", parts=visual_parts)],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_json_schema=GEMINI_RESPONSE_JSON_SCHEMA,
            system_instruction=OBSERVATION_SYSTEM,
            temperature=settings.gemini_temperature,
            top_p=settings.gemini_top_p,
            max_output_tokens=settings.gemini_max_output_tokens,
            media_resolution=types.MediaResolution.MEDIA_RESOLUTION_HIGH,
            thinking_config=types.ThinkingConfig(thinking_budget=-1),
        ),
    )
    text = response.text or "{}"
    raw_record: dict | None = None
    if raw_attempts is not None:
        raw_record = {"kind": "call1_observation", "model": model, "raw_text": text}
        raw_attempts.append(raw_record)
    parsed = parse_gemini_json(text, trace_id=trace_id, report_id=report_id, user_id=user_id)
    if raw_record is not None:
        raw_record["parsed_json"] = parsed.model_dump()
    log_trace(
        "gemini_observation_response_received",
        trace_id=trace_id,
        user_id=user_id,
        report_id=report_id,
        status="ok",
        model=model,
    )
    return parsed


def _build_diagnostic_prompt(
    *,
    raw_observations_json: str,
    player_context: str | None,
    years_playing: int | None,
    player_age: int | None = None,
    physical_limitations: str | None = None,
) -> str:
    miss = _profile_value(player_context, ("Typical miss", "Miss"))
    score = _profile_value(player_context, ("Average 9-hole score", "Average score", "Score"))
    years = _profile_value(player_context, ("Years playing", "Years"), years_playing)
    goal = _profile_value(player_context, ("Main goal", "Goals", "Goal"))
    physical_block = _format_physical_boundaries_block(
        age=player_age,
        years_playing=years_playing,
        physical_limitations=physical_limitations,
    )
    physical_section = f"\n\n{physical_block}" if physical_block else ""
    return f"""You are a golf diagnostic engine. You will receive raw swing observations and a golfer profile.
Your job is to grade each checkpoint and determine report_mode BEFORE any coaching language is written.

GOLFER PROFILE:
- Typical miss: {miss}
- Average score: {score}
- Years playing: {years}
- Goals: {goal}
{physical_section}

RAW OBSERVATIONS:
{raw_observations_json}

GRADING RULES:
- Grade each visible phase: Optimal | Compensating | Constraint | Not Visible
- A phase is Optimal ONLY if the observation contains zero mechanical inefficiency
- A phase is Constraint if it is the earliest link causing downstream issues
- Do NOT grade a phase Constraint unless at least one downstream phase shows a visible symptom
- If 5 or more phases are Optimal and no Constraint exists → report_mode = maintenance
- If ANY Constraint phase exists with downstream symptoms → report_mode = development
- If unsure between maintenance and development → development with medium confidence
- When physical limitations imply a mobility ceiling, grade compensations fairly — do not mark Constraint
  for moves the body cannot make without visible downstream symptoms on film

MISS PATTERN CROSS-CHECK:
- Does the graded Constraint logically explain the player's typical miss ({miss})?
- If yes → confidence high. If partial match → medium. If no match → low, flag conflict.

Return JSON only:
{{
  "grades": {{
    "setup": {{ "grade": "...", "reason": "one line" }},
    "takeaway": {{ "grade": "...", "reason": "one line" }},
    "backswing": {{ "grade": "...", "reason": "one line" }},
    "transition": {{ "grade": "...", "reason": "one line" }},
    "downswing": {{ "grade": "...", "reason": "one line" }},
    "impact": {{ "grade": "...", "reason": "one line" }},
    "finish": {{ "grade": "...", "reason": "one line" }}
  }},
  "report_mode": "maintenance | development",
  "foundational_missing_piece": "...",
  "secondary_fix": "...",
  "miss_pattern_match": "high | medium | low",
  "miss_conflict_note": "...",
  "confidence": 0.0
}}"""


def _call_diagnostic_gemini(
    client: genai.Client,
    model: str,
    raw_observations_json: str,
    *,
    player_context: str | None,
    years_playing: int | None,
    player_age: int | None = None,
    physical_limitations: str | None = None,
    trace_id: str | None = None,
    report_id: str | None = None,
    user_id: str | None = None,
    raw_attempts: list[dict] | None = None,
) -> GeminiReportOut:
    settings = get_settings()
    log_trace(
        "gemini_diagnostic_request_sent",
        trace_id=trace_id,
        user_id=user_id,
        report_id=report_id,
        status="sent",
        mode="diagnostic_json",
        model=model,
    )
    try:
        response = client.models.generate_content(
            model=model,
            contents=[
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_text(
                            text=_build_diagnostic_prompt(
                                raw_observations_json=raw_observations_json,
                                player_context=player_context,
                                years_playing=years_playing,
                                player_age=player_age,
                                physical_limitations=physical_limitations,
                            )
                        )
                    ],
                )
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_json_schema=DIAGNOSTIC_RESPONSE_JSON_SCHEMA,
                system_instruction=DIAGNOSTIC_SYSTEM,
                temperature=settings.gemini_temperature,
                top_p=settings.gemini_top_p,
                max_output_tokens=settings.gemini_max_output_tokens,
                thinking_config=types.ThinkingConfig(thinking_budget=-1),
            ),
        )
        text = response.text or "{}"
        raw_record: dict | None = None
        if raw_attempts is not None:
            raw_record = {"kind": "diagnostic", "model": model, "raw_text": text}
            raw_attempts.append(raw_record)
        diagnostic = parse_gemini_json(
            text,
            trace_id=trace_id,
            report_id=report_id,
            user_id=user_id,
        )
        if raw_record is not None:
            raw_record["parsed_json"] = diagnostic.model_dump()
        log_trace(
            "gemini_diagnostic_response_received",
            trace_id=trace_id,
            user_id=user_id,
            report_id=report_id,
            status="ok",
            model=model,
        )
        return diagnostic
    except Exception as exc:
        log_trace(
            "gemini_diagnostic_response_received",
            trace_id=trace_id,
            user_id=user_id,
            report_id=report_id,
            status="error",
            model=model,
            error=str(exc)[:500],
        )
        raise


def _apply_diagnostic_report(
    report: CoachingReportSchema,
    diagnostic: GeminiReportOut,
    *,
    swing_mode: SwingMode,
) -> CoachingReportSchema:
    observer_payload = json.loads(report.pga_analysis or "{}")
    if not isinstance(observer_payload, dict) or "observations" not in observer_payload:
        return report
    combined = {
        **observer_payload,
        "grades": diagnostic.grades.model_dump() if diagnostic.grades else {},
        "report_mode": diagnostic.report_mode or "development",
        "foundational_missing_piece": diagnostic.foundational_missing_piece,
        "secondary_fix": diagnostic.secondary_fix,
        "miss_pattern_match": diagnostic.miss_pattern_match or "low",
        "miss_conflict_note": diagnostic.miss_conflict_note,
        "confidence": diagnostic.confidence,
    }
    updated = gemini_out_to_coaching_report(GeminiReportOut.model_validate(combined))
    if not updated.disclaimer:
        updated.disclaimer = DISCLAIMER
    return _normalize_report(updated)


def _preserve_preanalyzed_diagnosis(
    original: CoachingReportSchema,
    updated: CoachingReportSchema,
) -> CoachingReportSchema:
    original_adv = original.advanced_details
    updated_adv = updated.advanced_details.model_copy(
        update={
            "report_mode": original_adv.report_mode,
            "foundational_missing_piece": original_adv.foundational_missing_piece,
            "diagnostic_checkpoints": original_adv.diagnostic_checkpoints,
            "root_cause": original_adv.root_cause,
            "symptom": original_adv.symptom,
            "evidence_metrics": original_adv.evidence_metrics,
            "secondary_fix": original_adv.secondary_fix,
            "optional_fix": original_adv.optional_fix,
            "chain_reaction": original_adv.chain_reaction,
            "why_it_caused_the_miss": original_adv.why_it_caused_the_miss,
            "confidence_score": original_adv.confidence_score,
            "next_checkpoint": original_adv.next_checkpoint,
        }
    )
    return updated.model_copy(update={"advanced_details": updated_adv})


def _call_gemini(
    client: genai.Client,
    model: str,
    content_parts: list[types.Part],
    swing_mode: SwingMode = "full_swing",
    *,
    trace_id: str | None = None,
    report_id: str | None = None,
    user_id: str | None = None,
    raw_attempts: list[dict] | None = None,
) -> CoachingReportSchema:
    settings = get_settings()
    log_trace(
        "gemini_request_sent",
        trace_id=trace_id,
        user_id=user_id,
        report_id=report_id,
        status="sent",
        mode="json_only",
        model=model,
    )
    config = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_json_schema=GEMINI_COACHING_SCHEMA,
        system_instruction=COACHING_SYSTEM,
        temperature=settings.gemini_temperature,
        top_p=settings.gemini_top_p,
        max_output_tokens=settings.gemini_max_output_tokens,
        media_resolution=types.MediaResolution.MEDIA_RESOLUTION_HIGH,
        thinking_config=types.ThinkingConfig(thinking_budget=-1),
    )
    try:
        response = client.models.generate_content(
            model=model,
            contents=[types.Content(role="user", parts=content_parts)],
            config=config,
        )
        text = response.text or "{}"
        raw_record: dict | None = None
        if raw_attempts is not None:
            raw_record = {"kind": "call3_coaching", "model": model, "raw_text": text}
            raw_attempts.append(raw_record)
        raw = parse_gemini_json(
            text,
            trace_id=trace_id,
            report_id=report_id,
            user_id=user_id,
        )
        if raw_record is not None:
            raw_record["parsed_json"] = raw.model_dump()
        report = gemini_out_to_coaching_report(raw)
        if raw_record is not None:
            raw_record["converted_report"] = {
                "pga_analysis": report.pga_analysis,
                "main_fix": report.main_fix,
                "advanced_details": report.advanced_details.model_dump(),
            }
        if not report.disclaimer:
            report.disclaimer = DISCLAIMER
        report = _normalize_report(report)
        log_trace(
            "gemini_response_received",
            trace_id=trace_id,
            user_id=user_id,
            report_id=report_id,
            status="ok",
            model=model,
        )
        return report
    except Exception as exc:
        log_trace(
            "gemini_response_received",
            trace_id=trace_id,
            user_id=user_id,
            report_id=report_id,
            status="error",
            model=model,
            error=str(exc)[:500],
        )
        raise


def generate_coaching_report(
    *,
    video_path: Path | None,
    frames: list[np.ndarray] | None,
    phase_result: PhaseDetectionResult | None,
    swing_window: dict | None = None,
    swing_mode: SwingMode = "full_swing",
    pose_sequence=None,
    history_summary: str | None,
    player_name: str | None = None,
    swing_number: int | None = None,
    player_context: str | None = None,
    player_age: int | None = None,
    years_playing: int | None = None,
    physical_limitations: str | None = None,
    trace_id: str | None = None,
    report_id: str | None = None,
    user_id: str | None = None,
) -> tuple[CoachingReportSchema, bool, dict]:
    settings = get_settings()
    meta: dict = {"model_used": None, "error": None, "video_attached": False, "raw_responses": []}

    if not settings.gemini_api_key:
        logger.warning("GEMINI_API_KEY not set; using fallback report")
        meta["error"] = "GEMINI_API_KEY not configured"
        return _fallback_report(meta["error"], player_name, swing_mode), False, meta

    prompt = _build_prompt(
        swing_mode=swing_mode,
        history_summary=history_summary,
        player_name=player_name,
        swing_number=swing_number,
        player_context=player_context,
        player_age=player_age,
        years_playing=years_playing,
        physical_limitations=physical_limitations,
    )

    client = genai.Client(api_key=settings.gemini_api_key)
    uploaded_file: types.File | None = None
    errors: list[str] = []

    try:
        # ── Call 1 visual parts: video + phase evidence + keyframes ──────────
        call1_visual_parts: list[types.Part] = []

        if video_path and video_path.exists():
            logger.info("Uploading swing video for Call 1 observation...")
            uploaded_file = upload_video(client, video_path)
            meta["video_attached"] = True
            file_uri = uploaded_file.uri
            if not file_uri and uploaded_file.name:
                file_uri = f"https://generativelanguage.googleapis.com/v1beta/{uploaded_file.name}"
            call1_visual_parts.append(
                types.Part.from_uri(
                    file_uri=file_uri,
                    mime_type=uploaded_file.mime_type or "video/mp4",
                )
            )
            mode_label = {"full_swing": "swing", "chipping": "chip", "putting": "putting stroke"}.get(
                swing_mode, "swing"
            )
            call1_visual_parts.append(
                types.Part.from_text(
                    text=(
                        f"Watch the {mode_label} video first — it is the primary truth for motion, club, and timing.\n"
                        "Then use the PHASE EVIDENCE PACKET:\n"
                        "- pose_tracking.pose_timeline = server-computed body curves over the swing window\n"
                        "- pose_tracking.phase_metrics = geometry only for pose-validated phase frames\n"
                        "- phases[] = approximate anchors; keyframe stills are sent ONLY for pose-validated phases\n"
                        "Describe what you see in each phase. Inspect address posture, visual body lines, "
                        "takeaway shaft/clubface, top-of-backswing arm and face structure, transition sequencing, "
                        "downswing hip/chest clearing, shaft plane, head level, impact-window geometry, and finish "
                        "balance. When pose_timeline or phase_metrics conflict with visible video motion, trust the "
                        "video and note the mismatch in usability_note or phase not_visible fields. "
                        "Describe the club, the body, and any camera limitations with enough detail that "
                        "another coach could reconstruct the motion. Do NOT diagnose, coach, or grade. Return the "
                        "requested JSON only."
                    )
                )
            )

        if phase_result:
            call1_visual_parts.append(
                types.Part.from_text(
                    text=(
                        "PHASE EVIDENCE PACKET (server-verified; treat as authoritative):\n"
                        + build_phase_evidence_packet(phase_result, swing_window, pose_sequence)
                    )
                )
            )

        if frames and phase_result:
            call1_visual_parts.extend(
                build_keyframe_parts(frames, phase_result, swing_mode, pose_sequence)
            )

        for model in _models_to_try(settings.gemini_model, settings.gemini_fallback_model):
            try:
                # ── Call 1: Observation (video + phase evidence → raw observations) ──
                logger.info("Call 1 — observation with %s...", model)
                observation = _call_json_with_retry(
                    lambda: _call_observation_gemini(
                        client,
                        model,
                        call1_visual_parts,
                        trace_id=trace_id,
                        report_id=report_id,
                        user_id=user_id,
                        raw_attempts=meta["raw_responses"],
                    ),
                    label="call1_observation",
                )

                # Poor video → stop the chain and ask for re-upload
                if observation.video_usability == "poor":
                    reason = observation.usability_note or "Video quality blocked analysis."
                    logger.warning("Call 1 returned video_usability=poor: %s", reason)
                    meta["error"] = reason
                    return _fallback_report(reason, player_name, swing_mode), False, meta

                # ── Call 2: Grading (text only — no video) ───────────────────────
                logger.info("Call 2 — grading with %s...", model)
                obs_json = json.dumps(
                    {
                        "camera_angle": observation.camera_angle,
                        "usability_note": observation.usability_note,
                        "observations": observation.observations.model_dump()
                        if observation.observations
                        else {},
                    },
                    indent=2,
                )
                grading = _call_json_with_retry(
                    lambda: _call_diagnostic_gemini(
                        client,
                        model,
                        obs_json,
                        player_context=player_context,
                        years_playing=years_playing,
                        player_age=player_age,
                        physical_limitations=physical_limitations,
                        trace_id=trace_id,
                        report_id=report_id,
                        user_id=user_id,
                        raw_attempts=meta["raw_responses"],
                    ),
                    label="call2_grading",
                )

                # ── Call 3: Coaching report (text only — locked context + prompt) ─
                locked_context = _build_locked_context(observation, grading)
                call3_parts = [
                    types.Part.from_text(text=locked_context),
                    types.Part.from_text(text=prompt),
                ]
                logger.info("Call 3 — coaching report with %s...", model)
                report = _audit_with_revisions(
                    client,
                    model,
                    call3_parts,
                    swing_mode=swing_mode,
                    player_context=player_context,
                    history_summary=history_summary,
                    phase_map=phase_result.phase_map if phase_result else None,
                    max_revisions=settings.gemini_max_quality_revisions,
                    trace_id=trace_id,
                    report_id=report_id,
                    user_id=user_id,
                    locked_observation=observation,
                    locked_grading=grading,
                    raw_attempts=meta["raw_responses"],
                )
                meta["model_used"] = model
                return report, True, meta
            except ReportQualityError as exc:
                err = f"{model}: {exc}"
                logger.warning("Gemini report failed quality audit after revisions: %s", err)
                meta["error"] = err[:300]
                raise ReportQualityError(err) from exc
            except Exception as exc:
                err = f"{model}: {exc}"
                logger.warning("Gemini model failed: %s", err)
                errors.append(err)
                if not _is_retryable_model_error(exc):
                    break

        last_error = errors[-1] if errors else "Unknown Gemini error"
        if "429" in last_error or "quota" in last_error.lower():
            meta["error"] = "Gemini API quota exceeded — enable billing or wait and retry"
        else:
            meta["error"] = last_error[:300]
        return _fallback_report(meta["error"], player_name, swing_mode), False, meta
    except ReportQualityError:
        raise
    except Exception as exc:
        logger.exception("Gemini coaching report failed: %s", exc)
        meta["error"] = str(exc)[:300]
        return _fallback_report(meta["error"], player_name, swing_mode), False, meta
    finally:
        delete_uploaded_file(client, uploaded_file)
