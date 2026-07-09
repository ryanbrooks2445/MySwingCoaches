from app.gemini_report_schema import (
    GeminiReportOut,
    PhaseGrade,
    PhaseObservation,
    SwingGrades,
    SwingObservations,
)
from app.report_converter import apply_film_first_report, gemini_out_to_coaching_report, parse_gemini_json
from app.schemas import CoachingReportSchema


def _gemini_out(**overrides) -> GeminiReportOut:
    payload = {
        "greeting": "Bill, your rotation gives us a real base to build on.",
        "analysis": (
            "What's working\nStrong lower body and balanced finish.\n\n"
            "Setup to finish\nSetup sits too low, takeaway rolls inside, downswing rescues late.\n\n"
            "The missing piece\nStand taller and hinge from the hips.\n\n"
            "What changes when you unlock it\nCleaner path and more predictable contact."
        ),
        "main_fix": "Stand taller at address and hinge from the hips so the arms hang naturally.",
        "tips": ["Feel pressure under the laces.", "Keep the clubhead outside your hands early."],
        "drill1": "Setup mirror|Trains taller posture|10 rehearsal setups, then half-speed shots.",
        "next_check": "Film face-on and confirm taller setup.",
        "mode": "development",
        "missing": "Squatty setup on the heels at address.",
        "profile": "",
        "checkpoints": [
            "Setup: posture | constraint | Sits back on heels.",
            "Takeaway: hand path | constraint | Wrists roll open inside.",
            "Backswing: width | compensation | Some width remains.",
            "Transition: sequencing | constraint | Hands fire early.",
            "Downswing: swing path | constraint | Club works out and across.",
            "Impact: contact | compensation | Hands save it late.",
            "Finish: balance | optimal | Held in balance.",
        ],
        "root": "Setup posture steals room to swing.",
        "secondary": "Keep the head quieter through transition.",
        "symptom": "Timing-dependent contact.",
        "evidence": [
            "Setup: posture sits low",
            "Takeaway: club whips inside",
            "Head movement: fairly stable",
            "Downswing: path gets steep",
            "Impact: depends on hand save",
            "Finish: balanced",
        ],
        "chain": "Low setup forces inside takeaway and a late rescue through impact.",
        "confidence": 0.78,
        "focus": "Setup",
        "day7": "Taller setup holds on video.",
        "letter_open": (
            "Bill shows real athletic intent. His hips work, but a squatty setup forces a handsy rescue mission."
        ),
        "letter_headline": "The Sitting Stance Loop",
        "strength1": "Excellent lower body action|He clears his lead hip aggressively instead of standing and flipping.",
        "strength2": "Balanced finish|He rotates through and holds a stable finish on his lead side.",
        "flaw1": "The setup: sitting stance|He sits back on his heels and robs himself of room to swing.",
        "flaw2": "Inside wrist-roll takeaway|The first move rolls the face open and lifts the club inside.",
        "flaw3": "Downswing over-correction|He throws the club out to recover, which needs perfect timing.",
        "ceiling_now": "If this stays, he likely lives in a 14 to 18 handicap range with timing-dependent misses.",
        "ceiling_unlock": "Fixing setup could realistically unlock 9 to 11 handicap golf with his current rotation.",
        "fix1": "Stand up and tilt|Unlock the knees, stand taller, and hinge from the hips.",
        "fix2": "Toe up, not rolled open|Keep the clubhead outside the hands until parallel to the ground.",
        "body_cue": "Feel pressure under the balls of your feet.",
        "space_cue": "Keep the clubhead outside your hands on the way back.",
    }
    payload.update(overrides)
    return GeminiReportOut.model_validate(payload)


