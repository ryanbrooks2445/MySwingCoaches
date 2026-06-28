from app.gemini_coach import _apply_phase_limitations
from app.schemas import CoachingReportSchema, DISCLAIMER


def _report() -> CoachingReportSchema:
    return CoachingReportSchema.model_validate(
        {
            "personalized_greeting": "Alek, your balance is a useful base.",
            "pga_analysis": "What's working\nBalanced finish.\n\nSetup to finish\nGood motion.",
            "main_fix": "Keep the club working on a cleaner path.",
            "tips_and_feels": ["Feel the club travel around you.", "Feel steady tempo."],
            "drills": [],
            "next_swing_check": "Film one full swing.",
            "advanced_details": {
                "report_mode": "development",
                "foundational_missing_piece": "Path control",
                "profile_constraints_applied": "",
                "diagnostic_checkpoints": [],
                "root_cause": "Path control",
                "symptom": "Timing-dependent contact",
                "evidence_metrics": [],
                "secondary_fix": "Transition sequence",
                "optional_fix": "",
                "chain_reaction": "Path control changes contact timing.",
                "why_it_caused_the_miss": "Timing changes contact.",
                "confidence_score": 0.75,
                "next_checkpoint": "downswing",
            },
            "blueprint": {
                "headline": "Path",
                "intro": "Train one feel.",
                "steps": [
                    {"title": "Feel", "step_type": "visual_cue", "feel": "Club around you."},
                    {"title": "Film", "step_type": "visual_cue", "feel": "Hold finish."},
                ],
            },
            "roadmap": {
                "weekly_focus": "Path",
                "milestones": [
                    {"days": "Day 1-2", "title": "Reps", "detail": "Slow reps."},
                    {"days": "Day 3-5", "title": "Blend", "detail": "Half swings."},
                    {"days": "Day 6-7", "title": "Film", "detail": "Record it."},
                ],
                "day_7_test": "Path looks cleaner.",
            },
            "next_upload_focus": "Film path",
            "disclaimer": DISCLAIMER,
        }
    )


def test_adds_impact_limitation_for_estimated_impact_window() -> None:
    report = _apply_phase_limitations(
        _report(),
        [{"phase": "impact_window_estimate", "confidence": 0.45, "person_visible": True}],
    )

    assert "impact window is estimated" in report.pga_analysis
