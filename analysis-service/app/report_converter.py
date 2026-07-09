"""Convert slim Gemini JSON output to full CoachingReportSchema."""

from __future__ import annotations

import json
import re

from app.gemini_report_schema import GeminiReportOut
from app.trace_log import log_trace
from app.schemas import (
    AccountabilityPlan,
    AdvancedDetails,
    AnalysisBullet,
    BlueprintStep,
    CategoryRating,
    CoachVerdict,
    CoachingReportSchema,
    DiagnosticCheckpointGrade,
    DrillSummary,
    FeelBlueprintDiagnostic,
    KinestheticBlueprint,
    MilestoneBlock,
    PrioritizedFeelFix,
    ProFix,
)

_VALID_GRADES = frozenset({"optimal", "compensation", "constraint", "not_visible"})
_OBSERVER_ONLY_LABEL = "Observation-only output"
_GRADE_MAP = {
    "Optimal": "optimal",
    "Compensating": "compensation",
    "Constraint": "constraint",
    "Not Visible": "not_visible",
}


def _cap_words(text: str, max_words: int) -> str:
    cleaned = re.sub(r"\s+", " ", (text or "").strip())
    if not cleaned:
        return ""
    words = cleaned.split(" ")
    if len(words) <= max_words:
        return cleaned
    sentences = re.split(r"(?<=[.!?])\s+", cleaned)
    if sentences and 0 < len(sentences[0].split()) <= max_words + 8:
        return sentences[0].strip()
    capped = " ".join(words[:max_words]).rstrip(" ,;:")
    dangling = {
        "a",
        "an",
        "and",
        "at",
        "by",
        "for",
        "from",
        "in",
        "not",
        "of",
        "on",
        "or",
        "that",
        "the",
        "this",
        "to",
        "until",
        "with",
        "your",
    }
    capped_words = capped.split()
    while capped_words and capped_words[-1].lower().strip(".,;:") in dangling:
        capped_words.pop()
    return " ".join(capped_words).rstrip(" ,;:") + "."


def _polish_cue(text: str, max_words: int = 42) -> str:
    cleaned = re.sub(r"\s+", " ", (text or "").strip())
    if not cleaned:
        return ""
    if len(cleaned.split()) <= max_words:
        return cleaned
    sentences = re.split(r"(?<=[.!?])\s+", cleaned)
    kept: list[str] = []
    count = 0
    for sentence in sentences:
        words = sentence.split()
        if not words:
            continue
        if kept and count + len(words) > max_words:
            break
        if not kept and len(words) > max_words:
            return _cap_words(sentence, max_words)
        kept.append(sentence)
        count += len(words)
    return " ".join(kept).strip() or _cap_words(cleaned, max_words)


def _cap_section(text: str, max_words: int) -> str:
    cleaned = re.sub(r"\s+", " ", (text or "").strip())
    if not cleaned:
        return ""
    if len(cleaned.split()) <= max_words:
        return cleaned

    pieces = re.split(r"(?<=[.!?])\s+", cleaned)
    kept: list[str] = []
    count = 0
    for piece in pieces:
        words = piece.split()
        if not words:
            continue
        if kept and count + len(words) > max_words:
            break
        kept.append(piece)
        count += len(words)
    if kept:
        return " ".join(kept).strip()
    return _cap_words(cleaned, max_words)


def _cap_drill(drill: DrillSummary) -> DrillSummary:
    return DrillSummary(
        name=_cap_words(drill.name, 10) or drill.name,
        why_it_helps=_cap_words(drill.why_it_helps, 45),
        how_to_do_it=_cap_words(drill.how_to_do_it, 70),
    )


def _repair_drill(drill: DrillSummary) -> DrillSummary:
    capped = _cap_drill(drill)
    blob = f"{capped.name} {capped.why_it_helps} {capped.how_to_do_it}".lower()
    how = _polish_cue(capped.how_to_do_it, 70)
    too_short = len(how.split()) < 9
    incomplete_setup = how.lower().endswith(("across your hips.", "across your chest.", "on the ground."))

    if too_short or incomplete_setup:
        if any(term in blob for term in ("setup", "posture", "hinge", "knee", "hips", "address")):
            how = (
                "Hold a club across your hips, soften your knees, hinge until hamstrings engage, "
                "then let arms hang for 10 clean reps."
            )
        elif any(term in blob for term in ("path", "plane", "shallow", "slot", "steep", "outside")):
            how = (
                "Make 15 half-speed pump reps, pause when the club slots behind you, "
                "then swing through and hold the finish."
            )
        elif any(term in blob for term in ("tempo", "transition", "sequence", "lower body")):
            how = (
                "Make 15 slow reps: pressure shifts first, arms fall second, chest turns last. "
                "Only count unhurried reps."
            )
        elif any(term in blob for term in ("head", "dip", "height", "stable")):
            how = (
                "Make 10 slow mirror reps keeping head height steady, then hit 10 half-speed balls "
                "without dipping."
            )
        else:
            how = "Make 15 slow rehearsals, then hit 10 half-speed balls and only count reps that match the feel."

    return DrillSummary(
        name=capped.name,
        why_it_helps=capped.why_it_helps,
        how_to_do_it=how,
    )


def _parse_category_rating(raw: str) -> CategoryRating | None:
    text = (raw or "").strip()
    if not text:
        return None
    match = re.match(
        r"^(?P<label>.+?)[:]\s*(?P<rating>\d+(?:\.\d+)?(?:\s*/\s*10|\s*out of\s*10)?)$",
        text,
        flags=re.IGNORECASE,
    )
    if not match:
        return None
    label = match.group("label").strip()
    rating = match.group("rating").strip()
    if not re.search(r"/\s*10|out of\s*10", rating, flags=re.IGNORECASE):
        rating = f"{rating}/10"
    return CategoryRating(label=label, rating=rating.replace(" ", ""))


def _normalize_overall_rating(raw: str) -> str:
    text = (raw or "").strip()
    if not text:
        return ""
    if re.search(r"/\s*10|out of\s*10", text, flags=re.IGNORECASE):
        return text
    if re.fullmatch(r"\d+(?:\.\d+)?", text):
        return f"{text}/10 overall"
    return text


def _extract_labeled_field(text: str, label: str) -> str:
    pattern = re.compile(
        rf"{re.escape(label)}\s*:?\s*(.+?)(?=(?:The big positive|Main issue|Best fix|Power:|Tempo:|Sequence|Overall|I'd rate|\Z))",
        re.IGNORECASE | re.DOTALL,
    )
    match = pattern.search(text or "")
    if not match:
        return ""
    return re.sub(r"\s+", " ", match.group(1)).strip(" .")


def _extract_category_ratings_from_text(text: str) -> list[CategoryRating]:
    ratings: list[CategoryRating] = []
    for line in re.split(r"[\n.]+", text or ""):
        parsed = _parse_category_rating(line.strip())
        if parsed:
            ratings.append(parsed)
    return ratings[:6]


def _parse_rating_number(rating: str) -> float | None:
    match = re.search(r"(\d+(?:\.\d+)?)", rating or "")
    if not match:
        return None
    return float(match.group(1))


def _format_overall_rating(value: float) -> str:
    clamped = max(1.0, min(9.5, value))
    rounded = round(clamped * 2) / 2
    if rounded == int(rounded):
        return f"{int(rounded)}/10 overall"
    return f"{rounded:.1f}/10 overall"


def _checkpoint_issue_score(checkpoints: list[DiagnosticCheckpointGrade]) -> float:
    score = 0.0
    for item in checkpoints:
        if item.grade == "constraint":
            score += 1.0
        elif item.grade == "compensation":
            score += 0.45
    return score


