from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import cv2
import numpy as np

from app.schemas import (
    DrillPrescription,
    FixPriorityBlock,
    SwingDiagnosisEngine,
    SwingIssueDiagnosis,
    SwingMetricEvidence,
    SwingMode,
)

FULL_SWING_CHECKPOINT_LABELS: dict[str, str] = {
    "setup_address": "setup/address",
    "takeaway": "takeaway",
    "club_parallel_back": "club parallel back",
    "lead_arm_parallel_back": "lead arm parallel back",
    "top_of_backswing": "top of backswing",
    "transition": "transition",
    "lead_arm_parallel_down": "lead arm parallel down",
    "shaft_parallel_down": "shaft parallel down",
    "impact": "impact",
    "release": "release",
    "finish": "finish",
}

METRIC_NAMES = [
    "head_position_x_movement",
    "head_position_y_movement",
    "spine_angle",
    "shoulder_tilt",
    "shoulder_rotation",
    "hip_rotation_estimate",
    "hip_sway",
    "pelvis_depth_early_extension_proxy",
    "knee_flex",
    "lead_arm_angle",
    "trail_elbow_position",
    "hand_path",
    "wrist_hinge_proxy",
    "club_forearm_plane_proxy",
    "center_of_mass_shift_proxy",
    "tempo_ratio",
    "balance_score",
]


@dataclass
class BodyProxy:
    bbox: tuple[int, int, int, int]
    center: tuple[float, float]
    confidence: float


def _foreground_bbox(frame: np.ndarray) -> BodyProxy:
    height, width = frame.shape[:2]
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (9, 9), 0)
    edges = cv2.Canny(blur, 40, 120)
    kernel = np.ones((7, 7), np.uint8)
    dilated = cv2.dilate(edges, kernel, iterations=2)
    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    candidates: list[tuple[int, int, int, int]] = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        area = w * h
        if area < width * height * 0.01:
            continue
        if h < height * 0.20:
            continue
        candidates.append((x, y, w, h))

    if not candidates:
        x, y, w, h = int(width * 0.25), int(height * 0.12), int(width * 0.5), int(height * 0.78)
        return BodyProxy((x, y, w, h), (x + w / 2, y + h / 2), 0.2)

    x1 = min(x for x, _, _, _ in candidates)
    y1 = min(y for _, y, _, _ in candidates)
    x2 = max(x + w for x, y, w, h in candidates)
    y2 = max(y + h for x, y, w, h in candidates)
    w = max(1, x2 - x1)
    h = max(1, y2 - y1)
    area_ratio = min(1.0, (w * h) / (width * height * 0.55))
    confidence = max(0.25, min(0.72, area_ratio))
    return BodyProxy((x1, y1, w, h), (x1 + w / 2, y1 + h / 2), confidence)


def _round(value: float, places: int = 1) -> float:
    if math.isnan(value) or math.isinf(value):
        return 0.0
    return round(value, places)


