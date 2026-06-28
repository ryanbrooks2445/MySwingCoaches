from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.gemini_coach import (
    OBSERVATION_SYSTEM,
    _apply_narrative_response,
    _audit_with_revisions,
    _build_diagnostic_prompt,
    _build_narrative_prompt,
    _build_prompt,
    _call_gemini,
    _call_narrative_gemini,
    _dynamic_priority_guard,
    _preserve_preanalyzed_diagnosis,
)
from app.gemini_report_schema import DIAGNOSTIC_RESPONSE_JSON_SCHEMA, GEMINI_RESPONSE_JSON_SCHEMA
from app.report_audit import ReportQualityError
from app.schemas import CoachingReportSchema, DISCLAIMER


ROOT = Path(__file__).resolve().parents[1]


def _read(relative: str) -> str:
    return (ROOT / relative).read_text()


def _minimal_report() -> CoachingReportSchema:
    return CoachingReportSchema.model_validate(
        {
            "personalized_greeting": "Test, solid base.",
            "pga_analysis": "What's working\nTempo.\n\nSetup to finish\nConnected.\n\nThe missing piece\nPath.\n\nWhat changes when you unlock it\nBetter contact.",
            "main_fix": "Shallow the path.",
            "tips_and_feels": ["Feel the drop.", "Turn through after slot."],
            "drills": [
                {
                    "name": "Pump",
                    "why_it_helps": "Trains slot.",
                    "how_to_do_it": "Pump twice.",
                }
            ],
            "next_swing_check": "Film face-on.",
            "advanced_details": {
                "report_mode": "development",
                "foundational_missing_piece": "Steep downswing path.",
                "profile_constraints_applied": "",
                "diagnostic_checkpoints": [],
                "root_cause": "Arms fire early.",
                "symptom": "Timing miss.",
                "evidence_metrics": ["Path steep"],
                "secondary_fix": "Keep head quieter.",
                "optional_fix": "",
                "chain_reaction": "Arms fire early and the club stays steep through impact.",
                "why_it_caused_the_miss": "Contact relies on timing.",
                "confidence_score": 0.7,
                "next_checkpoint": "address",
            },
            "blueprint": {
                "headline": "Path",
                "intro": "Shallow it.",
                "steps": [
                    {"title": "Drop", "step_type": "setup", "feel": "Hands first."},
                    {"title": "Turn", "step_type": "visual_cue", "feel": "Rotate through."},
                ],
            },
            "roadmap": {
                "weekly_focus": "Path",
                "milestones": [
                    {"days": "Day 1", "title": "Rehearse", "detail": "Ten reps."},
                    {"days": "Day 2", "title": "Blend", "detail": "Half speed."},
                    {"days": "Day 3", "title": "Test", "detail": "Film again."},
                ],
                "day_7_test": "Path shallow.",
            },
            "next_upload_focus": "Path",
            "disclaimer": DISCLAIMER,
        }
    )


def test_observation_system_is_observer_only() -> None:
    lower_prompt = OBSERVATION_SYSTEM.lower()

    for phrase in (
        "your only job is to describe what you see",
        "do not diagnose",
        "do not suggest fixes",
        "do not pick a report mode",
        "return json only",
        "setup",
        "takeaway",
        "backswing",
        "transition",
        "downswing",
        "impact",
        "finish",
    ):
        assert phrase in lower_prompt


def test_call3_prompt_requires_coaching_language() -> None:
    prompt = _build_prompt(
        swing_mode="full_swing",
        history_summary="Prior swing 1: main priority: steep path.",
        player_name="Jordan",
        swing_number=2,
        player_context="Typical miss: slice.",
        player_age=35,
        years_playing=10,
        physical_limitations="Bad lower back",
    )
    lower_prompt = prompt.lower()

    for phrase in (
        "forefixed",
        "head coach",
        "locked",
        "film first",
        "main_fix",
        "jordan",
        "prior swing history",
        "do not contradict",
        "evidence",
    ):
        assert phrase in lower_prompt

    for phrase in ("do not diagnose", "do not suggest fixes", "your only job is to describe"):
        assert phrase not in lower_prompt


