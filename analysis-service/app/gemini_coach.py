from __future__ import annotations

import json
import logging
from pathlib import Path
import re

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
from app.frame_sampler import keyframe_debug_metadata, keyframe_timestamps
from app.schemas import (
    AccountabilityPlan,
    AnalysisBullet,
    BlueprintStep,
    CoachSummaryReport,
    CoachingReportSchema,
    DISCLAIMER,
    DrillPrescription,
    FeelBlueprintDiagnostic,
    FixPriorityBlock,
    FixItDrill,
    EstimatedScoreImpact,
    ImprovementBenchmark,
    ImprovementConfidence,
    ImprovementEngine,
    ImprovementFixPriority,
    ImprovementPracticePlan,
    KinestheticBlueprint,
    MilestoneBlock,
    PgaCoachAnalysis,
    PgaDrill,
    PracticeValueScore,
    ProFix,
    ProgressMetric,
    ProgressScore,
    AdvancedDetails,
    SwingDiagnosisEngine,
    SwingMetricEvidence,
    SwingMode,
)

logger = logging.getLogger(__name__)

COACHING_SYSTEM = """You are an expert golf swing coach. Deliver a useful, encouraging "Feel Blueprint" from the video — like a sharp teacher talking to the golfer on the range.

NO scores. NO generic boxes ("Standard Slice") when the root cause is unique.

CRITICAL PARALYSIS GUARD:
- Trace setup posture → takeaway → downswing rescue. Name flaws with nicknames (e.g. "The Sitting Stance").
- Explain WHY the brain triggers compensations from address.
- Call out real strengths you see — not only problems.
- Never diagnose only the ball-flight symptom. Trace the symptom backward through the swing sequence.
- Use the provided rule-based checkpoint metrics and evidence. Do not invent metrics that are not provided.
- If club visibility, camera angle, or confidence is limited, label conclusions as "likely" and avoid exact club path or face claims.

VOICE (specific, encouraging, useful):
- Make the golfer feel capable before you correct them.
- Praise what is genuinely working, then name the clearest visible flaw that limits improvement.
- Use "protect this" for strengths and "fix this first" for flaws.
- Never humiliate, never hype. The player should leave optimistic and know exactly what to practice.
- Good example: "Your rhythm is a real asset. The obvious leak is that transition gets quick, so the hands have to rescue the face late."

STRUCTURE — map JSON to feel_blueprint:

1. opening_narrative — 2-3 sentences: real strength first, then the main fight or watch-out.

2. strengths[] — "THE STRENGTHS (The Good Stuff)" — 2-4 items. title + detail each. Real video evidence.

3. flaws[] — "THE IMPROVEMENT PRIORITIES" — 2-4 items in order: the most obvious visible flaw first, then the compensation it creates. If the swing is strong, list the biggest repeatability watch-out and one small cleanup.

4. current_ceiling — honest improvement limit if the flaw/watch-out remains.

5. potential_ceiling — range IF root setup/flaw fixed; tie to existing athleticism. Pain-free.

6. pro_fixes[] — 2-3 prioritized fixes (title + detail). Align with physical constraints.

7. body_part_cue + spatial_cue — two exact feels, no jargon (e.g. "Toe up, not rolled open").

feel_blueprint.headline = unique pattern name (max 8 words).

PERSONALIZATION:
- personalized_greeting: first name, history callback, max 35 words.
- Use player age/years/limits when provided.

PHYSICAL BOUNDARIES: never violate stated constraints.

TRAINING LAYER (still required):
- blueprint: 2-3 steps; weave the two cues into feels; video_slug from catalog.
- roadmap: weekly_focus + 3 milestones + day_7_test.

CAUSE-AND-EFFECT DIAGNOSIS (required):
- diagnosis_engine must cite checkpoint evidence from the provided metrics/rule findings or visible video evidence.
- diagnosis_engine.fix_priority must include exactly one primary fix, one secondary fix, and one optional fix.
- diagnosis_engine.one_drill must be the simplest drill for the primary root cause.
- Avoid generic advice unless directly supported by the provided checkpoint metrics.

Minimal **bold** in details. disclaimer = exact string from prompt."""

