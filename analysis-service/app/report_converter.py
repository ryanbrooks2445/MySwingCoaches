"""Convert slim Gemini JSON output to full CoachingReportSchema."""

from __future__ import annotations

import json
import re

from app.gemini_report_schema import GeminiReportOut
from app.trace_log import log_trace
from app.schemas import (
    AccountabilityPlan,
    AdvancedDetails,
    BlueprintStep,
    CoachingReportSchema,
    DiagnosticCheckpointGrade,
    DrillSummary,
    KinestheticBlueprint,
    MilestoneBlock,
)

_VALID_GRADES = frozenset({"optimal", "compensation", "constraint", "not_visible"})


def _parse_checkpoint(raw: str) -> DiagnosticCheckpointGrade:
    parts = [p.strip() for p in raw.split("|", 2)]
    checkpoint = parts[0] if parts else raw.strip()
    grade = parts[1].lower() if len(parts) > 1 else "not_visible"
    observation = parts[2] if len(parts) > 2 else ""
    if grade not in _VALID_GRADES:
        grade = "not_visible"
    return DiagnosticCheckpointGrade(
        checkpoint=checkpoint or "Checkpoint",
        grade=grade,  # type: ignore[arg-type]
        observation=observation,
    )


def _clamp_confidence(value: float) -> float:
    if value != value:  # NaN
        return 0.75
    return max(0.0, min(1.0, value))


def _parse_drill_pipe(raw: str) -> DrillSummary | None:
    text = (raw or "").strip()
    if not text:
        return None
    parts = [p.strip() for p in text.split("|", 2)]
    if len(parts) >= 3:
        return DrillSummary(name=parts[0], why_it_helps=parts[1], how_to_do_it=parts[2])
    if len(parts) == 2:
        return DrillSummary(name=parts[0], why_it_helps=parts[1], how_to_do_it="15–20 half-speed reps.")
    return DrillSummary(name=parts[0], why_it_helps="Supports your main unlock.", how_to_do_it="15–20 half-speed reps.")


def _flatten_field(value: object) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        for key in ("pga_analysis", "analysis", "text", "content"):
            nested = value.get(key)
            if isinstance(nested, str) and nested.strip():
                return nested
        parts = [str(v) for v in value.values() if v]
        return "\n\n".join(parts)
    if value is None:
        return ""
    return str(value)


def _coerce_drill_field(value: object) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        name = str(value.get("name") or value.get("title") or "").strip()
        why = str(
            value.get("why")
            or value.get("why_it_helps")
            or value.get("reason")
            or ""
        ).strip()
        how = str(
            value.get("how")
            or value.get("how_to_do_it")
            or value.get("instructions")
            or ""
        ).strip()
        return f"{name}|{why}|{how}"
    return ""


def _coerce_string_list(value: object) -> list[str]:
    if not value:
        return []
    if not isinstance(value, list):
        return [str(value)] if value else []
    result: list[str] = []
    for item in value:
        if isinstance(item, str):
            result.append(item)
        elif isinstance(item, dict):
            label = str(item.get("checkpoint") or item.get("label") or "").strip()
            grade = str(item.get("grade") or item.get("value") or "").strip()
            obs = str(item.get("observation") or item.get("observed") or "").strip()
            parts = [p for p in (label, grade, obs) if p]
            result.append("|".join(parts) if parts else str(item))
        else:
            result.append(str(item))
    return result


def _normalize_gemini_dict(data: dict) -> dict:
    """Coerce loose Gemini JSON (nested drills, dict analysis, etc.) before Pydantic."""
    data = dict(data)

    if "drills" in data and isinstance(data["drills"], list):
        for i, drill in enumerate(data["drills"][:3], start=1):
            key = f"drill{i}"
            if not _coerce_drill_field(data.get(key)):
                data[key] = _coerce_drill_field(drill)

    for key in ("drill1", "drill2", "drill3"):
        if key in data:
            data[key] = _coerce_drill_field(data[key])

    for key in (
        "greeting",
        "analysis",
        "main_fix",
        "next_check",
        "missing",
        "profile",
        "root",
        "symptom",
        "chain",
        "focus",
        "day7",
    ):
        if key in data:
            data[key] = _flatten_field(data.get(key))

    if "mode" in data and not isinstance(data["mode"], str):
        data["mode"] = str(data["mode"] or "development")

    if "tips" in data:
        data["tips"] = _coerce_string_list(data["tips"])
    if "checkpoints" in data:
        data["checkpoints"] = _coerce_string_list(data["checkpoints"])
    if "evidence" in data:
        data["evidence"] = _coerce_string_list(data["evidence"])

    if "confidence" in data:
        try:
            data["confidence"] = float(data["confidence"])
        except (TypeError, ValueError):
            data["confidence"] = 0.75

    return data


def _coerce_gemini_raw(data: dict) -> GeminiReportOut:
    """Accept legacy long field names from older prompts or loose JSON."""
    if "greeting" not in data and "personalized_greeting" in data:
        data = {
            "greeting": data.get("personalized_greeting", ""),
            "analysis": data.get("pga_analysis", ""),
            "main_fix": data.get("main_fix", ""),
            "tips": data.get("tips_and_feels", data.get("tips", [])),
            "drill1": _legacy_drill(data, 0),
            "drill2": _legacy_drill(data, 1),
            "drill3": _legacy_drill(data, 2),
            "next_check": data.get("next_swing_check", data.get("next_check", "")),
            "mode": data.get("report_mode", data.get("mode", "development")),
            "missing": data.get("foundational_missing_piece", data.get("missing", "")),
            "profile": data.get("profile_constraints_applied", data.get("profile", "")),
            "checkpoints": data.get("diagnostic_checkpoints", data.get("checkpoints", [])),
            "root": data.get("root_cause", data.get("root", "")),
            "symptom": data.get("symptom", ""),
            "evidence": data.get("evidence_metrics", data.get("evidence", [])),
            "chain": data.get("chain_reaction", data.get("chain", "")),
            "confidence": data.get("confidence_score", data.get("confidence", 0.75)),
            "focus": data.get("weekly_focus", data.get("focus", "")),
            "day7": data.get("day_7_test", data.get("day7", "")),
        }

    return GeminiReportOut.model_validate(_normalize_gemini_dict(data))


