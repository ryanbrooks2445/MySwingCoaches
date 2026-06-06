from __future__ import annotations

from app.schemas import CHECKPOINTS_BY_MODE, SwingMode

FULL_SWING_CHECKPOINT_PCTS = {
    "setup_address": 0.03,
    "takeaway": 0.14,
    "club_parallel_back": 0.24,
    "lead_arm_parallel_back": 0.34,
    "top_of_backswing": 0.45,
    "transition": 0.52,
    "lead_arm_parallel_down": 0.62,
    "shaft_parallel_down": 0.72,
    "impact": 0.80,
    "release": 0.88,
    "finish": 0.97,
}


def checkpoints_for_mode(swing_mode: SwingMode) -> list[str]:
    return CHECKPOINTS_BY_MODE.get(swing_mode, CHECKPOINTS_BY_MODE["full_swing"])


def sample_keyframe_indices(num_frames: int, swing_mode: SwingMode = "full_swing") -> dict[str, int]:
    """Sample ordered swing checkpoints for Gemini and the report gallery."""
    phases = checkpoints_for_mode(swing_mode)
    if num_frames <= 0:
        return {phase: 0 for phase in phases}
    if num_frames == 1:
        return {phase: 0 for phase in phases}

    if swing_mode == "full_swing":
        return {
            phase: min(round(FULL_SWING_CHECKPOINT_PCTS.get(phase, 0) * (num_frames - 1)), num_frames - 1)
            for phase in phases
        }

    n = len(phases)
    return {
        phase: min(int(i * (num_frames - 1) / (n - 1)), num_frames - 1)
        for i, phase in enumerate(phases)
    }


def keyframe_timestamps(
    keyframe_indices: dict[str, int],
    *,
    fps: float,
    sample_every_n: int = 2,
) -> dict[str, float]:
    if fps <= 0:
        return {phase: 0.0 for phase in keyframe_indices}
    return {
        phase: round((idx * sample_every_n) / fps, 2)
        for phase, idx in keyframe_indices.items()
    }


def keyframe_debug_metadata(
    keyframe_indices: dict[str, int],
    *,
    fps: float,
    sample_every_n: int = 2,
) -> list[dict[str, float | int | str]]:
    timestamps = keyframe_timestamps(keyframe_indices, fps=fps, sample_every_n=sample_every_n)
    return [
        {
            "label": phase,
            "frame_index": idx,
            "timestamp_sec": timestamps.get(phase, 0.0),
        }
        for phase, idx in keyframe_indices.items()
    ]