def test_converts_observer_json_without_coaching_language() -> None:
    raw = """
    {
      "observations": {
        "setup": { "club": "Club rests behind the ball.", "body": "Feet are set with knees flexed.", "not_visible": "Grip detail is partly hidden." },
        "takeaway": { "club": "Club moves away from the ball.", "body": "Shoulders begin to turn.", "not_visible": "Clubface angle is unclear." },
        "backswing": { "club": "Club rises above shoulder height.", "body": "Torso turns away from the target.", "not_visible": "Lead wrist detail is unclear." },
        "transition": { "club": "Club changes direction near the top.", "body": "Lower body begins moving toward the target.", "not_visible": "Pressure shift is not directly visible." },
        "downswing": { "club": "Club travels downward toward the ball.", "body": "Hips and torso rotate toward the target.", "not_visible": "Shaft angle is partly blurred." },
        "impact": { "club": "Club passes through the ball area.", "body": "Head and torso remain in frame.", "not_visible": "Exact strike location is not visible." },
        "finish": { "club": "Club wraps around the body.", "body": "Body rotates to face the target.", "not_visible": "Ball flight is not visible." }
      },
      "camera_angle": "down-the-line",
      "video_usability": "acceptable",
      "usability_note": "Full body and club are mostly visible, with some blur around impact."
    }
    """

    report = gemini_out_to_coaching_report(parse_gemini_json(raw))

    assert '"camera_angle": "down-the-line"' in report.pga_analysis
    assert '"setup"' in report.pga_analysis
    assert report.advanced_details.root_cause == "Observation-only output"
    assert report.drills == []


def test_converts_observer_json_with_diagnostic_grades() -> None:
    raw = """
    {
      "observations": {
        "setup": { "club": "Club rests behind the ball.", "body": "Feet are set with knees flexed.", "not_visible": "Grip detail is partly hidden." },
        "takeaway": { "club": "Club moves inside the hands.", "body": "Shoulders begin to turn.", "not_visible": "Clubface angle is unclear." },
        "backswing": { "club": "Club rises above shoulder height.", "body": "Torso turns away from the target.", "not_visible": "Lead wrist detail is unclear." },
        "transition": { "club": "Club changes direction near the top.", "body": "Lower body begins moving toward the target.", "not_visible": "Pressure shift is not directly visible." },
        "downswing": { "club": "Club travels across the ball area.", "body": "Hips and torso rotate toward the target.", "not_visible": "Shaft angle is partly blurred." },
        "impact": { "club": "Club passes through the ball area.", "body": "Head and torso remain in frame.", "not_visible": "Exact strike location is not visible." },
        "finish": { "club": "Club wraps around the body.", "body": "Body rotates to face the target.", "not_visible": "Ball flight is not visible." }
      },
      "camera_angle": "down-the-line",
      "video_usability": "acceptable",
      "usability_note": "Full body and club are mostly visible.",
      "grades": {
        "setup": { "grade": "Optimal", "reason": "Setup observation does not show a visible inefficiency." },
        "takeaway": { "grade": "Constraint", "reason": "The inside takeaway appears before later across-path motion." },
        "backswing": { "grade": "Compensating", "reason": "Top position follows the inside takeaway." },
        "transition": { "grade": "Compensating", "reason": "Direction change follows the earlier club position." },
        "downswing": { "grade": "Compensating", "reason": "Across-path motion is visible downstream." },
        "impact": { "grade": "Not Visible", "reason": "Exact strike location is not visible." },
        "finish": { "grade": "Optimal", "reason": "Finish remains visible and balanced." }
      },
      "report_mode": "development",
      "foundational_missing_piece": "Inside takeaway",
      "secondary_fix": "Transition direction",
      "miss_pattern_match": "medium",
      "miss_conflict_note": "The grade partially matches the stated miss.",
      "confidence": 0.66
    }
    """

    report = gemini_out_to_coaching_report(parse_gemini_json(raw))

    assert '"diagnostic"' in report.pga_analysis
    assert report.advanced_details.report_mode == "development"
    assert report.advanced_details.foundational_missing_piece == "Inside takeaway"
    assert report.advanced_details.secondary_fix == "Transition direction"
    assert report.advanced_details.confidence_score == 0.66
    assert report.advanced_details.diagnostic_checkpoints[1].grade == "constraint"


def test_rating_calibration_pulls_down_generous_score_for_many_flaws() -> None:
    report = gemini_out_to_coaching_report(
        _gemini_out(
            rating="7/10 overall",
            categories=["Power: 8/10", "Contact consistency: 5/10", "Balance: 6/10"],
            checkpoints=[
                "Setup: posture | constraint | Sits back on heels.",
                "Takeaway: hand path | constraint | Wrists roll open inside.",
                "Backswing: width | compensation | Some width remains.",
                "Transition: sequencing | constraint | Hands fire early.",
                "Downswing: swing path | constraint | Club works out and across.",
                "Impact: contact | compensation | Hands save it late.",
                "Finish: balance | optimal | Held in balance.",
            ],
        )
    )

    assert report.coach_verdict is not None
    score = float(report.coach_verdict.overall_rating.split("/")[0])
    assert score <= 5.5


