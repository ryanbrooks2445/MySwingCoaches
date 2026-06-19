from pathlib import Path

import cv2
import numpy as np
import pytest

from app.media_validation import MediaValidationError, validate_and_normalize_video


def _write_video(path: Path, *, frames: int, fps: float = 10.0) -> None:
    writer = cv2.VideoWriter(
        str(path),
        cv2.VideoWriter_fourcc(*"mp4v"),
        fps,
        (160, 120),
    )
    for _ in range(frames):
        writer.write(np.zeros((120, 160, 3), dtype=np.uint8))
    writer.release()


def test_rejects_video_longer_than_30_seconds(tmp_path: Path) -> None:
    path = tmp_path / "long.mp4"
    _write_video(path, frames=311, fps=10.0)

    with pytest.raises(MediaValidationError, match="30 seconds"):
        validate_and_normalize_video(path, max_duration_sec=30)


def test_rejects_corrupt_video(tmp_path: Path) -> None:
    path = tmp_path / "broken.mp4"
    path.write_bytes(b"not a video")

    with pytest.raises(MediaValidationError, match="valid video"):
        validate_and_normalize_video(path)


def test_accepts_short_video_and_returns_metadata(tmp_path: Path) -> None:
    path = tmp_path / "swing.mp4"
    _write_video(path, frames=20, fps=10.0)

    result = validate_and_normalize_video(path)

    assert result.duration_sec == pytest.approx(2.0, abs=0.2)
    assert result.width == 160
    assert result.height == 120
    assert result.frame_count == 60
    assert result.fps == pytest.approx(30.0)

    cap = cv2.VideoCapture(str(path))
    codec = int(cap.get(cv2.CAP_PROP_FOURCC))
    cap.release()
    codec_name = "".join(chr((codec >> (8 * index)) & 0xFF) for index in range(4)).lower()
    assert codec_name in {"avc1", "h264"}
