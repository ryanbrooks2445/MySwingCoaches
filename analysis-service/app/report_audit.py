from __future__ import annotations

import re

from app.schemas import CoachingReportSchema, SwingMode
from app.debug_agent_log import agent_log


class ReportQualityError(ValueError):
    """Raised when a generated report is not safe to show as a completed analysis."""


_GENERIC_MAIN_FIXES = (
    "focus on one athletic feel",
    "feel balanced at address",
    "feel smooth through the ball",
    "own the pattern",
)

_BANNED_USER_FACING_FILLER = (
    "the key is",
    "from start to finish",
    "bottle this feeling",
    "model swing",
    "textbook",
)

_OVERPRAISE_TERMS = (
    "dominate the course",
    "scratch golfer",
    "tour-ready",
    "tour caliber",
    "tour-caliber",
    "elite consistency",
    "perfect",
    "textbook",
    "exceptionally high",
    "wins matches",
    "drops handicaps",
)

_UNSUPPORTED_OUTCOME_TERMS = (
    "scratch golfer",
    "handicap",
    "wins matches",
    "drops handicaps",
    "posting great scores",
)

_PRIMARY_CATEGORY_TERMS: dict[str, tuple[str, ...]] = {
    "setup": (
        "setup",
        "address",
        "posture",
        "heel",
        "stance",
        "hinge",
        "balance",
        "ball position",
        "distance from ball",
        "alignment",
        "grip",
    ),
    "takeaway": ("takeaway", "early wrist", "hand path", "clubface takeaway"),
    "backswing": ("backswing", "top", "lead arm", "trail elbow", "arm structure", "width", "shoulder turn", "hip turn"),
    "transition": ("transition", "sequence", "sequencing", "lower body", "arm drop", "tempo", "shallow"),
    "downswing_path": ("downswing", "swing path", "path", "over-the-top", "outside-in", "inside", "steep", "slot"),
    "clubface": ("clubface", "face", "open face", "closed face", "face-to-path", "face/path"),
    "head": ("head", "head movement", "head stability"),
    "rotation": ("rotation", "turn", "chest", "hips clear", "pivot"),
    "weight_shift": ("weight shift", "pressure shift", "weight transfer", "lead side", "trail side"),
    "impact": ("impact", "shaft lean", "low point", "contact", "early extension", "release"),
}

_FULL_SWING_PHASE_TERMS: dict[str, tuple[str, ...]] = {
    "setup": ("setup", "address", "grip", "posture", "alignment", "ball position", "distance"),
    "takeaway": ("takeaway", "hand path", "early wrist", "clubface takeaway"),
    "backswing": ("backswing", "top", "lead arm", "trail elbow", "shoulder turn", "hip turn", "width"),
    "transition": ("transition", "sequence", "sequencing", "lower body", "arm drop", "tempo"),
    "downswing_path": ("downswing", "swing path", "path", "steep", "shallow", "over-the-top", "slot"),
    "impact": ("impact", "face/path", "shaft lean", "low point", "contact", "weight location"),
    "finish": ("finish", "follow-through", "balance", "extension", "exit path", "rotation finish"),
}

_CHECKPOINT_PHASE_PREFIXES: dict[str, tuple[str, ...]] = {
    "setup": ("setup:", "address:"),
    "takeaway": ("takeaway:",),
    "backswing": ("backswing",),
    "transition": ("transition:",),
    "downswing_path": ("downswing:",),
    "impact": ("impact:",),
    "finish": ("finish:",),
}

_ALLOWED_DUPLICATE_PAIRS = frozenset(
    {
        frozenset({"early_follow_through", "finish"}),
        frozenset({"top", "transition"}),
    }
)

_REQUIRED_OBSERVATION_GROUPS: dict[str, tuple[str, ...]] = {
    "swing path": (
        "swing path",
        "path",
        "plane",
        "steep",
        "shallow",
        "over-the-top",
        "inside",
        "outside-in",
        "across",
        "slot",
        "exit",
        "club works",
        "club travels",
    ),
    "head movement": (
        "head",
        "head movement",
        "head stability",
        "centered",
        "spine",
        "upper body",
    ),
    "arm/hand path": (
        "arm",
        "arms",
        "hand path",
        "hands",
        "lead arm",
        "trail arm",
        "trail elbow",
        "elbow",
        "width",
    ),
    "clubface": (
        "clubface",
        "club face",
        "face-to-path",
        "face/path",
        "face angle",
        "open face",
        "closed face",
        "square",
        "start line",
    ),
    "weight transfer": (
        "weight transfer",
        "weight shift",
        "pressure shift",
        "trail side",
        "lead side",
        "hang back",
        "reverse pivot",
        "load into",
    ),
}


