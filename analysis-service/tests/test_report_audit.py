import pytest

from app.report_audit import ReportQualityError, audit_report_quality
from app.schemas import AnalysisBullet, CoachingReportSchema, DISCLAIMER, FeelBlueprintDiagnostic, ProFix


def _coach_letter() -> FeelBlueprintDiagnostic:
    return FeelBlueprintDiagnostic(
        opening_narrative=(
            "Bill shows real athletic intent on film. His lower body works, but a squatty setup "
            "forces a handsy rescue mission through impact."
        ),
        headline="The Sitting Stance Loop",
        strengths=[
            AnalysisBullet(
                title="Excellent lower body action",
                detail="He clears his lead hip aggressively on the downswing instead of standing and flipping.",
            ),
            AnalysisBullet(
                title="Balanced finish",
                detail="He rotates through and holds a stable finish on his lead side.",
            ),
        ],
        flaws=[
            AnalysisBullet(
                title="The setup: sitting stance",
                detail="At address he sits back on his heels, which steals room to swing the club back naturally.",
            ),
            AnalysisBullet(
                title="Inside wrist-roll takeaway",
                detail="The first move rolls the face open and whips the club severely inside the line.",
            ),
            AnalysisBullet(
                title="Downswing over-correction",
                detail="He lifts and throws the club out to recover, which needs perfect timing to save impact.",
            ),
        ],
        current_ceiling=(
            "If this pattern stays, he likely lives in a 14 to 18 handicap range with timing-dependent "
            "push-slice or heavy contact when the hands do not save it."
        ),
        potential_ceiling=(
            "Because his rotation is already strong, fixing setup could realistically unlock 9 to 11 "
            "handicap golf without rebuilding the whole swing."
        ),
        pro_fixes=[
            ProFix(
                title="Stand up and tilt",
                detail="Unlock the knees, stand taller, and hinge from the hips so the arms hang under the shoulders.",
            ),
            ProFix(
                title="Toe up, not rolled open",
                detail="Keep the clubhead outside the hands until the shaft is parallel to the ground.",
            ),
        ],
        body_part_cue="Feel pressure under the balls of your feet, not your heels.",
        spatial_cue="Let the clubhead stay outside your hands on the way back.",
    )


