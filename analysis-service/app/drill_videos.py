from __future__ import annotations

from app.schemas import BlueprintStep, CoachingReportSchema, SwingMode

# Curated drill library — Gemini picks a slug; we resolve to a stable embed URL.

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
        "for": "Over-the-top, shoulders spinning open too early",
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
        "for": "Steep downswing, over-the-top path",
        "modes": ["full_swing"],
    },
    "feet_together": {
        "title": "Feet-together balance swings",
        "embed_url": "https://www.youtube.com/embed/fOpifmb8KZo",
        "for": "Balance, tempo, centered rotation",
        "modes": ["full_swing", "chipping"],
    },
    "slow_motion_reps": {
        "title": "Slow-motion rehearsal swings",
        "embed_url": "https://www.youtube.com/embed/iwbHIX3IlhA",
        "for": "Building a new feel at half speed",
        "modes": ["full_swing", "chipping", "putting"],
    },
    "chip_landing_towel": {
        "title": "Towel landing zone — chip control",
        "embed_url": "https://www.youtube.com/embed/fOpifmb8KZo",
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
        "embed_url": "https://www.youtube.com/embed/zEtWHtQR0T0",
        "for": "Yips, decel, steering with the trail hand",
        "modes": ["chipping"],
    },
    "putting_gate": {
        "title": "Gate drill — start line",
        "embed_url": "https://www.youtube.com/embed/iwbHIX3IlhA",
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
    "generic_feel": {
        "title": "Range feel rehearsal",
        "embed_url": "https://www.youtube.com/embed/fOpifmb8KZo",
        "for": "General kinesthetic practice",
        "modes": ["full_swing", "chipping", "putting"],
    },
}

DEFAULT_SLUG_BY_MODE: dict[SwingMode, dict[str, str]] = {
    "full_swing": {
        "setup": "setup_posture",
        "visual_cue": "back_to_target",
        "constraint_drill": "wall_contact",
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
    lines = [f"Available video_slug values for {swing_mode} (pick best match per step):"]
    for slug, meta in DRILL_CATALOG.items():
        if slug == "generic_feel":
            continue
        if swing_mode not in _slug_modes(slug):
            continue
        lines.append(f"  - {slug}: {meta['for']}")
    lines.append("  - generic_feel: fallback when nothing else fits")
    return "\n".join(lines)


def resolve_drill_video(slug: str | None, step_type: str, swing_mode: SwingMode = "full_swing") -> dict[str, str]:
    defaults = DEFAULT_SLUG_BY_MODE.get(swing_mode, DEFAULT_SLUG_BY_MODE["full_swing"])
    key = slug if slug and slug in DRILL_CATALOG else defaults.get(step_type, "generic_feel")
    if key not in DRILL_CATALOG or swing_mode not in _slug_modes(key):
        key = defaults.get(step_type, "generic_feel")
    entry = DRILL_CATALOG[key]
    return {
        "video_slug": key,
        "video_url": str(entry["embed_url"]),
        "video_title": str(entry["title"]),
    }


def enrich_step_videos(step: BlueprintStep, swing_mode: SwingMode = "full_swing") -> BlueprintStep:
    resolved = resolve_drill_video(step.video_slug, step.step_type, swing_mode)
    return step.model_copy(update=resolved)


def enrich_coaching_report(
    report: CoachingReportSchema,
    swing_mode: SwingMode = "full_swing",
) -> CoachingReportSchema:
    enriched_steps = [enrich_step_videos(s, swing_mode) for s in report.blueprint.steps]
    blueprint = report.blueprint.model_copy(update={"steps": enriched_steps})
    return report.model_copy(update={"blueprint": blueprint})
