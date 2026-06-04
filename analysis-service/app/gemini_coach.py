from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
from google import genai
from google.genai import types

from app.config import get_settings
from app.drill_videos import catalog_for_prompt, enrich_coaching_report
from app.gemini_video import (
    build_keyframe_parts,
    delete_uploaded_file,
    upload_video,
)
from app.schemas import (
    AccountabilityPlan,
    BlueprintStep,
    CoachingReportSchema,
    DiagnosticTruth,
    DISCLAIMER,
    KinestheticBlueprint,
    MilestoneBlock,
)

logger = logging.getLogger(__name__)

COACHING_SYSTEM = """You are a sharp, on-the-range coach. Short sentences. Zero fluff. Every word earns attention.

NO scores. NO report-card language. NO long paragraphs.

VOICE:
- Talk like a caddie between shots — direct, confident, human.
- Physics in plain English: steep path → body stands up → slice. Done.
- One feel per step. One job this week. They should read the whole thing in under 90 seconds.

PERSONALIZATION (required when player info is provided):
- Use their first name in personalized_greeting.
- First swing ever → welcome them, set one clear focus.
- Returning player → reference last week's focus or pattern; note if the same fault persists or if they improved.
- Make them feel the app remembers them — that's why they'll come back.

BREVITY LIMITS (hard caps — shorter is better):
- personalized_greeting: max 35 words
- diagnostic fields: see schema
- blueprint.intro: one sentence
- feel: max 15 words — this is the line they repeat over the ball
- milestone detail: max 2 short sentences each
- day_7_test: one sentence
- next_upload_focus: max 20 words

THREE PARTS:

PART 1 — DIAGNOSTIC TRUTH
Ball flight → why → chain reaction. No lecturing.

PART 2 — KINESTHETIC BLUEPRINT
2-3 steps: setup → visual cue → constraint drill.
Each step needs video_slug from catalog. Leave video_url null.

PART 3 — 7-DAY ROADMAP
One weekly focus. Three milestones. One Day 7 test.

Use minimal Markdown (**bold** sparingly). No bullet dumps unless kinetic_chain.

OUTPUT: JSON matching schema. disclaimer = exact string from prompt."""


def _build_prompt(
    *,
    history_summary: str | None,
    player_name: str | None,
    swing_number: int | None,
    player_context: str | None,
) -> str:
    history = history_summary or "No prior swings."
    name_line = player_name or "Unknown (use 'there' sparingly — prefer no name if missing)"
    swing_line = str(swing_number) if swing_number else "Unknown"
    context = player_context or "No extra context."

    return f"""{COACHING_SYSTEM}

PLAYER
- First name: {name_line}
- This upload: swing #{swing_line} in our app
- Context: {context}

PRIOR SWINGS
{history}

{catalog_for_prompt()}

DISCLAIMER (copy exactly):
"{DISCLAIMER}"

Generate the personalized blueprint JSON. Short. Punchy. No scores."""


def _is_retryable_model_error(exc: Exception) -> bool:
    msg = str(exc)
    return any(
        token in msg
        for token in ("429", "RESOURCE_EXHAUSTED", "NOT_FOUND", "404", "quota")
    )


def _models_to_try(primary: str, fallback: str) -> list[str]:
    models: list[str] = []
    for model in (primary, fallback):
        if model and model not in models:
            models.append(model)
    return models


