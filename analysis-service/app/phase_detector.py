from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

from app.person_detection import frame_motion_score, score_frame_person
from app.pose_extractor import PoseSequence, hip_line_angle_for_frame, hip_rotation_proxy, wrist_height_proxy
from app.swing_window import SwingWindow
from app.vision_fusion import _image_quality
from app.debug_agent_log import agent_log

FULL_SWING_PHASE_ORDER = (
    "address",
    "takeaway",
    "top",
    "transition",
    "downswing",
    "impact",
    "early_follow_through",
    "finish",
)

PERSON_VISIBLE_THRESHOLD = 0.38
IMPACT_CONFIDENCE_THRESHOLD = 0.5
PHASE_CONFIDENCE_LOW = 0.4
COLLISION_ADJUSTMENT_NOTE = "Frame adjusted to avoid duplicate phase mapping."
COLLISION_CONFIDENCE_CAP = 0.45


@dataclass
class PhaseFrame:
    phase: str
    frame_index: int
    confidence: float
    person_visible: bool
    notes: str = ""

    def to_dict(self) -> dict:
        return {
            "phase": self.phase,
            "frame_index": self.frame_index,
            "confidence": round(self.confidence, 3),
            "person_visible": self.person_visible,
            "notes": self.notes,
        }


@dataclass
class PhaseDetectionResult:
    phases: list[PhaseFrame]
    keyframe_indices: dict[str, int]

    @property
    def phase_map(self) -> list[dict]:
        return [p.to_dict() for p in self.phases]

    def get(self, phase: str) -> PhaseFrame | None:
        for item in self.phases:
            if item.phase == phase:
                return item
        return None

    def impact_confidence(self) -> float:
        impact = self.get("impact") or self.get("impact_window_estimate")
        return impact.confidence if impact else 0.0

    def limitation_notes(self) -> list[str]:
        notes: list[str] = []
        impact = self.get("impact") or self.get("impact_window_estimate")
        if impact and (
            impact.phase == "impact_window_estimate"
            or impact.confidence < IMPACT_CONFIDENCE_THRESHOLD
        ):
            notes.append(
                "Impact frame was not clearly visible, so impact feedback is limited."
            )
        finish = self.get("finish")
        if finish and (not finish.person_visible or finish.confidence < PHASE_CONFIDENCE_LOW):
            notes.append("Finish was not clearly visible on this upload.")
        return notes


def _candidate_indices(window: SwingWindow, count: int = 10) -> list[int]:
    start, end = window.start_frame, window.end_frame
    span = end - start
    if span <= 0:
        return [start]
    n = max(8, min(12, count))
    return [start + int(i * span / (n - 1)) for i in range(n)]


def _rotation_proxy(
    frames: list[np.ndarray],
    index: int,
    setup: tuple[float, float],
    pose_sequence: PoseSequence | None = None,
    setup_hip_angle: float | None = None,
) -> float:
    if pose_sequence and pose_sequence.confidence_at(index) >= 0.4 and setup_hip_angle is not None:
        return hip_rotation_proxy(pose_sequence, index, setup_hip_angle)

    proxy = score_frame_person(frames[index])
    cx, cy = proxy.center
    sx, sy = setup
    shift = abs(cx - sx) / max(frames[index].shape[1], 1)
    width_ratio = proxy.bbox[2] / max(frames[index].shape[1], 1)
    return shift + width_ratio * 0.35


_EARLY_SLOT_PHASES = ("address", "takeaway", "top", "transition", "downswing")


def _dedupe_early_phase_slots(
    candidates: list[int],
    slot_indices: dict[str, int],
    impact_idx: int,
    adjusted: set[str],
) -> None:
    """Ensure setup-to-downswing slots stay unique without reshuffling finish."""
    candidate_count = len(candidates)
    if candidate_count == 0:
        return

    occupied = {
        impact_idx,
        slot_indices["early_follow_through"],
        slot_indices["finish"],
    }
    min_slot = 0
    for phase in _EARLY_SLOT_PHASES:
        current_idx = slot_indices[phase]
        if current_idx in occupied:
            reassigned = False
            for slot in range(min_slot, candidate_count):
                candidate_idx = candidates[slot]
                if candidate_idx not in occupied:
                    slot_indices[phase] = candidate_idx
                    adjusted.add(phase)
                    current_idx = candidate_idx
                    min_slot = slot + 1
                    reassigned = True
                    break
            if not reassigned:
                for slot in range(candidate_count):
                    candidate_idx = candidates[slot]
                    if candidate_idx not in occupied:
                        slot_indices[phase] = candidate_idx
                        adjusted.add(phase)
                        current_idx = candidate_idx
                        min_slot = slot + 1
                        break
        else:
            slot_pos = next(
                (slot for slot, candidate in enumerate(candidates) if candidate == current_idx),
                min_slot,
            )
            min_slot = max(min_slot, slot_pos + 1)
        occupied.add(current_idx)