_OBVIOUS_ARM_TERMS = (
    "lead arm",
    "arm bend",
    "bent arm",
    "collapsed",
    "wrap",
    "narrow width",
    "across the chest",
    "elbow",
    "width at the top",
    "arm structure",
)

_OBVIOUS_WEIGHT_TERMS = (
    "weight transfer",
    "weight shift",
    "pressure shift",
    "trail side",
    "hang back",
    "stuck on trail",
    "reverse pivot",
    "load into trail",
    "weight stays",
    "no shift",
)


def _checkpoint_flags_obvious_arm_miss(item) -> bool:
    blob = f"{item.checkpoint} {item.observation}".lower()
    if item.grade == "constraint":
        return any(term in blob for term in _OBVIOUS_ARM_TERMS)
    if item.grade == "compensation":
        strong = ("bend", "bent", "collapsed", "wrap", "across the chest", "narrow width", "sharp")
        return any(term in blob for term in strong)
    return False


def _checkpoint_flags_obvious_weight_miss(item) -> bool:
    if item.grade not in {"constraint", "compensation"}:
        return False
    blob = f"{item.checkpoint} {item.observation}".lower()
    transfer_terms = (
        "weight transfer",
        "weight shift",
        "pressure shift",
        "trail side",
        "hang back",
        "stuck on trail",
        "reverse pivot",
        "no shift",
        "weight stays",
        "weight stay",
        "fails to shift",
        "without shift",
    )
    return any(term in blob for term in transfer_terms)


def _user_facing_covers_weight_transfer(report: CoachingReportSchema) -> bool:
    weight_terms = (
        "weight transfer",
        "weight shift",
        "hang back",
        "trail side",
        "stuck on trail",
        "reverse pivot",
        "shift toward",
        "load into trail",
        "weight stays",
        "no shift",
        "pressure shift",
    )
    return _user_facing_covers_any(report, weight_terms)


def _user_facing_covers_any(report: CoachingReportSchema, terms: tuple[str, ...]) -> bool:
    parts = [
        report.personalized_greeting,
        report.pga_analysis,
        report.main_fix,
        report.next_swing_check,
        " ".join(report.tips_and_feels),
    ]
    for priority in report.priority_fixes:
        parts.extend(
            [
                priority.title,
                priority.issue,
                priority.why_first,
                " ".join(priority.body_feels),
                " ".join(priority.space_feels),
            ]
        )
    letter = report.feel_blueprint
    if letter:
        parts.extend(
            [
                letter.opening_narrative,
                " ".join(f"{s.title} {s.detail}" for s in letter.strengths),
                " ".join(f"{f.title} {f.detail}" for f in letter.flaws),
                " ".join(f"{p.title} {p.detail}" for p in letter.pro_fixes),
            ]
        )
    text = " ".join(part for part in parts if part).lower()
    return any(term in text for term in terms)


def _audit_obvious_visible_misses(report: CoachingReportSchema) -> None:
    """If a checkpoint grades an obvious arm or weight issue, the user must hear about it."""
    for item in report.advanced_details.diagnostic_checkpoints:
        if _checkpoint_flags_obvious_arm_miss(item):
            if not _user_facing_covers_any(report, _OBVIOUS_ARM_TERMS):
                raise ReportQualityError(
                    "Report hid an obvious lead-arm / width issue that was graded on a checkpoint."
                )
        if _checkpoint_flags_obvious_weight_miss(item):
            if not _user_facing_covers_weight_transfer(report):
                raise ReportQualityError(
                    "Report hid an obvious weight-transfer issue that was graded on a checkpoint."
                )