MODE_GUIDANCE: dict[SwingMode, str] = {
    "full_swing": """MODE: FULL SWING
Watch address → takeaway → top → downswing → impact → finish.
Relate setup posture to backswing coil (or lack of). Ball flight = kinetic_reaction proof.""",
    "chipping": """MODE: CHIPPING (short game)
10–40 yards: low point, strike, face, landing. Setup weight/hinge drives the fault — not generic "fat chip" labels.""",
    "putting": """MODE: PUTTING
Stroke only: setup, path, face, tempo, start line. Headline must be putting-specific, not full-swing jargon.""",
}


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

    return f"""[CONTEXT LAYER: PHYSICAL BOUNDARIES]
The golfer analyzing their swing has the following profile:
- Age: {age_line}
- Years Playing: {years_line}
- Physical Constraints: {limits}

CRITICAL INSTRUCTION FOR THE COACH:
You must NEVER suggest a drill or mechanical change that violates their physical constraints.
- If they have lower back pain, DO NOT tell them to aggressively arch or tilt their spine at impact, and DO NOT prescribe high-torque rotation drills.
- If they have high years playing, respect their existing muscle memory habits (e.g., don't try to entirely rewrite a 30-year swing; instead, optimize their setup boundaries to accommodate their natural path).
- Adjust the "Potential Peak Ceiling" to be an achievable, pain-free reality, not an idealized PGA Tour textbook swing."""


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
    camera_angle: str | None = None,
    handedness: str | None = None,
    skill_level: str | None = None,
    ball_flight: str | None = None,
    user_goal: str | None = None,
    club_used: str | None = None,
    practice_availability: str | None = None,
    handicap: str | None = None,
    prior_progress: dict | None = None,
    diagnosis_engine: SwingDiagnosisEngine | None = None,
    metric_payload: dict | None = None,
) -> str:
    history = history_summary or "No prior swings."
    name_line = player_name or "Unknown (use 'there' sparingly — prefer no name if missing)"
    swing_line = str(swing_number) if swing_number else "Unknown"
    context = player_context or "No extra context."
    camera_angle_line = (camera_angle or "Not provided").strip()
    handedness_line = (handedness or "Not provided").strip()
    skill_level_line = (skill_level or "Not provided").strip()
    ball_flight_line = (ball_flight or "Not provided").strip()
    user_goal_line = (user_goal or "Not provided").strip()
    club_used_line = (club_used or "Not provided").strip()
    practice_line = (practice_availability or "Not provided").strip()
    handicap_line = (handicap or "Not provided").strip()
    prior_progress_line = json.dumps(prior_progress or {}, default=str)[:6000]
    physical_block = _format_physical_boundaries_block(
        age=player_age,
        years_playing=years_playing,
        physical_limitations=physical_limitations,
    )
    if physical_block:
        physical_block = f"{physical_block}\n"

    mode_block = MODE_GUIDANCE.get(swing_mode, MODE_GUIDANCE["full_swing"])
    diagnosis_block = ""
    if diagnosis_engine or metric_payload:
        diagnosis_block = f"""
RULE-BASED DIAGNOSIS ENGINE INPUT
Use this as hybrid supporting evidence only. The full video is the primary source.
Evidence priority:
1. Full video vision.
2. Ordered checkpoint frames.
3. Hybrid vision evidence: SAM 3 segmentation when available, body proxy, club/shaft visibility, camera angle, checkpoint quality, confidence.
4. Rule-based/proxy measurements.

Do not invent unprovided measurements, and do not let weak proxy metrics override clear video evidence.
If hybrid_vision_evidence.sam3_segmentation.available is true, use it to decide whether the golfer, club/shaft, hands, and ball are visible enough for specific claims.
If hybrid_vision_evidence.club_tracking.usable is false, avoid exact club path, shaft plane, or face claims.
If hybrid_vision_evidence.fusion_confidence is below 0.5, make a coach-like but cautious read and explain what must be re-filmed.
{json.dumps({
    "rule_based_issues": diagnosis_engine.model_dump() if diagnosis_engine else None,
    "raw_detected_metrics": metric_payload or {},
}, default=str)[:18000]}

GEMINI DIAGNOSIS JSON CONTRACT
Your response must remain valid JSON for the full app schema. The diagnosis_engine field must include:
{{
  "main_diagnosis": string,
  "skill_level_note": string,
  "first_breakdown_checkpoint": string,
  "root_cause": string,
  "symptom": string,
  "chain_reaction": string,
  "fix_priority": {{
    "primary": string,
    "secondary": string,
    "optional": string
  }},
  "evidence": [
    {{
      "checkpoint": string,
      "metric": string,
      "observed": string,
      "expected": string,
      "interpretation": string,
      "confidence": number
    }}
  ],
  "what_to_feel": string,
  "one_drill": {{
    "name": string,
    "instructions": string,
    "sets_reps": string,
    "success_metric": string
  }},
  "next_upload_focus": string,
  "coach_warning": string
}}

Guardrails:
- If video angle is poor, say so in coach_warning.
- If confidence is low, do not overdiagnose.
- If club is not visible, do not claim exact club path.
- If only face-on or down-the-line is uploaded, limit diagnosis to what that angle can support.
- Label anything as "likely" if inferred rather than directly measured.
"""

    return f"""{COACHING_SYSTEM}

{mode_block}

PLAYER
- First name: {name_line}
- This upload: swing #{swing_line} in our app
- Context: {context}
- Camera angle: {camera_angle_line}
- Handedness: {handedness_line}
- Skill level: {skill_level_line}
- Handicap / scoring level: {handicap_line}
- Club used: {club_used_line}
- Ball flight / miss: {ball_flight_line}
- User goal: {user_goal_line}
- Practice availability: {practice_line}

{physical_block}PRIOR SWINGS
{history}

PRIOR PROGRESS SCORE JSON
{prior_progress_line}

{diagnosis_block}

{catalog_for_prompt(swing_mode)}

DISCLAIMER (copy exactly):
"{DISCLAIMER}"

PRIMARY COACHING TASK
You are an expert golf swing coach analyzing a user-uploaded swing video.

Analyze the swing in sequence. Do not give generic swing tips. Identify the first point in the swing
where the motion breaks down, then explain the chain reaction. Analyze like a golf coach watching the
swing, but only make claims visible in the video.

Rules:
- Do not say "over the top," "slice," "early extension," or "poor tempo" unless you explain where it starts.
- Do not claim exact club path or clubface unless the club is clearly visible.
- If unsure, say "likely" or "video angle makes this uncertain."
- Make the response useful, specific, coach-like, and skimmable.
- Treat body/club proxy metrics as supporting evidence, not the main coach.
- Use club/shaft proxy observations only when their confidence says they are usable.

IMPROVEMENT ENGINE TASK
Golfers do not buy analysis. They buy improvement. The report must answer:
A. What is costing me the most shots?
B. Where does it start?
C. What should I fix first?
D. What should I ignore for now?
E. What should I practice tomorrow?
F. How will I know if I improved?

Populate improvement_engine as the highest-value section in the report:
{{
  "main_diagnosis": "One sentence: the primary shot leak and where it starts.",
  "expected_ball_flight_consequence": "Tie the motion to likely contact/direction/consistency. Use the user's stated miss if provided.",
  "estimated_score_impact": {{
    "level": "low|medium|high",
    "shots_at_risk": "Plain-English estimate, e.g. 'High: this is likely costing strike and direction on many full swings.'",
    "explanation": "Why this costs shots without pretending exact strokes-gained precision."
  }},
  "fix_priority": {{
    "fix_first": "The single first fix.",
    "fix_second": "Only after the first fix improves.",
    "ignore_for_now": ["1-3 swing flaws or details they should not chase yet."],
    "why_this_order": "Why this order saves practice time."
  }},
  "practice_plan": {{
    "practice_goal": "Outcome for tomorrow's practice.",
    "tomorrow_plan": ["3-5 concrete steps the golfer can follow tomorrow."],
    "primary_drill": {{
      "name": "One drill tied to the primary fix.",
      "why_it_helps": "Why it helps this exact swing.",
      "how_to_do_it": "How to do it."
    }},
    "feels": ["2-3 simple feels."],
    "dosage": "Reps and time.",
    "success_check": "How they know a rep was successful."
  }},
  "improvement_benchmark": {{
    "metric": "The next-upload metric to improve.",
    "current_state": "What it looks like now.",
    "target_next_upload": "Specific improvement target, e.g. 'Improve hip depth retention by about 15%.'",
    "upload_instruction": "Exactly what to film next."
  }},
  "progress_score": {{
    "overall": 0,
    "previous_overall": null,
    "trend": "first_upload|improved|same|regressed|unknown",
    "summary": "Compare to the golfer's own history, not PGA Tour players.",
    "metrics": [
      {{"name": "Head stability", "current_score": 0, "previous_score": null, "change": null, "interpretation": "What it means."}},
      {{"name": "Balance", "current_score": 0, "previous_score": null, "change": null, "interpretation": "What it means."}},
      {{"name": "Posture retention", "current_score": 0, "previous_score": null, "change": null, "interpretation": "What it means."}},
      {{"name": "Hip depth", "current_score": 0, "previous_score": null, "change": null, "interpretation": "What it means."}},
      {{"name": "Sequencing", "current_score": 0, "previous_score": null, "change": null, "interpretation": "What it means."}},
      {{"name": "Consistency", "current_score": 0, "previous_score": null, "change": null, "interpretation": "What it means."}}
    ]
  }},
  "confidence": {{
    "level": "high|medium|low",
    "why": "Why this read has that confidence level.",
    "limiting_factors": ["Poor angle, club blurry, ball flight not provided, etc."],
    "evidence_used": ["Full video", "checkpoint frames", "ball flight context", "hybrid vision evidence"]
  }},
  "practice_value_score": {{
    "contact": "low|medium|high",
    "direction": "low|medium|high",
    "consistency": "low|medium|high",
    "distance": "low|medium|high",
    "summary": "If they fix the primary issue, what improves most."
  }}
}}

Populate pga_coach_analysis with this exact structure:
{{
  "pga_analysis": "Include: What is the biggest issue? Where does it first appear? Why does it matter?",
  "main_fix": "The one thing to fix first.",
  "tips_and_feels": ["Feel 1", "Feel 2", "Feel 3"],
  "drills": [
    {{
      "name": "Drill tied directly to the main fix.",
      "why_it_helps": "Why it helps this swing.",
      "how_to_do_it": "How to do it."
    }},
    {{
      "name": "Second drill tied directly to the same main fix.",
      "why_it_helps": "Why it helps this swing.",
      "how_to_do_it": "How to do it."
    }}
  ],
  "next_upload_focus": "What the golfer should record/check next.",
  "confidence_note": "Visibility and certainty note."
}}

Populate coach_summary_report as the public-facing paid report:
{{
  "coach_summary": "3-4 short coach sentences in this order: strength → missing piece → practice direction. Do not repeat yourself.",
  "whats_working": [
    "Specific strength #1 from the video, e.g. wrist lag, athletic rotation, balance, setup.",
    "Specific strength #2 from the video.",
    "Specific strength #3 if visible."
  ],
  "main_swing_leak": "One plain-English sentence naming the most obvious visible flaw/missing piece. If no major flaw is visible, name the first repeatability watch-out to protect under pressure.",
  "why_it_matters": "The Physics Problem: explain how this flaw changes swing center, radius, path, contact, or start line. Plain English.",
  "feel_this_week": "A memorable feel name and one-sentence mission, e.g. 'The Cylinder Turn — rotate inside a phone booth instead of sliding.'",
  "what_to_feel": ["1-3 simple feels. No duplicates."],
  "fix_it_drill": {{
    "name": "One drill only.",
    "steps": ["3-5 simple steps. No jargon."],
    "dose": "Reps/speed/time.",
    "success_check": "How they know it worked."
  }},
  "practice_plan_7_day": ["Day 1-2: ...", "Day 3-4: ...", "Day 5-6: ...", "Day 7: ..."],
  "next_upload_goal": "One clear filming + checkpoint goal.",
  "advanced_details": {{
    "first_breakdown_checkpoint": "checkpoint label",
    "root_cause": "plain English",
    "symptom": "plain English",
    "confidence_note": "why confidence is high/medium/low",
    "camera_angle_limitations": "what this angle can/cannot prove",
    "evidence_plain_english": ["Translate evidence. Do not show proxy units here."],
    "raw_metrics": {{}}
  }}
}}

Public report rules:
- Match this flow: What's Working → The Missing Piece → The Physics Problem → Your Feel This Week → 7-Day Plan.
- A paid report must make the golfer feel good about real strengths AND identify the most obvious flaw limiting improvement.
- Do not invent flaws. If no major flaw is visible, say exactly that and make the report a maintenance plan: what to protect, what can break under pressure, and how to prove repeatability.
- Every report must answer: "What should I keep?", "What is the obvious flaw or watch-out?", and "What do I practice next?"
- Do not say "perfect", "pure strike", "don't change a thing", or "incredible" unless the video clearly proves it and you immediately name the next risk to monitor.
- Do not repeat the same diagnosis in multiple sections.
- Do not use generic golf terms without explaining what caused them.
- Do not show raw proxy metrics in public-facing sections.
- Put all technical details into coach_summary_report.advanced_details only.
- Make the main output feel like one paid coaching note, not a full scouting report.

Generate the full app Feel Blueprint JSON too. Unique diagnosis. Two exact feels. No generic boxes."""


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


def _trace_log(event: str, *, swing_id: str | None, trace_id: str | None, error: str | None = None, **extra) -> None:
    logger.info(
        "%s swing_id=%s trace_id=%s error_message=%s extra=%s",
        event,
        swing_id or "",
        trace_id or "",
        error or "",
        extra,
    )


def _json_text(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.removeprefix("```json").removeprefix("```").strip()
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3].strip()
    return cleaned


def _gemini_response_schema() -> dict:
    """Gemini Developer API rejects open-ended additionalProperties in response_schema."""
    schema = CoachingReportSchema.model_json_schema()

    def scrub(value: object) -> object:
        if isinstance(value, dict):
            return {
                key: scrub(item)
                for key, item in value.items()
                if key != "additionalProperties"
            }
        if isinstance(value, list):
            return [scrub(item) for item in value]
        return value

    return scrub(schema)  # type: ignore[return-value]


def _is_schema_serving_error(exc: Exception) -> bool:
    text = str(exc).lower()
    return (
        "too many states" in text
        or "additionalproperties" in text
        or "specified schema" in text
        or "response schema" in text
    )


def _generate_gemini_content(
    client: genai.Client,
    *,
    model: str,
    content_parts: list[types.Part],
    use_schema: bool,
):
    config_kwargs: dict = {
        "response_mime_type": "application/json",
        "temperature": 0.45,
    }
    if use_schema:
        config_kwargs["response_json_schema"] = _gemini_response_schema()

    return client.models.generate_content(
        model=model,
        contents=[types.Content(role="user", parts=content_parts)],
        config=types.GenerateContentConfig(**config_kwargs),
    )