def _max_rating_for_evidence(
    *,
    issue_score: float,
    flaw_count: int,
    report_mode: str,
) -> float:
    if report_mode == "maintenance":
        return 8.5
    combined = issue_score + max(0, flaw_count - 2) * 0.35
    if combined >= 5.5:
        return 4.5
    if combined >= 4.5:
        return 5.0
    if combined >= 3.5:
        return 5.5
    if combined >= 2.5:
        return 6.0
    if combined >= 1.5:
        return 6.5
    if combined >= 0.75:
        return 7.0
    if combined >= 0.25:
        return 7.5
    return 8.5


def _calibrate_coach_verdict(
    verdict: CoachVerdict,
    *,
    checkpoints: list[DiagnosticCheckpointGrade],
    flaw_count: int,
    report_mode: str,
) -> CoachVerdict:
    raw = _parse_rating_number(verdict.overall_rating)
    if raw is None:
        return verdict

    issue_score = _checkpoint_issue_score(checkpoints)
    max_rating = _max_rating_for_evidence(
        issue_score=issue_score,
        flaw_count=flaw_count,
        report_mode=report_mode,
    )

    category_values = [
        value
        for item in verdict.category_ratings
        if (value := _parse_rating_number(item.rating)) is not None
    ]
    if category_values:
        max_rating = min(max_rating, (sum(category_values) / len(category_values)) + 0.5)

    calibrated = min(raw, max_rating)
    if calibrated >= raw - 0.01:
        return verdict

    return verdict.model_copy(update={"overall_rating": _format_overall_rating(calibrated)})


def _rewrite_verdict_rating_in_analysis(pga_analysis: str, new_rating: str) -> str:
    if not pga_analysis.strip():
        return pga_analysis
    updated = re.sub(
        r"(I'd rate this swing|I would rate this swing)\s*[^.\n]+",
        f"I'd rate this swing {new_rating.rstrip('.')}.",
        pga_analysis,
        count=1,
        flags=re.IGNORECASE,
    )
    return updated


def apply_rating_calibration(report: CoachingReportSchema) -> CoachingReportSchema:
    if not report.coach_verdict or not report.coach_verdict.overall_rating.strip():
        return report

    flaw_count = len(report.feel_blueprint.flaws) if report.feel_blueprint else 0
    if flaw_count == 0 and report.advanced_details.report_mode == "development":
        flaw_count = 2

    calibrated_verdict = _calibrate_coach_verdict(
        report.coach_verdict,
        checkpoints=report.advanced_details.diagnostic_checkpoints,
        flaw_count=flaw_count,
        report_mode=report.advanced_details.report_mode or "development",
    )
    if calibrated_verdict.overall_rating == report.coach_verdict.overall_rating:
        return report

    return report.model_copy(
        update={
            "coach_verdict": calibrated_verdict,
            "pga_analysis": _rewrite_verdict_rating_in_analysis(
                report.pga_analysis,
                calibrated_verdict.overall_rating,
            ),
        }
    )


def _build_coach_verdict(
    out: GeminiReportOut,
    *,
    strengths: list[AnalysisBullet],
    flaws: list[AnalysisBullet],
    fixes: list[ProFix],
    analysis_text: str,
) -> CoachVerdict | None:
    primary = flaws[0] if flaws else None
    primary_fix = fixes[0] if fixes else None
    overall = _normalize_overall_rating(out.rating)
    if not overall:
        match = re.search(
            r"(?:I'd rate this swing|I would rate this swing|Overall:?)\s*([^.\n]+)",
            analysis_text,
            flags=re.IGNORECASE,
        )
        if match:
            overall = _normalize_overall_rating(match.group(1).strip())

    biggest_positive = strengths[0].detail if strengths else _extract_labeled_field(analysis_text, "The big positive")
    main_issue = (
        primary.detail
        if primary
        else _extract_labeled_field(analysis_text, "Main issue") or out.missing or out.root
    )
    best_fix = (
        primary_fix.detail
        if primary_fix
        else _extract_labeled_field(analysis_text, "Best fix") or out.main_fix
    )

    categories = [
        parsed
        for raw in out.categories
        if (parsed := _parse_category_rating(raw)) is not None
    ]
    if not categories:
        categories = _extract_category_ratings_from_text(analysis_text)

    if not any((overall, biggest_positive, main_issue, best_fix, categories)):
        return None

    verdict = CoachVerdict(
        overall_rating=overall,
        biggest_positive=biggest_positive,
        main_issue=main_issue,
        best_fix=best_fix,
        category_ratings=categories,
    )
    return _calibrate_coach_verdict(
        verdict,
        checkpoints=[_parse_checkpoint(s) for s in out.checkpoints if s.strip()],
        flaw_count=len(flaws),
        report_mode=out.mode if out.mode in ("development", "maintenance") else "development",
    )