def _resolve_slot_collisions(
    candidates: list[int],
    slot_indices: dict[str, int],
    impact_idx: int,
    peak_motion_idx: int,
    peak_rotation_idx: int,
) -> tuple[int, set[str]]:
    """Ensure distinct frame indices for phases that audit treats as independent."""
    adjusted: set[str] = set()
    candidate_count = len(candidates)
    if candidate_count == 0:
        return impact_idx, adjusted

    if slot_indices["early_follow_through"] == slot_indices["finish"] and candidate_count >= 2:
        slot_indices["finish"] = candidates[-2]
        adjusted.add("finish")

    resolved_impact_idx = impact_idx
    follow_idx = slot_indices["early_follow_through"]
    finish_idx = slot_indices["finish"]
    if resolved_impact_idx == follow_idx or resolved_impact_idx == finish_idx:
        earlier_slot = max(peak_motion_idx - 1, 0)
        resolved_impact_idx = candidates[earlier_slot]
        adjusted.add("impact")

    if slot_indices["top"] == slot_indices["transition"] and candidate_count >= 3:
        later_slot = min(peak_rotation_idx + 2, candidate_count - 1)
        if candidates[later_slot] != slot_indices["top"]:
            slot_indices["transition"] = candidates[later_slot]
            adjusted.add("transition")

    occupied = {value for key, value in slot_indices.items() if key != "downswing"}
    occupied.add(resolved_impact_idx)
    if slot_indices["downswing"] in occupied:
        reassigned = False
        for offset in range(1, candidate_count):
            earlier_slot = max(peak_motion_idx - offset, 0)
            candidate = candidates[earlier_slot]
            if candidate not in occupied:
                slot_indices["downswing"] = candidate
                adjusted.add("downswing")
                reassigned = True
                break
        if not reassigned:
            for slot in range(peak_motion_idx + 1, candidate_count):
                candidate = candidates[slot]
                if candidate not in occupied:
                    slot_indices["downswing"] = candidate
                    adjusted.add("downswing")
                    break

    _dedupe_early_phase_slots(candidates, slot_indices, resolved_impact_idx, adjusted)

    return resolved_impact_idx, adjusted


def _frame_confidence(
    frames: list[np.ndarray],
    index: int,
    pose_sequence: PoseSequence | None = None,
) -> tuple[float, bool, str]:
    proxy = score_frame_person(frames[index])
    quality = _image_quality(frames[index])
    sharpness = float(quality.get("sharpness", 0))
    pose_conf = pose_sequence.confidence_at(index) if pose_sequence else 0.0
    person_visible = proxy.confidence >= PERSON_VISIBLE_THRESHOLD or pose_conf >= 0.45
    quality_factor = min(1.0, sharpness / 120.0)
    confidence = max(proxy.confidence, pose_conf) * 0.7 + quality_factor * 0.3
    notes = ""
    if not person_visible:
        notes = "Person not clearly visible in frame."
    elif sharpness < 45:
        notes = "Frame is soft or blurry."
    elif pose_conf >= 0.55:
        notes = "Pose landmarks detected."
    return confidence, person_visible, notes


