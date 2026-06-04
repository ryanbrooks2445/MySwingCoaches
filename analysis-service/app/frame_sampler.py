from __future__ import annotations

from app.schemas import CHECKPOINTS


def sample_keyframe_indices(num_frames: int) -> dict[str, int]:
    """Evenly sample frames across the clip for Gemini and the report gallery."""
    if num_frames <= 0:
        return {phase: 0 for phase in CHECKPOINTS}
    if num_frames == 1:
        return {phase: 0 for phase in CHECKPOINTS}

    n = len(CHECKPOINTS)
    return {
        phase: min(int(i * (num_frames - 1) / (n - 1)), num_frames - 1)
        for i, phase in enumerate(CHECKPOINTS)
    }
