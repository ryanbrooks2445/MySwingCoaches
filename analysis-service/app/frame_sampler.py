from __future__ import annotations

from app.schemas import CHECKPOINTS_BY_MODE, SwingMode


def checkpoints_for_mode(swing_mode: SwingMode) -> list[str]:
    return CHECKPOINTS_BY_MODE.get(swing_mode, CHECKPOINTS_BY_MODE["full_swing"])


def sample_keyframe_indices(num_frames: int, swing_mode: SwingMode = "full_swing") -> dict[str, int]:
    """Evenly sample frames across the clip for Gemini and the report gallery."""
    phases = checkpoints_for_mode(swing_mode)
    if num_frames <= 0:
        return {phase: 0 for phase in phases}
    if num_frames == 1:
        return {phase: 0 for phase in phases}

    n = len(phases)
    return {
        phase: min(int(i * (num_frames - 1) / (n - 1)), num_frames - 1)
        for i, phase in enumerate(phases)
    }