def _coerce_str(value: object, fallback: str = "") -> str:
    if isinstance(value, str):
        return value
    if value is None:
        return fallback
    if isinstance(value, dict):
        title = value.get("title")
        detail = value.get("detail") or value.get("description")
        if isinstance(title, str) and isinstance(detail, str):
            return f"{title}: {detail}"
        if isinstance(detail, str):
            return detail
        for key in (
            "pga_analysis",
            "main_diagnosis",
            "analysis",
            "summary",
            "name",
            "headline",
            "current_ceiling",
            "potential_ceiling",
            "text",
            "value",
            "why",
            "explanation",
        ):
            if isinstance(value.get(key), str):
                return value[key]
        string_values = [item for item in value.values() if isinstance(item, str)]
        if string_values:
            return " ".join(string_values)
    if isinstance(value, list):
        parts = [_coerce_str(item) for item in value]
        joined = " ".join(part for part in parts if part)
        return joined or fallback
    return str(value)


def _normalize_analysis_bullets(value: object, *, fallback_title: str, fallback_detail: str) -> list[dict]:
    items = value if isinstance(value, list) else []
    repaired: list[dict] = []
    for index, item in enumerate(items[:4], start=1):
        if isinstance(item, dict):
            title = _coerce_str(item.get("title"), f"{fallback_title} {index}")
            detail = _coerce_str(item.get("detail") or item.get("description") or item, fallback_detail)
        else:
            title = f"{fallback_title} {index}"
            detail = _coerce_str(item, fallback_detail)
        repaired.append({"title": title, "detail": detail})
    while len(repaired) < 2:
        repaired.append({"title": fallback_title, "detail": fallback_detail})
    return repaired[:4]


def _normalize_pro_fixes(value: object, *, fallback_detail: str) -> list[dict]:
    items = value if isinstance(value, list) else []
    repaired: list[dict] = []
    for index, item in enumerate(items[:3], start=1):
        if isinstance(item, dict):
            title = _coerce_str(item.get("title") or item.get("name"), f"Fix {index}")
            detail = _coerce_str(item.get("detail") or item.get("description") or item, fallback_detail)
        else:
            title = f"Fix {index}"
            detail = _coerce_str(item, fallback_detail)
        repaired.append({"title": title, "detail": detail})
    while len(repaired) < 2:
        repaired.append({"title": "Fix first", "detail": fallback_detail})
    return repaired[:3]


def _normalize_feel_blueprint(payload: dict) -> None:
    feel = payload.get("feel_blueprint")
    if not isinstance(feel, dict):
        return

    feel["opening_narrative"] = _coerce_str(
        feel.get("opening_narrative"),
        _coerce_str(payload.get("personalized_greeting"), "Here is the clearest coaching read from this swing."),
    )
    feel["headline"] = _coerce_str(feel.get("headline"), "Main Priority")[:80]
    feel["strengths"] = _normalize_analysis_bullets(
        feel.get("strengths"),
        fallback_title="Useful strength",
        fallback_detail="This upload showed at least one useful piece to build from.",
    )
    feel["flaws"] = _normalize_analysis_bullets(
        feel.get("flaws"),
        fallback_title="Primary flaw",
        fallback_detail="The main issue needs to be traced from the first breakdown, not impact alone.",
    )
    feel["current_ceiling"] = _coerce_str(
        feel.get("current_ceiling"),
        "If this pattern stays, contact and direction will remain timing-dependent.",
    )
    feel["potential_ceiling"] = _coerce_str(
        feel.get("potential_ceiling"),
        "If the first priority improves, the swing should become more repeatable.",
    )
    feel["pro_fixes"] = _normalize_pro_fixes(
        feel.get("pro_fixes"),
        fallback_detail="Start with the first priority and ignore secondary issues until it improves.",
    )
    feel["body_part_cue"] = _coerce_str(feel.get("body_part_cue"), "One simple body feel.")
    feel["spatial_cue"] = _coerce_str(feel.get("spatial_cue"), "One simple space feel.")


def _dedupe_strings(items: list[str], *, limit: int) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        cleaned = " ".join(_coerce_str(item).split())
        if not cleaned:
            continue
        key = cleaned.lower().strip(".")
        if key in seen:
            continue
        seen.add(key)
        result.append(cleaned)
        if len(result) >= limit:
            break
    return result


def _plain_metric_name(value: object) -> str:
    text = _coerce_str(value, "checkpoint evidence").replace("_", " ")
    replacements = {
        "trail elbow position": "trail arm position",
        "club forearm plane proxy": "club/arm plane",
        "pelvis depth early extension proxy": "space through impact",
        "head position x movement": "head movement",
        "head position y movement": "head height",
    }
    return replacements.get(text.lower(), text)


def _plain_evidence(item: object) -> str:
    if not isinstance(item, dict):
        return _coerce_str(item, "The video evidence supports the main swing leak.")
    checkpoint = _coerce_str(item.get("checkpoint"), "the key checkpoint").replace("_", " ")
    metric = _plain_metric_name(item.get("metric"))
    interpretation = _coerce_str(item.get("interpretation"), "")
    if interpretation:
        return f"At {checkpoint}, the {metric} shows why the main leak starts there: {interpretation}"
    return f"At {checkpoint}, the {metric} supports the main leak."


def _working_points(report: dict, feel: dict, pga: dict) -> list[str]:
    explicit = report.get("whats_working")
    if isinstance(explicit, list):
        points = _dedupe_strings([_coerce_str(item) for item in explicit], limit=3)
        if points:
            return points

    strengths = feel.get("strengths") if isinstance(feel.get("strengths"), list) else []
    points = []
    for item in strengths:
        if isinstance(item, dict):
            points.append(_coerce_str(item.get("detail") or item.get("title")))
        else:
            points.append(_coerce_str(item))
    if pga.get("pga_analysis"):
        points.append(_coerce_str(pga.get("pga_analysis")))

    points = _dedupe_strings(points, limit=3)
    while len(points) < 1:
        points.append("There is at least one useful athletic pattern to build around; the priority is making it repeatable.")
    return points[:3]


def _looks_like_praise_only_report(
    *,
    summary: str,
    main_leak: str,
    why: str,
    drill_name: str,
) -> bool:
    text = " ".join([summary, main_leak, why, drill_name]).lower()
    praise_tokens = (
        "perfect",
        "don't change",
        "do not change",
        "great position",
        "huge strength",
        "picture-perfect",
        "pure strike",
        "incredible",
        "wins matches",
        "drops handicaps fast",
        "nothing mechanically",
        "bottle this feeling",
    )
    coaching_tokens = (
        "watch-out",
        "watch out",
        "risk",
        "leak",
        "breaks",
        "break down",
        "priority",
        "improve",
        "protect",
        "pressure",
        "repeatability",
        "prove",
        "tendency",
    )
    has_praise = any(token in text for token in praise_tokens)
    has_coaching = any(token in text for token in coaching_tokens) or bool(re.search(r"\bmiss\b", text))
    return has_praise and not has_coaching


def _has_actionable_public_report(*, main_leak: str, why: str) -> bool:
    text = " ".join([main_leak, why]).lower()
    if "no major" in text and "watch-out" in text:
        return True
    action_tokens = (
        "missing piece",
        "physics problem",
        "setup",
        "posture",
        "hinge",
        "sway",
        "slide",
        "early extension",
        "hip thrust",
        "hips push",
        "lunge",
        "collapse",
        "lose",
        "inconsistent",
        "contact",
        "direction",
        "swing center",
        "space",
        "timing",
    )
    return any(token in text for token in action_tokens)


def _maintenance_watchout_report(*, confidence_note: str, camera_warning: str) -> dict:
    return {
        "coach_summary": (
            "This swing is in a good place, so this is a maintenance report, not a rebuild. "
            "The first priority is proving the same tempo and finish repeat when you add speed or pressure. "
            "The watch-out is transition getting quick from the top, because that is when strong swings usually lose start line and strike."
        ),
        "whats_working": [
            "Your rhythm and athletic motion are strengths worth protecting.",
            "A balanced finish gives you a useful checkpoint for whether the swing stayed organized.",
        ],
        "main_swing_leak": (
            "No major rebuild is visible; the first watch-out is whether transition tempo holds up under pressure."
        ),
        "why_it_matters": (
            "If transition gets quick, contact and start line can become timing-dependent even when the motion looks athletic. "
            "The next upload should prove repeatability, not chase a new mechanic."
        ),
        "feel_this_week": "The Repeatable Finish — same tempo, same start line, same balanced finish five swings in a row.",
        "what_to_feel": [
            "Same speed back, same speed through.",
            "Start down from the ground, not from the hands.",
            "Hold the finish until the ball lands.",
        ],
        "fix_it_drill": {
            "name": "Five-Ball Repeatability Ladder",
            "steps": [
                "Hit five balls at 70 percent speed.",
                "Use one tempo cue only.",
                "Hold every finish for three seconds.",
                "Only count shots that start on your intended line.",
                "If two fail, restart the set at slower speed.",
            ],
            "dose": "Three sets of five balls.",
            "success_check": "At least four of five swings keep the same tempo, start line, and balanced finish.",
        },
        "practice_plan_7_day": [
            "Day 1-2: five-ball ladder at 70 percent speed.",
            "Day 3-4: repeat the ladder with your normal club speed.",
            "Day 5-6: change targets every ball and keep the same tempo.",
            "Day 7: upload five swings, not one highlight swing.",
        ],
        "next_upload_goal": (
            "Film five consecutive swings from the same angle and prove the tempo and balanced finish repeat."
        ),
        "advanced_details": {
            "first_breakdown_checkpoint": "transition",
            "root_cause": "No major flaw was visible from this upload; repeatability under pressure is the checkpoint to test.",
            "symptom": "The likely miss, if it appears, is start-line or strike variability when transition gets quick.",
            "confidence_note": confidence_note,
            "camera_angle_limitations": camera_warning,
            "evidence_plain_english": [
                "A single strong swing proves capability, but it does not prove repeatability.",
                "The next test should use consecutive swings so the app can separate a stable pattern from one good rep.",
            ],
            "raw_metrics": {},
        },
    }


