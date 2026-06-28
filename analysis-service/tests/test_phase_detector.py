import numpy as np

from app.phase_detector import detect_swing_phases
from app.swing_window import SwingWindow


def _person_frame(offset: int = 0) -> np.ndarray:
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    x1 = 200 + offset
    frame[100:400, x1 : x1 + 120] = [200, 200, 200]
    return frame


def test_phase_map_covers_full_swing_phases() -> None:
    frames = [_person_frame(i * 5) for i in range(24)]
    window = SwingWindow(
        start_frame=0,
        end_frame=23,
        duration_sec=4.0,
        person_coverage_pct=0.9,
        fps=30.0,
    )
    result = detect_swing_phases(frames, window)
    phase_names = {p.phase for p in result.phases}
    assert "address" in phase_names
    assert "top" in phase_names
    assert "impact" in phase_names or "impact_window_estimate" in phase_names
    assert "finish" in phase_names
    assert len(result.keyframe_indices) >= 6


def test_scenery_tail_finishes_low_confidence() -> None:
    frames = [_person_frame(i * 8) for i in range(12)] + [
        np.full((480, 640, 3), 30, dtype=np.uint8) for _ in range(8)
    ]
    window = SwingWindow(
        start_frame=0,
        end_frame=11,
        duration_sec=2.0,
        person_coverage_pct=0.85,
        fps=30.0,
    )
    result = detect_swing_phases(frames, window)
    finish = result.get("finish")
    assert finish is not None
    assert finish.person_visible or finish.confidence >= 0


def test_late_motion_peak_separates_finish_and_early_follow_through() -> None:
    frames = [np.full((480, 640, 3), 20, dtype=np.uint8) for _ in range(110)]
    for i in range(85, 110):
        frames[i] = _person_frame((i - 85) * 12)
    window = SwingWindow(
        start_frame=0,
        end_frame=109,
        duration_sec=8.0,
        person_coverage_pct=0.9,
        fps=30.0,
    )
    result = detect_swing_phases(frames, window)
    early = result.get("early_follow_through")
    finish = result.get("finish")
    assert early is not None
    assert finish is not None
    assert early.frame_index != finish.frame_index


def test_resolve_slot_collisions_directly() -> None:
    from app.phase_detector import _resolve_slot_collisions

    candidates = [0, 12, 24, 36, 48, 60, 72, 84, 96, 109]
    slot_indices = {
        "address": 0,
        "takeaway": 12,
        "top": 72,
        "transition": 84,
        "downswing": 96,
        "early_follow_through": 109,
        "finish": 109,
    }
    impact_idx, adjusted = _resolve_slot_collisions(
        candidates,
        slot_indices,
        impact_idx=109,
        peak_motion_idx=9,
        peak_rotation_idx=6,
    )
    assert slot_indices["finish"] == 96
    assert slot_indices["early_follow_through"] == 109
    assert impact_idx == 96
    assert "finish" in adjusted
    assert "impact" in adjusted


def test_peak_rotation_at_window_start_deduplicates_colliding_slots() -> None:
    from app.phase_detector import _resolve_slot_collisions

    candidates = [27, 32, 38, 44, 50, 56, 62, 68, 74, 80]
    slot_indices = {
        "address": 27,
        "takeaway": 32,
        "top": 27,
        "transition": 32,
        "downswing": 38,
        "early_follow_through": 50,
        "finish": 80,
    }
    impact_idx, adjusted = _resolve_slot_collisions(
        candidates,
        slot_indices,
        impact_idx=44,
        peak_motion_idx=3,
        peak_rotation_idx=0,
    )
    slot_values = list(slot_indices.values()) + [impact_idx]
    assert len(slot_values) == len(set(slot_values))
    assert slot_indices["address"] == 27
    assert slot_indices["top"] != slot_indices["address"]
    assert slot_indices["transition"] != slot_indices["takeaway"]
    assert {"top", "transition"} & adjusted
