from __future__ import annotations

import json
import logging
import mimetypes
import time
from pathlib import Path

import cv2
import numpy as np
from google import genai
from google.genai import types

from app.phase_detector import PhaseDetectionResult

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


def upload_video(client: genai.Client, video_path: Path) -> types.File:
    mime = _mime_for_video(video_path)
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


def frame_to_jpeg_bytes(frame: np.ndarray, quality: int = 90) -> bytes:
    bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
    ok, encoded = cv2.imencode(".jpg", bgr, [cv2.IMWRITE_JPEG_QUALITY, quality])
    if not ok:
        raise ValueError("Failed to encode frame as JPEG")
    return encoded.tobytes()


def build_phase_evidence_packet(
    phase_result: PhaseDetectionResult,
    swing_window: dict | None = None,
) -> str:
    payload = {
        "swing_window": swing_window or {},
        "phases": phase_result.phase_map,
        "limitations": phase_result.limitation_notes(),
        "rules": [
            "Only grade setup from address/takeaway when person_visible and confidence >= 0.4.",
            "Only grade path/sequencing from downswing/impact when person_visible and confidence >= 0.4.",
            "Only grade finish/balance from early_follow_through/finish when person_visible and confidence >= 0.4.",
            "If impact phase is impact_window_estimate or confidence < 0.5, include limitation language and avoid precise impact claims.",
            "Mark checkpoints not_visible when person_visible is false for that phase.",
        ],
    }
    return json.dumps(payload, indent=2)


def build_keyframe_parts(
    frames: list[np.ndarray],
    phase_result: PhaseDetectionResult,
    swing_mode: str = "full_swing",
) -> list[types.Part]:
    motion_label = {"full_swing": "swing", "chipping": "chip", "putting": "putting stroke"}.get(
        swing_mode, "swing"
    )
    parts: list[types.Part] = []
    total = len(frames)

    for phase_frame in phase_result.phases:
        idx = phase_frame.frame_index
        if idx < 0 or idx >= total:
            continue
        if not phase_frame.person_visible and phase_frame.confidence < 0.4:
            parts.append(
                types.Part.from_text(
                    text=(
                        f"Phase '{phase_frame.phase.replace('_', ' ')}' — NOT USABLE "
                        f"(person not visible, confidence {phase_frame.confidence:.2f}). "
                        "Do not claim observations for this phase."
                    )
                )
            )
            continue

        pct = int((idx / max(total - 1, 1)) * 100)
        label = phase_frame.phase.replace("_", " ")
        notes = f" Notes: {phase_frame.notes}" if phase_frame.notes else ""
        parts.append(
            types.Part.from_text(
                text=(
                    f"Verified still — {pct}% through the {motion_label}. "
                    f"Phase: {label}. Confidence: {phase_frame.confidence:.2f}. "
                    f"Person visible: {phase_frame.person_visible}.{notes}"
                )
            )
        )
        jpeg = frame_to_jpeg_bytes(frames[idx])
        parts.append(types.Part.from_bytes(data=jpeg, mime_type="image/jpeg"))

    return parts