def _drill_steps_from_text(text: str) -> list[str]:
    cleaned = text.replace("\n", " ")
    parts = [part.strip(" .") for part in cleaned.split(".") if part.strip()]
    steps = _dedupe_strings(parts, limit=5)
    while len(steps) < 3:
        fallbacks = [
            "Put a towel under your trail armpit.",
            "Make slow three-quarter swings.",
            "Keep the connection light through the top.",
            "Hit easy shots before adding speed.",
        ]
        steps.append(fallbacks[len(steps)])
    return [step if step.endswith(".") else f"{step}." for step in steps[:5]]


def _normalize_diagnosis_engine(payload: dict) -> None:
    diagnosis = payload.get("diagnosis_engine")
    if not isinstance(diagnosis, dict):
        diagnosis = {}

    improvement = payload.get("improvement_engine") if isinstance(payload.get("improvement_engine"), dict) else {}
    coach = payload.get("coach_summary_report") if isinstance(payload.get("coach_summary_report"), dict) else {}
    feel = payload.get("feel_blueprint") if isinstance(payload.get("feel_blueprint"), dict) else {}
    practice = improvement.get("practice_plan") if isinstance(improvement.get("practice_plan"), dict) else {}
    fix_priority = diagnosis.get("fix_priority") if isinstance(diagnosis.get("fix_priority"), dict) else {}
    improvement_priority = improvement.get("fix_priority") if isinstance(improvement.get("fix_priority"), dict) else {}

    main = _coerce_str(
        diagnosis.get("main_diagnosis")
        or improvement.get("main_diagnosis")
        or coach.get("main_swing_leak")
        or feel.get("headline"),
        "The main improvement priority needs one clear first fix.",
    )
    root = _coerce_str(diagnosis.get("root_cause") or coach.get("main_swing_leak"), main)
    symptom = _coerce_str(
        diagnosis.get("symptom")
        or improvement.get("expected_ball_flight_consequence")
        or coach.get("why_it_matters"),
        "Contact and direction can become timing-dependent.",
    )
    chain = _coerce_str(
        diagnosis.get("chain_reaction") or coach.get("why_it_matters"),
        "The first breakdown creates a compensation later in the swing.",
    )

    primary = _coerce_str(
        fix_priority.get("primary") or improvement_priority.get("fix_first"),
        "Fix the first visible breakdown before changing anything else.",
    )
    secondary = _coerce_str(
        fix_priority.get("secondary") or improvement_priority.get("fix_second"),
        "Recheck the compensation after the first fix improves.",
    )
    optional = _coerce_str(
        fix_priority.get("optional"),
        "Ignore small style preferences until the main pattern improves.",
    )

    one_drill = diagnosis.get("one_drill") if isinstance(diagnosis.get("one_drill"), dict) else {}
    primary_drill = practice.get("primary_drill") if isinstance(practice.get("primary_drill"), dict) else {}
    drill_steps = one_drill.get("steps") if isinstance(one_drill.get("steps"), list) else None
    instructions = _coerce_str(
        one_drill.get("instructions")
        or primary_drill.get("how_to_do_it")
        or drill_steps,
        "Make slow rehearsals, then hit easy shots while keeping the main feel.",
    )

    evidence = diagnosis.get("evidence") if isinstance(diagnosis.get("evidence"), list) else []
    repaired_evidence = []
    for item in evidence[:5]:
        if not isinstance(item, dict):
            continue
        repaired_evidence.append(
            {
                "checkpoint": _coerce_str(item.get("checkpoint"), diagnosis.get("first_breakdown_checkpoint") or "key checkpoint"),
                "metric": _coerce_str(item.get("metric"), "video evidence"),
                "observed": _coerce_str(item.get("observed"), root),
                "expected": _coerce_str(item.get("expected"), "A repeatable position that does not require compensation."),
                "interpretation": _coerce_str(item.get("interpretation"), chain),
                "confidence": item.get("confidence") if isinstance(item.get("confidence"), (int, float)) else 0.62,
            }
        )

    diagnosis.update(
        {
            "main_diagnosis": main,
            "skill_level_note": _coerce_str(
                diagnosis.get("skill_level_note"),
                "Fix the first breakdown while protecting the strengths already present.",
            ),
            "first_breakdown_checkpoint": _coerce_str(
                diagnosis.get("first_breakdown_checkpoint")
                or coach.get("advanced_details", {}).get("first_breakdown_checkpoint") if isinstance(coach.get("advanced_details"), dict) else None,
                "first visible breakdown",
            ),
            "root_cause": root,
            "symptom": symptom,
            "chain_reaction": chain,
            "fix_priority": {
                "primary": primary,
                "secondary": secondary,
                "optional": optional,
            },
            "evidence": repaired_evidence,
            "what_to_feel": _coerce_str(
                diagnosis.get("what_to_feel")
                or coach.get("feel_this_week")
                or (practice.get("feels") or [None])[0] if isinstance(practice.get("feels"), list) else None,
                "Make the first fix simple enough to repeat.",
            ),
            "one_drill": {
                "name": _coerce_str(one_drill.get("name") or primary_drill.get("name"), "Main Fix Drill"),
                "instructions": instructions,
                "sets_reps": _coerce_str(one_drill.get("sets_reps") or practice.get("dosage"), "15-20 slow reps, then 10 easy balls."),
                "success_metric": _coerce_str(one_drill.get("success_metric") or practice.get("success_check"), "You can repeat the checkpoint without a late compensation."),
            },
            "next_upload_focus": _coerce_str(
                diagnosis.get("next_upload_focus")
                or coach.get("next_upload_goal")
                or payload.get("next_upload_focus"),
                "Film the same angle and check the first breakdown.",
            ),
            "coach_warning": _coerce_str(
                diagnosis.get("coach_warning"),
                "This is an AI-supported read; confirm with another upload if visibility is limited.",
            ),
            "issues": diagnosis.get("issues") if isinstance(diagnosis.get("issues"), list) else [],
        }
    )
    payload["diagnosis_engine"] = diagnosis


def _normalize_coach_summary_report(payload: dict) -> None:
    report = payload.get("coach_summary_report")
    if not isinstance(report, dict):
        report = {}

    improvement = payload.get("improvement_engine") if isinstance(payload.get("improvement_engine"), dict) else {}
    pga = payload.get("pga_coach_analysis") if isinstance(payload.get("pga_coach_analysis"), dict) else {}
    diagnosis = payload.get("diagnosis_engine") if isinstance(payload.get("diagnosis_engine"), dict) else {}
    feel = payload.get("feel_blueprint") if isinstance(payload.get("feel_blueprint"), dict) else {}
    practice = improvement.get("practice_plan") if isinstance(improvement.get("practice_plan"), dict) else {}
    primary_drill = practice.get("primary_drill") if isinstance(practice.get("primary_drill"), dict) else {}
    benchmark = improvement.get("improvement_benchmark") if isinstance(improvement.get("improvement_benchmark"), dict) else {}
    confidence = improvement.get("confidence") if isinstance(improvement.get("confidence"), dict) else {}
    evidence = diagnosis.get("evidence") if isinstance(diagnosis.get("evidence"), list) else []

    main_leak = _coerce_str(
        report.get("main_swing_leak")
        or improvement.get("main_diagnosis")
        or diagnosis.get("main_diagnosis")
        or (feel.get("flaws") or [{}])[0],
        "Your swing has one primary leak that should be fixed first.",
    )
    why = _coerce_str(
        report.get("why_it_matters") or improvement.get("expected_ball_flight_consequence") or diagnosis.get("chain_reaction"),
        "It makes contact and direction depend too much on timing.",
    )
    summary = _coerce_str(
        report.get("coach_summary") or pga.get("pga_analysis") or feel.get("opening_narrative"),
        f"{main_leak} {why}",
    )

    feels = []
    if isinstance(report.get("what_to_feel"), list):
        feels.extend(report["what_to_feel"])
    if isinstance(practice.get("feels"), list):
        feels.extend(practice["feels"])
    feels.extend([feel.get("body_part_cue"), feel.get("spatial_cue"), diagnosis.get("what_to_feel")])
    feels = _dedupe_strings([item for item in feels if item], limit=3)
    while len(feels) < 1:
        feels.append("Keep the main fix simple and slow enough to feel.")

    drill = report.get("fix_it_drill") if isinstance(report.get("fix_it_drill"), dict) else {}
    one_drill = diagnosis.get("one_drill") if isinstance(diagnosis.get("one_drill"), dict) else {}
    drill_name = _coerce_str(
        drill.get("name") or primary_drill.get("name") or one_drill.get("name"),
        "Fix-It Drill",
    )
    drill_text = _coerce_str(
        drill.get("how_to_do_it")
        or drill.get("steps")
        or primary_drill.get("how_to_do_it")
        or one_drill.get("instructions"),
        "Make slow rehearsals, then hit easy balls while keeping the main feel.",
    )

    plan = report.get("practice_plan_7_day") if isinstance(report.get("practice_plan_7_day"), list) else []
    if not plan:
        plan = [
            "Day 1-2: rehearsal swings only.",
            "Day 3-4: 15-20 half-speed balls.",
            "Day 5-6: blend the feel into normal swings.",
            "Day 7: upload the same swing from the recommended angle.",
        ]
    plan = _dedupe_strings(plan, limit=4)
    while len(plan) < 3:
        plan.append("Day 7: upload a comparison video.")

    advanced = report.get("advanced_details") if isinstance(report.get("advanced_details"), dict) else {}
    evidence_plain = advanced.get("evidence_plain_english") if isinstance(advanced.get("evidence_plain_english"), list) else []
    if not evidence_plain:
        evidence_plain = [_plain_evidence(item) for item in evidence[:3]]

    raw_metrics = advanced.get("raw_metrics") if isinstance(advanced.get("raw_metrics"), dict) else {}
    if not raw_metrics and evidence:
        raw_metrics = {"evidence": evidence}

    whats_working = _working_points(report, feel, pga)
    feel_this_week = _coerce_str(
        report.get("feel_this_week")
        or practice.get("practice_goal")
        or feel.get("body_part_cue")
        or diagnosis.get("what_to_feel"),
        "The main feel this week is to make the first fix simple enough to repeat.",
    )

    confidence_note = _coerce_str(
        advanced.get("confidence_note") or pga.get("confidence_note") or confidence.get("why"),
        "Confidence depends on video angle and club visibility.",
    )
    camera_warning = _coerce_str(
        advanced.get("camera_angle_limitations") or diagnosis.get("coach_warning"),
        "A second camera angle may confirm path and face details.",
    )

    if _looks_like_praise_only_report(
        summary=summary,
        main_leak=main_leak,
        why=why,
        drill_name=drill_name,
    ) and not _has_actionable_public_report(
        main_leak=main_leak,
        why=why,
    ):
        payload["coach_summary_report"] = _maintenance_watchout_report(
            confidence_note=confidence_note,
            camera_warning=camera_warning,
        )
        return

    payload["coach_summary_report"] = {
        "coach_summary": summary,
        "whats_working": whats_working,
        "main_swing_leak": main_leak,
        "why_it_matters": why,
        "feel_this_week": feel_this_week,
        "what_to_feel": feels[:3],
        "fix_it_drill": {
            "name": drill_name,
            "steps": drill.get("steps") if isinstance(drill.get("steps"), list) and drill.get("steps") else _drill_steps_from_text(drill_text),
            "dose": _coerce_str(drill.get("dose") or practice.get("dosage") or one_drill.get("sets_reps"), "15-20 balls at 60% speed."),
            "success_check": _coerce_str(drill.get("success_check") or practice.get("success_check") or one_drill.get("success_metric"), "You can repeat the feel without rushing."),
        },
        "practice_plan_7_day": plan[:4],
        "next_upload_goal": _coerce_str(report.get("next_upload_goal") or benchmark.get("upload_instruction") or pga.get("next_upload_focus") or diagnosis.get("next_upload_focus"), "Film the same swing from down-the-line and check the main checkpoint."),
        "advanced_details": {
            "first_breakdown_checkpoint": _coerce_str(advanced.get("first_breakdown_checkpoint") or diagnosis.get("first_breakdown_checkpoint"), "unknown"),
            "root_cause": _coerce_str(advanced.get("root_cause") or diagnosis.get("root_cause"), main_leak),
            "symptom": _coerce_str(advanced.get("symptom") or diagnosis.get("symptom"), why),
            "confidence_note": confidence_note,
            "camera_angle_limitations": camera_warning,
            "evidence_plain_english": _dedupe_strings(evidence_plain, limit=4),
            "raw_metrics": raw_metrics,
        },
    }