def test_rating_calibration_leaves_solid_swing_near_model_score() -> None:
    report = gemini_out_to_coaching_report(
        _gemini_out(
            rating="7/10 overall",
            categories=["Power: 7/10", "Tempo: 7.5/10"],
            checkpoints=[
                "Setup: posture | optimal | Balanced.",
                "Takeaway: hand path | compensation | Slight inside roll.",
                "Backswing: width | optimal | Good width.",
                "Transition: sequencing | compensation | Slightly early hands.",
                "Downswing: swing path | optimal | Shallow enough.",
                "Impact: contact | optimal | Solid strike window.",
                "Finish: balance | optimal | Held in balance.",
            ],
            flaw2="",
            flaw3="",
        )
    )

    assert report.coach_verdict is not None
    score = float(report.coach_verdict.overall_rating.split("/")[0])
    assert score >= 6.5


def test_builds_coach_verdict_with_rating_and_categories() -> None:
    report = gemini_out_to_coaching_report(
        _gemini_out(
            rating="7.5/10 overall",
            categories=[
                "Power: 8.5/10",
                "Sequence/timing: 7/10",
                "Consistency potential: 6.5/10",
            ],
        )
    )

    assert report.coach_verdict is not None
    assert report.coach_verdict.overall_rating
    assert report.coach_verdict.biggest_positive
    assert report.coach_verdict.main_issue
    assert report.coach_verdict.best_fix
    assert len(report.coach_verdict.category_ratings) == 3
    assert report.coach_verdict.category_ratings[0].label == "Power"
    assert "8.5" in report.coach_verdict.category_ratings[0].rating


def test_builds_feel_blueprint_from_coach_letter_fields() -> None:
    report = gemini_out_to_coaching_report(_gemini_out())

    assert report.feel_blueprint is not None
    assert report.feel_blueprint.headline == "The Sitting Stance Loop"
    assert len(report.feel_blueprint.strengths) == 2
    assert len(report.feel_blueprint.flaws) == 3
    assert len(report.feel_blueprint.pro_fixes) == 2
    assert "14 to 18" in report.feel_blueprint.current_ceiling
    assert "Stand up and tilt" in report.feel_blueprint.pro_fixes[0].title


def test_compact_report_uses_gemini_style_chain_and_complete_cues() -> None:
    report = gemini_out_to_coaching_report(
        _gemini_out(
            flaw1=(
                "The Shift: driver posture|With the longer club, his weight sags deeper into his knees "
                "and shifts back toward his heels."
            ),
            flaw2=(
                "The Consequence: hand height|Because the hip turn stops early, the hands lift more "
                "vertically and the shaft gets steeper at the top."
            ),
            fix1=(
                "Bring iron posture to the tee box|The Remedy: stand a fraction taller, hook pressure "
                "into the balls of the feet, and turn the chest deep instead of lifting the arms."
            ),
            body_cue=(
                "Feel your driver setup match your iron posture: taller legs, pressure mid-foot, "
                "and chest turning deep around you."
            ),
        )
    )

    assert report.feel_blueprint is not None
    assert "The Shift: driver posture" in report.feel_blueprint.flaws[0].title
    assert "The Consequence: hand height" in report.feel_blueprint.flaws[1].title
    assert "Bring iron posture to the tee box" in report.feel_blueprint.pro_fixes[0].title
    assert report.feel_blueprint.body_part_cue.startswith("Feel your driver setup")


def test_deep_gemini_analysis_is_not_shortened_or_rewritten() -> None:
    deep_analysis = (
        "Full coach-style analysis\n\n"
        + "This swing shows a useful athletic base, but the priority is in the transition. " * 20
        + "\n\nMain swing fault\n\nThe downswing path steepens when the hands work out before the body clears. "
        + "\n\nSecondary swing fault\n\nThe head lowers slightly through transition, which narrows room for the arms. "
        + "\n\nSetup/grip notes\n\nGrip is partly blocked, so setup certainty is medium. "
        + "\n\nSwing path notes\n\nThe club exits left after impact. "
        + "\n\nHead movement notes\n\nThere is a small dip before impact. "
        + "\n\nArm/hand structure\n\nLead arm width softens near the top. "
        + "\n\nImpact-window notes\n\nImpact is estimated from the adjacent frames. "
        + "\n\nPractice plan\n\nTrain half-speed transition reps for one week. "
        + "\n\nConfidence/visibility limitations\n\nCamera angle limits clubface certainty."
    )

    report = gemini_out_to_coaching_report(_gemini_out(analysis=deep_analysis))

    assert report.pga_analysis == deep_analysis
    assert "Confidence/visibility limitations" in report.pga_analysis
    assert len(report.pga_analysis.split()) > 180