def _fallback_report(reason: str | None = None, player_name: str | None = None) -> CoachingReportSchema:
    note = reason or "Try again in a few minutes."
    name = (player_name or "there").split()[0]
    report = CoachingReportSchema(
        personalized_greeting=f"{name}, we couldn't build your blueprint this time. Re-upload when you're ready — we'll pick up where you left off.",
        diagnostic=DiagnosticTruth(
            headline="Analysis unavailable",
            what_your_eye_sees="Something blocked the video read.",
            mechanical_cause=note,
            kinetic_chain="- Re-upload with full body in frame\n- Stable camera, good light",
        ),
        blueprint=KinestheticBlueprint(
            headline="Try again",
            intro="Get a fresh blueprint on your next upload.",
            steps=[
                BlueprintStep(
                    title="Film it",
                    step_type="setup",
                    adjustment="Face-on or down-the-line. Full body in frame.",
                    feel="Tripod-steady — no shaky hands.",
                    video_slug="setup_posture",
                ),
                BlueprintStep(
                    title="Half-speed reps",
                    step_type="visual_cue",
                    action="25 balls at 50% with one feel only.",
                    feel="Hold the finish until the ball stops.",
                    success_condition="Balanced finish every rep.",
                    video_slug="slow_motion_reps",
                ),
            ],
        ),
        roadmap=AccountabilityPlan(
            weekly_focus="Re-upload",
            milestones=[
                MilestoneBlock(days="Today", title="Film", detail="One clean swing on video."),
                MilestoneBlock(days="Tomorrow", title="Upload", detail="Open your new blueprint."),
                MilestoneBlock(days="This week", title="Train", detail="Phase 1 only at the range."),
            ],
            day_7_test="New blueprint received and Phase 1 done at the range.",
        ),
        next_upload_focus="Full body, stable camera, good light.",
        disclaimer=DISCLAIMER,
    )
    return enrich_coaching_report(report)


def _call_gemini(
    client: genai.Client,
    model: str,
    content_parts: list[types.Part],
) -> CoachingReportSchema:
    response = client.models.generate_content(
        model=model,
        contents=[types.Content(role="user", parts=content_parts)],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=CoachingReportSchema,
            temperature=0.45,
        ),
    )
    text = response.text or "{}"
    report = CoachingReportSchema.model_validate_json(text)
    if DISCLAIMER not in report.disclaimer:
        report.disclaimer = DISCLAIMER
    return enrich_coaching_report(report)


def generate_coaching_report(
    *,
    video_path: Path | None,
    frames: list[np.ndarray] | None,
    keyframe_indices: dict[str, int] | None,
    history_summary: str | None,
    player_name: str | None = None,
    swing_number: int | None = None,
    player_context: str | None = None,
) -> tuple[CoachingReportSchema, bool, dict]:
    settings = get_settings()
    meta: dict = {"model_used": None, "error": None, "video_attached": False}

    if not settings.gemini_api_key:
        logger.warning("GEMINI_API_KEY not set; using fallback report")
        meta["error"] = "GEMINI_API_KEY not configured"
        return _fallback_report(meta["error"], player_name), False, meta

    prompt = _build_prompt(
        history_summary=history_summary,
        player_name=player_name,
        swing_number=swing_number,
        player_context=player_context,
    )

    client = genai.Client(api_key=settings.gemini_api_key)
    uploaded_file: types.File | None = None
    errors: list[str] = []

    try:
        content_parts: list[types.Part] = []

        if video_path and video_path.exists():
            logger.info("Uploading swing video for coaching blueprint...")
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
            content_parts.append(
                types.Part.from_text(
                    text="Full swing video above. Watch once, then write a short personalized blueprint."
                )
            )

        if frames and keyframe_indices:
            content_parts.extend(build_keyframe_parts(frames, keyframe_indices))

        content_parts.append(types.Part.from_text(text=prompt))

        for model in _models_to_try(settings.gemini_model, settings.gemini_fallback_model):
            try:
                logger.info("Generating coaching blueprint with %s...", model)
                report = _call_gemini(client, model, content_parts)
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
        return _fallback_report(meta["error"], player_name), False, meta
    except Exception as exc:
        logger.exception("Gemini coaching blueprint failed: %s", exc)
        meta["error"] = str(exc)[:300]
        return _fallback_report(meta["error"], player_name), False, meta
    finally:
        delete_uploaded_file(client, uploaded_file)
