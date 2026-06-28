from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np


@dataclass
class BodyProxy:
    bbox: tuple[int, int, int, int]
    center: tuple[float, float]
    confidence: float


def score_frame_person(frame: np.ndarray) -> BodyProxy:
    """Estimate person presence via contour bbox heuristics (no ML)."""
    height, width = frame.shape[:2]
    gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
    blur = cv2.GaussianBlur(gray, (9, 9), 0)
    edges = cv2.Canny(blur, 40, 120)
    kernel = np.ones((7, 7), np.uint8)
    dilated = cv2.dilate(edges, kernel, iterations=2)
    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    candidates: list[tuple[int, int, int, int]] = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        area = w * h
        if area < width * height * 0.01:
            continue
        if h < height * 0.20:
            continue
        candidates.append((x, y, w, h))

    if not candidates:
        x, y, w, h = int(width * 0.25), int(height * 0.12), int(width * 0.5), int(height * 0.78)
        return BodyProxy((x, y, w, h), (x + w / 2, y + h / 2), 0.2)

    x1 = min(x for x, _, _, _ in candidates)
    y1 = min(y for _, y, _, _ in candidates)
    x2 = max(x + w for x, y, w, h in candidates)
    y2 = max(y + h for x, y, w, h in candidates)
    w = max(1, x2 - x1)
    h = max(1, y2 - y1)
    area_ratio = min(1.0, (w * h) / (width * height * 0.55))
    height_ratio = h / max(height, 1)
    confidence = max(0.25, min(0.92, area_ratio * 0.6 + height_ratio * 0.4))
    return BodyProxy((x1, y1, w, h), (x1 + w / 2, y1 + h / 2), confidence)


def frame_motion_score(frames: list[np.ndarray], index: int) -> float:
    """Frame-to-frame diff magnitude normalized 0-1."""
    if index <= 0 or index >= len(frames):
        return 0.0
    prev_gray = cv2.cvtColor(frames[index - 1], cv2.COLOR_RGB2GRAY)
    curr_gray = cv2.cvtColor(frames[index], cv2.COLOR_RGB2GRAY)
    diff = cv2.absdiff(prev_gray, curr_gray)
    return float(min(1.0, np.mean(diff) / 40.0))