def _report(**overrides) -> CoachingReportSchema:
    payload = {
        "personalized_greeting": "Alek, your balance gives us a useful base.",
        "pga_analysis": "What's working\nBalanced finish and steady tempo.\n\nSetup to finish\nSetup pressure starts centered. Takeaway stays connected, but the downswing path gets steep into impact.\n\nThe missing piece\nShallow the downswing path.\n\nWhat changes when you unlock it\nCleaner contact and a more predictable start line.",
        "main_fix": "Let the hands fall before you turn hard so the club can approach from a shallower path.",
        "tips_and_feels": ["Feel the hands drop first.", "Turn through after the club slots."],
        "drills": [
            {
                "name": "Pump to slot",
                "why_it_helps": "It trains the club to approach from a shallower path.",
                "how_to_do_it": "Pump down twice, then swing through at half speed.",
            }
        ],
        "next_swing_check": "Film face-on and confirm centered pressure at address.",
        "advanced_details": {
            "report_mode": "development",
            "foundational_missing_piece": "Steep downswing path from arms firing before the club slots.",
            "profile_constraints_applied": "",
            "diagnostic_checkpoints": [
                {"checkpoint": "Setup: grip and posture", "grade": "optimal", "observation": "Athletic balance and usable distance from ball."},
                {"checkpoint": "Takeaway: hand path", "grade": "optimal", "observation": "Hands stay connected early."},
                {"checkpoint": "Backswing/top: lead arm", "grade": "compensation", "observation": "Lead arm keeps enough width, slight softening at top."},
                {"checkpoint": "Transition: sequencing", "grade": "constraint", "observation": "Arms start down before lower body creates room."},
                {"checkpoint": "Downswing: swing path", "grade": "constraint", "observation": "Club approaches steep and slightly across the ball."},
                {"checkpoint": "Impact: clubface", "grade": "compensation", "observation": "Clubface looks managed late relative to the path."},
                {"checkpoint": "Finish: balance", "grade": "optimal", "observation": "Finish is held in balance."},
            ],
            "root_cause": "Arms fire before the club shallows in transition.",
            "symptom": "Contact depends on timing.",
            "evidence_metrics": [
                "Setup: grip/posture look playable from this angle",
                "Takeaway: hand path stays connected",
                "Head movement: head stays fairly stable until transition",
                "Arm/hand path: hands move out toward the ball in transition",
                "Downswing: swing path gets steep into impact",
                "Clubface: face appears managed late against the path",
                "Impact: low point depends on timing",
                "Finish: balanced finish",
            ],
            "secondary_fix": "Keep the head quieter through the change of direction.",
            "optional_fix": "",
            "chain_reaction": "Arms fire early, the club stays steep, and the face has to be saved late through impact.",
            "why_it_caused_the_miss": "The club reaches the ball from a sharper angle, so contact and start line rely on timing.",
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
            "weekly_focus": "Path",
            "milestones": [
                {"days": "Day 1-2", "title": "Rehearse", "detail": "Ten setup reps."},
                {"days": "Day 3-5", "title": "Blend", "detail": "Hit half-speed shots."},
                {"days": "Day 6-7", "title": "Test", "detail": "Film the change."},
            ],
            "day_7_test": "Pressure begins centered.",
        },
        "next_upload_focus": "Shallower transition path",
        "disclaimer": DISCLAIMER,
        "feel_blueprint": _coach_letter(),
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


def test_rejects_full_swing_report_without_complete_checkpoint_coverage() -> None:
    report = _report(
        advanced_details={
            **_report().advanced_details.model_dump(),
            "diagnostic_checkpoints": [
                {"checkpoint": "Setup", "grade": "constraint", "observation": "Posture is low."},
                {"checkpoint": "Impact", "grade": "compensation", "observation": "Posture rises."},
                {"checkpoint": "Finish", "grade": "optimal", "observation": "Balanced finish."},
            ],
            "evidence_metrics": ["Setup: posture is low", "Impact: posture rises"],
        }
    )

    with pytest.raises(ReportQualityError, match="setup through finish"):
        audit_report_quality(report, swing_mode="full_swing")


def test_rejects_posture_primary_without_decisive_multi_category_evidence() -> None:
    base = _report().model_dump()
    base["main_fix"] = "Start with taller posture so the swing has more room."
    base["advanced_details"]["foundational_missing_piece"] = "Posture is too seated at setup."
    base["advanced_details"]["root_cause"] = "Setup posture is too seated."
    base["advanced_details"]["chain_reaction"] = "Seated setup changes space and can force late compensations."
    base["advanced_details"]["evidence_metrics"] = [
        "Setup: posture looks seated",
        "Impact: posture rises",
        "Finish: balanced finish",
        "Takeaway: hard to judge",
    ]
    report = CoachingReportSchema.model_validate(base)

    with pytest.raises(ReportQualityError, match="Posture/setup was chosen"):
        audit_report_quality(report, swing_mode="full_swing")


def test_rejects_repeated_setup_diagnosis_without_strong_fresh_evidence() -> None:
    base = _report().model_dump()
    base["main_fix"] = "Start with taller posture so the swing has more room."
    base["advanced_details"]["foundational_missing_piece"] = "Setup posture limits space."
    base["advanced_details"]["root_cause"] = "Setup posture limits space."
    base["advanced_details"]["chain_reaction"] = "Setup posture limits space and creates compensations through impact."
    base["advanced_details"]["evidence_metrics"] = [
        "Setup: posture looks seated",
        "Address: distance from ball looks crowded",
        "Takeaway: hand path is visible",
        "Backswing: lead arm is visible",
        "Transition: sequencing is visible",
        "Downswing: swing path is visible",
        "Impact: clubface is visible",
        "Finish: balanced finish",
    ]
    report = CoachingReportSchema.model_validate(base)

    with pytest.raises(ReportQualityError, match="Repeated setup/posture"):
        audit_report_quality(
            report,
            swing_mode="full_swing",
            history_summary="Prior swing 1: main priority: seated setup posture. Evidence: setup posture was seated.",
        )


def test_rejects_full_swing_report_without_secondary_flaw() -> None:
    base = _report().model_dump()
    base["advanced_details"]["secondary_fix"] = ""
    report = CoachingReportSchema.model_validate(base)

    with pytest.raises(ReportQualityError, match="secondary flaw"):
        audit_report_quality(report, swing_mode="full_swing")


def test_rejects_generic_filler_language() -> None:
    report = _report(main_fix="The key is to keep doing one athletic feel through the ball.")

    with pytest.raises(ReportQualityError, match="generic filler"):
        audit_report_quality(report, swing_mode="full_swing")


def test_rejects_finish_praise_without_visible_finish_phase() -> None:
    report = _report()
    phase_map = [
        {"phase": "address", "frame_index": 0, "confidence": 0.8, "person_visible": True},
        {"phase": "finish", "frame_index": 10, "confidence": 0.2, "person_visible": False},
    ]
    with pytest.raises(ReportQualityError, match="without visible person"):
        audit_report_quality(report, swing_mode="full_swing", phase_map=phase_map)


def test_requires_impact_limitation_when_low_confidence() -> None:
    report = _report()
    report.pga_analysis = (
        "What's working\nBalanced finish.\n\nSetup to finish\nSteep downswing path.\n\n"
        "The missing piece\nShallow the path.\n\nWhat changes when you unlock it\nCleaner contact."
    )
    phase_map = [
        {
            "phase": "impact_window_estimate",
            "frame_index": 5,
            "confidence": 0.3,
            "person_visible": True,
        },
    ]
    with pytest.raises(ReportQualityError, match="limitation language"):
        audit_report_quality(report, swing_mode="full_swing", phase_map=phase_map)

    report.pga_analysis += "\n\nCamera note: the impact window is estimated, so contact feedback is limited."
    audit_report_quality(report, swing_mode="full_swing", phase_map=phase_map)


def test_rejects_duplicate_secondary_fix() -> None:
    report = _report()
    missing = report.advanced_details.foundational_missing_piece
    report.advanced_details.secondary_fix = missing
    with pytest.raises(ReportQualityError, match="Secondary fix duplicated"):
        audit_report_quality(report, swing_mode="full_swing")


def test_accepts_checkpoint_prefix_coverage_with_minimal_observation_keywords() -> None:
    report = _report(
        advanced_details={
            **_report().advanced_details.model_dump(),
            "diagnostic_checkpoints": [
                {"checkpoint": "Setup: posture", "grade": "optimal", "observation": "Athletic balance."},
                {"checkpoint": "Takeaway: path", "grade": "optimal", "observation": "Connected early."},
                {"checkpoint": "Backswing: width", "grade": "compensation", "observation": "Slight softening."},
                {"checkpoint": "Transition: timing", "grade": "constraint", "observation": "Arms lead."},
                {"checkpoint": "Downswing: plane", "grade": "constraint", "observation": "Steep approach."},
                {"checkpoint": "Impact: window", "grade": "compensation", "observation": "Managed late."},
                {"checkpoint": "Finish: hold", "grade": "optimal", "observation": "Held in balance."},
            ],
            "evidence_metrics": [
                "Setup: posture looks playable",
                "Takeaway: hand path stays connected",
                "Head movement: head stays fairly stable until change of direction",
                "Arm/hand path: hands move out toward the ball",
                "Downswing: club approaches steep",
                "Clubface: face appears managed late",
                "Impact: low point depends on timing",
                "Finish: balanced finish",
            ],
        }
    )
    audit_report_quality(report, swing_mode="full_swing")


def test_rejects_generic_checkpoint_labels_without_phase_prefixes() -> None:
    report = _report(
        pga_analysis=(
            "What's working\nTempo and intent.\n\nSetup to finish\nArms lead early.\n\n"
            "The missing piece\nImprove arm order.\n\nWhat changes when you unlock it\nMore consistent timing."
        ),
        main_fix="Let the arms work in better order so timing improves.",
        advanced_details={
            **_report().advanced_details.model_dump(),
            "foundational_missing_piece": "Arms fire before the club slots.",
            "root_cause": "Arms fire before the club slots.",
            "chain_reaction": "Arms fire early and timing varies late in the motion.",
            "secondary_fix": "Keep head quieter through change of direction.",
            "diagnostic_checkpoints": [
                {"checkpoint": "Hand path", "grade": "optimal", "observation": "Connected early."},
                {"checkpoint": "Sequencing", "grade": "constraint", "observation": "Arms lead."},
                {"checkpoint": "Plane", "grade": "constraint", "observation": "Steep approach."},
                {"checkpoint": "Contact window", "grade": "compensation", "observation": "Managed late."},
                {"checkpoint": "Balance", "grade": "optimal", "observation": "Held well."},
                {"checkpoint": "Posture", "grade": "optimal", "observation": "Athletic."},
                {"checkpoint": "Width", "grade": "compensation", "observation": "Soft at top."},
            ],
            "evidence_metrics": [
                "Hand path stays connected early",
                "Head stays fairly stable",
                "Arms move out toward the ball",
                "Club approaches from a sharp angle",
                "Face appears managed late",
                "Low point depends on timing",
                "Held in balance at the end",
                "Athletic posture at start",
            ],
        }
    )
    with pytest.raises(ReportQualityError, match="setup through finish"):
        audit_report_quality(report, swing_mode="full_swing")


def test_allows_adjacent_duplicate_phase_pair_on_same_frame() -> None:
    report = _report()
    phase_map = [
        {"phase": "early_follow_through", "frame_index": 109, "confidence": 0.8, "person_visible": True},
        {"phase": "finish", "frame_index": 109, "confidence": 0.75, "person_visible": True},
        {"phase": "address", "frame_index": 0, "confidence": 0.8, "person_visible": True},
    ]
    audit_report_quality(report, swing_mode="full_swing", phase_map=phase_map)


def test_rejects_hidden_lead_arm_bend_when_checkpoint_grades_it() -> None:
    report = _report(
        advanced_details={
            **_report().advanced_details.model_dump(),
            "diagnostic_checkpoints": [
                {"checkpoint": "Setup: posture", "grade": "optimal", "observation": "Balanced."},
                {"checkpoint": "Takeaway: hand path", "grade": "optimal", "observation": "Connected."},
                {
                    "checkpoint": "Backswing: lead arm",
                    "grade": "constraint",
                    "observation": "Lead arm bends sharply across the chest with narrow width at the top.",
                },
                {"checkpoint": "Transition: sequencing", "grade": "constraint", "observation": "Arms fire early."},
                {"checkpoint": "Downswing: swing path", "grade": "constraint", "observation": "Steep path."},
                {"checkpoint": "Impact: contact", "grade": "compensation", "observation": "Timing save."},
                {"checkpoint": "Finish: balance", "grade": "optimal", "observation": "Held finish."},
            ],
        }
    )

    with pytest.raises(ReportQualityError, match="lead-arm"):
        audit_report_quality(report, swing_mode="full_swing")


def test_rejects_hidden_weight_transfer_when_checkpoint_grades_it() -> None:
    report = _report(
        advanced_details={
            **_report().advanced_details.model_dump(),
            "diagnostic_checkpoints": [
                {"checkpoint": "Setup: posture", "grade": "optimal", "observation": "Balanced."},
                {"checkpoint": "Takeaway: hand path", "grade": "optimal", "observation": "Connected."},
                {"checkpoint": "Backswing: width", "grade": "compensation", "observation": "Some width."},
                {
                    "checkpoint": "Transition: weight shift",
                    "grade": "constraint",
                    "observation": "Weight stays on the trail side with no shift toward the lead foot.",
                },
                {"checkpoint": "Downswing: swing path", "grade": "constraint", "observation": "Steep path."},
                {"checkpoint": "Impact: contact", "grade": "compensation", "observation": "Hang back save."},
                {"checkpoint": "Finish: balance", "grade": "compensation", "observation": "Falls back."},
            ],
        }
    )

    with pytest.raises(ReportQualityError, match="weight-transfer"):
        audit_report_quality(report, swing_mode="full_swing")


def test_rejects_disallowed_duplicate_phases_on_same_frame() -> None:
    report = _report()
    phase_map = [
        {"phase": "address", "frame_index": 5, "confidence": 0.8, "person_visible": True},
        {"phase": "impact", "frame_index": 5, "confidence": 0.7, "person_visible": True},
    ]
    with pytest.raises(ReportQualityError, match="Multiple high-confidence phases"):
        audit_report_quality(report, swing_mode="full_swing", phase_map=phase_map)