def test_short_drill_is_passed_through_from_gemini() -> None:
    report = gemini_out_to_coaching_report(
        _gemini_out(
            drill1="Setup Posture Check|Build a better hip hinge|Place a club across your hips.",
        )
    )

    assert report.drills[0].name == "Setup Posture Check"
    assert report.drills[0].why_it_helps == "Build a better hip hinge"
    assert report.drills[0].how_to_do_it == "Place a club across your hips."


def test_colon_checkpoint_format_preserves_constraint_grades() -> None:
    report = gemini_out_to_coaching_report(
        _gemini_out(
            checkpoints=[
                "Setup: Constraint",
                "Transition: Compensation: Shoulders start first",
                "Finish: Optimal",
            ],
        )
    )

    grades = [item.grade for item in report.advanced_details.diagnostic_checkpoints[:3]]
    assert grades == ["constraint", "compensation", "optimal"]
    assert report.advanced_details.diagnostic_checkpoints[1].observation == "Shoulders start first"


def test_apply_film_first_report_elaborates_call1_observations() -> None:
    observation = GeminiReportOut(
        video_usability="good",
        camera_angle="face-on",
        observations=SwingObservations(
            setup=PhaseObservation(club="Square at address.", body="Weight on heels.", not_visible=""),
            backswing=PhaseObservation(club="Club gets deep.", body="Lead arm bends sharply.", not_visible=""),
        ),
    )
    grading = GeminiReportOut(
        grades=SwingGrades(
            setup=PhaseGrade(grade="Constraint", reason="Heels-heavy posture"),
            backswing=PhaseGrade(grade="Constraint", reason="Lead arm collapse"),
        ),
        report_mode="development",
        foundational_missing_piece="Lead arm collapse at the top",
        secondary_fix="Heels-heavy setup",
        confidence=0.8,
    )
    base = gemini_out_to_coaching_report(
        GeminiReportOut(
            greeting="Test",
            analysis="Generic invented analysis that should be replaced.",
            main_fix="Generic fix",
            tips=["tip"],
            next_check="Film again",
            mode="development",
            missing="issue",
            checkpoints=[],
            root="issue",
            secondary="",
            symptom="",
            evidence=["made up"],
            chain="",
            confidence=0.8,
            focus="",
            day7="",
            letter_open="",
            letter_headline="",
            strength1="",
            strength2="",
            flaw1="",
            flaw2="",
            flaw3="",
            ceiling_now="",
            ceiling_unlock="",
            fix1="",
            fix2="",
            body_cue="",
            space_cue="",
        )
    )
    updated = apply_film_first_report(base, observation, grading)

    assert "Lead arm bends sharply" in updated.pga_analysis
    assert "Weight on heels" in updated.pga_analysis
    assert "Setup to finish" in updated.pga_analysis
    assert updated.feel_blueprint is None
    assert any("lead arm" in item.lower() for item in updated.advanced_details.evidence_metrics)
    assert "Generic invented analysis" not in updated.pga_analysis