def coach_verdict_from_analysis(
    analysis_text: str,
    *,
    fallback_main_fix: str = "",
    fallback_issue: str = "",
    existing: CoachVerdict | None = None,
) -> CoachVerdict | None:
    quick_section = ""
    match = re.search(
        r"Quick coach verdict\s*(.*?)(?=\n\s*Full coach-style analysis|\Z)",
        analysis_text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if match:
        quick_section = match.group(1)
    search_text = quick_section or analysis_text

    overall = ""
    rating_match = re.search(
        r"(?:I'd rate this swing|I would rate this swing)\s*([^.\n]+)",
        search_text,
        flags=re.IGNORECASE,
    )
    if rating_match:
        overall = _normalize_overall_rating(rating_match.group(1).strip())

    biggest_positive = _extract_labeled_field(search_text, "The big positive")
    main_issue = _extract_labeled_field(search_text, "Main issue") or fallback_issue
    best_fix = _extract_labeled_field(search_text, "Best fix") or fallback_main_fix
    categories = _extract_category_ratings_from_text(search_text)

    if existing:
        overall = overall or existing.overall_rating
        biggest_positive = biggest_positive or existing.biggest_positive
        main_issue = main_issue or existing.main_issue
        best_fix = best_fix or existing.best_fix
        categories = categories or existing.category_ratings

    if not any((overall, biggest_positive, main_issue, best_fix, categories)):
        return existing

    return CoachVerdict(
        overall_rating=overall,
        biggest_positive=biggest_positive,
        main_issue=main_issue,
        best_fix=best_fix,
        category_ratings=categories,
    )


def _format_verdict_text(verdict: CoachVerdict) -> str:
    parts: list[str] = []
    if verdict.overall_rating:
        parts.append(f"I'd rate this swing {verdict.overall_rating}.")
    if verdict.biggest_positive:
        parts.append(f"The big positive: {verdict.biggest_positive}")
    if verdict.main_issue:
        parts.append(f"Main issue: {verdict.main_issue}")
    if verdict.best_fix:
        parts.append(f"Best fix: {verdict.best_fix}")
    for item in verdict.category_ratings:
        parts.append(f"{item.label}: {item.rating}")
    return " ".join(parts)


def _shorten_analysis(text: str) -> str:
    """Normalize whitespace while preserving the model's user-facing coaching detail."""
    cleaned = (text or "").strip()
    if not cleaned:
        return ""
    return re.sub(r"\n{3,}", "\n\n", cleaned)


def _compact_legacy_analysis(text: str) -> str:
    """Legacy compactor kept for fallback-only summaries."""
    cleaned = (text or "").strip()
    if not cleaned:
        return ""

    lines = [line.strip() for line in cleaned.splitlines()]
    output: list[str] = []
    current_title = ""
    current_body: list[str] = []
    saw_title = False

    known_titles = {
        "what's working",
        "setup to finish",
        "the missing piece",
        "what changes when you unlock it",
        "what to keep doing",
        "your ceiling at this level",
    }

    def flush() -> None:
        nonlocal current_body
        body = " ".join(part for part in current_body if part)
        if current_title:
            output.append(current_title)
            if body:
                output.append(_cap_section(body, 55))
        elif body:
            output.append(_cap_section(body, 55))
        current_body = []

    for line in lines:
        if not line:
            continue
        if line.lower() in known_titles:
            flush()
            current_title = line
            saw_title = True
        else:
            current_body.append(line)
    flush()

    if not saw_title:
        return _cap_words(cleaned, 120)

    return "\n\n".join(part for part in output if part).strip()


def _analysis_has_depth(text: str) -> bool:
    cleaned = re.sub(r"\s+", " ", (text or "").strip())
    if len(cleaned.split()) >= 180:
        return True
    section_hits = sum(
        1
        for title in (
            "main swing fault",
            "secondary swing fault",
            "setup/grip notes",
            "swing path notes",
            "head movement notes",
            "arm/hand structure",
            "impact-window notes",
            "practice plan",
            "confidence/visibility limitations",
        )
        if title in text.lower()
    )
    return section_hits >= 4


def _extract_section(text: str, title: str) -> str:
    pattern = re.compile(
        rf"{re.escape(title)}\s*(.*?)(?=\n\s*(?:What's working|Setup to finish|The missing piece|What changes when you unlock it|What to keep doing|Your ceiling at this level)\s*\n|\Z)",
        re.IGNORECASE | re.DOTALL,
    )
    match = pattern.search(text or "")
    if not match:
        return ""
    return re.sub(r"\s+", " ", match.group(1)).strip()


def _specific_setup_tips(text: str) -> list[str]:
    lower = text.lower()
    if not any(token in lower for token in ("setup", "heel", "posture", "hinge", "rounded", "balance")):
        return []
    tips = [
        "Feel pressure under your laces, not your heels.",
        "Hinge from your hips instead of sitting down.",
        "Keep your chest taller before the takeaway.",
    ]
    return tips


def _specific_setup_drill() -> DrillSummary:
    return DrillSummary(
        name="Athletic Setup Reps",
        why_it_helps="Builds the posture and balance before the swing starts.",
        how_to_do_it="Rehearse 10 setups, then hit 15 half-speed balls with that same stance.",
    )


def _parse_checkpoint(raw: str) -> DiagnosticCheckpointGrade:
    text = (raw or "").strip()
    parts = [p.strip() for p in text.split("|", 2)]
    checkpoint = parts[0] if parts else text
    grade = parts[1].lower() if len(parts) > 1 else "not_visible"
    observation = parts[2] if len(parts) > 2 else ""

    if len(parts) == 1:
        match = re.match(
            r"^(?P<checkpoint>.+?)(?:\s*[:\-]\s*)(?P<grade>optimal|compensation|constraint|not_visible)\b(?:\s*[:\-]\s*(?P<observation>.*))?$",
            text,
            flags=re.IGNORECASE,
        )
        if match:
            checkpoint = match.group("checkpoint").strip()
            grade = match.group("grade").lower()
            observation = (match.group("observation") or "").strip()

    if grade not in _VALID_GRADES:
        grade = "not_visible"
    return DiagnosticCheckpointGrade(
        checkpoint=checkpoint or "Checkpoint",
        grade=grade,  # type: ignore[arg-type]
        observation=observation,
    )


def _is_visible_evidence_line(line: str) -> bool:
    text = (line or "").strip()
    if not text:
        return False
    lower = text.lower()
    if lower.endswith("not visible") or lower.endswith(": not visible"):
        return False
    if re.fullmatch(r"[\w\s]+:\s*not visible\.?", lower):
        return False
    if "| not visible" in lower or "|not visible" in lower:
        return False
    return True


def _filter_visible_checkpoints(
    checkpoints: list[DiagnosticCheckpointGrade],
) -> list[DiagnosticCheckpointGrade]:
    visible: list[DiagnosticCheckpointGrade] = []
    for item in checkpoints:
        if item.grade == "not_visible":
            continue
        observation = (item.observation or "").strip()
        checkpoint = (item.checkpoint or "").strip()
        if not observation and not checkpoint:
            continue
        if observation.lower() in {"not visible", "n/a"}:
            continue
        visible.append(item)
    return visible


def _filter_visible_evidence(lines: list[str]) -> list[str]:
    return [line.strip() for line in lines if _is_visible_evidence_line(line)]


def filter_phase_map(phase_map: list[dict] | None) -> list[dict]:
    if not phase_map:
        return []
    visible: list[dict] = []
    for item in phase_map:
        if item.get("person_visible") is False:
            continue
        confidence = float(item.get("confidence") or 0)
        if confidence < 0.35:
            continue
        visible.append(item)
    return visible


def _clamp_confidence(value: float) -> float:
    if value != value:  # NaN
        return 0.75
    return max(0.0, min(1.0, value))


def _parse_bullet_pipe(raw: str) -> AnalysisBullet | None:
    text = (raw or "").strip()
    if not text:
        return None
    parts = [part.strip() for part in text.split("|", 1)]
    if len(parts) >= 2 and parts[0] and parts[1]:
        return AnalysisBullet(title=parts[0], detail=parts[1])
    if parts[0]:
        return AnalysisBullet(title=parts[0], detail=parts[0])
    return None


def _parse_pro_fix_pipe(raw: str) -> ProFix | None:
    bullet = _parse_bullet_pipe(raw)
    if bullet:
        return ProFix(title=bullet.title, detail=bullet.detail)
    return None


_PHASE_RANK_ORDER = {
    "setup": 1,
    "address": 1,
    "takeaway": 2,
    "backswing": 3,
    "top": 3,
    "transition": 4,
    "downswing": 5,
    "impact": 6,
    "finish": 7,
}


def _split_compound_feels(raw: str) -> list[str]:
    text = (raw or "").strip()
    if not text:
        return []
    if ";;" in text:
        return [part.strip() for part in text.split(";;") if part.strip()]
    if ";" in text:
        return [part.strip() for part in text.split(";") if part.strip()]
    return [text]


def _parse_priority_pipe(raw: str) -> PrioritizedFeelFix | None:
    text = (raw or "").strip()
    if not text:
        return None
    parts = [part.strip() for part in text.split("|")]
    if len(parts) < 5:
        return None
    try:
        rank = int(parts[0])
    except ValueError:
        rank = 1
    phase = parts[1]
    title = parts[2]
    issue = parts[3]
    why_first = parts[4]
    body_feels = _split_compound_feels(parts[5]) if len(parts) > 5 else []
    space_feels = _split_compound_feels(parts[6]) if len(parts) > 6 else []
    drill: DrillSummary | None = None
    if len(parts) >= 10 and any(parts[7:10]):
        drill = DrillSummary(
            name=parts[7],
            why_it_helps=parts[8],
            how_to_do_it=parts[9],
        )
    if not body_feels:
        body_feels = [why_first]
    if not space_feels:
        space_feels = [issue]
    return PrioritizedFeelFix(
        rank=max(1, min(5, rank)),
        phase=phase,
        title=title,
        issue=issue,
        why_first=why_first,
        body_feels=body_feels[:3],
        space_feels=space_feels[:3],
        drill=drill if drill and drill.name.strip() else None,
    )


def _infer_phase_label(text: str) -> str:
    lowered = (text or "").strip().lower()
    for key, label in (
        ("setup", "Setup"),
        ("address", "Setup"),
        ("takeaway", "Takeaway"),
        ("backswing", "Backswing"),
        ("transition", "Transition"),
        ("downswing", "Downswing"),
        ("impact", "Impact"),
        ("finish", "Finish"),
    ):
        if key in lowered:
            return label
    return "Swing"


def _checkpoint_phase_rank(checkpoint: DiagnosticCheckpointGrade) -> int:
    label = (checkpoint.checkpoint or "").strip().lower()
    for key, rank in _PHASE_RANK_ORDER.items():
        if label.startswith(key):
            return rank
    return 99


def _fallback_priority_fixes(
    out: GeminiReportOut,
    drills: list[DrillSummary],
) -> list[PrioritizedFeelFix]:
    priorities: list[PrioritizedFeelFix] = []

    flaws = [
        bullet
        for raw in (out.flaw1, out.flaw2, out.flaw3)
        if (bullet := _parse_bullet_pipe(raw)) is not None
    ]
    fixes = [
        fix
        for raw in (out.fix1, out.fix2, out.fix3)
        if (fix := _parse_pro_fix_pipe(raw)) is not None
    ]

    for index, flaw in enumerate(flaws[:5]):
        fix = fixes[index] if index < len(fixes) else None
        drill = drills[index] if index < len(drills) else None
        body_feels = []
        space_feels = []
        if index == 0 and out.body_cue.strip():
            body_feels.append(_polish_cue(out.body_cue))
        if index == 0 and out.space_cue.strip():
            space_feels.append(_polish_cue(out.space_cue))
        if fix:
            body_feels.append(f"{fix.title}: {fix.detail}")
        for tip in out.tips:
            polished = _polish_cue(tip)
            if polished and polished not in body_feels and polished not in space_feels:
                if len(body_feels) < 2:
                    body_feels.append(polished)
                elif len(space_feels) < 2:
                    space_feels.append(polished)
        if not body_feels:
            body_feels = [flaw.detail]
        if not space_feels:
            space_feels = [fix.detail if fix else flaw.detail]
        why_first = (
            "Root cause on film — later compensations trace back here."
            if index == 0
            else "Downstream link in the cause-effect chain from earlier phases."
        )
        priorities.append(
            PrioritizedFeelFix(
                rank=index + 1,
                phase=_infer_phase_label(flaw.title),
                title=flaw.title,
                issue=flaw.detail,
                why_first=why_first,
                body_feels=body_feels[:3],
                space_feels=space_feels[:3],
                drill=drill,
            )
        )

    if len(priorities) >= 2:
        return priorities[:5]

    checkpoints = [
        _parse_checkpoint(raw)
        for raw in out.checkpoints
        if raw.strip()
    ]
    constraint_checkpoints = sorted(
        [
            item
            for item in checkpoints
            if item.grade in ("constraint", "compensation")
            and (item.observation or "").strip()
        ],
        key=_checkpoint_phase_rank,
    )
    for index, checkpoint in enumerate(constraint_checkpoints[:5]):
        phase = _infer_phase_label(checkpoint.checkpoint)
        title = checkpoint.checkpoint.split(":", 1)[0].strip() or phase
        issue = checkpoint.observation.strip()
        body_feels = [_polish_cue(out.body_cue)] if out.body_cue.strip() else [issue]
        space_feels = [_polish_cue(out.space_cue)] if out.space_cue.strip() else [issue]
        drill = drills[index] if index < len(drills) else None
        priorities.append(
            PrioritizedFeelFix(
                rank=index + 1,
                phase=phase,
                title=title,
                issue=issue,
                why_first=(
                    "Earliest visible constraint on film."
                    if index == 0
                    else "Compensation that follows earlier setup or takeaway limits."
                ),
                body_feels=body_feels[:3],
                space_feels=space_feels[:3],
                drill=drill,
            )
        )

    if priorities:
        return priorities[:5]

    if out.main_fix.strip():
        return [
            PrioritizedFeelFix(
                rank=1,
                phase="Swing",
                title="Priority fix",
                issue=out.main_fix.strip(),
                why_first=out.root.strip() or out.missing.strip() or "Primary change from film.",
                body_feels=[_polish_cue(t) for t in out.tips[:2] if t.strip()]
                or [out.main_fix.strip()],
                space_feels=[_polish_cue(out.space_cue)] if out.space_cue.strip() else [out.main_fix.strip()],
                drill=drills[0] if drills else None,
            )
        ]
    return []


def _build_priority_fixes(
    out: GeminiReportOut,
    drills: list[DrillSummary],
) -> list[PrioritizedFeelFix]:
    parsed = [
        fix
        for raw in (out.pri1, out.pri2, out.pri3, out.pri4, out.pri5)
        if (fix := _parse_priority_pipe(raw)) is not None
    ]
    if len(parsed) >= 2:
        return sorted(parsed, key=lambda item: item.rank)[:5]
    return _fallback_priority_fixes(out, drills)


def _priority_main_fix(priorities: list[PrioritizedFeelFix], fallback: str) -> str:
    if not priorities:
        return fallback
    primary = priorities[0]
    return f"{primary.title}: {primary.issue} {primary.why_first}".strip()


def _build_feel_blueprint(out: GeminiReportOut) -> FeelBlueprintDiagnostic | None:
    if not out.letter_open.strip() or not out.strength1.strip() or not out.flaw1.strip():
        return None

    strengths = [
        bullet
        for raw in (out.strength1, out.strength2, out.strength3)
        if (bullet := _parse_bullet_pipe(raw)) is not None
    ]
    flaws = [
        bullet
        for raw in (out.flaw1, out.flaw2, out.flaw3)
        if (bullet := _parse_bullet_pipe(raw)) is not None
    ]
    fixes = [
        fix
        for raw in (out.fix1, out.fix2, out.fix3)
        if (fix := _parse_pro_fix_pipe(raw)) is not None
    ]
    if len(strengths) < 2 or len(flaws) < 2 or len(fixes) < 2:
        return None

    return FeelBlueprintDiagnostic(
        opening_narrative=out.letter_open.strip(),
        headline=out.letter_headline.strip() or "Your swing pattern",
        strengths=strengths[:4],
        flaws=flaws[:4],
        current_ceiling=out.ceiling_now.strip() or "Timing-dependent results likely continue.",
        potential_ceiling=out.ceiling_unlock.strip() or "Cleaner contact with the root fix.",
        pro_fixes=fixes[:3],
        body_part_cue=out.body_cue.strip() or fixes[0].detail,
        spatial_cue=out.space_cue.strip() or fixes[0].detail,
    )


def _letter_main_fix(out: GeminiReportOut, fallback: str) -> str:
    primary = _parse_pro_fix_pipe(out.fix1)
    if primary:
        return f"{primary.title}: {primary.detail}"
    return fallback


def _letter_tips(out: GeminiReportOut, fallback: list[str]) -> list[str]:
    tips = [tip for tip in (out.body_cue.strip(), out.space_cue.strip()) if tip]
    for raw in (out.fix2, out.fix3):
        fix = _parse_pro_fix_pipe(raw)
        if fix:
            tips.append(f"{fix.title}: {fix.detail}")
    if len(tips) >= 2:
        return tips[:4]
    return fallback


def _gemini_style_analysis(out: GeminiReportOut, fallback: str) -> str:
    """Build the full visible report from Gemini's structured reasoning fields."""
    strengths = [
        bullet
        for raw in (out.strength1, out.strength2, out.strength3)
        if (bullet := _parse_bullet_pipe(raw)) is not None
    ]
    flaws = [
        bullet
        for raw in (out.flaw1, out.flaw2, out.flaw3)
        if (bullet := _parse_bullet_pipe(raw)) is not None
    ]
    fixes = [
        fix
        for raw in (out.fix1, out.fix2, out.fix3)
        if (fix := _parse_pro_fix_pipe(raw)) is not None
    ]
    if len(strengths) < 2 and len(flaws) < 2 and not fixes:
        return fallback

    evidence_text = " ".join(out.evidence[:8])
    checkpoint_text = " ".join(out.checkpoints[:14])
    combined_evidence = " ".join(part for part in (evidence_text, checkpoint_text) if part)

    def section(title: str, body: str) -> str:
        body = re.sub(r"\s+", " ", body.strip())
        return f"{title}\n\n{body}" if body else ""

    primary = flaws[0] if flaws else None
    secondary = flaws[1] if len(flaws) > 1 else None
    setup_notes = _notes_from_bullets(
        flaws,
        title_terms=("setup", "address", "posture", "grip", "stance"),
        body_terms=("weight", "heel", "hinge", "balance"),
    )
    path_notes = _notes_from_bullets(
        flaws,
        title_terms=("path", "downswing", "over-the-top"),
        body_terms=("steep", "shallow", "outside", "across", "inside"),
    )
    head_notes = " ".join(
        item for item in out.evidence if any(term in item.lower() for term in ("head", "spine", "center"))
    )
    arm_notes = _notes_from_bullets(
        flaws,
        title_terms=("arm", "hand", "elbow", "width", "wrist"),
        body_terms=("lead arm", "trail arm", "hands", "wrist", "width"),
    )
    impact_notes = " ".join(
        item for item in out.evidence if any(term in item.lower() for term in ("impact", "contact", "low point", "strike"))
    )

    opening = " ".join(
        part
        for part in (
            out.letter_open,
            fallback if fallback and len(fallback.split()) >= 20 else "",
            out.chain,
        )
        if part
    )
    rating_line = (
        f"I'd rate this swing {out.rating.strip()}."
        if out.rating.strip()
        else "Rating is limited by the available video, so the coaching priority matters more than the number."
    )
    biggest_positive = (
        f"The big positive: {strengths[0].detail}" if strengths else ""
    )
    main_issue = (
        f"The main issue: {primary.detail}" if primary else (out.missing or out.root)
    )
    best_fix = (
        f"Best fix: {fixes[0].detail}" if fixes else out.main_fix
    )
    category_lines = " ".join(
        f"{parsed.label}: {parsed.rating}"
        for raw in out.categories[:6]
        if raw.strip()
        for parsed in [_parse_category_rating(raw)]
        if parsed
    )
    verdict = " ".join(
        part
        for part in (rating_line, biggest_positive, main_issue, best_fix, category_lines)
        if part
    )
    drill = next((raw for raw in (out.drill1, out.drill2, out.drill3) if raw.strip()), "")
    parsed_drill = _parse_drill_pipe(drill) if drill else None

    sections = [
        section("Quick coach verdict", verdict),
        section("Full coach-style analysis", opening),
        section("Main swing fault", f"{primary.title}: {primary.detail}" if primary else out.missing),
        section("Secondary swing fault", f"{secondary.title}: {secondary.detail}" if secondary else out.secondary),
        section("What you do well", " ".join(f"{item.title}: {item.detail}" for item in strengths[:3])),
        section("Setup/grip notes", setup_notes or _extract_evidence_for_terms(combined_evidence, ("setup", "address", "grip", "posture", "stance", "balance"))),
        section("Swing path notes", path_notes or _extract_evidence_for_terms(combined_evidence, ("path", "downswing", "steep", "shallow", "over-the-top", "club"))),
        section("Head movement notes", head_notes or _extract_evidence_for_terms(combined_evidence, ("head", "spine", "center")) or "Head movement is not clearly visible enough to make it the main priority."),
        section("Arm/hand structure", arm_notes or _extract_evidence_for_terms(combined_evidence, ("arm", "hand", "elbow", "width", "wrist"))),
        section("Impact-window notes", impact_notes or _extract_evidence_for_terms(combined_evidence, ("impact", "contact", "strike", "low point")) or "Impact feedback is limited to the visible impact window and nearby frames."),
        section("Drill", f"{parsed_drill.name}: {parsed_drill.why_it_helps} {parsed_drill.how_to_do_it}" if parsed_drill else ""),
        section("Feel", " ".join(t for t in (out.body_cue, out.space_cue) if t.strip())),
        section("Practice plan", _practice_plan_from_out(out, fixes)),
        section("Confidence/visibility limitations", _confidence_limitations(out)),
    ]
    return "\n\n".join(item for item in sections if item).strip() or fallback


def _extract_evidence_for_terms(text: str, terms: tuple[str, ...]) -> str:
    pieces = re.split(r"(?<=[.!?])\s+|;", text)
    matches = [piece.strip() for piece in pieces if any(term in piece.lower() for term in terms)]
    return " ".join(matches[:3])


def _notes_from_bullets(
    bullets: list[AnalysisBullet],
    *,
    title_terms: tuple[str, ...],
    body_terms: tuple[str, ...],
) -> str:
    title_matches = [
        bullet.detail
        for bullet in bullets
        if any(term in bullet.title.lower() for term in title_terms)
    ]
    if title_matches:
        return " ".join(title_matches)
    body_matches = [
        bullet.detail
        for bullet in bullets
        if any(term in bullet.detail.lower() for term in body_terms)
    ]
    return " ".join(body_matches[:2])


def _practice_plan_from_out(out: GeminiReportOut, fixes: list[ProFix]) -> str:
    focus = out.focus.strip() or out.missing.strip() or "the main swing priority"
    fix_text = " ".join(f"{fix.title}: {fix.detail}" for fix in fixes[:2])
    day7 = out.day7.strip() or out.next_check.strip()
    return (
        f"Spend the first two sessions rehearsing {focus} without worrying about ball flight. "
        f"Then blend it into half-speed shots using one feel at a time. {fix_text} "
        f"By the end of the week, use this check: {day7}"
    ).strip()


def _confidence_limitations(out: GeminiReportOut) -> str:
    confidence = _clamp_confidence(out.confidence)
    limits: list[str] = []
    evidence_blob = " ".join([*out.evidence, *out.checkpoints]).lower()
    if any(term in evidence_blob for term in ("not_visible", "estimated", "limited", "blocked", "hidden")):
        limits.append("Some details are limited by camera angle or phase visibility.")
    if "grip" not in evidence_blob and "clubface" not in evidence_blob:
        limits.append("Grip and clubface certainty are limited unless the camera clearly shows the hands and face.")
    limits.append(f"Overall confidence in the main diagnosis: {confidence:.0%}.")
    return " ".join(limits)


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
            for key in ("tip", "feel", "text", "content", "cue"):
                direct = item.get(key)
                if isinstance(direct, str) and direct.strip():
                    result.append(direct.strip())
                    break
            else:
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
        "rating",
        "categories",
        "analysis",
        "main_fix",
        "next_check",
        "missing",
        "profile",
        "root",
        "secondary",
        "symptom",
        "chain",
        "focus",
        "day7",
        "letter_open",
        "letter_headline",
        "strength1",
        "strength2",
        "strength3",
        "flaw1",
        "flaw2",
        "flaw3",
        "ceiling_now",
        "ceiling_unlock",
        "fix1",
        "fix2",
        "fix3",
        "body_cue",
        "space_cue",
        "pri1",
        "pri2",
        "pri3",
        "pri4",
        "pri5",
        "foundational_missing_piece",
        "secondary_fix",
        "miss_conflict_note",
    ):
        if key in data:
            data[key] = _flatten_field(data.get(key))

    if "mode" in data and not isinstance(data["mode"], str):
        data["mode"] = str(data["mode"] or "development")
    if "report_mode" in data and not isinstance(data["report_mode"], str):
        data["report_mode"] = str(data["report_mode"] or "development")
    if "miss_pattern_match" in data and not isinstance(data["miss_pattern_match"], str):
        data["miss_pattern_match"] = str(data["miss_pattern_match"] or "low")

    if "tips" in data:
        data["tips"] = _coerce_string_list(data["tips"])[:4]
    if "checkpoints" in data:
        data["checkpoints"] = _coerce_string_list(data["checkpoints"])[:14]
    if "evidence" in data:
        data["evidence"] = _coerce_string_list(data["evidence"])[:8]

    if "categories" in data:
        data["categories"] = _coerce_string_list(data["categories"])[:6]

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
            "rating": data.get("rating", ""),
            "categories": data.get("categories", []),
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
            "secondary": data.get("secondary_fix", data.get("secondary", "")),
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


