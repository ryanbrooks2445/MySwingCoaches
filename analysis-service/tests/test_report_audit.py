import pytest

from app.report_audit import ReportQualityError, audit_report_quality
from app.schemas import CoachingReportSchema, DISCLAIMER


def _report(**overrides) -> CoachingReportSchema:
    payload = {
        "personalized_greeting": "Alek, your balance gives us a useful base.",
        "pga_analysis": "What's working\nBalanced finish.\n\nSetup to finish\nYour setup creates the first compensation.\n\nThe missing piece\nCenter pressure at address.\n\nWhat changes when you unlock it\nMore room through impact.",
        "main_fix": "Start with pressure under your laces so your hips can stay back through impact.",
        "tips_and_feels": ["Feel pressure under your laces.", "Keep your belt line back."],
        "drills": [
            {
                "name": "Setup checkpoint",
                "why_it_helps": "It establishes centered pressure before motion.",
                "how_to_do_it": "Rehearse ten setups, then hit ten half-speed shots.",
            }
        ],
        "next_swing_check": "Film face-on and confirm centered pressure at address.",
        "advanced_details": {
            "report_mode": "development",
            "foundational_missing_piece": "Pressure begins too far toward the heels.",
            "profile_constraints_applied": "",
            "diagnostic_checkpoints": [
                {"checkpoint": "Address", "grade": "constraint", "observation": "Pressure favors heels."},
                {"checkpoint": "Downswing", "grade": "compensation", "observation": "Hips move toward the ball."},
                {"checkpoint": "Impact", "grade": "compensation", "observation": "Posture rises before contact."},
            ],
            "root_cause": "Pressure starts too far toward the heels.",
            "symptom": "Contact depends on timing.",
            "evidence_metrics": ["Address: pressure favors heels", "Impact: posture rises"],
            "secondary_fix": "",
            "optional_fix": "",
            "chain_reaction": "Heel pressure leads to hip movement toward the ball and reduced space.",
            "why_it_caused_the_miss": "The body has to create room late.",
            "confidence_score": 0.75,
            "next_checkpoint": "address",
        },
        "blueprint": {
            "headline": "Center Pressure",
            "intro": "Change the starting boundary.",
            "steps": [
                {"title": "Set pressure", "step_type": "setup", "feel": "Pressure under laces."},
                {"title": "Hold posture", "step_type": "visual_cue", "feel": "Belt line stays back."},
            ],
        },
        "roadmap": {
            "weekly_focus": "Setup",
            "milestones": [
                {"days": "Day 1-2", "title": "Rehearse", "detail": "Ten setup reps."},
                {"days": "Day 3-5", "title": "Blend", "detail": "Hit half-speed shots."},
                {"days": "Day 6-7", "title": "Test", "detail": "Film the change."},
            ],
            "day_7_test": "Pressure begins centered.",
        },
        "next_upload_focus": "Centered address pressure",
        "disclaimer": DISCLAIMER,
    }
    payload.update(overrides)
    return CoachingReportSchema.model_validate(payload)


def test_rejects_unsupported_handicap_prediction() -> None:
    report = _report(pga_analysis="This pattern has the mechanics of a scratch golfer.")

    with pytest.raises(ReportQualityError, match="unsupported scoring or handicap"):
        audit_report_quality(report, swing_mode="full_swing", player_context="Average 9-hole score: 58.")


def test_accepts_specific_evidence_led_development_report() -> None:
    audit_report_quality(
        _report(),
        swing_mode="full_swing",
        player_context="Average 9-hole score: 58. Typical miss: thin.",
    )