def test_apply_film_first_report_uses_call3_evidence_when_observations_sparse() -> None:
    observation = GeminiReportOut(
        video_usability="good",
        observations=SwingObservations(),
    )
    grading = GeminiReportOut(
        grades=SwingGrades(
            setup=PhaseGrade(grade="Constraint", reason="Heels-heavy posture"),
            backswing=PhaseGrade(grade="Constraint", reason="Lead arm collapse"),
            transition=PhaseGrade(grade="Compensating", reason="Shoulders fire first"),
        ),
        report_mode="development",
        foundational_missing_piece="Athletic setup and hip hinge at address",
        secondary_fix="Keep weight centered",
        confidence=0.75,
    )
    base = gemini_out_to_coaching_report(
        GeminiReportOut(
            greeting="Alek, strong commitment.",
            analysis=(
                "What's working\nGood speed.\n\n"
                "Setup to finish\nGeneric template.\n\n"
                "The missing piece\nSetup only.\n\n"
                "What changes when you unlock it\nMore power."
            ),
            main_fix="Let's focus on your setup and hinge from your hips.",
            tips=["Feel weight in the middle of your feet."],
            next_check="Film face-on.",
            mode="development",
            missing="Setup",
            checkpoints=[],
            root="Setup",
            secondary="",
            symptom="",
            evidence=[
                "Rounded upper back (C-posture) at address.",
                "Weight appears settled on heels.",
                "Visible bend in the lead arm at the top of the backswing.",
                "Shoulders and arms start the downswing.",
                "Loss of spine angle through impact.",
            ],
            chain="",
            confidence=0.75,
            focus="",
            day7="",
            letter_open="",
            letter_headline="",
            strength1="",
            strength2="",
            flaw1="",
            flaw2="",
            flaw3="",
            ceiling_now="",
            ceiling_unlock="",
            fix1="",
            fix2="",
            body_cue="",
            space_cue="",
        )
    )
    updated = apply_film_first_report(base, observation, grading)

    analysis = updated.pga_analysis.lower()
    assert "the missing piece" not in analysis
    assert "what's working" not in analysis
    assert "lead arm" in analysis
    assert "setup to finish" in analysis
    assert "lead arm extended" in updated.main_fix.lower()
    assert "heel" in updated.advanced_details.secondary_fix.lower()
    assert len(updated.advanced_details.evidence_metrics) >= 5


def test_filters_not_visible_evidence_and_phase_map() -> None:
    from app.report_converter import (
        _filter_visible_checkpoints,
        _filter_visible_evidence,
        filter_phase_map,
    )
    from app.schemas import DiagnosticCheckpointGrade

    assert _filter_visible_evidence(
        [
            "address: Not visible",
            "top: not visible",
            "Lead arm bent at the top.",
        ]
    ) == ["Lead arm bent at the top."]

    checkpoints = _filter_visible_checkpoints(
        [
            DiagnosticCheckpointGrade(
                checkpoint="Setup",
                grade="not_visible",
                observation="Not visible",
            ),
            DiagnosticCheckpointGrade(
                checkpoint="Finish",
                grade="optimal",
                observation="Held in balance.",
            ),
        ]
    )
    assert len(checkpoints) == 1
    assert checkpoints[0].checkpoint == "Finish"

    assert filter_phase_map(
        [
            {"phase": "address", "confidence": 0.1, "person_visible": True},
            {"phase": "top", "confidence": 0.8, "person_visible": True},
            {"phase": "impact", "confidence": 0.9, "person_visible": False},
        ]
    ) == [{"phase": "top", "confidence": 0.8, "person_visible": True}]


def test_builds_priority_fixes_from_pri_fields() -> None:
    report = gemini_out_to_coaching_report(
        _gemini_out(
            pri1=(
                "1|Setup|Athletic spine angle|Rounded upper spine at address|"
                "Root cause on film|Feel sternum over belt;;Push chest toward ball|"
                "Room to turn without lifting head|Wall posture|Trains neutral spine|10 reps"
            ),
            pri2=(
                "2|Takeaway|Club in front of hands|Clubhead outside hands with closed face|"
                "Steepens backswing|Feel hands under sternum;;Toe stays outside hands|"
                "Clubhead in front of trail shoulder|Headcover drill|Stops roll-open takeaway|10 half swings"
            ),
            pri3=(
                "3|Backswing|Turn without standing up|Spine straightens and head lifts|"
                "Compensation for setup limit|Feel belt buckle turning;;Head stays level|"
                "Club points at target line at top"
            ),
        )
    )

    assert len(report.priority_fixes) == 3
    assert report.priority_fixes[0].rank == 1
    assert report.priority_fixes[0].phase == "Setup"
    assert len(report.priority_fixes[0].body_feels) == 2
    assert len(report.priority_fixes[0].space_feels) >= 1
    assert report.priority_fixes[0].drill is not None
    assert report.priority_fixes[0].drill.name == "Wall posture"
    assert "Athletic spine angle" in report.main_fix


def test_fallback_priority_fixes_from_flaws_when_pri_missing() -> None:
    report = gemini_out_to_coaching_report(_gemini_out())

    assert len(report.priority_fixes) >= 2
    assert report.priority_fixes[0].rank == 1
    assert report.priority_fixes[0].body_feels
    assert report.priority_fixes[0].space_feels
    assert "sitting stance" in report.priority_fixes[0].title.lower()
