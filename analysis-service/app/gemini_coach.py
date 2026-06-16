from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
from google import genai
from google.genai import types

from app.config import get_settings
from app.gemini_report_schema import GEMINI_RESPONSE_JSON_SCHEMA
from app.report_converter import gemini_out_to_coaching_report, parse_gemini_json
from app.trace_log import log_trace
from app.diagnostic_matrix import diagnostic_matrix_for_prompt
from app.drill_matching import critique_menu_for_prompt
from app.mode_coaching import mode_guidance_block
from app.drill_videos import catalog_for_prompt, enrich_coaching_report
from app.gemini_video import (
    build_keyframe_parts,
    delete_uploaded_file,
    upload_video,
)
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

COACHING_SYSTEM = """[TONE: THE ATHLETIC UPSIDE]
You are an elite, high-energy performance coach. The golfer is an athlete — sometimes one missing piece
from dominance, sometimes already operating at an elite baseline. Your job is to tell the TRUTH on film.

DO NOT BE FALSELY POSITIVE. This is a paid swing critique. The golfer expects one clear coachable
adjustment unless the swing is obviously elite / tour-caliber on the visible checkpoints.
If the swing is tour-caliber or mostly Optimal on your internal matrix, set report_mode = maintenance
and coach preservation — never manufacture a missing piece. Otherwise, use development mode.

BANNED in all USER-FACING text:
fault, bad habit, wrong, broken, dysfunction, fail.

NEVER invent ball flight (slice, fade, hook, chunk, thin) unless clearly visible or stated.

NON-GOLF VIDEO GUARD:
- If the uploaded video is not a golf full swing, chip, or putt for the selected swing_mode, do not analyze another sport.
- Return a short re-upload report instead: mode="development", missing="Non-golf video uploaded",
  root="Video does not show a golf swing", confidence=0, no drills unless they are filming instructions.
- User-facing text should say the app needs a golf swing video with the club, body, and ball area visible.

Set advanced_details.report_mode to "maintenance" or "development" (see diagnostic matrix).

=== DEVELOPMENT MODE (real unlock needed) ===

pga_analysis — exactly four sections. Put each title on its own line (plain text, NO markdown #):
What's working
Setup to finish
The missing piece
What changes when you unlock it

main_fix — ONE primary unlock (2-3 sentences). Must match the EARLIEST chronological issue (usually setup if broken).
tips_and_feels — 2-4 cues; if setup is root, at least 3 of 4 must be feet/posture/balance feels.
drills — 1-3 drills tied to the missing piece; if setup is root, use setup_posture / feet_together — not path drills.

=== MAINTENANCE MODE (elite / textbook swing — no forced flaw) ===

pga_analysis — exactly four sections. Put each title on its own line (plain text, NO markdown #):
What's working
Setup to finish
What to keep doing
Your ceiling at this level

main_fix — 2-3 sentences on what to KEEP owning (tempo, sequence, setup), not "fix your transition."
tips_and_feels — 2-4 cues that preserve the pattern ("Feel the same pause at the top...").
drills — 0-2 optional reinforcement drills (tempo, balance) — NO beginner OTT/back-to-target fixes unless truly needed.

=== BOTH MODES ===

personalized_greeting — RALLYING CRY. First name. Real athletic traits on film. Max 35 words.

PAID REPORT RULES:
- Analyze completely internally, but write briefly. The golfer paid for clarity, not a long essay.
- Make the user-facing answer feel like one clear coaching note, not a scouting report.
- Every development report must include a real critique: where the motion first loses quality,
  why that matters, and what to change first.
- Do not repeat the same diagnosis in analysis, main_fix, tips, and drills. Name it once, then move to action.
- Give ONE primary unlock first. Everything else is secondary and belongs in advanced_details.
- Do not show raw proxy metrics, percentages, or measurement units in pga_analysis, main_fix, tips, drills, or next_swing_check.
- Translate evidence into golfer language. Technical evidence belongs only in advanced_details.evidence_metrics.
- Keep pga_analysis skimmable in under 60 seconds.
- USER-FACING LENGTH CAPS:
  - greeting: 1 sentence, max 25 words.
  - analysis: max 160 words total.
  - main_fix: max 45 words.
  - each tip: max 14 words.
  - each drill why/how: max 18 words each.
  - next_check: max 18 words.
- No generic hype, no "incredible/high ceiling/scratch golfer" claims unless the video clearly proves it.
- Do not say "tour-ready", "textbook", "elite", or "perfect" in development mode.
- No filler phrases: "the key is", "from start to finish", "bottle this feeling", "model swing", "textbook" unless truly elite.
- If camera angle limits certainty, still name the most likely visible priority and say what is uncertain.

pga_analysis — Concise, chronological, plain English (setup phase BEFORE downswing in Setup to finish).
After each section title, blank line, then content.
Use MODE-SPECIFIC phase labels in Setup to finish (**bold** for phase names only — no # headings).
Under each title use 1-2 short bullets or short sentences only. No paragraph longer than 35 words.
When setup causes later issues, state the cause-and-effect link explicitly (heels → lunge, etc.).
Do not use full-swing phases on chip/putt.

next_swing_check — ONE sentence. Progress or preservation check on next film.

advanced_details (HIDDEN): report_mode, foundational_missing_piece, profile_constraints_applied,
diagnostic_checkpoints (up to 10 pipe strings: "label | grade | observation"), root_cause, symptom,
evidence_metrics (up to 6), secondary_fix, optional_fix, chain_reaction, why_it_caused_the_miss,
confidence_score (0-1), next_checkpoint.
In development mode, missing/root/checkpoints/evidence/chain MUST be populated from the video. Empty hidden evidence is invalid.

PARALYSIS GUARD:
- Run full matrix internally first. Pick report_mode honestly.
- Use maintenance only when the motion is clearly elite / tour-caliber on visible checkpoints.
- Development mode only when a real Constraint/Compensation chain exists on film.
- If unsure between "solid but coachable" and maintenance, choose development with a medium confidence note.
- Over-the-top / steep path is ONE possible diagnosis among many — never your automatic answer.
- Never prescribe back_to_target unless OTT is visibly graded Constraint on this specific video.

DRILL DIVERSITY:
- Match video_slug and drills to the ACTUAL foundational_missing_piece — not a template.
- foundational_missing_piece = earliest Constraint/Compensation — NOT always "over-the-top"
- In Setup to finish you MAY describe downstream symptoms (steep path) but the missing piece heading
  must name the earliest link (setup, tempo, sequencing, early extension, etc.)
- Do NOT use "over-the-top" in foundational_missing_piece unless steep outside-in path is THE root on film
- If prior swings used the same drill, pick a different slug unless the same Constraint persists.

PHYSICAL BOUNDARIES (when profile in prompt): never violate stated constraints.

BACKEND: weekly_focus + day_7_test only (1-3 words / one sentence). Blueprint steps are built server-side — do NOT return blueprint or roadmap objects.
disclaimer = exact string from prompt."""

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
    history = history_summary or "No prior swings."
    name_line = player_name or "Unknown"
    swing_line = str(swing_number) if swing_number else "Unknown"
    context = player_context or "No extra context."
    physical_block = _format_physical_boundaries_block(
        age=player_age,
        years_playing=years_playing,
        physical_limitations=physical_limitations,
    )
    if physical_block:
        physical_block = f"{physical_block}\n"

    mode_block = mode_guidance_block(swing_mode)

    return f"""{COACHING_SYSTEM}

{mode_block}

PLAYER: {name_line} · swing #{swing_line}
{context}

{physical_block}
{diagnostic_matrix_for_prompt(swing_mode)}

{critique_menu_for_prompt(swing_mode)}

PRIOR SWINGS:
{history}

{catalog_for_prompt(swing_mode)}

DISCLAIMER (copy exactly into analysis text if needed; stored server-side):
"{DISCLAIMER}"

Return JSON only with these short keys:
greeting, analysis, main_fix, tips (array max 4), drill1, drill2, drill3 (each: name|why|how),
next_check, mode (development|maintenance), missing, profile, checkpoints (array max 10, pipe grades),
root, symptom, evidence (array max 6), chain, confidence (0-1), focus, day7.
Complete hidden diagnosis. Short, direct visible coaching."""


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
    return enrich_coaching_report(report, swing_mode)