def _normalize_gemini_payload(payload: dict, *, player_name: str | None, swing_mode: SwingMode) -> dict:
    name = (player_name or "there").split()[0]
    if not isinstance(payload.get("improvement_engine"), dict):
        payload["improvement_engine"] = _fallback_improvement_engine(
            "Gemini omitted the improvement engine wrapper, so the app repaired the report shell."
        ).model_dump()
    improvement = payload.get("improvement_engine") if isinstance(payload.get("improvement_engine"), dict) else {}
    pga = payload.get("pga_coach_analysis") if isinstance(payload.get("pga_coach_analysis"), dict) else {}
    diagnosis = payload.get("diagnosis_engine") if isinstance(payload.get("diagnosis_engine"), dict) else {}
    fallback_improvement = _fallback_improvement_engine(
        "Gemini omitted a valid progress score, so the app repaired the progress shell without changing the swing diagnosis."
    ).model_dump()
    progress = improvement.get("progress_score") if isinstance(improvement.get("progress_score"), dict) else {}
    progress_metrics = progress.get("metrics") if isinstance(progress.get("metrics"), list) else []
    if len(progress_metrics) < 3:
        repaired_progress = fallback_improvement["progress_score"]
        repaired_progress["summary"] = _coerce_str(
            progress.get("summary") if isinstance(progress, dict) else None,
            "First upload baseline. Use the next upload to measure repeatability and checkpoint change.",
        )
        repaired_progress["overall"] = progress.get("overall", repaired_progress["overall"]) if isinstance(progress, dict) else repaired_progress["overall"]
        repaired_progress["previous_overall"] = progress.get("previous_overall") if isinstance(progress, dict) else None
        repaired_progress["trend"] = progress.get("trend", repaired_progress["trend"]) if isinstance(progress, dict) else repaired_progress["trend"]
        improvement["progress_score"] = repaired_progress

    if "personalized_greeting" not in payload:
        main = _coerce_str(improvement.get("main_diagnosis") or pga.get("main_fix") or diagnosis.get("main_diagnosis"), "your priority is clear")
        payload["personalized_greeting"] = f"{name}, your paid focus is simple: {main[:120]}"

    if "blueprint" not in payload or not isinstance(payload.get("blueprint"), dict):
        practice = improvement.get("practice_plan") if isinstance(improvement.get("practice_plan"), dict) else {}
        primary_drill = practice.get("primary_drill") if isinstance(practice.get("primary_drill"), dict) else {}
        feels = practice.get("feels") if isinstance(practice.get("feels"), list) else []
        payload["blueprint"] = {
            "headline": _coerce_str(practice.get("practice_goal"), "Practice plan")[:60],
            "intro": "One priority, one practice goal, one next-upload benchmark.",
            "steps": [
                {
                    "title": "Fix first",
                    "step_type": "setup",
                    "adjustment": _coerce_str((improvement.get("fix_priority") or {}).get("fix_first") if isinstance(improvement.get("fix_priority"), dict) else None, "Work on the primary diagnosis."),
                    "feel": _coerce_str(feels[0] if feels else None, "One feel only."),
                    "video_slug": "setup_posture",
                },
                {
                    "title": "Main drill",
                    "step_type": "constraint_drill",
                    "action": _coerce_str(primary_drill.get("how_to_do_it"), _coerce_str(practice.get("success_check"), "Rehearse the main drill slowly.")),
                    "feel": _coerce_str(feels[1] if len(feels) > 1 else practice.get("success_check"), "Slow enough to feel it."),
                    "success_condition": _coerce_str(practice.get("success_check"), "The checkpoint improves on the next upload."),
                    "video_slug": "generic_feel",
                },
            ],
        }

    if "roadmap" not in payload or not isinstance(payload.get("roadmap"), dict):
        practice = improvement.get("practice_plan") if isinstance(improvement.get("practice_plan"), dict) else {}
        benchmark = improvement.get("improvement_benchmark") if isinstance(improvement.get("improvement_benchmark"), dict) else {}
        payload["roadmap"] = {
            "weekly_focus": _coerce_str(practice.get("practice_goal"), "Improve"),
            "milestones": [
                {"days": "Tomorrow", "title": "Practice", "detail": _coerce_str(practice.get("dosage"), "Do the assigned drill.")},
                {"days": "Next range", "title": "Check", "detail": _coerce_str(practice.get("success_check"), "Only count successful reps.")},
                {"days": "Next upload", "title": "Prove it", "detail": _coerce_str(benchmark.get("target_next_upload"), "Upload again to verify progress.")},
            ],
            "day_7_test": _coerce_str(benchmark.get("upload_instruction"), "Upload one comparable swing within a week."),
        }

    if "feel_blueprint" not in payload or not isinstance(payload.get("feel_blueprint"), dict):
        main = _coerce_str(improvement.get("main_diagnosis") or pga.get("pga_analysis"), "Analysis ready")
        consequence = _coerce_str(improvement.get("expected_ball_flight_consequence"), "This pattern affects contact and direction.")
        fix_priority = improvement.get("fix_priority") if isinstance(improvement.get("fix_priority"), dict) else {}
        payload["feel_blueprint"] = {
            "opening_narrative": main,
            "headline": main[:60] or "Main priority",
            "strengths": [
                {"title": "Coachability", "detail": "This upload produced a clear practice priority."},
                {"title": "Practice target", "detail": _coerce_str((improvement.get("improvement_benchmark") or {}).get("target_next_upload") if isinstance(improvement.get("improvement_benchmark"), dict) else None, "You have a next-upload benchmark.")},
            ],
            "flaws": [
                {"title": "Primary leak", "detail": main},
                {"title": "Ball-flight cost", "detail": consequence},
            ],
            "current_ceiling": _coerce_str((improvement.get("estimated_score_impact") or {}).get("explanation") if isinstance(improvement.get("estimated_score_impact"), dict) else None, "This is the current limiter."),
            "potential_ceiling": _coerce_str((improvement.get("practice_value_score") or {}).get("summary") if isinstance(improvement.get("practice_value_score"), dict) else None, "Fixing the priority should improve consistency."),
            "pro_fixes": [
                {"title": "Fix first", "detail": _coerce_str(fix_priority.get("fix_first"), "Work on the primary fix.")},
                {"title": "Ignore for now", "detail": "; ".join(fix_priority.get("ignore_for_now", ["Ignore secondary flaws until the primary improves."])) if isinstance(fix_priority.get("ignore_for_now"), list) else _coerce_str(fix_priority.get("ignore_for_now"), "Ignore secondary flaws until the primary improves.")},
            ],
            "body_part_cue": _coerce_str(((improvement.get("practice_plan") or {}).get("feels") or ["One feel only."])[0] if isinstance(improvement.get("practice_plan"), dict) else None, "One feel only."),
            "spatial_cue": _coerce_str(((improvement.get("practice_plan") or {}).get("feels") or ["Hold the finish."])[-1] if isinstance(improvement.get("practice_plan"), dict) else None, "Hold the finish."),
        }
    _normalize_feel_blueprint(payload)
    _normalize_diagnosis_engine(payload)
    _normalize_coach_summary_report(payload)

    payload.setdefault("next_upload_focus", _coerce_str((improvement.get("improvement_benchmark") or {}).get("upload_instruction") if isinstance(improvement.get("improvement_benchmark"), dict) else None, "Upload one comparable swing."))
    payload.setdefault("disclaimer", DISCLAIMER)

    if isinstance(payload.get("pga_coach_analysis"), dict):
        tips = payload["pga_coach_analysis"].get("tips_and_feels")
        if not isinstance(tips, list):
            tips = []
        while len(tips) < 3:
            tips.append(_coerce_str((improvement.get("practice_plan") or {}).get("success_check") if isinstance(improvement.get("practice_plan"), dict) else None, "Use one simple feel and hold the finish."))
        payload["pga_coach_analysis"]["tips_and_feels"] = [_coerce_str(item, "Use one simple feel.") for item in tips[:3]]

        drills = payload["pga_coach_analysis"].get("drills")
        if isinstance(drills, list):
            repaired_drills = [
                {
                    "name": _coerce_str(item.get("name") if isinstance(item, dict) else item, "Drill"),
                    "why_it_helps": _coerce_str(item.get("why_it_helps") if isinstance(item, dict) else None, "It supports the main fix."),
                    "how_to_do_it": _coerce_str(item.get("how_to_do_it") if isinstance(item, dict) else item, "Do it slowly and check the benchmark."),
                }
                for item in drills[:2]
            ]
            while len(repaired_drills) < 2:
                repaired_drills.append(
                    {
                        "name": "Benchmark Rehearsal",
                        "why_it_helps": "It ties practice directly to the next-upload goal.",
                        "how_to_do_it": "Make slow reps and only count reps that match the success check.",
                    }
                )
            payload["pga_coach_analysis"]["drills"] = repaired_drills

    return payload