def _checkpoint_metrics(
    *,
    phase: str,
    proxy: BodyProxy,
    setup: BodyProxy,
    frame_index: int,
    total_frames: int,
) -> dict[str, Any]:
    x, y, w, h = proxy.bbox
    sx, sy, sw, sh = setup.bbox
    cx, cy = proxy.center
    scx, scy = setup.center
    width_scale = max(sw, 1)
    height_scale = max(sh, 1)
    progress = frame_index / max(total_frames - 1, 1)

    head_x = ((x + w * 0.5) - (sx + sw * 0.5)) / width_scale * 100
    head_y = (y - sy) / height_scale * 100
    hip_sway = (cx - scx) / width_scale * 100
    com_shift = (cx - scx) / width_scale * 100
    pelvis_depth = ((x + w) - (sx + sw)) / width_scale * 100
    posture_loss = abs((h / max(w, 1)) - (sh / max(sw, 1))) * 8

    backswing_load = math.sin(min(progress, 0.5) * math.pi)
    downswing_load = max(0.0, math.sin(max(progress - 0.45, 0) * math.pi))
    spine_angle = 38 - posture_loss - max(0, pelvis_depth) * 0.15
    shoulder_tilt = (head_y * 0.35) + (backswing_load * 8)
    shoulder_rotation = backswing_load * 72 - downswing_load * 35
    hip_rotation = backswing_load * 42 - downswing_load * 24
    knee_flex = 24 - max(0, head_y) * 0.18 - max(0, pelvis_depth) * 0.12
    lead_arm_angle = 22 + backswing_load * 110 - downswing_load * 76
    trail_elbow = abs(hip_sway) * 0.35 + max(0, shoulder_tilt - 10) * 0.65
    hand_path = head_x * 0.4 + shoulder_rotation * 0.08
    wrist_hinge = backswing_load * 82 - max(0, progress - 0.72) * 55
    plane_proxy = shoulder_tilt * 0.5 + hand_path * 0.45
    tempo_ratio = 3.0 if total_frames < 2 else _round(max(frame_index, 1) / max(total_frames - frame_index, 1), 2)
    balance = 100 - min(50, abs(com_shift) * 1.4 + abs(head_y) * 1.1 + max(0, pelvis_depth) * 1.2)

    return {
        "checkpoint": phase,
        "label": FULL_SWING_CHECKPOINT_LABELS.get(phase, phase.replace("_", " ")),
        "frame_index": frame_index,
        "confidence": _round(proxy.confidence, 2),
        "body_box": {"x": x, "y": y, "width": w, "height": h},
        "metrics": {
            "head_position_x_movement": _round(head_x),
            "head_position_y_movement": _round(head_y),
            "spine_angle": _round(spine_angle),
            "shoulder_tilt": _round(shoulder_tilt),
            "shoulder_rotation": _round(shoulder_rotation),
            "hip_rotation_estimate": _round(hip_rotation),
            "hip_sway": _round(hip_sway),
            "pelvis_depth_early_extension_proxy": _round(pelvis_depth),
            "knee_flex": _round(knee_flex),
            "lead_arm_angle": _round(lead_arm_angle),
            "trail_elbow_position": _round(trail_elbow),
            "hand_path": _round(hand_path),
            "wrist_hinge_proxy": _round(wrist_hinge),
            "club_forearm_plane_proxy": _round(plane_proxy),
            "center_of_mass_shift_proxy": _round(com_shift),
            "tempo_ratio": tempo_ratio,
            "balance_score": _round(balance),
        },
    }


def _annotations(frame: np.ndarray, item: dict[str, Any]) -> dict[str, Any]:
    height, width = frame.shape[:2]
    box = item["body_box"]
    x, y, w, h = box["x"], box["y"], box["width"], box["height"]

    def pt(px: float, py: float) -> dict[str, float]:
        return {"x": _round(px / width, 3), "y": _round(py / height, 3)}

    shoulder_y = y + h * 0.24
    hip_y = y + h * 0.54
    knee_y = y + h * 0.78
    return {
        "checkpoint": item["checkpoint"],
        "lines": [
            {"type": "shoulder_line", "from": pt(x + w * 0.28, shoulder_y), "to": pt(x + w * 0.72, shoulder_y + h * 0.03)},
            {"type": "hip_line", "from": pt(x + w * 0.32, hip_y), "to": pt(x + w * 0.68, hip_y)},
            {"type": "spine_angle_line", "from": pt(x + w * 0.52, shoulder_y), "to": pt(x + w * 0.46, hip_y)},
            {"type": "hip_depth_line", "from": pt(x + w * 0.78, hip_y), "to": pt(x + w * 0.92, hip_y)},
            {"type": "knee_flex_marker", "from": pt(x + w * 0.36, knee_y), "to": pt(x + w * 0.64, knee_y)},
        ],
        "boxes": [
            {"type": "head_box_from_setup", "x": _round((x + w * 0.36) / width, 3), "y": _round(y / height, 3), "width": _round(w * 0.28 / width, 3), "height": _round(h * 0.18 / height, 3)}
        ],
        "traces": [
            {"type": "hand_path_trace", "points": [pt(x + w * 0.58, y + h * 0.35), pt(x + w * 0.67, y + h * 0.45), pt(x + w * 0.60, y + h * 0.58)]}
        ],
    }


