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

# Wrist y decreases as hands rise in the frame.
TAKEAWAY_RISE_TARGET = 0.28
TAKEAWAY_RISE_MIN = 0.10
TAKEAWAY_RISE_MAX = 0.55
ADDRESS_EARLY_FRACTION = 0.20

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


def _pick_address_local(
    motions: list[float],
    wrist: list[float],
    pose_sequence: PoseSequence,
    window_indices: list[int],
    motion_threshold: float,
) -> int:
    """Quiet early frame: lowest motion, preferring hands-down setup pose."""
    n = len(window_indices)
    moving_locals = [i for i, motion in enumerate(motions) if motion >= motion_threshold]
    first_motion = moving_locals[0] if moving_locals else max(1, int(n * ADDRESS_EARLY_FRACTION))
    search_end = max(1, min(first_motion, max(2, int(n * ADDRESS_EARLY_FRACTION))))

    best_local = 0
    best_score: tuple[float, float, float] | None = None
    for local in range(0, search_end):
        frame_idx = window_indices[local]
        pose_conf = pose_sequence.confidence_at(frame_idx)
        if pose_conf < 0.35 and local > 0:
            continue
        # Lower motion is better; higher wrist y (hands lower) is better; higher pose conf is better.
        score = (motions[local], -wrist[local], -pose_conf)
        if best_score is None or score < best_score:
            best_score = score
            best_local = local

    return best_local


def _pick_takeaway_local(
    address_local: int,
    top_local: int,
    motions: list[float],
    wrist: list[float],
    motion_threshold: float,
) -> int:
    """Early club-away: ~20–35% of address→top wrist rise with motion started."""
    span = max(1, top_local - address_local)
    fallback = address_local + max(1, span // 4)

    if top_local <= address_local + 1:
        return fallback

    address_wrist = wrist[address_local]
    top_wrist = wrist[top_local]
    # Wrist y drops as hands rise; rise amount is positive when top is higher.
    wrist_travel = address_wrist - top_wrist
    if wrist_travel < 0.02:
        # Flat/unusable pose curve — fall back to span fraction.
        return min(top_local - 1, fallback)

    target_wrist = address_wrist - TAKEAWAY_RISE_TARGET * wrist_travel
    search_start = address_local + 1
    search_end = max(search_start + 1, top_local)

    best_local = fallback
    best_distance = float("inf")
    for local in range(search_start, search_end):
        rise_frac = (address_wrist - wrist[local]) / wrist_travel
        if rise_frac < TAKEAWAY_RISE_MIN or rise_frac > TAKEAWAY_RISE_MAX:
            continue
        if motions[local] < motion_threshold * 0.5 and rise_frac < 0.15:
            continue
        distance = abs(wrist[local] - target_wrist)
        # Prefer frames that have started moving.
        if motions[local] < motion_threshold * 0.35:
            distance += 0.05
        if distance < best_distance:
            best_distance = distance
            best_local = local

    return min(top_local - 1, max(address_local + 1, best_local))


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
    address_local = _pick_address_local(
        motions, wrist, pose_sequence, window_indices, motion_threshold
    )

    top_search_start = max(address_local + 2, int(n * 0.12))
    top_search_end = max(top_search_start + 4, int(n * 0.58))
    top_local = top_search_start + int(np.argmin(wrist[top_search_start:top_search_end]))

    takeaway_local = _pick_takeaway_local(
        address_local, top_local, motions, wrist, motion_threshold
    )

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

    span_td = max(1, impact_local - top_local)

    local_indices = {
        "address": address_local,
        "takeaway": takeaway_local,
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
    takeaway_idx = phase_indices.get("takeaway")

    early_motion_baseline = 0.0
    if motion_curve is not None and len(motion_curve) >= 3:
        early_end = max(2, int(len(motion_curve) * ADDRESS_EARLY_FRACTION))
        early_motion_baseline = float(np.median(motion_curve[:early_end]))

    early_wrist_min = None
    if wrist_curve is not None and len(wrist_curve) >= 3:
        early_end = max(2, int(len(wrist_curve) * ADDRESS_EARLY_FRACTION))
        early_wrist_min = min(wrist_curve[:early_end])

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
            local = local_lookup.get(address_idx)
            if local is not None and motion_curve is not None and local < len(motion_curve):
                if motion_curve[local] > max(0.12, early_motion_baseline * 2.5):
                    validated = False
                    reason = "Address frame has too much motion for a setup still."
                elif (
                    early_wrist_min is not None
                    and wrist_curve is not None
                    and local < len(wrist_curve)
                    and wrist_curve[local] < early_wrist_min - 0.08
                ):
                    validated = False
                    reason = "Address frame wrists are already raised above early setup."
                else:
                    reason = "Address anchor frame."
            else:
                reason = "Address anchor frame."
        elif phase == "takeaway" and takeaway_idx is not None and wrist_curve is not None:
            local = local_lookup.get(takeaway_idx)
            address_local = local_lookup.get(address_idx) if address_idx is not None else None
            top_local = local_lookup.get(top_idx) if top_idx is not None else None
            if (
                local is not None
                and address_local is not None
                and top_local is not None
                and address_local < len(wrist_curve)
                and top_local < len(wrist_curve)
                and local < len(wrist_curve)
            ):
                travel = wrist_curve[address_local] - wrist_curve[top_local]
                if travel >= 0.02:
                    rise_frac = (wrist_curve[address_local] - wrist_curve[local]) / travel
                    if rise_frac < TAKEAWAY_RISE_MIN:
                        validated = False
                        reason = "Takeaway frame is still too close to address."
                    elif rise_frac > TAKEAWAY_RISE_MAX:
                        validated = False
                        reason = "Takeaway frame is too close to the top of the swing."
                    else:
                        reason = "Takeaway mid-rise frame."
                else:
                    reason = "Takeaway span fallback (flat wrist curve)."
            else:
                reason = "Takeaway frame."

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
