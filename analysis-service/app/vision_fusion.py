from __future__ import annotations

import math
from typing import Any

import cv2
import numpy as np

from app.config import get_settings
from app.sam3_adapter import analyze_with_sam3


def _round(value: float, places: int = 2) -> float:
    if math.isnan(value) or math.isinf(value):
        return 0.0
    return round(value, places)


def _image_quality(frame: np.ndarray) -> dict[str, float | str]:
    gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
    brightness = float(np.mean(gray))
    contrast = float(np.std(gray))
    sharpness = float(cv2.Laplacian(gray, cv2.CV_64F).var())

    if brightness < 45:
        lighting = "too_dark"
    elif brightness > 215:
        lighting = "too_bright"
    else:
        lighting = "usable"

    if sharpness < 45:
        focus = "soft"
    elif sharpness < 100:
        focus = "fair"
    else:
        focus = "sharp"

    quality_score = min(
        1.0,
        max(0.0, brightness / 120)
        * 0.25
        + min(1.0, contrast / 55) * 0.25
        + min(1.0, sharpness / 180) * 0.5,
    )

    return {
        "brightness": _round(brightness, 1),
        "contrast": _round(contrast, 1),
        "sharpness": _round(sharpness, 1),
        "lighting": lighting,
        "focus": focus,
        "quality_score": _round(quality_score),
    }


def _body_visibility(checkpoints: list[dict[str, Any]]) -> dict[str, Any]:
    if not checkpoints:
        return {
            "provider": "opencv_proxy",
            "average_confidence": 0.0,
            "minimum_confidence": 0.0,
            "usable": False,
            "note": "No body checkpoints were available.",
        }

    confidences = [float(item.get("confidence", 0)) for item in checkpoints]
    avg = sum(confidences) / len(confidences)
    minimum = min(confidences)
    usable = avg >= 0.42 and minimum >= 0.25
    return {
        "provider": "opencv_proxy",
        "average_confidence": _round(avg),
        "minimum_confidence": _round(minimum),
        "usable": usable,
        "note": (
            "Body proxy is usable as supporting evidence."
            if usable
            else "Body proxy confidence is low; Gemini video read should dominate."
        ),
    }


def _line_angle(x1: int, y1: int, x2: int, y2: int) -> float:
    return math.degrees(math.atan2(y2 - y1, x2 - x1))