def _observer_payload(out: GeminiReportOut) -> dict:
    observations = out.observations.model_dump() if out.observations else {}
    payload = {
        "observations": observations,
        "camera_angle": out.camera_angle,
        "video_usability": out.video_usability,
        "usability_note": out.usability_note,
    }
    if out.grades is not None:
        payload["diagnostic"] = {
            "grades": out.grades.model_dump(),
            "report_mode": out.report_mode or "development",
            "foundational_missing_piece": out.foundational_missing_piece,
            "secondary_fix": out.secondary_fix,
            "miss_pattern_match": out.miss_pattern_match or "low",
            "miss_conflict_note": out.miss_conflict_note,
            "confidence": out.confidence,
        }
    return payload


_PHASE_ORDER = (
    "setup",
    "takeaway",
    "backswing",
    "transition",
    "downswing",
    "impact",
    "finish",
)


def _phase_display_name(phase: str) -> str:
    return phase.replace("_", " ").title()


_PHASE_EVIDENCE_KEYWORDS: dict[str, tuple[str, ...]] = {
    "setup": ("address", "setup", "posture", "heel", "stance", "grip", "c-posture", "rounded", "upper back"),
    "takeaway": ("takeaway", "first move", "initial"),
    "backswing": ("backswing", "top", "lead arm", "arm bend", "width", "collapse", "takeback"),
    "transition": ("transition", "start the downswing", "shoulders and arms", "shoulders start", "upper body first"),
    "downswing": ("downswing", "path", "steep", "shallow", "over-the-top", "slot"),
    "impact": ("impact", "spine angle", "early extension", "contact", "strike", "low point", "spine"),
    "finish": ("finish", "follow through", "balance at finish"),
}


