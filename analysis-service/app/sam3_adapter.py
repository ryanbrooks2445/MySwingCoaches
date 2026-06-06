from __future__ import annotations

import logging
import math
from functools import lru_cache
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)

SAM_CONCEPTS = ["golfer", "golf club", "club shaft", "club head", "golf ball", "hands"]


def _round(value: float, places: int = 2) -> float:
    if math.isnan(value) or math.isinf(value):
        return 0.0
    return round(value, places)


@lru_cache(maxsize=2)
def _load_sam_model(model_name: str):
    from ultralytics import SAM

    return SAM(model_name)


def _mask_summary(results: Any, frame_shape: tuple[int, int, int]) -> dict[str, Any]:
    height, width = frame_shape[:2]
    summaries: list[dict[str, Any]] = []

    for result in results or []:
        masks = getattr(result, "masks", None)
        boxes = getattr(result, "boxes", None)
        if masks is None:
            continue

        mask_data = getattr(masks, "data", None)
        if mask_data is None:
            continue

        try:
            mask_array = mask_data.detach().cpu().numpy()
        except AttributeError:
            mask_array = np.asarray(mask_data)

        try:
            xyxy = boxes.xyxy.detach().cpu().numpy() if boxes is not None and boxes.xyxy is not None else []
        except AttributeError:
            xyxy = np.asarray(getattr(boxes, "xyxy", []))

        try:
            confs = boxes.conf.detach().cpu().numpy() if boxes is not None and boxes.conf is not None else []
        except AttributeError:
            confs = np.asarray(getattr(boxes, "conf", []))

        for idx, mask in enumerate(mask_array):
            area_ratio = float(np.count_nonzero(mask > 0.5)) / max(width * height, 1)
            box = xyxy[idx].tolist() if idx < len(xyxy) else None
            confidence = float(confs[idx]) if idx < len(confs) else None
            summaries.append(
                {
                    "area_ratio": _round(area_ratio, 4),
                    "box": [round(float(v), 1) for v in box] if box else None,
                    "confidence": _round(confidence) if confidence is not None else None,
                }
            )

    return {
        "mask_count": len(summaries),
        "largest_area_ratio": max((item["area_ratio"] for item in summaries), default=0.0),
        "masks": summaries[:5],
    }


def _safe_predict(model: Any, frame: np.ndarray, *, conf: float, **kwargs: Any) -> list[Any]:
    try:
        return model.predict(frame, verbose=False, conf=conf, **kwargs)
    except Exception as exc:
        logger.debug("SAM prediction attempt failed: %s", exc)
        return []


def _bbox_from_line(line: dict[str, Any], frame_shape: tuple[int, int, int]) -> list[float]:
    height, width = frame_shape[:2]
    x1 = float(line.get("x1", 0))
    y1 = float(line.get("y1", 0))
    x2 = float(line.get("x2", 0))
    y2 = float(line.get("y2", 0))
    pad = max(10.0, min(width, height) * 0.04)
    return [
        max(0.0, min(x1, x2) - pad),
        max(0.0, min(y1, y2) - pad),
        min(float(width - 1), max(x1, x2) + pad),
        min(float(height - 1), max(y1, y2) + pad),
    ]


def _bbox_from_body(body_box: dict[str, Any]) -> list[float]:
    return [
        float(body_box.get("x", 0)),
        float(body_box.get("y", 0)),
        float(body_box.get("x", 0)) + float(body_box.get("width", 0)),
        float(body_box.get("y", 0)) + float(body_box.get("height", 0)),
    ]


def analyze_with_sam3(
    *,
    frames: list[np.ndarray],
    frame_evidence: list[dict[str, Any]],
    model_name: str,
    enabled: bool,
    max_frames: int,
    confidence: float,
) -> dict[str, Any]:
    if not enabled:
        return {
            "provider": "sam3",
            "available": False,
            "reason": "SAM 3 is disabled by configuration.",
        }

    if not frames or not frame_evidence:
        return {
            "provider": "sam3",
            "available": False,
            "reason": "No frames were available for SAM 3 segmentation.",
        }

    try:
        model = _load_sam_model(model_name)
    except Exception as exc:
        return {
            "provider": "sam3",
            "available": False,
            "model": model_name,
            "reason": f"SAM 3 model could not be loaded: {str(exc)[:220]}",
            "fallback": "opencv_hough_line_proxy",
        }

    selected = frame_evidence[: max(1, max_frames)]
    concept_hits: dict[str, int] = {concept: 0 for concept in SAM_CONCEPTS}
    frame_results: list[dict[str, Any]] = []
    box_prompt_hits = {"golfer": 0, "club_or_shaft": 0}

    for item in selected:
        idx = int(item.get("frame_index", -1))
        if idx < 0 or idx >= len(frames):
            continue
        frame = frames[idx]
        concepts: dict[str, Any] = {}

        for concept in SAM_CONCEPTS:
            results = (
                _safe_predict(model, frame, conf=confidence, texts=[concept])
                or _safe_predict(model, frame, conf=confidence, text=concept)
                or _safe_predict(model, frame, conf=confidence, prompts={"texts": [concept]})
            )
            summary = _mask_summary(results, frame.shape)
            concepts[concept] = summary
            if summary["mask_count"] > 0:
                concept_hits[concept] += 1

        prompted: dict[str, Any] = {}
        body_box = item.get("body_box")
        if isinstance(body_box, dict):
            summary = _mask_summary(
                _safe_predict(model, frame, conf=confidence, bboxes=[_bbox_from_body(body_box)]),
                frame.shape,
            )
            prompted["golfer_body_box"] = summary
            if summary["mask_count"] > 0:
                box_prompt_hits["golfer"] += 1

        shaft_line = item.get("club_shaft", {}).get("shaft_line") if isinstance(item.get("club_shaft"), dict) else None
        if isinstance(shaft_line, dict):
            summary = _mask_summary(
                _safe_predict(model, frame, conf=confidence, bboxes=[_bbox_from_line(shaft_line, frame.shape)]),
                frame.shape,
            )
            prompted["shaft_line_box"] = summary
            if summary["mask_count"] > 0:
                box_prompt_hits["club_or_shaft"] += 1

        frame_results.append(
            {
                "label": item.get("label"),
                "frame_index": idx,
                "concepts": concepts,
                "box_prompted_masks": prompted,
            }
        )

    analyzed_count = len(frame_results)
    club_concept_hits = max(
        concept_hits.get("golf club", 0),
        concept_hits.get("club shaft", 0),
        concept_hits.get("club head", 0),
        box_prompt_hits["club_or_shaft"],
    )
    golfer_hits = max(concept_hits.get("golfer", 0), box_prompt_hits["golfer"])
    ball_hits = concept_hits.get("golf ball", 0)

    return {
        "provider": "sam3",
        "available": True,
        "model": model_name,
        "frames_analyzed": analyzed_count,
        "concepts": SAM_CONCEPTS,
        "concept_hits": concept_hits,
        "box_prompt_hits": box_prompt_hits,
        "golfer_visible_confidence": _round(golfer_hits / max(analyzed_count, 1)),
        "club_visible_confidence": _round(club_concept_hits / max(analyzed_count, 1)),
        "ball_visible_confidence": _round(ball_hits / max(analyzed_count, 1)),
        "usable_for_club_tracking": club_concept_hits > 0,
        "note": (
            "SAM 3/SAM segmentation found golf club or shaft evidence."
            if club_concept_hits > 0
            else "SAM did not confidently segment the club/shaft; avoid exact club delivery claims."
        ),
        "frame_results": frame_results,
    }
