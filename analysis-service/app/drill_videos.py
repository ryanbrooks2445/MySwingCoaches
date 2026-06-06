from __future__ import annotations

import logging

from app.chronological_evaluation import setup_is_primary_constraint
from app.drill_matching import (
    audit_report_bias,
    is_back_to_target_drill_name,
    pick_drill_slug,
    primary_diagnosis_blob,
    slug_allowed_for_diagnosis,
    suggests_ott,
)
from app.schemas import BlueprintStep, CoachingReportSchema, DrillSummary, SwingMode

DRILL_CATALOG: dict[str, dict[str, str | list[str]]] = {
    "wall_contact": {
        "title": "Wall / glute contact drill",
        "embed_url": "https://www.youtube.com/embed/fOpifmb8KZo",
        "for": "Early extension, maintaining posture through impact",
        "modes": ["full_swing"],
    },
    "chair_drill": {
        "title": "Chair drill — spine angle retention",
        "embed_url": "https://www.youtube.com/embed/5bHGjJ_6Kis",
        "for": "Early extension, staying in your angles",
        "modes": ["full_swing"],
    },
    "hip_slide_rotation": {
        "title": "Hip slide + rotation sequence",
        "embed_url": "https://www.youtube.com/embed/zEtWHtQR0T0",
        "for": "Transition, clearing hips without thrusting at the ball",
        "modes": ["full_swing"],
    },
    "back_to_target": {
        "title": "Back-to-target turn",
        "embed_url": "https://www.youtube.com/embed/iwbHIX3IlhA",
        "for": "ONLY when over-the-top is confirmed on film — shoulders spinning open too early",
        "modes": ["full_swing"],
    },
    "setup_posture": {
        "title": "Athletic setup & posture",
        "embed_url": "https://www.youtube.com/embed/5bHGjJ_6Kis",
        "for": "Address position, hip hinge, balance",
        "modes": ["full_swing", "chipping"],
    },
    "alignment_stick_shallow": {
        "title": "Shallowing with alignment stick",
        "embed_url": "https://www.youtube.com/embed/zEtWHtQR0T0",
        "for": "ONLY when steep path / OTT is confirmed on film",
        "modes": ["full_swing"],
    },
    "feet_together": {
        "title": "Feet-together balance swings",
        "embed_url": "https://www.youtube.com/embed/fOpifmb8KZo",
        "for": "Balance, tempo, centered rotation, weight transfer",
        "modes": ["full_swing", "chipping"],
    },
    "slow_motion_reps": {
        "title": "Slow-motion rehearsal swings",
        "embed_url": "https://www.youtube.com/embed/iwbHIX3IlhA",
        "for": "Tempo, sequencing, building a new feel at half speed",
        "modes": ["full_swing", "chipping", "putting"],
    },
    "chip_landing_towel": {
        "title": "Towel landing zone — chip control",
        "embed_url": "https://www.youtube.com/embed/zEtWHtQR0T0",
        "for": "Distance control, low point, landing spot focus",
        "modes": ["chipping"],
    },
    "chip_hinge_punch": {
        "title": "Hinge and punch chip",
        "embed_url": "https://www.youtube.com/embed/5bHGjJ_6Kis",
        "for": "Steep chips, fat/thin, wrists flipping",
        "modes": ["chipping"],
    },
    "chip_one_hand": {
        "title": "Lead-hand only chips",
        "embed_url": "https://www.youtube.com/embed/fOpifmb8KZo",
        "for": "Yips, decel, steering with the trail hand",
        "modes": ["chipping"],
    },
    "chip_bump_run": {
        "title": "Bump-and-run setup",
        "embed_url": "https://www.youtube.com/embed/iwbHIX3IlhA",
        "for": "Low runner, weight forward, minimal hinge",
        "modes": ["chipping"],
    },
    "putting_gate": {
        "title": "Gate drill — start line",
        "embed_url": "https://www.youtube.com/embed/IqhVY4XRls8",
        "for": "Pushes/pulls, face control at impact",
        "modes": ["putting"],
    },
    "putting_metronome": {
        "title": "Tempo metronome strokes",
        "embed_url": "https://www.youtube.com/embed/fOpifmb8KZo",
        "for": "Rushed backstroke, jerky forward stroke",
        "modes": ["putting"],
    },
    "putting_eyes_closed": {
        "title": "Eyes-closed feel rehearsal",
        "embed_url": "https://www.youtube.com/embed/5bHGjJ_6Kis",
        "for": "Tension, steering, poor distance feel",
        "modes": ["putting"],
    },
    "putting_ruler": {
        "title": "Ruler backstroke length drill",
        "embed_url": "https://www.youtube.com/embed/zEtWHtQR0T0",
        "for": "Distance control, consistent backstroke length",
        "modes": ["putting"],
    },
    "generic_feel": {
        "title": "Range feel rehearsal",
        "embed_url": "https://www.youtube.com/embed/fOpifmb8KZo",
        "for": "General kinesthetic practice",
        "modes": ["full_swing", "chipping", "putting"],
    },
}

logger = logging.getLogger(__name__)

DEFAULT_SLUG_BY_MODE: dict[SwingMode, dict[str, str]] = {
    "full_swing": {
        "setup": "setup_posture",
        "visual_cue": "slow_motion_reps",
        "constraint_drill": "feet_together",
    },
    "chipping": {
        "setup": "setup_posture",
        "visual_cue": "chip_landing_towel",
        "constraint_drill": "chip_hinge_punch",
    },
    "putting": {
        "setup": "putting_gate",
        "visual_cue": "putting_metronome",
        "constraint_drill": "putting_eyes_closed",
    },
}