def _evidence(
    checkpoint: str,
    metric: str,
    observed: str,
    expected: str,
    interpretation: str,
    confidence: float,
) -> SwingMetricEvidence:
    return SwingMetricEvidence(
        checkpoint=FULL_SWING_CHECKPOINT_LABELS.get(checkpoint, checkpoint.replace("_", " ")),
        metric=metric,
        observed=observed,
        expected=expected,
        interpretation=interpretation,
        confidence=_round(confidence, 2),
    )


def _camera_angle(metrics: list[dict[str, Any]]) -> tuple[str, str]:
    setup_box = metrics[0]["body_box"]
    ratio = setup_box["width"] / max(setup_box["height"], 1)
    if ratio > 0.62:
        return "face_on", "Face-on style read: strongest for sway, head movement, pressure shift proxy, low-point control, and balance."
    if ratio < 0.42:
        return "down_the_line", "Down-the-line style read: strongest for posture, early extension proxy, hand path, shoulder plane, and hip depth."
    return "unknown", "Camera angle is ambiguous, so exact path/face claims are limited."


def _issue_from_rules(metrics: list[dict[str, Any]], camera_angle: str) -> SwingIssueDiagnosis:
    by_phase = {m["checkpoint"]: m for m in metrics}
    setup = by_phase.get("setup_address", metrics[0])
    top = by_phase.get("top_of_backswing", metrics[min(len(metrics) - 1, 4)])
    transition = by_phase.get("transition", top)
    impact = by_phase.get("impact", metrics[-2])

    setup_m = setup["metrics"]
    top_m = top["metrics"]
    transition_m = transition["metrics"]
    impact_m = impact["metrics"]
    conf = min(setup["confidence"], top["confidence"], impact["confidence"])

    evidence: list[SwingMetricEvidence] = []
    if abs(top_m["hip_sway"]) > 10 and camera_angle in ("face_on", "unknown"):
        evidence.append(_evidence("top_of_backswing", "hip_sway", f"{top_m['hip_sway']}% from setup", "Within about 8-10% of setup center", "Likely sway/reverse-pivot pattern starts before transition.", conf))
        evidence.append(_evidence("transition", "center_of_mass_shift_proxy", f"{transition_m['center_of_mass_shift_proxy']}% from setup", "Pressure should begin moving lead-side before arms fire", "Lower-body sequence is likely late.", conf))
        return SwingIssueDiagnosis(
            symptom="Poor contact or curvature caused by low-point drift",
            root_cause="Likely excessive sway before the top of the backswing",
            first_breakdown_checkpoint="top of backswing",
            evidence=evidence,
            chain_reaction="The body center drifts, pressure arrives late, and the hands have to rescue the low point through impact.",
            fix_priority=1,
            why_this_comes_first="Low point and path cannot stabilize until the body stops drifting before transition.",
            recommended_feel="Turn around a steady chest while pressure gathers under the trail instep.",
            drill=DrillPrescription(
                name="Trail-Instep Coil Drill",
                instructions="Make slow backswings with the trail foot rolled slightly inward. Stop at the top and confirm your head and belt buckle have not slid outside the trail foot.",
                sets_reps="3 sets of 8 slow rehearsals, then 10 half-speed balls",
                success_metric="Top checkpoint shows hip sway inside 10% of setup width.",
            ),
            next_video_focus="Film face-on and pause at the top checkpoint.",
        )

    if impact_m["pelvis_depth_early_extension_proxy"] > 8 and camera_angle in ("down_the_line", "unknown"):
        evidence.append(_evidence("impact", "pelvis_depth_early_extension_proxy", f"{impact_m['pelvis_depth_early_extension_proxy']}% toward the ball", "Maintain hip depth within about 5-8% of setup", "Likely early extension near impact.", conf))
        evidence.append(_evidence("transition", "spine_angle", f"{transition_m['spine_angle']} degrees proxy", "Preserve address spine angle into delivery", "Posture loss likely forces the hands outward.", conf))
        return SwingIssueDiagnosis(
            symptom="Crowded impact with path/strike compensation",
            root_cause="Likely loss of hip depth and posture through delivery",
            first_breakdown_checkpoint="transition",
            evidence=evidence,
            chain_reaction="As the pelvis moves toward the ball, the arms lose space, the handle rises, and contact/path become timing-dependent.",
            fix_priority=1,
            why_this_comes_first="Impact cannot be cleaned up until the body keeps enough space for the hands to return.",
            recommended_feel="Lead hip turns back behind you while your chest stays over the ball.",
            drill=DrillPrescription(
                name="Chair Hip-Depth Rehearsal",
                instructions="Set a chair just behind your hips. Keep light contact in the backswing and regain it in transition before brushing a tee.",
                sets_reps="2 sets of 10 rehearsals, then 15 waist-high shots",
                success_metric="Impact checkpoint keeps pelvis depth within 8% of setup.",
            ),
            next_video_focus="Film down-the-line with hips, feet, and hands visible.",
        )

    if top_m["trail_elbow_position"] > 12 or top_m["club_forearm_plane_proxy"] > 12:
        evidence.append(_evidence("top_of_backswing", "trail_elbow_position", f"{top_m['trail_elbow_position']} proxy units", "Trail elbow connected enough to start down without throwing outward", "Arms are likely disconnected before the downswing begins.", conf))
        evidence.append(_evidence("transition", "club_forearm_plane_proxy", f"{transition_m['club_forearm_plane_proxy']} proxy units", "Plane should shallow or neutralize in transition", "Transition likely steepens instead of shallows.", conf))
        return SwingIssueDiagnosis(
            symptom="Likely over-the-top delivery or pull/slice pattern",
            root_cause="Trail arm and shoulder plane appear disconnected by the top checkpoint",
            first_breakdown_checkpoint="top of backswing",
            evidence=evidence,
            chain_reaction="A disconnected top makes the arms start out first, moving the delivery left/steep before impact can be fixed.",
            fix_priority=1,
            why_this_comes_first="The path problem is created before impact, so transition sequencing beats a face/path bandage.",
            recommended_feel="Trail elbow folds in front of the ribs, then the lower body starts first.",
            drill=DrillPrescription(
                name="Trail-Elbow Towel Pump",
                instructions="Hold a small towel under the trail armpit. Make three slow pumps from the top to lead-arm-parallel-down, then hit a half shot.",
                sets_reps="3 pump rehearsals before each of 20 balls",
                success_metric="Top and transition checkpoints show the trail elbow closer to the rib line.",
            ),
            next_video_focus="Film down-the-line and capture top plus transition clearly.",
        )

    evidence.append(_evidence("setup_address", "balance_score", f"{setup_m['balance_score']}/100", "Stable setup and finish balance above 80/100", "No single high-confidence root fault dominated the proxy metrics.", conf))
    return SwingIssueDiagnosis(
        symptom="Timing-dependent strike pattern",
        root_cause="No single high-confidence root cause detected from the available angle",
        first_breakdown_checkpoint="setup/address",
        evidence=evidence,
        chain_reaction="When the video or angle limits measurement, the safest fix is a setup and balance checkpoint before chasing impact.",
        fix_priority=1,
        why_this_comes_first="A stable setup is the lowest-risk checkpoint when confidence is limited.",
        recommended_feel="Balanced feet, quiet head, hold the finish.",
        drill=DrillPrescription(
            name="Three-Second Finish Drill",
            instructions="Hit half-speed shots and hold your finish until the ball lands. Reject reps where you step or fall out.",
            sets_reps="20 balls at 60% speed",
            success_metric="Finish balance score remains above 80/100.",
        ),
        next_video_focus="Upload a stable face-on or down-the-line video with full body in frame.",
    )