def _observations_have_content(observation: GeminiReportOut) -> bool:
    if not observation.observations:
        return False
    for phase in _PHASE_ORDER:
        obs = observation.observations.model_dump().get(phase, {})
        if isinstance(obs, dict) and any(str(obs.get(key, "")).strip() for key in ("club", "body", "not_visible")):
            return True
    return False


def _phase_for_evidence_line(line: str) -> str | None:
    lower = line.lower()
    best_phase: str | None = None
    best_score = 0
    for phase, keywords in _PHASE_EVIDENCE_KEYWORDS.items():
        score = sum(1 for keyword in keywords if keyword in lower)
        if score > best_score:
            best_score = score
            best_phase = phase
    return best_phase if best_score > 0 else None


def _resolve_film_evidence(combined: GeminiReportOut, report: CoachingReportSchema) -> list[str]:
    """Prefer structured Call 1 lines; merge accurate Call 3 evidence bullets when needed."""
    structured = _film_evidence_lines(combined, max_words=200)
    call3 = [item.strip() for item in report.advanced_details.evidence_metrics if item.strip()]
    if structured:
        merged = list(structured)
        seen = {line.lower() for line in merged}
        for line in call3:
            lower = line.lower()
            if lower in seen:
                continue
            if any(lower in existing.lower() or existing.lower() in lower for existing in merged):
                continue
            merged.append(line)
            seen.add(lower)
        return merged[:12]
    return call3[:12]