def _slug_modes(slug: str) -> list[str]:
    modes = DRILL_CATALOG[slug].get("modes", ["full_swing"])
    if isinstance(modes, str):
        return [modes]
    return list(modes)


def catalog_for_prompt(swing_mode: SwingMode = "full_swing") -> str:
    lines = [
        f"Available video_slug values for {swing_mode} (pick the slug that matches the ACTUAL missing piece on film):",
        "IMPORTANT: back_to_target and alignment_stick_shallow ONLY when steep/OTT is visibly graded — not your default.",
    ]
    for slug, meta in DRILL_CATALOG.items():
        if slug == "generic_feel":
            continue
        if swing_mode not in _slug_modes(slug):
            continue
        lines.append(f"  - {slug}: {meta['for']}")
    lines.append("  - generic_feel: fallback when nothing else fits")
    lines.append("Pick a DIFFERENT slug than prior uploads unless the same Constraint is still visible.")
    return "\n".join(lines)


def resolve_drill_video(
    slug: str | None,
    step_type: str,
    swing_mode: SwingMode = "full_swing",
    *,
    diagnosis_text: str = "",
    exclude: set[str] | None = None,
) -> dict[str, str]:
    exclude = exclude or set()
    defaults = DEFAULT_SLUG_BY_MODE.get(swing_mode, DEFAULT_SLUG_BY_MODE["full_swing"])

    key = slug if slug and slug in DRILL_CATALOG else defaults.get(step_type, "generic_feel")
    if key not in DRILL_CATALOG or swing_mode not in _slug_modes(key):
        key = defaults.get(step_type, "generic_feel")
    if key in exclude or not slug_allowed_for_diagnosis(key, diagnosis_text):
        key = pick_drill_slug(
            diagnosis_text=diagnosis_text,
            step_type=step_type,
            swing_mode=swing_mode,
            exclude=exclude,
        )
    elif key == "back_to_target" and not suggests_ott(diagnosis_text):
        key = pick_drill_slug(
            diagnosis_text=diagnosis_text,
            step_type=step_type,
            swing_mode=swing_mode,
            exclude=exclude | {"back_to_target"},
        )
    entry = DRILL_CATALOG.get(key, DRILL_CATALOG["generic_feel"])
    return {
        "video_slug": key,
        "video_url": str(entry["embed_url"]),
        "video_title": str(entry["title"]),
    }


def enrich_step_videos(
    step: BlueprintStep,
    swing_mode: SwingMode = "full_swing",
    *,
    diagnosis_text: str = "",
    exclude: set[str] | None = None,
) -> BlueprintStep:
    resolved = resolve_drill_video(
        step.video_slug,
        step.step_type,
        swing_mode,
        diagnosis_text=diagnosis_text,
        exclude=exclude,
    )
    return step.model_copy(update=resolved)


def _catalog_drill(slug: str) -> DrillSummary:
    entry = DRILL_CATALOG.get(slug, DRILL_CATALOG["generic_feel"])
    return DrillSummary(
        name=str(entry["title"]),
        why_it_helps=str(entry["for"]),
        how_to_do_it="15–20 reps at half speed before full swings.",
    )


def _sanitize_drills(
    drills: list[DrillSummary],
    *,
    primary_diagnosis: str,
    swing_mode: SwingMode,
    exclude: set[str],
) -> list[DrillSummary]:
    """Replace OTT-themed drill names when primary diagnosis is not OTT."""
    sanitized: list[DrillSummary] = []
    for drill in drills:
        if is_back_to_target_drill_name(drill.name) and not suggests_ott(primary_diagnosis):
            slug = pick_drill_slug(
                diagnosis_text=primary_diagnosis,
                step_type="constraint_drill",
                swing_mode=swing_mode,
                exclude=exclude,
            )
            exclude.add(slug)
            sanitized.append(_catalog_drill(slug))
        else:
            sanitized.append(drill)
    return sanitized


def enrich_coaching_report(
    report: CoachingReportSchema,
    swing_mode: SwingMode = "full_swing",
) -> CoachingReportSchema:
    adv = report.advanced_details
    primary_diagnosis = primary_diagnosis_blob(
        foundational_missing_piece=adv.foundational_missing_piece,
        main_fix=report.main_fix,
        root_cause=adv.root_cause,
    )

    if setup_is_primary_constraint(adv.foundational_missing_piece, report.main_fix):
        primary_diagnosis = f"{primary_diagnosis} setup feet posture heels stance hinge address"

    used_slugs: set[str] = set()
    enriched_steps: list[BlueprintStep] = []
    for step in report.blueprint.steps:
        enriched = enrich_step_videos(
            step,
            swing_mode,
            diagnosis_text=primary_diagnosis,
            exclude=used_slugs,
        )
        used_slugs.add(enriched.video_slug or "")
        enriched_steps.append(enriched)

    sanitized_drills = _sanitize_drills(
        list(report.drills),
        primary_diagnosis=primary_diagnosis,
        swing_mode=swing_mode,
        exclude=used_slugs,
    )

    flags = audit_report_bias(
        foundational_missing_piece=adv.foundational_missing_piece,
        main_fix=report.main_fix,
        drill_names=[d.name for d in sanitized_drills],
        blueprint_slugs=[s.video_slug or "" for s in enriched_steps],
    )
    if flags:
        logger.warning("OTT/back-to-target bias flags: %s", "; ".join(flags))

    blueprint = report.blueprint.model_copy(update={"steps": enriched_steps})
    return report.model_copy(update={"blueprint": blueprint, "drills": sanitized_drills})
