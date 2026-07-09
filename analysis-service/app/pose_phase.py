from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from app.person_detection import frame_motion_score
from app.pose_extractor import (
    PoseSequence,
    hip_line_angle_for_frame,
    hip_rotation_proxy,
    wrist_height_proxy,
)
from app.swing_window import SwingWindow

POSE_TIMELINE_MAX_POINTS = 60
POSE_PHASE_MIN_CONFIDENCE = 0.45

PHASE_ORDER = (
    "address",
    "takeaway",
    "top",
    "transition",
    "downswing",
    "impact",
    "early_follow_through",
    "finish",
)


@dataclass
class PhasePickResult:
    indices: dict[str, int]
    validation: dict[str, dict[str, Any]]
    timeline: dict[str, Any]
    method: str = "pose_timeline"


def _window_indices(window: SwingWindow) -> list[int]:
    return list(range(window.start_frame, window.end_frame + 1))


def _downsample_indices(indices: list[int], max_points: int = POSE_TIMELINE_MAX_POINTS) -> list[int]:
    if len(indices) <= max_points:
        return indices
    step = max(1, len(indices) // max_points)
    sampled = indices[::step]
    if sampled[-1] != indices[-1]:
        sampled.append(indices[-1])
    return sampled


def build_pose_timeline(
    frames: list[np.ndarray],
    pose_sequence: PoseSequence,
    window: SwingWindow,
) -> dict[str, Any]:
    """Compact body/motion curves inside the swing window for Gemini."""
    indices = _downsample_indices(_window_indices(window))
    setup_hip = hip_line_angle_for_frame(pose_sequence, window.start_frame)

    wrist_heights: list[float] = []
    hip_rotations: list[float] = []
    motions: list[float] = []
    confidences: list[float] = []

    for idx in indices:
        wrist_heights.append(round(wrist_height_proxy(pose_sequence, idx), 3))
        if setup_hip is not None:
            hip_rotations.append(round(hip_rotation_proxy(pose_sequence, idx, setup_hip), 3))
        else:
            hip_rotations.append(0.0)
        motions.append(round(frame_motion_score(frames, idx), 3))
        confidences.append(round(pose_sequence.confidence_at(idx), 3))

    return {
        "frame_indices": indices,
        "wrist_height_norm": wrist_heights,
        "hip_rotation_proxy": hip_rotations,
        "motion": motions,
        "pose_confidence": confidences,
        "note": "Lower wrist_height_norm = hands higher in frame. Motion peaks often near impact.",
    }


def _enforce_monotonic(local_indices: dict[str, int], window_indices: list[int]) -> dict[str, int]:
    """Ensure phase local indices strictly increase."""
    locals_map = dict(local_indices)
    n = len(window_indices) - 1
    for i in range(1, len(PHASE_ORDER)):
        prev = PHASE_ORDER[i - 1]
        curr = PHASE_ORDER[i]
        if locals_map[curr] <= locals_map[prev]:
            locals_map[curr] = min(n, locals_map[prev] + 1)
    return {phase: window_indices[locals_map[phase]] for phase in PHASE_ORDER}


def pick_phases_from_pose_timeline(
    frames: list[np.ndarray],
    window: SwingWindow,
    pose_sequence: PoseSequence,
) -> PhasePickResult:
    """Pick swing phase frames by scanning the full swing window on pose + motion curves."""
    window_indices = _window_indices(window)
    n = len(window_indices)
    if n < 8:
        raise ValueError("Swing window too short for pose timeline phase detection")

    motions = [frame_motion_score(frames, idx) for idx in window_indices]
    wrist = [wrist_height_proxy(pose_sequence, idx) for idx in window_indices]

    motion_threshold = max(0.06, float(np.percentile(motions, 65)) * 0.45)
    moving_locals = [i for i, motion in enumerate(motions) if motion >= motion_threshold]
    address_local = max(0, moving_locals[0] - 1) if moving_locals else 0

    top_search_start = max(address_local + 2, int(n * 0.12))
    top_search_end = max(top_search_start + 4, int(n * 0.58))
    top_local = top_search_start + int(np.argmin(wrist[top_search_start:top_search_end]))

    min_downswing_span = max(4, int(n * 0.08))
    impact_search_start = min(max(top_local + min_downswing_span, int(n * 0.35)), n - 3)
    impact_search_end = max(impact_search_start + 1, int(n * 0.92))
    impact_local = impact_search_start + int(
        np.argmax(motions[impact_search_start:impact_search_end])
    )

    if impact_local <= top_local + 2:
        impact_local = min(n - 2, top_local + min_downswing_span + 2)

    finish_local = n - 1
    follow_span = max(2, finish_local - impact_local)
    early_follow_local = min(finish_local - 1, impact_local + max(1, follow_span // 2))

    span_at = max(1, top_local - address_local)
    span_td = max(1, impact_local - top_local)

    local_indices = {
        "address": address_local,
        "takeaway": address_local + max(1, span_at // 4),
        "top": top_local,
        "transition": top_local + max(1, span_td // 3),
        "downswing": top_local + max(2, (2 * span_td) // 3),
        "impact": impact_local,
        "early_follow_through": early_follow_local,
        "finish": finish_local,
    }

    indices = _enforce_monotonic(local_indices, window_indices)
    timeline = build_pose_timeline(frames, pose_sequence, window)
    validation = validate_phase_assignments(
        pose_sequence,
        indices,
        window_indices,
        wrist,
        motions,
    )

    return PhasePickResult(
        indices=indices,
        validation=validation,
        timeline=timeline,
        method="pose_timeline",
    )


def _is_local_minimum(values: list[float], center: int, radius: int = 2) -> bool:
    start = max(0, center - radius)
    end = min(len(values), center + radius + 1)
    segment = values[start:end]
    if not segment:
        return False
    return values[center] <= min(segment) + 0.02


def validate_phase_assignments(
    pose_sequence: PoseSequence,
    phase_indices: dict[str, int],
    window_indices: list[int] | None = None,
    wrist_curve: list[float] | None = None,
    motion_curve: list[float] | None = None,
) -> dict[str, dict[str, Any]]:
    """Validate that each phase frame matches expected pose/motion signals."""
    validation: dict[str, dict[str, Any]] = {}
    ordered_values = [phase_indices[phase] for phase in PHASE_ORDER if phase in phase_indices]

    monotonic = all(ordered_values[i] < ordered_values[i + 1] for i in range(len(ordered_values) - 1))

    local_lookup: dict[int, int] = {}
    if window_indices is not None:
        local_lookup = {frame_idx: local for local, frame_idx in enumerate(window_indices)}

    top_idx = phase_indices.get("top")
    impact_idx = phase_indices.get("impact")
    address_idx = phase_indices.get("address")

    for phase, frame_idx in phase_indices.items():
        pose_conf = pose_sequence.confidence_at(frame_idx)
        validated = pose_conf >= 0.4 and monotonic
        reason = ""

        if not monotonic:
            validated = False
            reason = "Phase frame order is not strictly increasing."
        elif pose_conf < 0.4:
            validated = False
            reason = "Pose confidence too low at this frame."
        elif phase == "top" and wrist_curve is not None and top_idx is not None:
            local = local_lookup.get(top_idx)
            if local is not None and not _is_local_minimum(wrist_curve, local, radius=3):
                validated = False
                reason = "Top frame is not a local minimum in wrist height."
        elif phase == "impact" and motion_curve is not None and impact_idx is not None:
            local = local_lookup.get(impact_idx)
            if local is not None and top_idx is not None:
                top_local = local_lookup.get(top_idx, 0)
                if local <= top_local:
                    validated = False
                    reason = "Impact frame must occur after top."
                elif local < len(motion_curve):
                    region = motion_curve[top_local : min(len(motion_curve), local + 4)]
                    if region and motion_curve[local] < max(region) * 0.55:
                        validated = False
                        reason = "Impact frame motion is not in the downswing peak window."
        elif phase == "address" and address_idx is not None:
            validated = True
            reason = "Address anchor frame."

        if validated and not reason:
            reason = "Pose-validated phase frame."

        validation[phase] = {
            "validated": validated,
            "frame_index": frame_idx,
            "pose_confidence": round(pose_conf, 3),
            "reason": reason,
        }

    return validation


def validated_phase_indices(validation: dict[str, dict[str, Any]]) -> dict[str, int]:
    return {
        phase: info["frame_index"]
        for phase, info in validation.items()
        if info.get("validated") and isinstance(info.get("frame_index"), int)
    }