def _film_walkthrough_from_evidence(
    evidence_lines: list[str],
    combined: GeminiReportOut,
    coach_verdict: CoachVerdict | None,
) -> str:
    """Build phase walkthrough by grouping accurate film evidence lines."""
    if not evidence_lines:
        return ""

    by_phase: dict[str, list[str]] = {phase: [] for phase in _PHASE_ORDER}
    general: list[str] = []
    for line in evidence_lines:
        phase = _phase_for_evidence_line(line)
        if phase:
            by_phase[phase].append(line)
        else:
            general.append(line)

    grade_map = combined.grades.model_dump() if combined.grades else {}
    phase_blocks: list[str] = []
    for phase in _PHASE_ORDER:
        lines = by_phase[phase]
        if not lines:
            continue
        block = [f"**{_phase_display_name(phase)}**", *lines]
        grade_info = grade_map.get(phase, {})
        if isinstance(grade_info, dict):
            grade = str(grade_info.get("grade", "")).strip()
            reason = str(grade_info.get("reason", "")).strip()
            if grade and grade != "Not Visible":
                coach_line = f"Coach read: {grade}"
                if reason:
                    coach_line += f" — {reason}"
                block.append(coach_line)
        phase_blocks.append("\n".join(block))

    if general:
        phase_blocks.append("**Other on film**\n" + "\n".join(general))

    sections = ["Setup to finish", "\n\n".join(phase_blocks)]
    if combined.usability_note.strip():
        sections.append(f"Camera note\n\n{combined.usability_note.strip()}")
    return "\n\n".join(sections).strip()


def _film_priority_main_fix(
    grading: GeminiReportOut,
    evidence_lines: list[str],
    fallback: str,
) -> str:
    """Prefer the earliest visible dynamic issue over a generic setup-only lesson."""
    blob = " ".join(evidence_lines).lower()
    foundation = (grading.foundational_missing_piece or fallback or "").strip()
    setup_only = foundation and all(
        term not in foundation.lower()
        for term in ("arm", "path", "transition", "downswing", "impact", "spine", "shoulder", "sequenc")
    ) and any(term in foundation.lower() for term in ("setup", "posture", "heel", "address", "stance"))

    dynamic_count = sum(
        1
        for terms in (
            ("lead arm", "arm bend", "collapse", "at the top"),
            ("shoulder", "arms start", "sequenc", "upper body"),
            ("spine", "early extension", "stand up", "through impact"),
        )
        if any(term in blob for term in terms)
    )
    if not setup_only or dynamic_count < 1:
        return foundation or fallback

    if any(term in blob for term in ("lead arm", "arm bend", "collapse", "at the top")):
        return (
            "Keep the lead arm extended through the top instead of folding it across your chest. "
            "That width is what lets the downswing sequence from the ground up."
        )
    if any(term in blob for term in ("shoulder", "arms start", "sequenc")):
        return (
            "Start the downswing from the lower body before the shoulders and arms fire. "
            "The film shows the upper body leading — let pressure shift first, then turn."
        )
    if any(term in blob for term in ("spine", "early extension", "stand up", "through impact")):
        return (
            "Maintain your spine angle through impact instead of standing up to help the club. "
            "Stay in the posture you set while the body rotates through."
        )
    return foundation or fallback


def _film_secondary_fix(grading: GeminiReportOut, evidence_lines: list[str], main_fix: str) -> str:
    blob = " ".join(evidence_lines).lower()
    if any(term in blob for term in ("heel", "posture", "rounded", "c-posture", "upper back")):
        setup_context = (
            "Setup context: balance weight over the middle of your feet, not your heels, "
            "and hinge from the hips instead of rounding the upper back."
        )
        if setup_context.lower() not in main_fix.lower():
            return setup_context
    return (grading.secondary_fix or "").strip()


def _film_evidence_lines(out: GeminiReportOut, *, max_words: int = 120) -> list[str]:
    """Detailed per-phase film evidence from Call 1 observations."""
    if not out.observations:
        return []
    grade_map = out.grades.model_dump() if out.grades else {}
    lines: list[str] = []
    for phase in _PHASE_ORDER:
        observation = out.observations.model_dump().get(phase, {})
        if not isinstance(observation, dict):
            continue
        club = str(observation.get("club", "")).strip()
        body = str(observation.get("body", "")).strip()
        not_visible = str(observation.get("not_visible", "")).strip()
        if not any((club, body, not_visible)):
            continue
        parts: list[str] = []
        if club:
            parts.append(f"Club: {club}")
        if body:
            parts.append(f"Body: {body}")
        if not_visible:
            parts.append(f"Camera: {not_visible}")
        grade_info = grade_map.get(phase, {})
        if isinstance(grade_info, dict):
            grade = str(grade_info.get("grade", "")).strip()
            reason = str(grade_info.get("reason", "")).strip()
            if grade and grade != "Not Visible":
                grade_line = f"Grade: {grade}"
                if reason:
                    grade_line += f" — {reason}"
                parts.append(grade_line)
        lines.append(_cap_words(f"{_phase_display_name(phase)} — {' '.join(parts)}", max_words))
    return lines


