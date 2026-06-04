from __future__ import annotations

from app.schemas import BlueprintStep, CoachingReportSchema

# Curated drill library — Gemini picks a slug; we resolve to a stable embed URL.
# Replace or extend with your own hosted MP4s in Supabase `drill-videos` when ready.

DRILL_CATALOG: dict[str, dict[str, str]] = {
    "wall_contact": {
        "title": "Wall / glute contact drill",
        "embed_url": "https://www.youtube.com/embed/fOpifmb8KZo",
        "for": "Early extension, maintaining posture through impact",
    },
    "chair_drill": {
        "title": "Chair drill — spine angle retention",
        "embed_url": "https://www.youtube.com/embed/5bHGjJ_6Kis",
        "for": "Early extension, staying in your angles",
    },
    "hip_slide_rotation": {
        "title": "Hip slide + rotation sequence",
        "embed_url": "https://www.youtube.com/embed/zEtWHtQR0T0",
        "for": "Transition, clearing hips without thrusting at the ball",
    },
    "back_to_target": {
        "title": "Back-to-target turn",
        "embed_url": "https://www.youtube.com/embed/iwbHIX3IlhA",
        "for": "Over-the-top, shoulders spinning open too early",
    },
    "setup_posture": {
        "title": "Athletic setup & posture",
        "embed_url": "https://www.youtube.com/embed/5bHGjJ_6Kis",
        "for": "Address position, hip hinge, balance",
    },
    "alignment_stick_shallow": {
        "title": "Shallowing with alignment stick",
        "embed_url": "https://www.youtube.com/embed/zEtWHtQR0T0",
        "for": "Steep downswing, over-the-top path",
    },
    "feet_together": {
        "title": "Feet-together balance swings",
        "embed_url": "https://www.youtube.com/embed/fOpifmb8KZo",
        "for": "Balance, tempo, centered rotation",
    },
    "slow_motion_reps": {
        "title": "Slow-motion rehearsal swings",
        "embed_url": "https://www.youtube.com/embed/iwbHIX3IlhA",
        "for": "Building a new feel at half speed",
    },
    "generic_feel": {
        "title": "Range feel rehearsal",
        "embed_url": "https://www.youtube.com/embed/fOpifmb8KZo",
        "for": "General kinesthetic practice",
    },
}

DEFAULT_SLUG_BY_STEP_TYPE = {
    "setup": "setup_posture",
    "visual_cue": "back_to_target",
    "constraint_drill": "wall_contact",
}


def catalog_for_prompt() -> str:
    lines = ["Available video_slug values (pick the best match for each blueprint step):"]
    for slug, meta in DRILL_CATALOG.items():
        if slug == "generic_feel":
            continue
        lines.append(f"  - {slug}: {meta['for']}")
    lines.append("  - generic_feel: fallback when nothing else fits")
    return "\n".join(lines)


def resolve_drill_video(slug: str | None, step_type: str) -> dict[str, str]:
    key = slug if slug and slug in DRILL_CATALOG else DEFAULT_SLUG_BY_STEP_TYPE.get(step_type, "generic_feel")
    if key not in DRILL_CATALOG:
        key = "generic_feel"
    entry = DRILL_CATALOG[key]
    return {
        "video_slug": key,
        "video_url": entry["embed_url"],
        "video_title": entry["title"],
    }


def enrich_step_videos(step: BlueprintStep) -> BlueprintStep:
    resolved = resolve_drill_video(step.video_slug, step.step_type)
    return step.model_copy(update=resolved)


def enrich_coaching_report(report: CoachingReportSchema) -> CoachingReportSchema:
    enriched_steps = [enrich_step_videos(s) for s in report.blueprint.steps]
    blueprint = report.blueprint.model_copy(update={"steps": enriched_steps})
    return report.model_copy(update={"blueprint": blueprint})
