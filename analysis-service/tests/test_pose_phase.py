import numpy as np

from app.pose_extractor import FramePose, PoseLandmark, PoseSequence
from app.pose_phase import (
    build_pose_timeline,
    pick_phases_from_pose_timeline,
    validate_phase_assignments,
)
from app.swing_window import SwingWindow


def _landmarks(*, wrist_y: float = 0.5) -> list[PoseLandmark]:
    points: list[PoseLandmark | None] = [None] * 33
    mapping = {
        0: (0.5, 0.2),
        11: (0.45, 0.3),
        12: (0.55, 0.3),
        13: (0.43, 0.42),
        14: (0.57, 0.42),
        15: (0.42, wrist_y),
        16: (0.58, wrist_y + 0.02),
        23: (0.46, 0.55),
        24: (0.54, 0.55),
        25: (0.46, 0.72),
        26: (0.54, 0.72),
        27: (0.46, 0.9),
        28: (0.54, 0.9),
    }
    for idx, (x, y) in mapping.items():
        points[idx] = PoseLandmark(x=x, y=y, z=0.0, visibility=0.95)
    return [point if point is not None else PoseLandmark(0, 0, 0, 0) for point in points]


def _synthetic_frames(count: int = 30) -> list[np.ndarray]:
    frames: list[np.ndarray] = []
    for i in range(count):
        frame = np.full((240, 320, 3), 20, dtype=np.uint8)
        x = 120 + i * 2
        frame[40:200, x : x + 40] = [180, 180, 180]
        frames.append(frame)
    return frames


def test_build_pose_timeline_returns_curves() -> None:
    frames = _synthetic_frames(20)
    window = SwingWindow(0, 19, 2.0, 1.0, 30.0)
    sequence = PoseSequence(
        frames=[FramePose(i, 0.8, _landmarks(wrist_y=0.8 - i * 0.02)) for i in range(20)],
        average_confidence=0.8,
    )
    timeline = build_pose_timeline(frames, sequence, window)
    assert len(timeline["frame_indices"]) >= 10
    assert len(timeline["wrist_height_norm"]) == len(timeline["frame_indices"])
    assert len(timeline["motion"]) == len(timeline["frame_indices"])


def test_pick_phases_from_pose_timeline_is_monotonic() -> None:
    frames = _synthetic_frames(40)
    window = SwingWindow(0, 39, 4.0, 1.0, 30.0)
    wrist_curve = [0.8 - abs(i - 12) * 0.03 for i in range(40)]
    sequence = PoseSequence(
        frames=[FramePose(i, 0.8, _landmarks(wrist_y=wrist_curve[i])) for i in range(40)],
        average_confidence=0.8,
    )
    result = pick_phases_from_pose_timeline(frames, window, sequence)
    ordered = [result.indices[phase] for phase in (
        "address",
        "takeaway",
        "top",
        "transition",
        "downswing",
        "impact",
        "early_follow_through",
        "finish",
    )]
    assert ordered == sorted(ordered)
    assert result.indices["top"] < result.indices["impact"]
    assert result.timeline["frame_indices"]


def test_validate_phase_assignments_flags_bad_top() -> None:
    wrist_curve = [0.9 - abs(i - 2) * 0.05 for i in range(10)]
    validation = validate_phase_assignments(
        PoseSequence(frames=[FramePose(i, 0.8, _landmarks()) for i in range(10)], average_confidence=0.8),
        {"address": 0, "top": 5, "impact": 8, "finish": 9},
        window_indices=list(range(10)),
        wrist_curve=wrist_curve,
        motion_curve=[0.1] * 10,
    )
    assert validation["address"]["validated"] is True
    assert validation["top"]["validated"] is False