def _film_walkthrough_analysis(out: GeminiReportOut, coach_verdict: CoachVerdict | None = None) -> str:
    """Build user-facing analysis by elaborating Call 1 observations phase by phase."""
    if not out.observations:
        return ""

    sections: list[str] = []
    if coach_verdict and coach_verdict.overall_rating and not coach_verdict.main_issue:
        verdict_parts = [
            coach_verdict.overall_rating,
            f"The big positive: {coach_verdict.biggest_positive}" if coach_verdict.biggest_positive else "",
            f"Main issue: {coach_verdict.main_issue}" if coach_verdict.main_issue else "",
            f"Best fix: {coach_verdict.best_fix}" if coach_verdict.best_fix else "",
        ]
        verdict_text = "\n".join(part for part in verdict_parts if part)
        if verdict_text:
            sections.append(f"Quick coach verdict\n\n{verdict_text}")

    sections.append("Setup to finish")
    grade_map = out.grades.model_dump() if out.grades else {}
    phase_blocks: list[str] = []
    for phase in _PHASE_ORDER:
        observation = out.observations.model_dump().get(phase, {})
        if not isinstance(observation, dict):
            continue
        club = str(observation.get("club", "")).strip()
        body = str(observation.get("body", "")).strip()
        not_visible = str(observation.get("not_visible", "")).strip()
        if not any((club, body, not_visible)):
            continue
        lines = [f"**{_phase_display_name(phase)}**"]
        if club:
            lines.append(f"Club: {club}")
        if body:
            lines.append(f"Body: {body}")
        if not_visible:
            lines.append(f"Camera limit: {not_visible}")
        grade_info = grade_map.get(phase, {})
        if isinstance(grade_info, dict):
            grade = str(grade_info.get("grade", "")).strip()
            reason = str(grade_info.get("reason", "")).strip()
            if grade:
                coach_line = f"Coach read: {grade}"
                if reason:
                    coach_line += f" — {reason}"
                lines.append(coach_line)
        phase_blocks.append("\n".join(lines))

    if phase_blocks:
        sections.append("\n\n".join(phase_blocks))
    else:
        return ""

    if out.usability_note.strip():
        sections.append(f"Camera note\n\n{out.usability_note.strip()}")

    return "\n\n".join(sections).strip()


def apply_film_first_report(
    report: CoachingReportSchema,
    observation: GeminiReportOut,
    grading: GeminiReportOut,
) -> CoachingReportSchema:
    """Replace generic coaching prose with elaborated Call 1 film observations."""
    has_structured = _observations_have_content(observation)
    has_call3_evidence = bool(report.advanced_details.evidence_metrics)
    if not has_structured and not has_call3_evidence:
        return report

    combined = observation.model_copy(
        update={
            "grades": grading.grades,
            "report_mode": grading.report_mode,
            "foundational_missing_piece": grading.foundational_missing_piece,
            "secondary_fix": grading.secondary_fix,
            "miss_pattern_match": grading.miss_pattern_match,
            "miss_conflict_note": grading.miss_conflict_note,
            "confidence": grading.confidence,
        }
    )
    film_evidence = _resolve_film_evidence(combined, report)
    if not film_evidence:
        return report

    film_analysis = _film_walkthrough_analysis(combined, report.coach_verdict)
    if not film_analysis:
        film_analysis = _film_walkthrough_from_evidence(film_evidence, combined, report.coach_verdict)

    main_fix = _film_priority_main_fix(grading, film_evidence, report.main_fix)
    secondary_fix = _film_secondary_fix(grading, film_evidence, main_fix)

    adv = report.advanced_details.model_copy(
        update={
            "evidence_metrics": _filter_visible_evidence(film_evidence),
            "diagnostic_checkpoints": _observer_grade_checkpoints(combined)
            or report.advanced_details.diagnostic_checkpoints,
            "foundational_missing_piece": main_fix,
            "secondary_fix": secondary_fix or report.advanced_details.secondary_fix,
            "root_cause": main_fix,
            "report_mode": grading.report_mode or report.advanced_details.report_mode,
            "confidence_score": _clamp_confidence(grading.confidence)
            if grading.confidence
            else report.advanced_details.confidence_score,
        }
    )

    coach_verdict = report.coach_verdict
    if coach_verdict:
        coach_verdict = coach_verdict.model_copy(
            update={
                "main_issue": coach_verdict.main_issue or main_fix,
                "best_fix": coach_verdict.best_fix or main_fix,
            }
        )

    priority_fixes = list(report.priority_fixes)
    if priority_fixes:
        primary = priority_fixes[0]
        priority_fixes[0] = primary.model_copy(
            update={
                "issue": main_fix,
                "why_first": primary.why_first or adv.root_cause or main_fix,
            }
        )
    elif film_evidence:
        priority_fixes = _fallback_priority_fixes(
            GeminiReportOut(
                main_fix=main_fix,
                root=main_fix,
                missing=grading.foundational_missing_piece or main_fix,
                secondary=secondary_fix,
                body_cue=report.tips_and_feels[0] if report.tips_and_feels else "",
                space_cue=report.tips_and_feels[1] if len(report.tips_and_feels) > 1 else "",
                tips=report.tips_and_feels,
                checkpoints=[
                    f"{item.checkpoint}|{item.grade}|{item.observation}"
                    for item in adv.diagnostic_checkpoints
                ],
            ),
            report.drills,
        )

    updated = report.model_copy(
        update={
            "pga_analysis": film_analysis,
            "main_fix": main_fix,
            "tips_and_feels": report.tips_and_feels,
            "advanced_details": adv,
            "coach_verdict": coach_verdict,
            "priority_fixes": priority_fixes,
        }
    )
    return updated


def _film_tips_from_evidence(evidence_lines: list[str], fallback: list[str]) -> list[str]:
    blob = " ".join(evidence_lines).lower()
    tips: list[str] = []
    if any(term in blob for term in ("lead arm", "arm bend", "collapse", "top")):
        tips.append("Feel width at the top — lead arm long, hands away from the chest.")
    if any(term in blob for term in ("shoulder", "arms start", "sequenc")):
        tips.append("Feel the lower body start down before the arms drop.")
    if any(term in blob for term in ("heel", "posture", "rounded", "c-posture")):
        tips.append("Feel weight over the middle of your feet, not the heels.")
    if any(term in blob for term in ("spine", "early extension", "stand up", "impact")):
        tips.append("Feel your chest staying over the ball through impact.")
    if len(tips) >= 2:
        return tips[:4]
    return tips + [tip for tip in fallback if tip not in tips][:4]


def _observer_evidence(out: GeminiReportOut) -> list[str]:
    if not out.observations:
        return []
    evidence: list[str] = []
    for phase, observation in out.observations.model_dump().items():
        club = observation.get("club", "").strip()
        body = observation.get("body", "").strip()
        not_visible = observation.get("not_visible", "").strip()
        parts = [part for part in (club, body, not_visible) if part]
        if parts:
            evidence.append(f"{phase}: {' '.join(parts)}")
    return [_cap_words(item, 40) for item in evidence[:8]]


def _observer_grade_checkpoints(out: GeminiReportOut) -> list[DiagnosticCheckpointGrade]:
    if out.grades is None:
        return []
    checkpoints: list[DiagnosticCheckpointGrade] = []
    for phase, item in out.grades.model_dump().items():
        checkpoints.append(
            DiagnosticCheckpointGrade(
                checkpoint=f"{phase.capitalize()}:",
                grade=_GRADE_MAP.get(str(item.get("grade")), "not_visible"),  # type: ignore[arg-type]
                observation=str(item.get("reason") or ""),
            )
        )
    return checkpoints


