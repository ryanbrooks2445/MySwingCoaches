from __future__ import annotations

import logging
import mimetypes
import time
from pathlib import Path

import cv2
import numpy as np
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

POLL_INTERVAL_SEC = 2
MAX_POLL_ATTEMPTS = 90


def _mime_for_video(path: Path) -> str:
    mime, _ = mimetypes.guess_type(str(path))
    if mime:
        return mime
    ext = path.suffix.lower()
    if ext in {".mov", ".qt"}:
        return "video/quicktime"
    return "video/mp4"


def upload_video(client: genai.Client, video_path: Path, mime_type: str | None = None) -> types.File:
    mime = mime_type or _mime_for_video(video_path)
    uploaded = client.files.upload(
        file=str(video_path),
        config=types.UploadFileConfig(mime_type=mime),
    )
    if not uploaded.name:
        raise ValueError("Gemini file upload did not return a file name")

    for _ in range(MAX_POLL_ATTEMPTS):
        file_info = client.files.get(name=uploaded.name)
        state = file_info.state
        if state == types.FileState.ACTIVE or str(state) == "ACTIVE":
            logger.info("Gemini video ready: %s", uploaded.name)
            return file_info
        if state == types.FileState.FAILED or str(state) == "FAILED":
            raise ValueError(f"Gemini video processing failed for {uploaded.name}")
        time.sleep(POLL_INTERVAL_SEC)

    raise TimeoutError("Timed out waiting for Gemini to process the uploaded video")


def delete_uploaded_file(client: genai.Client, uploaded: types.File | None) -> None:
    if not uploaded or not uploaded.name:
        return
    try:
        client.files.delete(name=uploaded.name)
    except Exception as exc:
        logger.warning("Could not delete Gemini uploaded file: %s", exc)


def frame_to_jpeg_bytes(frame: np.ndarray, quality: int = 92) -> bytes:
    bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
    ok, encoded = cv2.imencode(".jpg", bgr, [cv2.IMWRITE_JPEG_QUALITY, quality])
    if not ok:
        raise ValueError("Failed to encode frame as JPEG")
    return encoded.tobytes()


def build_keyframe_parts(
    frames: list[np.ndarray],
    keyframe_indices: dict[str, int],
    frame_timestamps: dict[str, float] | None = None,
) -> list[types.Part]:
    """Attach ordered checkpoint stills as visual reference to the full video."""
    parts: list[types.Part] = []
    total = len(frames)
    for phase, idx in keyframe_indices.items():
        if idx < 0 or idx >= total:
            continue
        pct = int((idx / max(total - 1, 1)) * 100)
        timestamp = frame_timestamps.get(phase) if frame_timestamps else None
        timestamp_text = f"{timestamp:.2f}s" if timestamp is not None else "unknown timestamp"
        jpeg = frame_to_jpeg_bytes(frames[idx])
        parts.append(
            types.Part.from_text(
                text=(
                    f"Ordered checkpoint still: {phase.replace('_', ' ')} at {timestamp_text} "
                    f"(roughly {pct}% through the sampled clip). Use the full video as primary evidence; "
                    "if this label appears slightly off, correct it from the video."
                )
            )
        )
        parts.append(types.Part.from_bytes(data=jpeg, mime_type="image/jpeg"))
    return parts
