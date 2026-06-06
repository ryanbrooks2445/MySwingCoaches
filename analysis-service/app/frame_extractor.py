from __future__ import annotations

import tempfile
import logging
from pathlib import Path

import cv2
import httpx
import numpy as np

logger = logging.getLogger(__name__)


def _log(event: str, *, swing_id: str | None, trace_id: str | None, error: str | None = None, **extra) -> None:
    logger.info(
        "%s swing_id=%s trace_id=%s error_message=%s extra=%s",
        event,
        swing_id or "",
        trace_id or "",
        error or "",
        extra,
    )


def _suffix_for_mime(mime_type: str | None) -> str:
    if mime_type == "video/quicktime":
        return ".mov"
    if mime_type == "video/x-m4v":
        return ".m4v"
    return ".mp4"


def download_video(
    video_url: str,
    *,
    mime_type: str | None = None,
    swing_id: str | None = None,
    trace_id: str | None = None,
) -> Path:
    tmp = tempfile.NamedTemporaryFile(suffix=_suffix_for_mime(mime_type), delete=False)
    tmp.close()
    path = Path(tmp.name)
    _log("video_download_started", swing_id=swing_id, trace_id=trace_id)
    with httpx.Client(timeout=120.0) as client:
        try:
            response = client.get(video_url)
            response.raise_for_status()
            path.write_bytes(response.content)
        except Exception as exc:
            _log("video_download_started", swing_id=swing_id, trace_id=trace_id, error=str(exc))
            raise
    _log(
        "video_download_complete",
        swing_id=swing_id,
        trace_id=trace_id,
        bytes=path.stat().st_size if path.exists() else 0,
    )
    return path


def extract_frames(
    video_path: Path,
    sample_every_n: int = 2,
    *,
    swing_id: str | None = None,
    trace_id: str | None = None,
) -> tuple[list[np.ndarray], float, int]:
    _log("opencv_open_attempt", swing_id=swing_id, trace_id=trace_id, path=str(video_path))
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        _log("opencv_open_attempt", swing_id=swing_id, trace_id=trace_id, error="Could not open video file")
        raise ValueError("Could not open video file")
    _log("opencv_open_success", swing_id=swing_id, trace_id=trace_id)

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    frames: list[np.ndarray] = []
    idx = 0

    while True:
        ok, frame = cap.read()
        if not ok:
            break
        if idx % sample_every_n == 0:
            frames.append(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        idx += 1

    cap.release()
    duration = len(frames) * sample_every_n / fps if fps else 0
    _log(
        "frames_extracted",
        swing_id=swing_id,
        trace_id=trace_id,
        frame_count=len(frames),
        fps=fps,
        duration_sec=int(duration),
    )
    return frames, fps, int(duration)


def save_frame_jpeg(frame: np.ndarray, path: Path) -> None:
    bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
    cv2.imwrite(str(path), bgr, [cv2.IMWRITE_JPEG_QUALITY, 90])


def get_frame_at_index(frames: list[np.ndarray], index: int) -> np.ndarray:
    index = max(0, min(index, len(frames) - 1))
    return frames[index]