def _detect_shaft_line(frame: np.ndarray, body_box: dict[str, Any] | None) -> dict[str, Any]:
    gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
    edges = cv2.Canny(gray, 60, 170)
    lines = cv2.HoughLinesP(
        edges,
        rho=1,
        theta=np.pi / 180,
        threshold=55,
        minLineLength=max(32, min(frame.shape[:2]) // 8),
        maxLineGap=12,
    )

    if lines is None:
        return {"visible": False, "confidence": 0.0, "reason": "No long straight shaft-like line found."}

    height, width = frame.shape[:2]
    bx = by = bw = bh = None
    if body_box:
        bx = float(body_box.get("x", 0))
        by = float(body_box.get("y", 0))
        bw = float(body_box.get("width", 0))
        bh = float(body_box.get("height", 0))

    candidates: list[dict[str, Any]] = []
    for raw in lines[:, 0]:
        x1, y1, x2, y2 = [int(v) for v in raw]
        length = math.hypot(x2 - x1, y2 - y1)
        if length < min(width, height) * 0.12:
            continue
        angle = _line_angle(x1, y1, x2, y2)
        abs_angle = abs(angle)
        if abs_angle < 12 or abs_angle > 168:
            continue

        midpoint_x = (x1 + x2) / 2
        midpoint_y = (y1 + y2) / 2
        near_body = True
        if bx is not None and by is not None and bw is not None and bh is not None:
            margin_x = bw * 0.55
            margin_y = bh * 0.35
            near_body = (
                bx - margin_x <= midpoint_x <= bx + bw + margin_x
                and by - margin_y <= midpoint_y <= by + bh + margin_y
            )
        if not near_body:
            continue

        candidates.append(
            {
                "x1": x1,
                "y1": y1,
                "x2": x2,
                "y2": y2,
                "length": _round(length, 1),
                "angle_degrees": _round(angle, 1),
            }
        )

    if not candidates:
        return {
            "visible": False,
            "confidence": 0.15,
            "reason": "Straight lines were present, but none looked like a club shaft near the golfer.",
        }

    best = max(candidates, key=lambda item: float(item["length"]))
    length_score = min(1.0, float(best["length"]) / (min(width, height) * 0.45))
    confidence = 0.35 + length_score * 0.45
    return {
        "visible": True,
        "confidence": _round(confidence),
        "shaft_line": best,
        "candidate_count": len(candidates),
        "reason": "A long straight line near the golfer likely represents the shaft; treat as supporting evidence.",
    }


def _checkpoint_quality(
    keyframe_indices: dict[str, int],
    *,
    frame_count: int,
    expected_order: list[str],
) -> dict[str, Any]:
    ordered = [(phase, keyframe_indices.get(phase)) for phase in expected_order if phase in keyframe_indices]
    index_values = [idx for _, idx in ordered if idx is not None]
    monotonic = all(index_values[i] <= index_values[i + 1] for i in range(len(index_values) - 1))
    duplicated = len(set(index_values)) != len(index_values)
    coverage = 0.0 if frame_count <= 1 or not index_values else (max(index_values) - min(index_values)) / (frame_count - 1)

    if not monotonic:
        confidence = 0.2
    elif duplicated:
        confidence = 0.45
    elif coverage < 0.65:
        confidence = 0.55
    else:
        confidence = 0.78

    return {
        "ordered_labels": [phase for phase, _ in ordered],
        "monotonic": monotonic,
        "duplicated_indices": duplicated,
        "coverage": _round(coverage),
        "confidence": _round(confidence),
        "note": (
            "Checkpoint order is usable, but labels are still timing estimates unless Gemini confirms from video."
            if monotonic
            else "Checkpoint order is unreliable."
        ),
    }


def build_hybrid_vision_evidence(
    *,
    frames: list[np.ndarray],
    keyframe_indices: dict[str, int],
    metric_payload: dict[str, Any],
    expected_order: list[str],
) -> dict[str, Any]:
    checkpoints = metric_payload.get("checkpoints", [])
    ordered_phases = [phase for phase in expected_order if phase in keyframe_indices]

    frame_evidence: list[dict[str, Any]] = []
    shaft_scores: list[float] = []
    quality_scores: list[float] = []

    checkpoint_by_phase = {
        item.get("checkpoint"): item for item in checkpoints if isinstance(item, dict)
    }

    for phase in ordered_phases:
        idx = keyframe_indices[phase]
        if idx < 0 or idx >= len(frames):
            continue
        checkpoint = checkpoint_by_phase.get(phase, {})
        quality = _image_quality(frames[idx])
        shaft = _detect_shaft_line(frames[idx], checkpoint.get("body_box") if checkpoint else None)
        frame_evidence.append(
            {
                "label": phase,
                "frame_index": idx,
                "image_quality": quality,
                "body_confidence": checkpoint.get("confidence"),
                "body_box": checkpoint.get("body_box"),
                "club_shaft": shaft,
            }
        )
        quality_scores.append(float(quality["quality_score"]))
        shaft_scores.append(float(shaft.get("confidence", 0)))

    body = _body_visibility(checkpoints)
    checkpoint_quality = _checkpoint_quality(
        keyframe_indices,
        frame_count=len(frames),
        expected_order=expected_order,
    )
    avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
    best_shaft = max(shaft_scores) if shaft_scores else 0
    shaft_visible_count = sum(1 for item in frame_evidence if item["club_shaft"].get("visible"))
    settings = get_settings()
    sam3 = analyze_with_sam3(
        frames=frames,
        frame_evidence=frame_evidence,
        model_name=settings.sam3_model,
        enabled=settings.sam3_enabled,
        max_frames=settings.sam3_max_frames,
        confidence=settings.sam3_confidence,
    )
    sam3_club_confidence = (
        float(sam3.get("club_visible_confidence", 0))
        if sam3.get("available")
        else 0.0
    )
    best_club_confidence = max(best_shaft, sam3_club_confidence)
    fusion_confidence = (
        float(body["average_confidence"]) * 0.3
        + float(checkpoint_quality["confidence"]) * 0.25
        + avg_quality * 0.2
        + best_club_confidence * 0.25
    )

    return {
        "body_tracking": body,
        "club_tracking": {
            "provider": "sam3_plus_opencv_hough_line_proxy",
            "visible_frame_count": shaft_visible_count,
            "opencv_best_confidence": _round(best_shaft),
            "sam3_best_confidence": _round(sam3_club_confidence),
            "best_confidence": _round(best_club_confidence),
            "usable": best_club_confidence >= 0.45,
            "note": (
                "Club/shaft is visible enough for supporting shaft-plane observations."
                if best_club_confidence >= 0.45
                else "Club/shaft visibility is weak; avoid exact club path or face claims."
            ),
        },
        "sam3_segmentation": sam3,
        "camera_angle_detection": metric_payload.get("camera_angle", "unknown"),
        "checkpoint_quality": checkpoint_quality,
        "frame_evidence": frame_evidence,
        "fusion_confidence": _round(fusion_confidence),
        "primary_truth": "Gemini full-video vision",
        "supporting_evidence_order": [
            "full_video",
            "ordered_checkpoint_frames",
            "sam3_segmentation",
            "body_tracking_proxy",
            "club_shaft_proxy",
            "camera_angle_detection",
            "confidence_scores",
        ],
        "upgrade_path": {
            "body_tracking_adapter": "Replace opencv_proxy with RTMPose/MMPose keypoints.",
            "club_tracking_adapter": "Use SAM 3 segmentation now; later fine-tune a golf club/shaft detector for higher confidence.",
        },
    }