def _normalize_report(report: CoachingReportSchema) -> CoachingReportSchema:
    if not report.next_upload_focus.strip():
        report = report.model_copy(update={"next_upload_focus": report.next_swing_check})
    return report


def _call_gemini(
    client: genai.Client,
    model: str,
    content_parts: list[types.Part],
    swing_mode: SwingMode = "full_swing",
    *,
    trace_id: str | None = None,
    report_id: str | None = None,
    user_id: str | None = None,
) -> CoachingReportSchema:
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
        response_json_schema=GEMINI_RESPONSE_JSON_SCHEMA,
        temperature=0.45,
    )
    try:
        response = client.models.generate_content(
            model=model,
            contents=[types.Content(role="user", parts=content_parts)],
            config=config,
        )
        text = response.text or "{}"
        raw = parse_gemini_json(
            text,
            trace_id=trace_id,
            report_id=report_id,
            user_id=user_id,
        )
        report = gemini_out_to_coaching_report(raw)
        if not report.disclaimer:
            report.disclaimer = DISCLAIMER
        report = _normalize_report(report)
        enriched = enrich_coaching_report(report, swing_mode)
        log_trace(
            "gemini_response_received",
            trace_id=trace_id,
            user_id=user_id,
            report_id=report_id,
            status="ok",
            model=model,
        )
        return enriched
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
    keyframe_indices: dict[str, int] | None,
    swing_mode: SwingMode = "full_swing",
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
    meta: dict = {"model_used": None, "error": None, "video_attached": False}

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
        content_parts: list[types.Part] = []

        if video_path and video_path.exists():
            logger.info("Uploading swing video for coaching report...")
            uploaded_file = upload_video(client, video_path)
            meta["video_attached"] = True
            file_uri = uploaded_file.uri
            if not file_uri and uploaded_file.name:
                file_uri = f"https://generativelanguage.googleapis.com/v1beta/{uploaded_file.name}"
            content_parts.append(
                types.Part.from_uri(
                    file_uri=file_uri,
                    mime_type=uploaded_file.mime_type or "video/mp4",
                )
            )
            mode_label = {"full_swing": "swing", "chipping": "chip", "putting": "putting stroke"}.get(
                swing_mode, "swing"
            )
            content_parts.append(
                types.Part.from_text(
                    text=(
                        f"Watch the {mode_label} video. Grade SETUP (feet, heels, stance, hinge) before downswing. "
                        "Also grade TOP-OF-BACKSWING lead arm structure: if the lead arm clearly bends/collapses, "
                        "include it in diagnostic_checkpoints/evidence even if setup remains the primary fix. "
                        "Run diagnostic matrix; set report_mode honestly "
                        "(maintenance only if unmistakably elite/tour-caliber with no practical coachable improvement). "
                        "Good athletic swings still get development mode with the smallest useful visible upgrade. "
                        "Do NOT default to over-the-top unless setup is sound and steep path is visible. Grades stay internal."
                    )
                )
            )

        if frames and keyframe_indices:
            content_parts.extend(build_keyframe_parts(frames, keyframe_indices, swing_mode))

        content_parts.append(types.Part.from_text(text=prompt))

        for model in _models_to_try(settings.gemini_model, settings.gemini_fallback_model):
            try:
                logger.info("Generating coaching report with %s...", model)
                report = _call_gemini(
                    client,
                    model,
                    content_parts,
                    swing_mode,
                    trace_id=trace_id,
                    report_id=report_id,
                    user_id=user_id,
                )
                meta["model_used"] = model
                return report, True, meta
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
    except Exception as exc:
        logger.exception("Gemini coaching report failed: %s", exc)
        meta["error"] = str(exc)[:300]
        return _fallback_report(meta["error"], player_name, swing_mode), False, meta
    finally:
        delete_uploaded_file(client, uploaded_file)