def _blob(report: CoachingReportSchema) -> str:
    parts = [
        report.personalized_greeting,
        report.pga_analysis,
        report.main_fix,
        report.next_swing_check,
        report.advanced_details.root_cause,
        report.advanced_details.foundational_missing_piece,
        report.advanced_details.chain_reaction,
        " ".join(report.tips_and_feels),
        " ".join(report.advanced_details.evidence_metrics),
    ]
    return " ".join(part for part in parts if part).lower()


def _restricted_user_facing_text(report: CoachingReportSchema) -> str:
    """Compact UI fields — excludes coach letter ceilings and deep narrative."""
    return " ".join(
        part
        for part in (
            report.personalized_greeting,
            report.pga_analysis,
            report.main_fix,
            report.next_swing_check,
            " ".join(report.tips_and_feels),
        )
        if part
    ).lower()


def _audit_coach_letter(report: CoachingReportSchema, swing_mode: SwingMode) -> None:
    if swing_mode != "full_swing":
        return

    letter = report.feel_blueprint
    if letter is None:
        raise ReportQualityError("Full-swing report lacked the paid coach letter.")

    if len(letter.opening_narrative.strip()) < 40:
        raise ReportQualityError("Coach letter opening was too thin.")

    if len(letter.strengths) < 2:
        raise ReportQualityError("Coach letter lacked enough visible strengths.")

    if len(letter.flaws) < 2:
        raise ReportQualityError("Coach letter lacked the setup-to-finish missing-piece chain.")

    if len(letter.pro_fixes) < 2:
        raise ReportQualityError("Coach letter lacked enough pro fixes.")

    if len(letter.current_ceiling.strip()) < 30:
        raise ReportQualityError("Coach letter lacked an honest current ceiling.")

    if len(letter.potential_ceiling.strip()) < 30:
        raise ReportQualityError("Coach letter lacked an unlock ceiling.")

    banned = ("fault", "bad habit", "broken", "dysfunction", " fail")
    letter_text = " ".join(
        [
            letter.opening_narrative,
            " ".join(f"{s.title} {s.detail}" for s in letter.strengths),
            " ".join(f"{f.title} {f.detail}" for f in letter.flaws),
            " ".join(f"{p.title} {p.detail}" for p in letter.pro_fixes),
        ]
    ).lower()
    if any(term in letter_text for term in banned):
        raise ReportQualityError("Coach letter used shaming language.")


def _advanced_blob(report: CoachingReportSchema) -> str:
    adv = report.advanced_details
    checkpoint_text = " ".join(
        f"{item.checkpoint} {item.grade} {item.observation}" for item in adv.diagnostic_checkpoints
    )
    return " ".join(
        part
        for part in (
            report.main_fix,
            adv.foundational_missing_piece,
            adv.root_cause,
            adv.secondary_fix,
            adv.chain_reaction,
            " ".join(adv.evidence_metrics),
            checkpoint_text,
        )
        if part
    ).lower()


def _category_for_text(text: str) -> str | None:
    lower = text.lower()
    scores = {
        category: sum(1 for term in terms if term in lower)
        for category, terms in _PRIMARY_CATEGORY_TERMS.items()
    }
    category, score = max(scores.items(), key=lambda item: item[1])
    return category if score > 0 else None


def _primary_category(report: CoachingReportSchema) -> str | None:
    adv = report.advanced_details
    return _category_for_text(
        " ".join(
            [
                adv.foundational_missing_piece,
                adv.root_cause,
                report.main_fix,
            ]
        )
    )


def _mentioned_groups(text: str, groups: dict[str, tuple[str, ...]]) -> set[str]:
    lower = text.lower()
    return {
        group
        for group, terms in groups.items()
        if any(term in lower for term in terms)
    }


def _checkpoint_phase_coverage(report: CoachingReportSchema) -> set[str]:
    covered: set[str] = set()
    for item in report.advanced_details.diagnostic_checkpoints:
        label = item.checkpoint.lower().strip()
        for phase, prefixes in _CHECKPOINT_PHASE_PREFIXES.items():
            if any(label.startswith(prefix) for prefix in prefixes):
                covered.add(phase)
                break
    return covered