def analyze_swing_sequence(
    *,
    frames: list[np.ndarray],
    keyframe_indices: dict[str, int],
    swing_mode: SwingMode,
) -> tuple[SwingDiagnosisEngine, dict[str, Any]]:
    if not frames or not keyframe_indices:
        issue = SwingIssueDiagnosis(
            symptom="Unclear ball-flight or contact pattern",
            root_cause="No checkpoint frames were available for measurement",
            first_breakdown_checkpoint="setup/address",
            evidence=[],
            chain_reaction="Without checkpoint frames, the miss cannot be traced backward safely.",
            fix_priority=1,
            why_this_comes_first="A clear setup checkpoint is required before diagnosing impact symptoms.",
            recommended_feel="Full body in frame, stable camera, good light.",
            drill=DrillPrescription(
                name="Clean Upload Check",
                instructions="Record one stable full-body swing from face-on or down-the-line.",
                sets_reps="1 clean upload",
                success_metric="Setup through finish are visible.",
            ),
            next_video_focus="Upload a stable face-on or down-the-line video with full body in frame.",
        )
        engine = SwingDiagnosisEngine(
            main_diagnosis=issue.root_cause,
            skill_level_note="Video metrics were unavailable.",
            first_breakdown_checkpoint=issue.first_breakdown_checkpoint,
            root_cause=issue.root_cause,
            symptom=issue.symptom,
            chain_reaction=issue.chain_reaction,
            fix_priority=FixPriorityBlock(primary=issue.root_cause, secondary="Improve camera angle", optional="Recheck impact later"),
            evidence=issue.evidence,
            what_to_feel=issue.recommended_feel,
            one_drill=issue.drill,
            next_upload_focus=issue.next_video_focus,
            coach_warning="Confidence is low because no frame metrics were available.",
            issues=[issue],
        )
        return engine, {"checkpoints": [], "annotations": [], "camera_angle": "unknown"}

    ordered = sorted(keyframe_indices.items(), key=lambda item: item[1])
    proxies = {phase: _foreground_bbox(frames[idx]) for phase, idx in ordered}
    setup_proxy = proxies.get("setup_address") or next(iter(proxies.values()))
    checkpoints = [
        _checkpoint_metrics(
            phase=phase,
            proxy=proxies[phase],
            setup=setup_proxy,
            frame_index=idx,
            total_frames=len(frames),
        )
        for phase, idx in ordered
    ]
    annotations = [_annotations(frames[idx], item) for item, idx in zip(checkpoints, [idx for _, idx in ordered], strict=False)]
    camera_angle, warning = _camera_angle(checkpoints)
    issue = _issue_from_rules(checkpoints, camera_angle)
    confidence = min((ev.confidence for ev in issue.evidence), default=0.35)
    low_confidence = confidence < 0.45
    coach_warning = warning
    if low_confidence:
        coach_warning += " Confidence is low, so diagnosis should be treated as likely rather than certain."

    engine = SwingDiagnosisEngine(
        main_diagnosis=issue.root_cause,
        skill_level_note="Use one checkpoint fix at a time. Do not stack multiple swing thoughts.",
        first_breakdown_checkpoint=issue.first_breakdown_checkpoint,
        root_cause=issue.root_cause,
        symptom=issue.symptom,
        chain_reaction=issue.chain_reaction,
        fix_priority=FixPriorityBlock(
            primary=issue.root_cause,
            secondary="Recheck the next checkpoint after the primary improves.",
            optional="Only address impact if the same miss remains after the root checkpoint changes.",
        ),
        evidence=issue.evidence,
        what_to_feel=issue.recommended_feel,
        one_drill=issue.drill,
        next_upload_focus=issue.next_video_focus,
        coach_warning=coach_warning,
        issues=[issue],
    )
    return engine, {
        "camera_angle": camera_angle,
        "checkpoints": checkpoints,
        "annotations": annotations,
        "metric_names": METRIC_NAMES,
    }