def test_call3_prompt_includes_physical_boundaries_when_provided() -> None:
    prompt = _build_prompt(
        swing_mode="full_swing",
        history_summary=None,
        player_name="Alex",
        swing_number=None,
        player_context=None,
        player_age=52,
        years_playing=20,
        physical_limitations="Left knee replacement",
    )
    lower_prompt = prompt.lower()

    assert "human blueprint" in lower_prompt
    assert "left knee replacement" in lower_prompt
    assert "52" in prompt
    assert "20" in prompt


def test_diagnostic_prompt_includes_physical_limitations() -> None:
    prompt = _build_diagnostic_prompt(
        raw_observations_json='{"observations":{"setup":{"club":"visible","body":"visible","not_visible":""}}}',
        player_context="Average 9-hole score: 48. Typical miss: slice. Main goal: more fairways.",
        years_playing=7,
        player_age=45,
        physical_limitations="Shoulder impingement",
    )
    lower_prompt = prompt.lower()

    assert "shoulder impingement" in lower_prompt
    assert "human blueprint" in lower_prompt
    assert "mobility ceiling" in lower_prompt
    assert "45" in prompt


def test_gemini_schema_is_observer_shape() -> None:
    properties = GEMINI_RESPONSE_JSON_SCHEMA["properties"]

    assert set(GEMINI_RESPONSE_JSON_SCHEMA["required"]) == {
        "observations",
        "camera_angle",
        "video_usability",
        "usability_note",
    }
    assert set(properties["observations"]["required"]) == {
        "setup",
        "takeaway",
        "backswing",
        "transition",
        "downswing",
        "impact",
        "finish",
    }
    assert properties["camera_angle"]["enum"] == ["face-on", "down-the-line", "behind", "unclear"]
    assert properties["video_usability"]["enum"] == ["good", "acceptable", "poor"]


def test_diagnostic_prompt_uses_profile_and_raw_observations() -> None:
    prompt = _build_diagnostic_prompt(
        raw_observations_json='{"observations":{"setup":{"club":"visible","body":"visible","not_visible":""}}}',
        player_context="Average 9-hole score: 48. Typical miss: slice. Main goal: more fairways.",
        years_playing=7,
    )
    lower_prompt = prompt.lower()

    for phrase in (
        "you are a golf diagnostic engine",
        "typical miss: slice",
        "average score: 48",
        "years playing: 7",
        "goals: more fairways",
        "raw observations",
        "report_mode",
        "miss_pattern_match",
    ):
        assert phrase in lower_prompt


def test_diagnostic_schema_shape() -> None:
    properties = DIAGNOSTIC_RESPONSE_JSON_SCHEMA["properties"]

    assert set(DIAGNOSTIC_RESPONSE_JSON_SCHEMA["required"]) == {
        "grades",
        "report_mode",
        "foundational_missing_piece",
        "secondary_fix",
        "miss_pattern_match",
        "miss_conflict_note",
        "confidence",
    }
    assert set(properties["grades"]["required"]) == {
        "setup",
        "takeaway",
        "backswing",
        "transition",
        "downswing",
        "impact",
        "finish",
    }
    assert properties["report_mode"]["enum"] == ["maintenance", "development"]
    assert properties["miss_pattern_match"]["enum"] == ["high", "medium", "low"]


def test_narrative_prompt_locks_preanalyzed_observations_and_grades() -> None:
    report = _minimal_report().model_copy(
        update={
            "pga_analysis": """
            {
              "observations": {
                "setup": { "club": "Club starts behind ball.", "body": "Feet are set.", "not_visible": "Grip hidden." }
              },
              "camera_angle": "down-the-line",
              "video_usability": "acceptable",
              "usability_note": "Mostly visible.",
              "diagnostic": {
                "grades": {
                  "setup": { "grade": "Constraint", "reason": "Setup is the earliest graded link." }
                },
                "report_mode": "development",
                "foundational_missing_piece": "Setup spacing",
                "secondary_fix": "Transition timing",
                "miss_pattern_match": "medium",
                "miss_conflict_note": "Partial match.",
                "confidence": 0.66
              }
            }
            """,
        }
    )
    report.advanced_details.report_mode = "development"
    report.advanced_details.foundational_missing_piece = "Setup spacing"

    prompt = _build_narrative_prompt(report)

    assert "PRE-ANALYZED EVIDENCE (DO NOT OVERRIDE)" in prompt
    assert "OBSERVATIONS:" in prompt
    assert "GRADES:" in prompt
    assert "report_mode is already set to: development" in prompt
    assert "foundational_missing_piece is already set to: Setup spacing" in prompt
    assert "Your job is to write the coaching output only. Do not re-diagnose." in prompt
    assert "Do not change report_mode. Do not introduce flaws not present in the grades above." in prompt