def _observer_out_to_coaching_report(out: GeminiReportOut) -> CoachingReportSchema:
    analysis_json = json.dumps(_observer_payload(out), ensure_ascii=False, indent=2)
    usability_note = out.usability_note or "Observation-only response generated from the available video."
    next_check = _cap_words(usability_note, 18) or "Camera visibility noted in observer output."
    report_mode = out.report_mode or "development"
    primary = out.foundational_missing_piece or _OBSERVER_ONLY_LABEL
    secondary = out.secondary_fix or _OBSERVER_ONLY_LABEL
    miss_note = out.miss_conflict_note or ""

    return CoachingReportSchema(
        personalized_greeting="Biomechanics observation only.",
        pga_analysis=analysis_json,
        main_fix="Observation-only output. No movement guidance generated.",
        tips_and_feels=[
            "Club and body motion described by phase.",
            "Camera limitations described by phase.",
        ],
        drills=[],
        next_swing_check=next_check,
        coach_verdict=None,
        advanced_details=AdvancedDetails(
            report_mode=report_mode,
            foundational_missing_piece=primary,
            profile_constraints_applied="",
            diagnostic_checkpoints=_observer_grade_checkpoints(out),
            root_cause=primary,
            symptom=miss_note,
            evidence_metrics=_observer_evidence(out),
            secondary_fix=secondary,
            optional_fix="",
            chain_reaction=_OBSERVER_ONLY_LABEL,
            why_it_caused_the_miss=miss_note,
            confidence_score=(
                _clamp_confidence(out.confidence)
                if out.grades is not None
                else 1.0 if out.video_usability == "good" else 0.75 if out.video_usability == "acceptable" else 0.4
            ),
            next_checkpoint="",
        ),
        feel_blueprint=None,
        priority_fixes=[],
        blueprint=KinestheticBlueprint(
            headline="Observation",
            intro="Phase-by-phase visible movement notes.",
            steps=[
                BlueprintStep(
                    title="Club",
                    step_type="visual_cue",
                    action="Review the club notes for each phase.",
                    feel="Visible club motion only.",
                ),
                BlueprintStep(
                    title="Body",
                    step_type="visual_cue",
                    action="Review the body notes for each phase.",
                    feel="Visible body motion only.",
                ),
            ],
        ),
        roadmap=AccountabilityPlan(
            weekly_focus="Observation",
            milestones=[
                MilestoneBlock(days="Setup", title="Club", detail="Read the setup club note."),
                MilestoneBlock(days="Motion", title="Body", detail="Read the phase body notes."),
                MilestoneBlock(days="Camera", title="Visibility", detail="Read the camera limitation notes."),
            ],
            day_7_test="Use the camera usability note as the visibility summary.",
        ),
        next_upload_focus=next_check,
        disclaimer="",
    )


def _gemini_blueprint(out: GeminiReportOut, tips: list[str]) -> KinestheticBlueprint:
    focus = (out.focus or "Focus").strip()[:40] or "Focus"
    primary_feel = tips[0] if tips else (out.body_cue or out.main_fix or "")
    secondary_feel = tips[1] if len(tips) > 1 else (out.space_cue or primary_feel)
    return KinestheticBlueprint(
        headline=focus,
        intro=(out.main_fix or "")[:120],
        steps=[
            BlueprintStep(
                title=focus,
                step_type="visual_cue",
                action="",
                feel=primary_feel,
            ),
            BlueprintStep(
                title="Cue",
                step_type="visual_cue",
                action="",
                feel=secondary_feel,
            ),
        ],
    )


def _gemini_roadmap(out: GeminiReportOut) -> AccountabilityPlan:
    focus = (out.focus or "Practice").strip()[:20] or "Practice"
    day7 = (out.day7 or out.next_check or "").strip()
    tip = (out.tips[0] if out.tips else "").strip()
    drill_name = ""
    for raw in (out.drill1, out.drill2, out.drill3):
        parsed = _parse_drill_pipe(raw)
        if parsed and parsed.name.strip():
            drill_name = parsed.name.strip()
            break
    range_detail = (
        f"Hit 20 balls at the range using the {drill_name} drill."
        if drill_name
        else "Hit 20 half-speed balls with the priority drill feel."
    )
    return AccountabilityPlan(
        weekly_focus=focus,
        milestones=[
            MilestoneBlock(
                days="Days 1-2",
                title="Shadow reps",
                detail=tip or "25 film-free shadow reps a day focusing on your one feel.",
            ),
            MilestoneBlock(days="Days 3-5", title="Range drill", detail=range_detail),
            MilestoneBlock(
                days="Days 6-7",
                title="Film check",
                detail=day7 or out.next_check.strip() or "Upload a new video from the same angle.",
            ),
        ],
        day_7_test=day7[:160] or out.next_check.strip()[:160],
    )


def gemini_out_to_coaching_report(out: GeminiReportOut) -> CoachingReportSchema:
    if out.observations is not None:
        return _observer_out_to_coaching_report(out)

    mode = out.mode if out.mode in ("development", "maintenance") else "development"
    checkpoints = _filter_visible_checkpoints(
        [_parse_checkpoint(s) for s in out.checkpoints if s.strip()]
    )
    feel_blueprint = _build_feel_blueprint(out)
    tips = [_polish_cue(t) for t in out.tips if t.strip()][:4]
    analysis_text = out.analysis.strip()

    coach_verdict = _build_coach_verdict(
        out,
        strengths=[
            bullet
            for raw in (out.strength1, out.strength2, out.strength3)
            if (bullet := _parse_bullet_pipe(raw)) is not None
        ],
        flaws=[
            bullet
            for raw in (out.flaw1, out.flaw2, out.flaw3)
            if (bullet := _parse_bullet_pipe(raw)) is not None
        ],
        fixes=[
            fix
            for raw in (out.fix1, out.fix2, out.fix3)
            if (fix := _parse_pro_fix_pipe(raw)) is not None
        ],
        analysis_text=analysis_text,
    )

    drills: list[DrillSummary] = []
    for raw in (out.drill1, out.drill2, out.drill3):
        parsed = _parse_drill_pipe(raw)
        if parsed:
            drills.append(parsed)

    priority_fixes = _build_priority_fixes(out, drills[:3])
    main_fix = _priority_main_fix(priority_fixes, out.main_fix.strip())

    next_check = out.next_check.strip()

    return CoachingReportSchema(
        personalized_greeting=out.greeting.strip(),
        pga_analysis=analysis_text,
        main_fix=main_fix,
        tips_and_feels=tips,
        drills=drills[:3],
        next_swing_check=next_check,
        coach_verdict=coach_verdict,
        advanced_details=AdvancedDetails(
            report_mode=mode,  # type: ignore[arg-type]
            foundational_missing_piece=out.missing.strip(),
            profile_constraints_applied=out.profile.strip(),
            diagnostic_checkpoints=checkpoints,
            root_cause=out.root.strip(),
            symptom=out.symptom.strip(),
            evidence_metrics=_filter_visible_evidence(
                [item.strip() for item in out.evidence if item.strip()]
            )[:8],
            secondary_fix=out.secondary.strip(),
            optional_fix="",
            chain_reaction=out.chain.strip(),
            why_it_caused_the_miss=out.symptom.strip(),
            confidence_score=_clamp_confidence(out.confidence),
            next_checkpoint="",
        ),
        feel_blueprint=feel_blueprint,
        priority_fixes=priority_fixes,
        blueprint=_gemini_blueprint(out, tips),
        roadmap=_gemini_roadmap(out),
        next_upload_focus=next_check,
        disclaimer="",
    )