def _legacy_drill(data: dict, index: int) -> str:
    drills = data.get("drills") or []
    if index < len(drills):
        return _coerce_drill_field(drills[index])
    return ""


def parse_gemini_json(
    text: str,
    *,
    trace_id: str | None = None,
    report_id: str | None = None,
    user_id: str | None = None,
) -> GeminiReportOut:
    try:
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
            cleaned = re.sub(r"\s*```$", "", cleaned)
        data = json.loads(cleaned or "{}")
        if not isinstance(data, dict):
            raise ValueError("Gemini response is not a JSON object")
        result = _coerce_gemini_raw(data)
        log_trace(
            "report_parsed",
            trace_id=trace_id,
            user_id=user_id,
            report_id=report_id,
            status="ok",
        )
        return result
    except Exception as exc:
        log_trace(
            "report_parsed",
            trace_id=trace_id,
            user_id=user_id,
            report_id=report_id,
            status="error",
            error=str(exc)[:500],
        )
        raise


def _build_blueprint(out: GeminiReportOut, tips: list[str]) -> KinestheticBlueprint:
    primary_feel = tips[0] if tips else (out.main_fix[:80] if out.main_fix else "Stay athletic.")
    secondary_feel = tips[1] if len(tips) > 1 else "Smooth tempo through the ball."
    headline = (out.focus or "Your unlock").strip()[:40] or "Your blueprint"
    return KinestheticBlueprint(
        headline=headline,
        intro="One feel at a time — setup first, then train the unlock.",
        steps=[
            BlueprintStep(
                title="Setup anchor",
                step_type="setup",
                adjustment="Athletic posture and balance before you swing.",
                feel=primary_feel,
                video_slug="setup_posture",
            ),
            BlueprintStep(
                title="Train the unlock",
                step_type="visual_cue",
                action="Half-speed reps with one cue only.",
                feel=secondary_feel,
                video_slug="slow_motion_reps",
            ),
            BlueprintStep(
                title="Constraint rep",
                step_type="constraint_drill",
                action="15–20 reps; quality over speed.",
                feel=out.main_fix[:80] if out.main_fix else "Own the pattern.",
                video_slug=None,
            ),
        ],
    )


def _build_roadmap(out: GeminiReportOut) -> AccountabilityPlan:
    focus = (out.focus or "Unlock").strip() or "Unlock"
    return AccountabilityPlan(
        weekly_focus=focus,
        milestones=[
            MilestoneBlock(
                days="Day 1-2",
                title="Setup reps",
                detail="Film-free reps on setup and primary feel only.",
            ),
            MilestoneBlock(
                days="Day 3-5",
                title="Train unlock",
                detail=f"Apply: {out.main_fix[:120] if out.main_fix else 'your main fix.'}",
            ),
            MilestoneBlock(
                days="Day 6-7",
                title="Film check",
                detail=out.next_check[:160] if out.next_check else "Film one rep face-on.",
            ),
        ],
        day_7_test=out.day7.strip() or "Main feel locked in at the range.",
    )


def gemini_out_to_coaching_report(out: GeminiReportOut) -> CoachingReportSchema:
    mode = out.mode if out.mode in ("development", "maintenance") else "development"
    checkpoints = [_parse_checkpoint(s) for s in out.checkpoints if s.strip()]

    tips = [t.strip() for t in out.tips if t.strip()][:4]
    if len(tips) < 2:
        tips.extend(["Feel balanced at address.", "Feel smooth through the ball."][: 2 - len(tips)])

    drills: list[DrillSummary] = []
    for raw in (out.drill1, out.drill2, out.drill3):
        parsed = _parse_drill_pipe(raw)
        if parsed:
            drills.append(parsed)
    if not drills and mode == "development":
        drills = [
            DrillSummary(
                name="Half-speed reps",
                why_it_helps="Builds the new feel without rushing.",
                how_to_do_it="20 balls at 50% with one cue only.",
            )
        ]

    next_check = out.next_check.strip() or "Film one swing face-on."

    return CoachingReportSchema(
        personalized_greeting=out.greeting or "Let's unlock your next level.",
        pga_analysis=out.analysis or "Analysis pending.",
        main_fix=out.main_fix or "Focus on one athletic feel at the range.",
        tips_and_feels=tips,
        drills=drills[:3],
        next_swing_check=next_check,
        advanced_details=AdvancedDetails(
            report_mode=mode,  # type: ignore[arg-type]
            foundational_missing_piece=out.missing or out.root,
            profile_constraints_applied=out.profile,
            diagnostic_checkpoints=checkpoints,
            root_cause=out.root or out.missing,
            symptom=out.symptom,
            evidence_metrics=out.evidence[:8],
            secondary_fix="",
            optional_fix="",
            chain_reaction=out.chain,
            why_it_caused_the_miss=out.symptom,
            confidence_score=_clamp_confidence(out.confidence),
            next_checkpoint="address",
        ),
        feel_blueprint=None,
        blueprint=_build_blueprint(out, tips),
        roadmap=_build_roadmap(out),
        next_upload_focus=next_check,
        disclaimer="",
    )