def test_preserve_preanalyzed_diagnosis_keeps_grades_after_narrative() -> None:
    original = _minimal_report()
    updated = _minimal_report()
    original.advanced_details.report_mode = "maintenance"
    original.advanced_details.foundational_missing_piece = "None — maintain current baseline"
    original.advanced_details.secondary_fix = "Tempo preservation"
    original.advanced_details.confidence_score = 0.91
    updated.advanced_details.report_mode = "development"
    updated.advanced_details.foundational_missing_piece = "New narrative diagnosis"
    updated.advanced_details.secondary_fix = "Changed by writer"
    updated.advanced_details.confidence_score = 0.12

    preserved = _preserve_preanalyzed_diagnosis(original, updated)

    assert preserved.advanced_details.report_mode == "maintenance"
    assert preserved.advanced_details.foundational_missing_piece == "None — maintain current baseline"
    assert preserved.advanced_details.secondary_fix == "Tempo preservation"
    assert preserved.advanced_details.confidence_score == 0.91


def test_gemini_quality_failure_supports_multiple_revisions_for_legacy_reports() -> None:
    source = _read("app/gemini_coach.py")

    assert "ReportQualityError" in source
    assert "_audit_with_revisions" in source
    assert "gemini_max_quality_revisions" in _read("app/config.py")
    assert "_is_observer_only_report" in source
    assert "Observation-only output" in _read("app/report_converter.py")


def test_audit_with_revisions_retries_until_pass() -> None:
    report = _minimal_report()
    client = MagicMock()
    audit_side_effects = [
        ReportQualityError("Full-swing report did not cover setup through finish checkpoints."),
        ReportQualityError("Generated report used generic filler language."),
        None,
    ]

    with patch("app.gemini_coach._call_gemini", return_value=report) as call_gemini:
        with patch("app.gemini_coach.audit_report_quality") as audit:
            audit.side_effect = audit_side_effects
            result = _audit_with_revisions(
                client,
                "gemini-2.5-flash",
                [],
                swing_mode="full_swing",
                player_context=None,
                history_summary=None,
                phase_map=None,
                max_revisions=3,
                trace_id=None,
                report_id=None,
                user_id=None,
            )

    assert result is report
    assert call_gemini.call_count == 3
    assert audit.call_count == 3


