"""Map diagnoses to drills and prevent OTT / back-to-target defaults."""

from __future__ import annotations

from app.schemas import SwingMode

# Ordered: first match wins. Each tuple is (keywords, slug).
_DIAGNOSIS_DRILL_RULES: dict[SwingMode, list[tuple[tuple[str, ...], str]]] = {
    "full_swing": [
        (
            (
                "heel",
                "heels",
                "heel-heavy",
                "weight back",
                "weight stuck",
                "chair squat",
                "sitting on heels",
                "lunge forward",
                "stance width",
                "too narrow",
                "unstable base",
                "slouch",
                "shoulder slouch",
                "hip hinge",
                "posture",
                "setup",
                "address",
                "stance",
                "feet",
                "balance",
                "ball position",
                "alignment",
            ),
            "setup_posture",
        ),
        (("early extension", "stand up", "standing up", "hip thrust", "lose posture", "posture through"), "wall_contact"),
        (("chair", "spine angle", "stay in posture"), "chair_drill"),
        (("over the top", "over-the-top", " ott", "steep path", "steep downswing", "outside-in", "shoulder spin"), "alignment_stick_shallow"),
        (("shallow", "slot", "drop inside"), "hip_slide_rotation"),
        (("transition", "sequencing", "hips first", "clear hips", "hip rotation"), "hip_slide_rotation"),
        (("sway", "slide", "lateral", "weight transfer", "hang back", "stuck"), "feet_together"),
        (("tempo", "rush", "quick", "snatch", "pause at top"), "slow_motion_reps"),
        (("balance", "centered", "stable base"), "feet_together"),
        (("setup", "address", "ball position", "alignment", "posture", "hinge", "stance"), "setup_posture"),
        (("cast", "lag", "release early", "scoop"), "slow_motion_reps"),
    ],
    "chipping": [
        (("landing", "distance", "towel", "low point"), "chip_landing_towel"),
        (("hinge", "fat", "thin", "chunk", "skull", "flip", "wrist"), "chip_hinge_punch"),
        (("decel", "yips", "steer", "one hand", "lead hand"), "chip_one_hand"),
        (("bump", "run", "low runner", "weight forward"), "chip_bump_run"),
        (("setup", "address", "stance"), "setup_posture"),
    ],
    "putting": [
        (("start line", "gate", "push", "pull", "face"), "putting_gate"),
        (("tempo", "rush", "metronome", "jerky"), "putting_metronome"),
        (("tension", "steer", "feel", "eyes closed"), "putting_eyes_closed"),
        (("distance", "length", "backstroke"), "putting_ruler"),
        (("setup", "address", "eyes", "posture"), "putting_gate"),
    ],
}

_OOT_KEYWORDS = ("over the top", "over-the-top", " ott", "steep path", "steep downswing", "outside-in")
_OOT_SLUGS = frozenset({"back_to_target", "alignment_stick_shallow"})