def _duplicate_frame_is_blocking(phases: list[str]) -> bool:
    normalized = {phase.lower() for phase in phases if phase}
    if len(normalized) <= 1:
        return False
    if len(normalized) == 2:
        return frozenset(normalized) not in _ALLOWED_DUPLICATE_PAIRS
    return True


def _visible_or_limited_groups(report: CoachingReportSchema) -> set[str]:
    text = _advanced_blob(report)
    return _mentioned_groups(text, _REQUIRED_OBSERVATION_GROUPS)


def _history_repeats_primary(history_summary: str | None, category: str | None) -> bool:
    if not history_summary or not category:
        return False
    history_category = _category_for_text(history_summary)
    return history_category == category


def _setup_evidence_count(report: CoachingReportSchema) -> int:
    setup_evidence_terms = (
        "setup",
        "address",
        "posture",
        "heel",
        "stance",
        "hinge",
        "ball position",
        "distance from ball",
        "alignment",
        "grip",
    )
    text_items = [
        *report.advanced_details.evidence_metrics,
        *[
            f"{item.checkpoint} {item.observation}"
            for item in report.advanced_details.diagnostic_checkpoints
        ],
    ]
    count = 0
    for item in text_items:
        lower = item.lower()
        if any(term in lower for term in setup_evidence_terms):
            count += 1
    return count


def _setup_evidence_metric_count(report: CoachingReportSchema) -> int:
    setup_evidence_terms = (
        "setup",
        "address",
        "heel",
        "stance",
        "hinge",
        "ball position",
        "distance from ball",
        "alignment",
        "grip",
    )
    return sum(
        1
        for item in report.advanced_details.evidence_metrics
        if any(term in item.lower() for term in setup_evidence_terms)
    )


def _has_setup_chain_explanation(report: CoachingReportSchema) -> bool:
    text = " ".join(
        [
            report.advanced_details.chain_reaction,
            report.advanced_details.why_it_caused_the_miss,
            " ".join(report.advanced_details.evidence_metrics),
        ]
    ).lower()
    setup_terms = ("setup", "address", "posture", "heel", "stance", "hinge", "pressure")
    downstream_terms = (
        "hand height",
        "hands",
        "arm",
        "shaft",
        "plane",
        "path",
        "club",
        "sequence",
        "sequencing",
        "transition",
        "turn",
        "rotation",
        "release",
    )
    return any(term in text for term in setup_terms) and sum(
        1 for term in downstream_terms if term in text
    ) >= 2


def _high_score_context(player_context: str | None) -> bool:
    text = (player_context or "").lower()
    if not text:
        return False
    score_matches = re.findall(r"(?:9[- ]?hole score|average score|shoots?|score)[:\s]+(\d{2,3})", text)
    return any(int(score) >= 50 for score in score_matches)


def _phase_entry(phase_map: list[dict] | None, *names: str) -> dict | None:
    if not phase_map:
        return None
    lowered = {name.lower() for name in names}
    for entry in phase_map:
        phase = str(entry.get("phase", "")).lower()
        if phase in lowered:
            return entry
    return None


def _is_limited_preanalyzed_report(report: CoachingReportSchema) -> bool:
    adv = report.advanced_details
    checkpoints = adv.diagnostic_checkpoints or []
    if adv.confidence_score > 0.25 or len(checkpoints) < 5:
        return False

    not_visible_count = sum(1 for item in checkpoints if item.grade == "not_visible")
    if not_visible_count < 3:
        return False

    diagnostic_text = " ".join(
        [
            adv.foundational_missing_piece or "",
            adv.root_cause or "",
            adv.symptom or "",
            adv.why_it_caused_the_miss or "",
            report.next_swing_check or "",
        ]
    ).lower()
    return any(
        phrase in diagnostic_text
        for phrase in (
            "insufficient video",
            "poor video quality",
            "not visible",
            "new video",
            "video data is insufficient",
            "video quality",
        )
    )


