from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess

import cv2


class MediaValidationError(ValueError):
    """Raised when an uploaded file is not safe or useful for analysis."""


@dataclass(frozen=True)
class VideoMetadata:
    duration_sec: float
    width: int
    height: int
    frame_count: int
    fps: float


def validate_and_normalize_video(
    path: Path,
    *,
    max_duration_sec: int = 30,
    max_size_bytes: int = 100 * 1024 * 1024,
) -> VideoMetadata:
    if not path.exists() or path.stat().st_size <= 0:
        raise MediaValidationError("Upload is empty or missing.")
    if path.stat().st_size > max_size_bytes:
        raise MediaValidationError("Video must be under 100 MB.")

    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        raise MediaValidationError("Upload is not a valid video.")

    fps = float(cap.get(cv2.CAP_PROP_FPS) or 0)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
    ok, _frame = cap.read()
    cap.release()

    if not ok or fps <= 0 or frame_count < 5 or width <= 0 or height <= 0:
        raise MediaValidationError("Upload is not a valid video with visible frames.")

    duration = frame_count / fps
    if duration > max_duration_sec + 0.1:
        raise MediaValidationError(f"Video must be {max_duration_sec} seconds or shorter.")

    normalized = path.with_name(f"{path.stem}.normalized.mp4")
    command = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-i",
        str(path),
        "-map",
        "0:v:0",
        "-map",
        "0:a?",
        "-map_metadata",
        "-1",
        "-vf",
        "scale='min(1280,iw)':-2:force_original_aspect_ratio=decrease,fps=30",
        "-c:v",
        "libx264",
        "-preset",
        "fast",
        "-crf",
        "22",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-b:a",
        "128k",
        "-movflags",
        "+faststart",
        str(normalized),
    ]
    try:
        subprocess.run(command, check=True, capture_output=True, text=True, timeout=120)
        normalized.replace(path)
    except (FileNotFoundError, subprocess.SubprocessError) as exc:
        normalized.unlink(missing_ok=True)
        raise MediaValidationError("Video could not be prepared for analysis.") from exc

    normalized_cap = cv2.VideoCapture(str(path))
    normalized_fps = float(normalized_cap.get(cv2.CAP_PROP_FPS) or 0)
    normalized_frames = int(normalized_cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    normalized_width = int(normalized_cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
    normalized_height = int(normalized_cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
    normalized_cap.release()

    return VideoMetadata(
        duration_sec=normalized_frames / normalized_fps,
        width=normalized_width,
        height=normalized_height,
        frame_count=normalized_frames,
        fps=normalized_fps,
    )
