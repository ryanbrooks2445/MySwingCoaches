import numpy as np
import pytest

from app.swing_window import SwingWindowError, detect_swing_window


def _person_frame(width: int = 640, height: int = 480) -> np.ndarray:
    frame = np.zeros((height, width, 3), dtype=np.uint8)
    frame[height // 4 : height * 3 // 4, width // 4 : width * 3 // 4] = [180, 180, 180]
    return frame


def _scenery_frame(width: int = 640, height: int = 480) -> np.ndarray:
    frame = np.full((height, width, 3), 40, dtype=np.uint8)
    frame[0:20, :] = [120, 180, 120]
    return frame


def test_detects_contiguous_swing_window() -> None:
    frames = [_person_frame() for _ in range(30)] + [_scenery_frame() for _ in range(10)]
    window = detect_swing_window(frames, fps=30.0, sample_every_n=2)
    assert window.start_frame == 0
    assert window.end_frame == 29
    assert window.duration_sec >= 1.5


def test_accepts_trimmed_swing_window_over_one_and_quarter_seconds() -> None:
    frames = [_person_frame() for _ in range(21)] + [_scenery_frame() for _ in range(10)]
    window = detect_swing_window(frames, fps=30.0, sample_every_n=2)
    assert window.duration_sec >= 1.25


def test_rejects_mostly_scenery() -> None:
    frames = [_scenery_frame() for _ in range(30)]
    with pytest.raises(SwingWindowError, match="enough of your swing"):
        detect_swing_window(frames, fps=30.0, sample_every_n=2)


def test_rejects_short_person_segment() -> None:
    frames = [_scenery_frame() for _ in range(10)] + [_person_frame() for _ in range(4)] + [
        _scenery_frame() for _ in range(10)
    ]
    with pytest.raises(SwingWindowError, match="enough of your swing"):
        detect_swing_window(frames, fps=30.0, sample_every_n=2)