def _audit_phase_grounding(
    report: CoachingReportSchema,
    phase_map: list[dict] | None,
) -> None:
    if not phase_map:
        return

    adv = report.advanced_details

    indices: dict[int, list[str]] = {}
    for entry in phase_map:
        idx = entry.get("frame_index")
        if isinstance(idx, int):
            indices.setdefault(idx, []).append(str(entry.get("phase", "")))

    high_conf_dupes = False
    blocking_collision: dict | None = None
    for idx, phases in indices.items():
        if len(phases) <= 1:
            continue
        blocking = _duplicate_frame_is_blocking(phases)
        confidences = [
            float(entry.get("confidence", 0))
            for entry in phase_map
            if entry.get("frame_index") == idx
        ]
        max_conf = max(confidences) if confidences else 0.0
        # region agent log
        agent_log(
            hypothesis_id="H3",
            location="report_audit.py:duplicate_check",
            message="duplicate frame candidate",
            data={
                "frame_index": idx,
                "phases": phases,
                "blocking": blocking,
                "max_confidence": max_conf,
                "confidences": confidences,
            },
        )
        # endregion
        if not blocking:
            continue
        if confidences and max_conf >= 0.5:
            high_conf_dupes = True
            blocking_collision = {
                "frame_index": idx,
                "phases": phases,
                "max_confidence": max_conf,
            }
            break
    if high_conf_dupes:
        # region agent log
        agent_log(
            hypothesis_id="H4",
            location="report_audit.py:duplicate_fail",
            message="raising duplicate frame audit error",
            data={"blocking_collision": blocking_collision},
        )
        # endregion
        raise ReportQualityError("Multiple high-confidence phases mapped to the same frame.")

    finish_entry = _phase_entry(phase_map, "finish", "early_follow_through")
    finish_conf = float(finish_entry.get("confidence", 0)) if finish_entry else 0.0
    finish_visible = bool(finish_entry.get("person_visible")) if finish_entry else False
    if finish_conf < 0.4 or not finish_visible:
        finish_praise = ("optimal", "balanced finish", "full finish", "excellent balance")
        for item in adv.diagnostic_checkpoints:
            label = f"{item.checkpoint} {item.observation}".lower()
            if "finish" in label and item.grade == "optimal" and any(term in label for term in finish_praise):
                raise ReportQualityError("Report praised finish without visible finish phase evidence.")

    impact_entry = _phase_entry(phase_map, "impact", "impact_window_estimate")
    if impact_entry:
        impact_conf = float(impact_entry.get("confidence", 0))
        impact_phase = str(impact_entry.get("phase", ""))
        if impact_conf < 0.5 or impact_phase == "impact_window_estimate":
            user_text = " ".join(
                [
                    report.pga_analysis,
                    report.main_fix,
                    report.next_swing_check,
                    " ".join(report.tips_and_feels),
                ]
            ).lower()
            limitation_terms = ("limited", "not clearly visible", "contact window", "impact window")
            if not any(term in user_text for term in limitation_terms):
                raise ReportQualityError("Low-confidence impact requires explicit limitation language.")

    for entry in phase_map:
        if not entry.get("person_visible") and float(entry.get("confidence", 0)) < 0.4:
            phase_name = str(entry.get("phase", "")).replace("_", " ")
            for item in adv.diagnostic_checkpoints:
                if phase_name.split()[0] in item.checkpoint.lower() and item.grade != "not_visible":
                    raise ReportQualityError(
                        f"Report graded {item.checkpoint} without visible person in phase frame."
                    )

    primary = _primary_category(report)
    if primary == "setup":
        address_entry = _phase_entry(phase_map, "address", "setup")
        address_conf = float(address_entry.get("confidence", 0)) if address_entry else 0.0
        if address_conf < 0.6:
            raise ReportQualityError("Posture/setup primary chosen without confident address frame.")