def test_call_gemini_preserves_raw_response_before_conversion() -> None:
    raw_text = _gemini_out_json = """
    {
      "greeting": "Bill, good balance and a clear priority.",
      "analysis": "Quick coach verdict\\n\\nI would rate this swing 6.5/10 overall. Full coach-style analysis\\n\\nThe swing has enough detail to coach. Main swing fault\\n\\nThe path steepens in transition. Secondary swing fault\\n\\nThe head lowers slightly. What you do well\\n\\nBalance is useful. Setup/grip notes\\n\\nGrip is partly hidden. Swing path notes\\n\\nThe club works left. Head movement notes\\n\\nSmall dip. Arm/hand structure\\n\\nLead arm softens. Impact-window notes\\n\\nImpact is estimated. Drill\\n\\nPump reps. Feel\\n\\nHands drop. Practice plan\\n\\nUse half-speed reps. Confidence/visibility limitations\\n\\nFace angle is limited by camera.",
      "main_fix": "Let the arms fall before turning hard through impact.",
      "tips": ["Feel the hands drop first.", "Keep the head level."],
      "drill1": "Pump drill|Trains the slot|Make 15 pump reps, then hit 10 half-speed balls.",
      "next_check": "Film down the line.",
      "mode": "development",
      "missing": "Steep transition path.",
      "profile": "",
      "checkpoints": ["Setup: posture | optimal | Balanced.", "Takeaway: hand path | compensation | Slight inside roll.", "Backswing: width | compensation | Lead arm softens.", "Transition: sequence | constraint | Hands move out early.", "Downswing: path | constraint | Club steepens.", "Impact: contact | compensation | Timing dependent.", "Finish: balance | optimal | Stable finish."],
      "root": "Hands move out before the body clears.",
      "secondary": "Head lowers slightly in transition.",
      "symptom": "Timing-dependent contact.",
      "evidence": ["Downswing: path steepens", "Head movement: slight dip", "Arm/hand path: lead arm softens", "Impact: estimated contact window"],
      "chain": "Hands move out early, the shaft steepens, and impact needs a late save.",
      "confidence": 0.74,
      "focus": "Transition",
      "day7": "Path shallows on video.",
      "letter_open": "Bill has a stable finish and enough athletic movement to build from. The main issue is the transition getting steep.",
      "letter_headline": "The Steep Transition Save",
      "strength1": "Balanced finish|He holds his finish without falling away.",
      "strength2": "Athletic turn|There is usable body rotation through the ball.",
      "flaw1": "Transition path|The hands work out early and steepen the shaft.",
      "flaw2": "Head level|The head lowers slightly and reduces arm room.",
      "flaw3": "Impact save|Contact depends on late hand timing.",
      "ceiling_now": "Contact remains timing dependent when the club stays steep.",
      "ceiling_unlock": "A shallower transition should make contact and start line more predictable.",
      "fix1": "Drop then turn|Let the hands fall before the chest fires through.",
      "fix2": "Level head|Keep height steadier through transition.",
      "body_cue": "Feel the hands drop first.",
      "space_cue": "Feel the club slot behind you."
    }
    """
    client = MagicMock()
    client.models.generate_content.return_value.text = raw_text
    raw_attempts: list[dict] = []

    _call_gemini(
        client,
        "gemini-2.5-flash",
        [],
        raw_attempts=raw_attempts,
    )

    assert raw_attempts[0]["raw_text"] == raw_text
    assert raw_attempts[0]["parsed_json"]["root"] == "Hands move out before the body clears."
    assert "pga_analysis" in raw_attempts[0]["converted_report"]


def test_apply_narrative_response_replaces_compact_report_with_full_coach_read() -> None:
    report = _minimal_report()
    narrative = {
        "analysis": (
            "Quick coach verdict\n\n"
            "I would rate this swing 7/10 overall: strong enough to play, with a transition priority.\n\n"
            "Full coach-style analysis\n\n"
            + "This is a specific video read with enough detail to feel like a coach watched the whole motion. " * 35
            + "\n\nMain swing fault\n\nThe path steepens because the hands move out before the body clears."
            + "\n\nSecondary swing fault\n\nThe head lowers slightly in transition."
            + "\n\nWhat you do well\n\nThe finish is balanced and the body keeps turning."
            + "\n\nSetup/grip notes\n\nGrip is partially hidden, but posture is readable."
            + "\n\nSwing path notes\n\nThe club works across the ball through the impact window."
            + "\n\nHead movement notes\n\nThere is a small level change before impact."
            + "\n\nArm/hand structure\n\nLead arm width softens near the top."
            + "\n\nImpact-window notes\n\nImpact is estimated from adjacent frames."
            + "\n\nDrill\n\nUse pump reps to rehearse the slot."
            + "\n\nFeel\n\nFeel the hands fall before the chest turns hard."
            + "\n\nPractice plan\n\nStart with rehearsals, then half-speed balls, then film again."
            + "\n\nConfidence/visibility limitations\n\nClubface certainty is limited by camera angle."
        ),
        "main_fix": "Let the hands fall into the slot before the chest turns through.",
        "secondary_fix": "Keep the head height steadier through transition.",
        "tips": ["Feel the hands drop first.", "Feel your head stay level."],
        "drill_name": "Slot pump reps",
        "drill_why": "It trains the downswing sequence without chasing ball flight.",
        "drill_how": "Make 15 slow pump reps, then hit 10 half-speed balls and only count clean slots.",
        "next_check": "Film down the line and check that the club shallows before impact.",
    }

    updated = _apply_narrative_response(report, narrative)

    assert updated.pga_analysis == narrative["analysis"]
    assert len(updated.pga_analysis.split()) > 600
    assert updated.main_fix == narrative["main_fix"]
    assert updated.advanced_details.secondary_fix == narrative["secondary_fix"]
    assert updated.drills[0].name == "Slot pump reps"
    assert updated.next_swing_check == narrative["next_check"]