_STEP_FALLBACK: dict[SwingMode, dict[str, str]] = {
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


def diagnosis_blob(*parts: str | None) -> str:
    return " ".join(p.strip() for p in parts if p and p.strip()).lower()


def primary_diagnosis_blob(
    *,
    foundational_missing_piece: str | None,
    main_fix: str | None,
    root_cause: str | None,
) -> str:
    """Diagnosis text for drill matching — root cause only, not downstream symptoms."""
    return diagnosis_blob(foundational_missing_piece, main_fix, root_cause)


def suggests_ott(text: str) -> bool:
    t = text.lower()
    return any(k in t for k in _OOT_KEYWORDS)


def user_facing_mentions_ott(text: str) -> bool:
    """Broader check for narrative copy — not used for drill slug selection."""
    return suggests_ott(text)


_BACK_TO_TARGET_NAMES = ("back to the target", "back-to-target", "back to target")


def is_back_to_target_drill_name(name: str) -> bool:
    n = name.lower()
    return any(token in n for token in _BACK_TO_TARGET_NAMES)


def audit_report_bias(
    *,
    foundational_missing_piece: str | None,
    main_fix: str | None,
    drill_names: list[str],
    blueprint_slugs: list[str],
) -> list[str]:
    """Return human-readable flags when OTT/back-to-target appear without primary evidence."""
    primary = primary_diagnosis_blob(
        foundational_missing_piece=foundational_missing_piece,
        main_fix=main_fix,
        root_cause=None,
    )
    flags: list[str] = []
    primary_has_ott = suggests_ott(primary)
    if not primary_has_ott:
        for name in drill_names:
            if is_back_to_target_drill_name(name):
                flags.append(f"drill '{name}' is OTT-themed but primary diagnosis is '{foundational_missing_piece}'")
        for slug in blueprint_slugs:
            if slug == "back_to_target":
                flags.append("blueprint used back_to_target slug without OTT in primary diagnosis")
    return flags
def slug_allowed_for_diagnosis(slug: str, primary_diagnosis: str) -> bool:
    if slug in _OOT_SLUGS and not suggests_ott(primary_diagnosis):
        return False
    return True


def pick_drill_slug(
    *,
    diagnosis_text: str,
    step_type: str,
    swing_mode: SwingMode,
    exclude: set[str] | None = None,
) -> str:
    """Pick the best catalog slug for the graded missing piece."""
    exclude = exclude or set()
    text = diagnosis_text.lower()
    rules = _DIAGNOSIS_DRILL_RULES.get(swing_mode, _DIAGNOSIS_DRILL_RULES["full_swing"])

    # Prefer transition/sequencing over OTT when both could match — OTT is a symptom, not always the root.
    if any(kw in text for kw in ("transition", "sequencing", "lower body", "hip lead", "slot")) and not suggests_ott(text):
        for keywords, slug in rules:
            if slug == "hip_slide_rotation" and any(kw in text for kw in keywords):
                if slug not in exclude:
                    return slug

    for keywords, slug in rules:
        if slug in exclude:
            continue
        if not slug_allowed_for_diagnosis(slug, text):
            continue
        if any(kw in text for kw in keywords):
            return slug

    fallbacks = _STEP_FALLBACK.get(swing_mode, _STEP_FALLBACK["full_swing"])
    slug = fallbacks.get(step_type, "generic_feel")
    if slug in exclude or not slug_allowed_for_diagnosis(slug, text):
        for candidate in fallbacks.values():
            if candidate not in exclude and slug_allowed_for_diagnosis(candidate, text):
                return candidate
        return "generic_feel"
    return slug


def critique_menu_for_prompt(swing_mode: SwingMode = "full_swing") -> str:
    if swing_mode == "chipping":
        return """COVERAGE MAP (inspect all, diagnose only what the film supports — never default to full-swing faults):
- Setup: weight forward, ball position, landing spot intent
- Backswing length vs distance needed
- Hinge amount / wrist flip / scoop
- Strike: low point, decel vs accelerate, fat/thin
- Face & path at impact
- Tempo & finish height"""
    if swing_mode == "putting":
        return """COVERAGE MAP (inspect all, diagnose only what the film supports):
- Setup: eyes, posture, grip pressure, aim
- Backstroke path & length
- Tempo & transition smoothness
- Face angle & start line at impact
- Head stability / steering
- Distance control"""
    return """COVERAGE MAP (inspect all, then pick ONE earliest Constraint that the film actually supports — OTT is NOT the default):
1. Setup & launchpad — ball position, hinge, alignment, balance
2. Takeaway — arms-only lift, club off-plane early
3. Sway vs rotation — lateral slide instead of turn
4. Tempo & transition — snatching down, no athletic pause
5. Sequencing — arms firing before hips clear (≠ automatic OTT)
6. Steep path / over-the-top — ONLY if shoulders visibly spin open first on film
7. Early extension — hips thrust toward ball, spine stands up through impact
8. Casting / lag loss — angles released early, scooping
9. Low point / strike — chunk, thin, inconsistent contact
10. Weight transfer — hanging back, stuck on trail side
11. Balance & finish — unstable hold, falling backward
12. Grip / face — only if clearly visible

ANTI-DEFAULT RULES:
- Do NOT label every swing over-the-top. Most amateurs need setup, tempo, or early extension work first.
- Grade setup (heels, stance width, hip hinge) BEFORE blaming downswing path.
- back_to_target video_slug ONLY when #6 is graded Constraint with visible evidence AND setup is sound.
- If 75%+ checkpoints Optimal → maintenance mode; no path critique needed.
- Vary drills across uploads — do not repeat the same drill slug unless the same Constraint persists on film."""