def detect_swing_phases(
    frames: list[np.ndarray],
    window: SwingWindow,
    pose_sequence: PoseSequence | None = None,
) -> PhaseDetectionResult:
    """Map swing phases within the detected window using motion and pose heuristics."""
    candidates = _candidate_indices(window)
    motions = [frame_motion_score(frames, i) for i in candidates]
    setup_center = score_frame_person(frames[candidates[0]]).center

    setup_hip_angle = hip_line_angle_for_frame(pose_sequence, candidates[0]) if pose_sequence else None

    rotations = [
        _rotation_proxy(frames, idx, setup_center, pose_sequence, setup_hip_angle)
        for idx in candidates
    ]

    peak_motion_idx = int(np.argmax(motions))

    if pose_sequence and pose_sequence.average_confidence >= 0.45:
        wrist_heights = [wrist_height_proxy(pose_sequence, idx) for idx in candidates]
        backswing_end = max(peak_motion_idx, 1)
        peak_rotation_idx = int(np.argmin(wrist_heights[:backswing_end]))
    else:
        peak_rotation_idx = int(np.argmax(rotations[: max(peak_motion_idx + 1, 1)]))

    slot_indices: dict[str, int] = {
        "address": candidates[0],
        "takeaway": candidates[min(1, len(candidates) - 1)],
        "top": candidates[peak_rotation_idx],
        "transition": candidates[min(peak_rotation_idx + 1, len(candidates) - 1)],
        "downswing": candidates[max(peak_rotation_idx, peak_motion_idx - 1)],
        "early_follow_through": candidates[min(peak_motion_idx + 1, len(candidates) - 1)],
        "finish": candidates[-1],
    }

    impact_idx, adjusted_phases = _resolve_slot_collisions(
        candidates,
        slot_indices,
        candidates[peak_motion_idx],
        peak_motion_idx,
        peak_rotation_idx,
    )
    # region agent log
    agent_log(
        hypothesis_id="H1",
        location="phase_detector.py:post_collision",
        message="slot assignment after collision resolve",
        data={
            "window_start": window.start_frame,
            "window_end": window.end_frame,
            "candidates": candidates,
            "peak_motion_idx": peak_motion_idx,
            "peak_rotation_idx": peak_rotation_idx,
            "slot_indices": dict(slot_indices),
            "impact_idx": impact_idx,
            "adjusted_phases": sorted(adjusted_phases),
        },
    )
    # endregion
    impact_conf, impact_visible, impact_notes = _frame_confidence(
        frames, impact_idx, pose_sequence
    )
    if "impact" in adjusted_phases:
        impact_conf = min(impact_conf, COLLISION_CONFIDENCE_CAP)
        impact_notes = (
            f"{impact_notes} {COLLISION_ADJUSTMENT_NOTE}".strip()
            if impact_notes
            else COLLISION_ADJUSTMENT_NOTE
        )
    use_exact_impact = impact_conf >= IMPACT_CONFIDENCE_THRESHOLD and impact_visible
    impact_phase_name = "impact" if use_exact_impact else "impact_window_estimate"
    if not use_exact_impact and not impact_notes:
        impact_notes = "Impact estimated from motion peak; exact contact not confirmed."

    phases: list[PhaseFrame] = []
    keyframe_indices: dict[str, int] = {}

    for phase_name in FULL_SWING_PHASE_ORDER:
        if phase_name == "impact":
            idx = impact_idx
            conf, visible, notes = impact_conf, impact_visible, impact_notes
            stored = impact_phase_name
        else:
            idx = slot_indices[phase_name]
            conf, visible, notes = _frame_confidence(frames, idx, pose_sequence)
            stored = phase_name
            if phase_name in adjusted_phases:
                conf = min(conf, COLLISION_CONFIDENCE_CAP)
                notes = (
                    f"{notes} {COLLISION_ADJUSTMENT_NOTE}".strip()
                    if notes
                    else COLLISION_ADJUSTMENT_NOTE
                )

        phases.append(
            PhaseFrame(
                phase=stored,
                frame_index=idx,
                confidence=conf,
                person_visible=visible,
                notes=notes,
            )
        )
        keyframe_indices[stored] = idx

    # region agent log
    index_groups: dict[int, list[str]] = {}
    for phase in phases:
        index_groups.setdefault(phase.frame_index, []).append(
            f"{phase.phase}:{round(phase.confidence, 3)}"
        )
    agent_log(
        hypothesis_id="H2",
        location="phase_detector.py:final_phase_map",
        message="final phase index groups",
        data={"index_groups": {str(k): v for k, v in index_groups.items()}},
    )
    # endregion

    return PhaseDetectionResult(phases=phases, keyframe_indices=keyframe_indices)
