from __future__ import annotations

from app.schemas import DetectedIssue, SwingMetrics

ISSUE_CATALOG = {
    "excessive_head_movement": {
        "issue": "Excessive head movement",
        "why": "Head stability helps maintain consistent contact and spine angle through impact.",
        "fix": "Keep eyes on the ball and feel your head stay centered over the ball through impact.",
        "drill": "Feet-together swings focusing on a quiet head through contact.",
    },
    "early_extension": {
        "issue": "Early extension",
        "why": "Standing up through impact reduces space for the arms and often causes thin or blocked shots.",
        "fix": "Maintain hip hinge and feel your belt buckle staying back through impact.",
        "drill": "Chair drill — set up with your glutes touching a chair and maintain contact through the swing.",
    },
    "poor_spine_retention": {
        "issue": "Poor spine angle retention",
        "why": "Changing spine angle dramatically alters swing plane and low-point control.",
        "fix": "Set a consistent forward tilt at address and maintain it through impact.",
        "drill": "Mirror drill checking spine angle at address and impact positions.",
    },
    "over_the_top": {
        "issue": "Over-the-top pattern",
        "why": "An outside-in path often produces pulls and slices under pressure.",
        "fix": "Feel the club drop to the inside on the downswing with hip rotation leading.",
        "drill": "Headcover under trail arm or alignment-stick shallowing drill.",
    },
    "weak_hip_rotation": {
        "issue": "Weak hip rotation",
        "why": "Limited hip turn reduces power and can force compensations with the upper body.",
        "fix": "Initiate the downswing with hip bump and rotation toward the target.",
        "drill": "Step-through drill or resistance-band hip rotation sets.",
    },
    "poor_finish_balance": {
        "issue": "Poor balance at finish",
        "why": "Falling off balance often indicates swing path or weight-transfer issues.",
        "fix": "Hold your finish until the ball lands; weight should be on the lead side.",
        "drill": "Swing to finish and hold for 3 seconds on every rep.",
    },
    "collapsing_lead_arm": {
        "issue": "Collapsing lead arm",
        "why": "A buckling lead arm reduces width and consistency at impact.",
        "fix": "Maintain lead arm structure through impact without excessive tension.",
        "drill": "Towel under lead armpit half-swings keeping connection.",
    },
    "reverse_pivot": {
        "issue": "Reverse pivot",
        "why": "Weight moving toward the target on the backswing limits coil and power.",
        "fix": "Feel pressure load into the trail foot and hip during the backswing.",
        "drill": "Trail-foot-only backswing drill with pause at the top.",
    },
    "casting": {
        "issue": "Casting (early release)",
        "why": "Releasing the club too early costs lag, compression, and distance.",
        "fix": "Maintain wrist hinge longer into the downswing; rotate through impact.",
        "drill": "Impact bag or pump drill with pause at hip height.",
    },
    "poor_setup_posture": {
        "issue": "Poor setup posture",
        "why": "A weak setup makes repeating a good motion much harder.",
        "fix": "Athletic posture: slight knee flex, hip hinge, arms hanging naturally.",
        "drill": "Setup checklist — grip, posture, alignment — before every swing.",
    },
}


def _issue(code: str, severity: str, evidence: dict) -> DetectedIssue:
    cat = ISSUE_CATALOG[code]
    return DetectedIssue(
        issue_code=code,
        issue=cat["issue"],
        severity=severity,  # type: ignore[arg-type]
        why_it_matters=cat["why"],
        fix=cat["fix"],
        drill=cat["drill"],
        metric_evidence=evidence,
    )


def evaluate_rules(metrics: SwingMetrics) -> list[DetectedIssue]:
    issues: list[DetectedIssue] = []

    if metrics.head_movement > 8:
        sev = "high" if metrics.head_movement > 15 else "medium"
        issues.append(_issue("excessive_head_movement", sev, {"head_movement": metrics.head_movement}))

    if metrics.spine_angle_change > 12:
        sev = "high" if metrics.spine_angle_change > 20 else "medium"
        issues.append(_issue("poor_spine_retention", sev, {"spine_angle_change": metrics.spine_angle_change}))

    if metrics.spine_angle_impact > metrics.spine_angle_address + 8:
        issues.append(_issue("early_extension", "medium", {
            "spine_angle_address": metrics.spine_angle_address,
            "spine_angle_impact": metrics.spine_angle_impact,
        }))

    if metrics.hip_rotation_address_to_top < 15:
        sev = "high" if metrics.hip_rotation_address_to_top < 8 else "medium"
        issues.append(_issue("weak_hip_rotation", sev, {"hip_rotation": metrics.hip_rotation_address_to_top}))

    if metrics.hip_rotation_top_to_impact < 5 and metrics.hip_rotation_address_to_top > 10:
        issues.append(_issue("reverse_pivot", "medium", {"hip_rotation_top_to_impact": metrics.hip_rotation_top_to_impact}))

    if metrics.finish_balance < 60:
        sev = "high" if metrics.finish_balance < 40 else "medium"
        issues.append(_issue("poor_finish_balance", sev, {"finish_balance": metrics.finish_balance}))

    if metrics.lead_arm_angle_impact < 120 and metrics.lead_arm_angle_top > 140:
        issues.append(_issue("collapsing_lead_arm", "medium", {
            "lead_arm_angle_top": metrics.lead_arm_angle_top,
            "lead_arm_angle_impact": metrics.lead_arm_angle_impact,
        }))

    if metrics.tempo_ratio < 2.0:
        issues.append(_issue("casting", "low", {"tempo_ratio": metrics.tempo_ratio}))

    if metrics.spine_angle_address < 15 or metrics.spine_angle_address > 45:
        issues.append(_issue("poor_setup_posture", "medium", {"spine_angle_address": metrics.spine_angle_address}))

    if metrics.shoulder_tilt_top < 5 and metrics.hip_rotation_address_to_top > 20:
        issues.append(_issue("over_the_top", "low", {"shoulder_tilt_top": metrics.shoulder_tilt_top}))

    return issues