def _parse_coaching_report(text: str, *, player_name: str | None, swing_mode: SwingMode) -> CoachingReportSchema:
    payload = json.loads(_json_text(text))
    if not isinstance(payload, dict):
        raise ValueError("Gemini JSON root was not an object")
    normalized = _normalize_gemini_payload(payload, player_name=player_name, swing_mode=swing_mode)
    return CoachingReportSchema.model_validate(normalized)


def _fallback_improvement_engine(note: str) -> ImprovementEngine:
    return ImprovementEngine(
        main_diagnosis="The video is not coachable enough to identify the shot leak responsibly.",
        expected_ball_flight_consequence=(
            "Because the first breakdown is unclear, any ball-flight explanation would be a guess."
        ),
        estimated_score_impact=EstimatedScoreImpact(
            level="high",
            shots_at_risk="High: practicing from a low-confidence diagnosis can waste range time.",
            explanation="The most valuable fix is a clearer upload before making mechanical changes.",
        ),
        fix_priority=ImprovementFixPriority(
            fix_first="Re-film from a stable face-on or down-the-line angle with the full body and club visible.",
            fix_second="Add your normal miss and club used so the next read can connect motion to ball flight.",
            ignore_for_now=[
                "Do not rebuild takeaway from this video.",
                "Do not chase club path or clubface until the club is visible.",
            ],
            why_this_order="A clear video prevents the app from guessing and protects your practice time.",
        ),
        practice_plan=ImprovementPracticePlan(
            practice_goal="Capture one coachable swing and hold the finish.",
            tomorrow_plan=[
                "Set the camera at hand height.",
                "Film one swing face-on or down-the-line.",
                "Keep head, feet, ball, hands, and club in frame.",
                "Add your normal miss before uploading.",
            ],
            primary_drill=PgaDrill(
                name="Clean Upload Rehearsal",
                why_it_helps="A stable recording lets the coach trace the first breakdown instead of guessing.",
                how_to_do_it="Make three practice swings, then record one normal swing and hold the finish.",
            ),
            feels=["Tripod-still camera.", "One swing only.", "Hold the finish."],
            dosage="One clean upload before any mechanical work.",
            success_check="The next report names a body checkpoint instead of camera setup.",
        ),
        improvement_benchmark=ImprovementBenchmark(
            metric="Video coachability",
            current_state="Low confidence: the upload does not support a responsible first-breakdown read.",
            target_next_upload="High enough visibility to identify address, top, transition, impact, and finish.",
            upload_instruction="Record one full-body swing from a stable face-on or down-the-line angle.",
        ),
        progress_score=ProgressScore(
            overall=0,
            previous_overall=None,
            trend="unknown",
            summary="No progress score yet because this upload was not measurable.",
            metrics=[
                ProgressMetric(name="Head stability", current_score=0, interpretation="Not measurable from this upload."),
                ProgressMetric(name="Balance", current_score=0, interpretation="Not measurable from this upload."),
                ProgressMetric(name="Posture retention", current_score=0, interpretation="Not measurable from this upload."),
                ProgressMetric(name="Hip depth", current_score=0, interpretation="Not measurable from this upload."),
                ProgressMetric(name="Sequencing", current_score=0, interpretation="Not measurable from this upload."),
                ProgressMetric(name="Consistency", current_score=0, interpretation="Not measurable from this upload."),
            ],
        ),
        confidence=ImprovementConfidence(
            level="low",
            why=note,
            limiting_factors=["Video clarity or service availability prevented a confident read."],
            evidence_used=["Upload metadata", "fallback report"],
        ),
        practice_value_score=PracticeValueScore(
            contact="low",
            direction="low",
            consistency="medium",
            distance="low",
            summary="The highest-value action is improving the next upload, not changing mechanics yet.",
        ),
    )