def test_apply_narrative_response_accepts_section_object_and_removes_filler() -> None:
    report = _minimal_report()
    narrative = {
        "analysis": {
            "Quick coach verdict": "I would rate this swing 6.5/10 overall, with useful balance and a takeaway priority.",
            "Full coach-style analysis": "This swing has a useful athletic base. " * 80,
            "Main swing fault": "The club gets too deep inside going back.",
            "Secondary swing fault": "Setup balance is heels-heavy.",
            "What you do well": "Balanced finish and useful speed.",
            "Setup/grip notes": "Setup is visible; grip is limited.",
            "Swing path notes": "The path works too far from the inside.",
            "Head movement notes": "Head is steady.",
            "Arm/hand structure": "Hands get deep behind the body.",
            "Impact-window notes": "Face closes quickly through impact.",
            "Drill": "Use a takeaway checkpoint.",
            "Feel": "The key feel is keeping the clubhead in front of you.",
            "Practice plan": "Rehearse, hit half-speed balls, film again.",
            "Confidence/visibility limitations": "Grip certainty is limited.",
        },
        "main_fix": "Neutralize the takeaway first.",
        "secondary_fix": "Setup balance.",
        "tips": ["Feel the clubhead stay in front.", "Feel a quiet face."],
        "drill_name": "Takeaway checkpoint",
        "drill_why": "It fixes the first dynamic leak.",
        "drill_how": "Make 15 slow reps and check the clubhead at waist high.",
        "next_check": "Film down the line.",
    }

    updated = _apply_narrative_response(report, narrative)

    assert "Full coach-style analysis" in updated.pga_analysis
    assert "The key feel" not in updated.pga_analysis
    assert "The main feel" in updated.pga_analysis


def test_dynamic_priority_guard_demotes_setup_when_path_face_evidence_is_stronger_action() -> None:
    report = _minimal_report()
    adv = report.advanced_details.model_copy(
        update={
            "foundational_missing_piece": "Athletic setup and balance",
            "root_cause": "Heels-heavy seated posture at address",
            "secondary_fix": "Overly inside takeaway plane",
            "evidence_metrics": [
                "Setup: weight is on heels.",
                "Takeaway: club moves well inside the hands.",
                "Downswing: path is excessively in-to-out.",
                "Impact: face closes rapidly and ball hooks.",
            ],
            "chain_reaction": "Setup encourages inside takeaway, deep top, in-to-out path, and face flip.",
        }
    )
    report = report.model_copy(
        update={
            "main_fix": "Fix posture at address.",
            "advanced_details": adv,
        }
    )

    guarded = _dynamic_priority_guard(report)

    assert "inside takeaway" in guarded.main_fix.lower()
    assert guarded.advanced_details.root_cause == "Overly inside takeaway plane"
    assert "Setup context" in guarded.advanced_details.secondary_fix


def test_call_narrative_gemini_stores_raw_second_pass_separately() -> None:
    report = _minimal_report()
    raw_text = """
    {
      "analysis": "Quick coach verdict\\n\\nI would rate this swing 6.5/10 overall. Full coach-style analysis\\n\\nThis is a long direct coach read. Main swing fault\\n\\nPath. Secondary swing fault\\n\\nHead. What you do well\\n\\nBalance. Setup/grip notes\\n\\nVisible. Swing path notes\\n\\nSteep. Head movement notes\\n\\nSmall dip. Arm/hand structure\\n\\nSoft width. Impact-window notes\\n\\nEstimated. Drill\\n\\nPump. Feel\\n\\nDrop. Practice plan\\n\\nRehearse. Confidence/visibility limitations\\n\\nMedium certainty.",
      "main_fix": "Let the arms fall before turning through.",
      "secondary_fix": "Keep head level.",
      "tips": ["Feel arms fall.", "Feel level head."],
      "drill_name": "Pump drill",
      "drill_why": "Trains the slot.",
      "drill_how": "Make 15 reps, then hit 10 half-speed balls.",
      "next_check": "Film down the line."
    }
    """
    client = MagicMock()
    client.models.generate_content.return_value.text = raw_text
    raw_attempts: list[dict] = []

    updated = _call_narrative_gemini(
        client,
        "gemini-2.5-flash",
        [],
        report,
        raw_attempts=raw_attempts,
    )

    assert updated.main_fix == "Let the arms fall before turning through."
    assert raw_attempts[0]["kind"] == "narrative"
    assert raw_attempts[0]["raw_text"] == raw_text
    assert raw_attempts[0]["parsed_json"]["drill_name"] == "Pump drill"


