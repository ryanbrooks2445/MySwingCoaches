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
from app.pose_extractor import PoseSequence, build_pose_evidence, overlay_pose_skeleton

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
    pose_sequence: PoseSequence | None = None,
) -> str:
    payload = {
        "swing_window": swing_window or {},
        "phases": phase_result.phase_map,
        "phase_detection_method": getattr(phase_result, "detection_method", "unknown"),
        "limitations": phase_result.limitation_notes(),
        "rules": [
            "Full video is the primary truth for club motion, timing, and phase labels.",
            "pose_tracking.pose_timeline provides server-computed body geometry over time.",
            "pose_tracking.phase_metrics are only attached for pose-validated phase frames.",
            "Keyframe stills are approximate anchors; if they conflict with the video, trust the video.",
            "Only grade setup from address/takeaway when person_visible and confidence >= 0.4.",
            "Only grade path/sequencing from downswing/impact when person_visible and confidence >= 0.4.",
            "Only grade finish/balance from early_follow_through/finish when person_visible and confidence >= 0.4.",
            "If impact phase is impact_window_estimate or confidence < 0.5, include limitation language and avoid precise impact claims.",
            "Mark checkpoints not_visible when person_visible is false for that phase.",
        ],
    }
    if pose_sequence and pose_sequence.average_confidence > 0:
        payload["pose_tracking"] = build_pose_evidence(
            pose_sequence,
            phase_result.keyframe_indices,
            validation=getattr(phase_result, "validation", None),
            timeline=getattr(phase_result, "timeline", None),
        )
    return json.dumps(payload, indent=2)


def build_keyframe_parts(
    frames: list[np.ndarray],
    phase_result: PhaseDetectionResult,
    swing_mode: str = "full_swing",
    pose_sequence: PoseSequence | None = None,
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

        if not phase_frame.pose_validated:
            parts.append(
                types.Part.from_text(
                    text=(
                        f"Phase '{phase_frame.phase.replace('_', ' ')}' — APPROXIMATE ANCHOR ONLY "
                        f"(frame {idx}, confidence {phase_frame.confidence:.2f}). "
                        "This still was not pose-validated. Use the full video as primary truth for this phase; "
                        "do not rely on this still for club or impact geometry."
                        + (f" Notes: {phase_frame.notes}" if phase_frame.notes else "")
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
                    f"Pose-validated still — {pct}% through the {motion_label}. "
                    f"Phase: {label}. Confidence: {phase_frame.confidence:.2f}. "
                    f"Person visible: {phase_frame.person_visible}.{notes}"
                )
            )
        )
        jpeg_frame = frames[idx]
        if pose_sequence and pose_sequence.confidence_at(idx) >= 0.45:
            jpeg_frame = overlay_pose_skeleton(
                frames[idx],
                pose_sequence.landmarks_at(idx),
            )
        jpeg = frame_to_jpeg_bytes(jpeg_frame)
        parts.append(types.Part.from_bytes(data=jpeg, mime_type="image/jpeg"))

    return parts