def _fallback_report(
    reason: str | None = None,
    player_name: str | None = None,
    swing_mode: SwingMode = "full_swing",
) -> CoachingReportSchema:
    note = reason or "Try again in a few minutes."
    name = (player_name or "there").split()[0]
    diagnosis = SwingDiagnosisEngine(
        main_diagnosis="Video clarity prevented a confident cause-and-effect diagnosis",
        skill_level_note="Re-upload a cleaner angle before changing mechanics.",
        first_breakdown_checkpoint="setup/address",
        root_cause="Camera angle or video quality prevented reliable checkpoint measurement",
        symptom="Unclear ball-flight or contact pattern",
        chain_reaction="Without reliable checkpoint evidence, impact symptoms cannot be traced backward safely.",
        fix_priority={
            "primary": "Film a stable full-body face-on or down-the-line video",
            "secondary": "Keep the same club and one swing per upload",
            "optional": "Add ball-flight context after the video is clear",
        },
        evidence=[],
        what_to_feel="Full body in frame, stable camera, good light.",
        one_drill={
            "name": "Clean Upload Check",
            "instructions": "Record one full swing from a stable face-on or down-the-line angle with head, hands, hips, knees, feet, ball, and club visible.",
            "sets_reps": "1 clean upload",
            "success_metric": "All checkpoints are visible from setup through finish.",
        },
        next_upload_focus="Full body, stable camera, good light.",
        coach_warning=note,
        issues=[],
    )
    report = CoachingReportSchema(
        personalized_greeting=f"{name}, we couldn't build your Feel Blueprint this time. Re-upload when you're ready.",
        feel_blueprint=FeelBlueprintDiagnostic(
            opening_narrative=f"{name}, we couldn't read this video clearly enough for a full breakdown.",
            headline="Analysis unavailable",
            strengths=[
                AnalysisBullet(
                    title="Willing to compete",
                    detail="You uploaded — that's the first step to fixing the pattern.",
                ),
                AnalysisBullet(
                    title="Finish balance",
                    detail="We'll assess this once we have a clear full-body view.",
                ),
            ],
            flaws=[
                AnalysisBullet(
                    title="Video quality",
                    detail=note,
                ),
                AnalysisBullet(
                    title="Camera angle",
                    detail="We need face-on or down-the-line with full body visible.",
                ),
            ],
            current_ceiling="Re-upload to get a real ceiling read.",
            potential_ceiling="A clear film unlocks an honest handicap range and fixes.",
            pro_fixes=[
                ProFix(
                    title="Film it right",
                    detail="Face-on or down-the-line, full body, stable camera, good light.",
                ),
                ProFix(
                    title="One swing only",
                    detail="Upload a single clean rep so we can read setup through finish.",
                ),
            ],
            body_part_cue="Athletic setup — weight on the balls of your feet.",
            spatial_cue="Full body in frame — head to feet visible.",
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
        improvement_engine=_fallback_improvement_engine(note),
        pga_coach_analysis=PgaCoachAnalysis(
            pga_analysis=(
                "The biggest issue is video clarity, so the first breakdown cannot be identified "
                "responsibly from this upload."
            ),
            main_fix="Re-film one stable full-body swing before changing mechanics.",
            tips_and_feels=[
                "Keep the camera still.",
                "Show the full body, ball, hands, and club.",
                "Record one normal swing from address through finish.",
            ],
            drills=[
                PgaDrill(
                    name="Clean Upload Check",
                    why_it_helps="A clear angle lets the coach trace the first breakdown instead of guessing.",
                    how_to_do_it="Film face-on or down-the-line from waist height with the full body in frame.",
                ),
                PgaDrill(
                    name="Hold-Finish Rehearsal",
                    why_it_helps="Holding the finish makes the full sequence easier to review.",
                    how_to_do_it="Make three smooth swings and hold the finish until the ball lands.",
                ),
            ],
            next_upload_focus="Stable face-on or down-the-line video with full body, ball, hands, and club visible.",
            confidence_note=note,
        ),
        coach_summary_report=CoachSummaryReport(
            coach_summary=(
                "This upload was not clear enough for a useful paid swing read. "
                "The best fix is to re-film before changing mechanics."
            ),
            whats_working=[
                "You took the right first step by uploading a swing for review.",
                "A cleaner angle will let the app find real strengths and flaws instead of guessing.",
            ],
            main_swing_leak="The video angle or clarity is the main issue right now.",
            why_it_matters="A low-confidence video can turn practice into guessing.",
            feel_this_week="The Clean Film Check — full body, ball, hands, and club visible from setup through finish.",
            what_to_feel=[
                "Keep the camera still.",
                "Show your full body and club.",
                "Hold the finish.",
            ],
            fix_it_drill=FixItDrill(
                name="Clean Upload Check",
                steps=[
                    "Set the camera at waist height.",
                    "Film face-on or down-the-line.",
                    "Keep your full body, ball, hands, and club in frame.",
                ],
                dose="Record one normal swing.",
                success_check="The next report names a body checkpoint instead of camera setup.",
            ),
            practice_plan_7_day=[
                "Day 1-2: film a clean swing.",
                "Day 3-4: upload one normal swing.",
                "Day 5-6: train only the first fix.",
                "Day 7: upload a comparison video.",
            ],
            next_upload_goal="Film a stable full-body swing from face-on or down-the-line.",
            advanced_details=AdvancedDetails(
                first_breakdown_checkpoint="camera setup",
                root_cause="Video clarity prevented reliable checkpoint analysis.",
                symptom="The miss could not be traced backward with enough confidence.",
                confidence_note=note,
                camera_angle_limitations="A clearer face-on or down-the-line angle is needed.",
                evidence_plain_english=["The video did not support a responsible first-breakdown read."],
                raw_metrics={},
            ),
        ),
        diagnosis_engine=diagnosis,
        next_upload_focus="Full body, stable camera, good light.",
        disclaimer=DISCLAIMER,
    )
    return enrich_coaching_report(report, swing_mode)


def _call_gemini(
    client: genai.Client,
    model: str,
    content_parts: list[types.Part],
    swing_mode: SwingMode = "full_swing",
    *,
    swing_id: str | None = None,
    trace_id: str | None = None,
    player_name: str | None = None,
    frame_count: int = 0,
    full_video_sent: bool = False,
) -> tuple[CoachingReportSchema, str]:
    _trace_log(
        "gemini_request_started",
        swing_id=swing_id,
        trace_id=trace_id,
        model_name=model,
        response_schema_used=True,
        frame_count=frame_count,
        full_video_sent=full_video_sent,
        content_part_count=len(content_parts),
    )
    schema_used = True
    try:
        response = _generate_gemini_content(
            client,
            model=model,
            content_parts=content_parts,
            use_schema=True,
        )
    except Exception as exc:
        if not _is_schema_serving_error(exc):
            raise
        schema_used = False
        _trace_log(
            "gemini_schema_fallback",
            swing_id=swing_id,
            trace_id=trace_id,
            error=str(exc),
            model_name=model,
            response_schema_used=True,
        )
        response = _generate_gemini_content(
            client,
            model=model,
            content_parts=content_parts,
            use_schema=False,
        )
    text = response.text or "{}"
    _trace_log(
        "gemini_response_received",
        swing_id=swing_id,
        trace_id=trace_id,
        model_name=model,
        response_schema_used=schema_used,
        response_chars=len(text),
    )
    report = _parse_coaching_report(text, player_name=player_name, swing_mode=swing_mode)
    _trace_log(
        "gemini_json_parse_success",
        swing_id=swing_id,
        trace_id=trace_id,
        model_name=model,
        response_schema_used=schema_used,
    )
    if DISCLAIMER not in report.disclaimer:
        report.disclaimer = DISCLAIMER
    return enrich_coaching_report(report, swing_mode), text


def _diagnosis_is_not_actionable(diagnosis: SwingDiagnosisEngine | None) -> bool:
    if diagnosis is None:
        return True
    text = " ".join(
        [
            diagnosis.main_diagnosis,
            diagnosis.root_cause,
            diagnosis.first_breakdown_checkpoint,
        ]
    ).lower()
    return (
        "no single high-confidence" in text
        or "no single high confidence" in text
        or "no single root" in text
        or "metrics were unavailable" in text
    )


def _report_text(report: CoachingReportSchema) -> str:
    feel = report.feel_blueprint
    chunks = [
        feel.opening_narrative,
        feel.headline,
        *(item.title + " " + item.detail for item in feel.flaws),
        *(fix.title + " " + fix.detail for fix in feel.pro_fixes),
        feel.body_part_cue,
        feel.spatial_cue,
    ]
    return " ".join(chunks).lower()


def _evidence_from_coach_read(
    *,
    checkpoint: str,
    observed: str,
    interpretation: str,
    confidence: float = 0.62,
) -> SwingMetricEvidence:
    return SwingMetricEvidence(
        checkpoint=checkpoint,
        metric="coach_video_read",
        observed=observed,
        expected="A stable checkpoint pattern that lets the next move happen without compensation.",
        interpretation=interpretation,
        confidence=confidence,
    )


def _synthesized_diagnosis_from_report(
    report: CoachingReportSchema,
    rule_diagnosis: SwingDiagnosisEngine | None,
) -> SwingDiagnosisEngine:
    text = _report_text(report)
    warning = (
        rule_diagnosis.coach_warning
        if rule_diagnosis
        else "This is an AI-supported coaching read because marker confidence was limited."
    )

    if any(token in text for token in ("sway", "reverse pivot", "lateral", "slides", "drift")):
        root = "Likely lateral sway before the top of the backswing"
        return SwingDiagnosisEngine(
            main_diagnosis=root,
            skill_level_note="Fix the body-center checkpoint before chasing impact.",
            first_breakdown_checkpoint="top of backswing",
            root_cause=root,
            symptom="Timing-dependent contact and face/path delivery",
            chain_reaction=(
                "When the body drifts off the ball, pressure arrives late in transition. "
                "The upper body and hands then have to rescue low point and direction through impact."
            ),
            fix_priority=FixPriorityBlock(
                primary="Stop the lateral drift by the top checkpoint",
                secondary="Recheck transition pressure shift after the sway improves",
                optional="Only tune impact face/path after the body center is stable",
            ),
            evidence=[
                _evidence_from_coach_read(
                    checkpoint="top of backswing",
                    observed="Coach narrative identified lateral sway/drift as the pattern creating the miss.",
                    interpretation="The first useful checkpoint is the top, where the body center should be coiled rather than slid.",
                )
            ],
            what_to_feel="Turn around a steady chest while pressure gathers under the inside of the trail foot.",
            one_drill=DrillPrescription(
                name="Trail-Instep Coil Drill",
                instructions="Make slow backswings with the trail foot rolled slightly inward. Stop at the top and confirm your head and belt buckle have not slid outside the trail foot.",
                sets_reps="3 sets of 8 slow rehearsals, then 10 half-speed balls",
                success_metric="At the top checkpoint, body center stays inside the trail foot.",
            ),
            next_upload_focus="Film face-on and pause the top checkpoint.",
            coach_warning=f"{warning} This finding is labeled likely because it is supported by the coaching read more than high-confidence markers.",
            issues=[],
        )

    if any(token in text for token in ("over the top", "steep", "disconnected", "throws", "outside")):
        root = "Likely disconnected top position causing a steep transition"
        return SwingDiagnosisEngine(
            main_diagnosis=root,
            skill_level_note="Fix transition sequence before fixing impact.",
            first_breakdown_checkpoint="top of backswing",
            root_cause=root,
            symptom="Likely pull/slice or steep contact pattern",
            chain_reaction="A disconnected top makes the arms start outward first, so the club arrives steep before impact can be cleaned up.",
            fix_priority=FixPriorityBlock(
                primary="Reconnect the trail arm at the top",
                secondary="Start transition from the lower body",
                optional="Recheck face control after path improves",
            ),
            evidence=[
                _evidence_from_coach_read(
                    checkpoint="top of backswing",
                    observed="Coach narrative identified a steep/disconnected delivery pattern.",
                    interpretation="The path issue is being created before impact.",
                )
            ],
            what_to_feel="Trail elbow folds in front of the ribs, then the lower body starts first.",
            one_drill=DrillPrescription(
                name="Trail-Elbow Towel Pump",
                instructions="Hold a small towel under the trail armpit. Make three slow pumps from the top to lead-arm-parallel-down, then hit a half shot.",
                sets_reps="3 pump rehearsals before each of 20 balls",
                success_metric="Top and transition checkpoints show the trail elbow closer to the rib line.",
            ),
            next_upload_focus="Film down-the-line and capture top plus transition clearly.",
            coach_warning=f"{warning} This finding is labeled likely because exact club path requires clearer marker/club visibility.",
            issues=[],
        )

    if any(token in text for token in ("early extension", "stands up", "posture", "hip depth", "crowded")):
        root = "Likely posture and hip-depth loss in transition"
        return SwingDiagnosisEngine(
            main_diagnosis=root,
            skill_level_note="Create space before trying to fix strike.",
            first_breakdown_checkpoint="transition",
            root_cause=root,
            symptom="Crowded impact and timing-dependent contact",
            chain_reaction="When hip depth is lost, the hands run out of space and the body has to stand up through the strike.",
            fix_priority=FixPriorityBlock(
                primary="Keep hip depth through transition",
                secondary="Preserve chest-over-ball posture into delivery",
                optional="Recheck contact pattern after space improves",
            ),
            evidence=[
                _evidence_from_coach_read(
                    checkpoint="transition",
                    observed="Coach narrative identified posture/space loss as the pattern.",
                    interpretation="Impact is a reaction to lost space earlier in the downswing.",
                )
            ],
            what_to_feel="Lead hip turns back behind you while your chest stays over the ball.",
            one_drill=DrillPrescription(
                name="Chair Hip-Depth Rehearsal",
                instructions="Set a chair just behind your hips. Keep light contact in the backswing and regain it in transition before brushing a tee.",
                sets_reps="2 sets of 10 rehearsals, then 15 waist-high shots",
                success_metric="Impact checkpoint keeps hip depth close to setup.",
            ),
            next_upload_focus="Film down-the-line with hips, feet, and hands visible.",
            coach_warning=f"{warning} This finding is labeled likely because it is inferred from the video pattern.",
            issues=[],
        )

    return SwingDiagnosisEngine(
        main_diagnosis="Video angle limited first-breakdown detection",
        skill_level_note="Do not change mechanics from a low-confidence read.",
        first_breakdown_checkpoint="camera setup",
        root_cause="Camera angle or visibility prevented a useful first-breakdown diagnosis",
        symptom="The miss could not be traced backward with enough confidence",
        chain_reaction="When checkpoint visibility is weak, the system cannot responsibly separate root cause from compensation.",
        fix_priority=FixPriorityBlock(
            primary="Re-film from a stable face-on or down-the-line angle",
            secondary="Keep the full body, ball, hands, and club in frame",
            optional="Add ball-flight context after the video is clear",
        ),
        evidence=[],
        what_to_feel="Full body in frame, camera still, one swing only.",
        one_drill=DrillPrescription(
            name="Clean Film Check",
            instructions="Record one swing from waist height with the full body, ball, and club visible from setup through finish.",
            sets_reps="1 upload",
            success_metric="The report names a body checkpoint instead of camera setup.",
        ),
        next_upload_focus="Stable face-on or down-the-line video with full body visible.",
        coach_warning=warning,
        issues=[],
    )


def _ensure_actionable_diagnosis(
    report: CoachingReportSchema,
    rule_diagnosis: SwingDiagnosisEngine | None,
) -> CoachingReportSchema:
    if _diagnosis_is_not_actionable(report.diagnosis_engine):
        report.diagnosis_engine = _synthesized_diagnosis_from_report(report, rule_diagnosis)
    return report


def generate_coaching_report(
    *,
    swing_id: str | None = None,
    trace_id: str | None = None,
    video_path: Path | None,
    video_mime_type: str | None = None,
    frames: list[np.ndarray] | None,
    keyframe_indices: dict[str, int] | None,
    fps: float = 30.0,
    sample_every_n: int = 2,
    swing_mode: SwingMode = "full_swing",
    diagnosis_engine: SwingDiagnosisEngine | None = None,
    metric_payload: dict | None = None,
    history_summary: str | None,
    player_name: str | None = None,
    swing_number: int | None = None,
    player_context: str | None = None,
    player_age: int | None = None,
    years_playing: int | None = None,
    physical_limitations: str | None = None,
    camera_angle: str | None = None,
    handedness: str | None = None,
    skill_level: str | None = None,
    ball_flight: str | None = None,
    user_goal: str | None = None,
    club_used: str | None = None,
    practice_availability: str | None = None,
    handicap: str | None = None,
    prior_progress: dict | None = None,
) -> tuple[CoachingReportSchema, bool, dict]:
    settings = get_settings()
    frame_debug = (
        keyframe_debug_metadata(keyframe_indices, fps=fps, sample_every_n=sample_every_n)
        if keyframe_indices
        else []
    )
    meta: dict = {
        "model_used": None,
        "error": None,
        "video_attached": False,
        "full_video_sent": False,
        "frame_count": len(frame_debug),
        "frame_labels": [item["label"] for item in frame_debug],
        "frame_timestamps": {
            str(item["label"]): item["timestamp_sec"] for item in frame_debug
        },
        "frames": frame_debug,
        "prompt": None,
        "gemini_raw_response": None,
        "input_parts": [],
    }

    if not settings.gemini_api_key:
        logger.warning("GEMINI_API_KEY not set; using fallback report")
        meta["error"] = "GEMINI_API_KEY not configured"
        _trace_log(
            "gemini_request_started",
            swing_id=swing_id,
            trace_id=trace_id,
            error=meta["error"],
            fallback_status="used",
            response_schema_used=False,
        )
        report = _fallback_report(meta["error"], player_name, swing_mode)
        if diagnosis_engine:
            report.diagnosis_engine = diagnosis_engine
        report = _ensure_actionable_diagnosis(report, diagnosis_engine)
        return report, False, meta

    prompt = _build_prompt(
        swing_mode=swing_mode,
        history_summary=history_summary,
        player_name=player_name,
        swing_number=swing_number,
        player_context=player_context,
        player_age=player_age,
        years_playing=years_playing,
        physical_limitations=physical_limitations,
        camera_angle=camera_angle,
        handedness=handedness,
        skill_level=skill_level,
        ball_flight=ball_flight,
        user_goal=user_goal,
        club_used=club_used,
        practice_availability=practice_availability,
        handicap=handicap,
        prior_progress=prior_progress,
        diagnosis_engine=diagnosis_engine,
        metric_payload=metric_payload,
    )
    meta["prompt"] = prompt

    client = genai.Client(api_key=settings.gemini_api_key)
    uploaded_file: types.File | None = None
    errors: list[str] = []

    try:
        content_parts: list[types.Part] = []

        if video_path and video_path.exists():
            logger.info("Uploading swing video for Feel Blueprint...")
            uploaded_file = upload_video(client, video_path, video_mime_type)
            meta["video_attached"] = True
            meta["full_video_sent"] = True
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
                        f"{mode_label.capitalize()} video above. Watch setup through finish, "
                        "then write the Feel Blueprint JSON."
                    )
                )
            )
            meta["input_parts"].append(
                {
                    "type": "video",
                    "mime_type": uploaded_file.mime_type or "video/mp4",
                    "file_name": uploaded_file.name,
                    "uri_available": bool(file_uri),
                }
            )

        if frames and keyframe_indices:
            timestamps = keyframe_timestamps(keyframe_indices, fps=fps, sample_every_n=sample_every_n)
            content_parts.extend(build_keyframe_parts(frames, keyframe_indices, timestamps))
            frame_debug = keyframe_debug_metadata(keyframe_indices, fps=fps, sample_every_n=sample_every_n)
            meta["frame_count"] = len(frame_debug)
            meta["frame_labels"] = [item["label"] for item in frame_debug]
            meta["frame_timestamps"] = {
                str(item["label"]): item["timestamp_sec"] for item in frame_debug
            }
            meta["frames"] = frame_debug
            meta["input_parts"].append(
                {
                    "type": "ordered_keyframes",
                    "count": len(frame_debug),
                    "frames": frame_debug,
                    "mime_type": "image/jpeg",
                }
            )

        content_parts.append(types.Part.from_text(text=prompt))
        meta["input_parts"].append({"type": "prompt", "text": prompt})

        for model in _models_to_try(settings.gemini_model, settings.gemini_fallback_model):
            try:
                logger.info("Generating Feel Blueprint with %s...", model)
                report, raw_response = _call_gemini(
                    client,
                    model,
                    content_parts,
                    swing_mode,
                    swing_id=swing_id,
                    trace_id=trace_id,
                    player_name=player_name,
                    frame_count=int(meta.get("frame_count") or 0),
                    full_video_sent=bool(meta.get("full_video_sent")),
                )
                if report.diagnosis_engine is None:
                    report.diagnosis_engine = diagnosis_engine
                report = _ensure_actionable_diagnosis(report, diagnosis_engine)
                meta["model_used"] = model
                meta["gemini_raw_response"] = raw_response
                return report, True, meta
            except Exception as exc:
                err = f"{model}: {exc}"
                _trace_log(
                    "gemini_response_received",
                    swing_id=swing_id,
                    trace_id=trace_id,
                    error=str(exc),
                    model_name=model,
                    response_schema_used=False,
                    raw_gemini_error=str(exc),
                    fallback_status="pending",
                )
                logger.warning(
                    "Gemini model failed model_name=%s response_schema_used=%s raw_gemini_error=%s fallback_status=%s",
                    model,
                    False,
                    str(exc),
                    "pending",
                )
                errors.append(err)
                if not _is_retryable_model_error(exc):
                    break

        last_error = errors[-1] if errors else "Unknown Gemini error"
        if "429" in last_error or "quota" in last_error.lower():
            meta["error"] = "Gemini API quota exceeded — enable billing or wait and retry"
        else:
            meta["error"] = last_error[:300]
        _trace_log(
            "gemini_response_received",
            swing_id=swing_id,
            trace_id=trace_id,
            error=meta["error"],
            response_schema_used=False,
            fallback_status="used",
        )
        report = _fallback_report(meta["error"], player_name, swing_mode)
        if diagnosis_engine:
            report.diagnosis_engine = diagnosis_engine
        report = _ensure_actionable_diagnosis(report, diagnosis_engine)
        return report, False, meta
    except Exception as exc:
        logger.exception("Gemini Feel Blueprint failed: %s", exc)
        meta["error"] = str(exc)[:300]
        _trace_log(
            "gemini_response_received",
            swing_id=swing_id,
            trace_id=trace_id,
            error=meta["error"],
            response_schema_used=False,
            raw_gemini_error=str(exc),
            fallback_status="used",
        )
        report = _fallback_report(meta["error"], player_name, swing_mode)
        if diagnosis_engine:
            report.diagnosis_engine = diagnosis_engine
        report = _ensure_actionable_diagnosis(report, diagnosis_engine)
        return report, False, meta
    finally:
        delete_uploaded_file(client, uploaded_file)