def test_audit_with_revisions_raises_after_max_attempts() -> None:
    report = _minimal_report()
    client = MagicMock()

    with patch("app.gemini_coach._call_gemini", return_value=report):
        with patch(
            "app.gemini_coach.audit_report_quality",
            side_effect=ReportQualityError("Generated report used generic filler language."),
        ):
            with pytest.raises(ReportQualityError, match="generic filler"):
                _audit_with_revisions(
                    client,
                    "gemini-2.5-flash",
                    [],
                    swing_mode="full_swing",
                    player_context=None,
                    history_summary=None,
                    phase_map=None,
                    max_revisions=2,
                    trace_id=None,
                    report_id=None,
                    user_id=None,
                )


def test_generate_coaching_report_runs_three_call_chain_in_order(tmp_path: Path) -> None:
    from app.gemini_coach import generate_coaching_report
    from app.gemini_report_schema import GeminiReportOut, PhaseGrade, SwingGrades, SwingObservations

    video_path = tmp_path / "swing.mp4"
    video_path.write_bytes(b"fake-video")

    observation = GeminiReportOut(
        video_usability="good",
        camera_angle="face-on",
        usability_note="Clear film",
        observations=SwingObservations(),
    )
    grading = GeminiReportOut(
        grades=SwingGrades(
            transition=PhaseGrade(grade="Constraint", reason="Steep from the top"),
        ),
        report_mode="development",
        foundational_missing_piece="Steep transition",
        secondary_fix="Keep head level through impact",
        miss_pattern_match="high",
        miss_conflict_note="",
        confidence=0.82,
    )
    final_report = _minimal_report()
    call_order: list[str] = []
    call3_parts: list = []

    def track_observation(*_args, **_kwargs):
        call_order.append("call1")
        return observation

    def track_diagnostic(*_args, **_kwargs):
        call_order.append("call2")
        return grading

    def track_audit(_client, _model, content_parts, **_kwargs):
        call_order.append("call3")
        call3_parts.extend(content_parts)
        return final_report

    settings = MagicMock()
    settings.gemini_api_key = "test-key"
    settings.gemini_model = "gemini-2.5-flash"
    settings.gemini_fallback_model = "gemini-2.5-flash"
    settings.gemini_max_quality_revisions = 0

    with patch("app.gemini_coach.get_settings", return_value=settings):
        with patch("app.gemini_coach.genai.Client"):
            with patch("app.gemini_coach.upload_video", return_value=MagicMock(uri="https://example/video", name="files/1", mime_type="video/mp4")):
                with patch("app.gemini_coach.delete_uploaded_file"):
                    with patch("app.gemini_coach._call_observation_gemini", side_effect=track_observation):
                        with patch("app.gemini_coach._call_diagnostic_gemini", side_effect=track_diagnostic):
                            with patch("app.gemini_coach._audit_with_revisions", side_effect=track_audit):
                                report, ai_ok, meta = generate_coaching_report(
                                    video_path=video_path,
                                    frames=None,
                                    phase_result=None,
                                    swing_mode="full_swing",
                                    history_summary="Prior swing 1: steep path.",
                                    player_name="Jordan",
                                    player_age=35,
                                    years_playing=10,
                                    physical_limitations="Bad lower back",
                                )

    assert call_order == ["call1", "call2", "call3"]
    assert ai_ok is True
    assert report.pga_analysis == final_report.pga_analysis or report.main_fix
    assert len(call3_parts) == 2
    call3_text = " ".join(getattr(part, "text", "") or "" for part in call3_parts).lower()
    assert "locked evidence" in call3_text
    assert "forefixed" in call3_text
    assert "jordan" in call3_text
    assert meta["model_used"] == "gemini-2.5-flash"