def audit_report_quality(
    report: CoachingReportSchema,
    *,
    swing_mode: SwingMode,
    player_context: str | None = None,
    history_summary: str | None = None,
    phase_map: list[dict] | None = None,
) -> None:
    adv = report.advanced_details
    text = _blob(report)

    if _is_limited_preanalyzed_report(report):
        return

    if adv.confidence_score <= 0 or "non-golf video uploaded" in text:
        raise ReportQualityError("Uploaded video could not be verified as a usable golf swing.")

    if any(term in report.main_fix.lower() for term in _GENERIC_MAIN_FIXES):
        raise ReportQualityError("Generated report used a generic main fix.")

    user_facing = " ".join(
        [
            report.personalized_greeting,
            report.pga_analysis,
            report.main_fix,
            report.next_swing_check,
            " ".join(report.tips_and_feels),
        ]
    ).lower()
    if any(term in user_facing for term in _BANNED_USER_FACING_FILLER):
        raise ReportQualityError("Generated report used generic filler language.")

    if any(term in text for term in _UNSUPPORTED_OUTCOME_TERMS):
        restricted = _restricted_user_facing_text(report)
        if any(term in restricted for term in _UNSUPPORTED_OUTCOME_TERMS):
            raise ReportQualityError("Generated report made an unsupported scoring or handicap prediction.")

    if _high_score_context(player_context) and any(term in _restricted_user_facing_text(report) for term in _OVERPRAISE_TERMS):
        raise ReportQualityError("Generated report overpraised a high-score golfer.")

    if adv.report_mode == "maintenance":
        if _high_score_context(player_context):
            raise ReportQualityError("Generated maintenance report for high-score golfer context.")
        if len(adv.diagnostic_checkpoints) < 4:
            raise ReportQualityError("Maintenance report lacked enough checkpoint evidence.")
        _audit_phase_grounding(report, phase_map)
        _audit_obvious_visible_misses(report)
        _audit_coach_letter(report, swing_mode)
        return

    min_checkpoints = 3 if swing_mode == "full_swing" else 2
    if len(adv.diagnostic_checkpoints) < min_checkpoints:
        raise ReportQualityError("Development report lacked required checkpoint evidence.")

    if len([item for item in adv.evidence_metrics if item.strip()]) < 2:
        raise ReportQualityError("Development report lacked required visible evidence.")

    if len((adv.root_cause or "").strip()) < 8:
        raise ReportQualityError("Development report lacked a clear root cause.")

    if len((adv.foundational_missing_piece or "").strip()) < 8:
        raise ReportQualityError("Development report lacked a foundational missing piece.")

    if len((adv.chain_reaction or "").strip()) < 20:
        raise ReportQualityError("Development report lacked a cause-and-effect chain.")

    if swing_mode == "full_swing" and len((adv.secondary_fix or "").strip()) < 8:
        raise ReportQualityError("Full-swing report lacked a secondary flaw.")

    secondary = (adv.secondary_fix or "").strip().lower()
    primary_text = (adv.foundational_missing_piece or report.main_fix or "").strip().lower()
    if secondary and primary_text and secondary == primary_text:
        raise ReportQualityError("Secondary fix duplicated the primary missing piece.")

    if swing_mode != "full_swing":
        return

    coverage_text = _advanced_blob(report)
    checkpoint_covered = _checkpoint_phase_coverage(report)
    if len(adv.diagnostic_checkpoints) >= 7:
        covered_phases = checkpoint_covered
    else:
        covered_phases = checkpoint_covered | _mentioned_groups(
            coverage_text, _FULL_SWING_PHASE_TERMS
        )
    required_phases = {"setup", "takeaway", "backswing", "transition", "downswing_path", "impact", "finish"}
    if len(adv.diagnostic_checkpoints) < 7 or not required_phases.issubset(covered_phases):
        raise ReportQualityError("Full-swing report did not cover setup through finish checkpoints.")

    observation_groups = _visible_or_limited_groups(report)
    if "swing path" not in observation_groups or len(observation_groups) < 2:
        raise ReportQualityError("Full-swing report lacked required path/head/arm/clubface observations.")

    primary = _primary_category(report)
    if primary == "setup":
        non_setup_groups = observation_groups - {"setup"}
        if (
            _setup_evidence_count(report) < 2
            or not _has_setup_chain_explanation(report)
            or len(non_setup_groups) < 2
        ):
            raise ReportQualityError("Posture/setup was chosen without decisive multi-category evidence.")

    if _history_repeats_primary(history_summary, primary):
        if primary == "setup" and _setup_evidence_count(report) < 4:
            raise ReportQualityError("Repeated setup/posture diagnosis without strong fresh evidence.")
        if primary and primary != "setup" and len(adv.evidence_metrics) < 4:
            raise ReportQualityError("Repeated main diagnosis without enough fresh evidence.")

    _audit_phase_grounding(report, phase_map)
    _audit_obvious_visible_misses(report)
    _audit_coach_letter(report, swing_mode)
