from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from app.person_detection import score_frame_person

PERSON_THRESHOLD = 0.38
MIN_WINDOW_FRAMES = 8
MIN_PERSON_COVERAGE = 0.40
MIN_WINDOW_SECONDS = 1.25


@dataclass
class SwingWindow:
    start_frame: int
    end_frame: int
    duration_sec: float
    person_coverage_pct: float
    fps: float

    def to_dict(self) -> dict:
        return {
            "start_frame": self.start_frame,
            "end_frame": self.end_frame,
            "duration_sec": round(self.duration_sec, 3),
            "person_coverage_pct": round(self.person_coverage_pct, 3),
            "fps": round(self.fps, 2),
        }


class SwingWindowError(ValueError):
    """Raised when no usable swing window can be detected."""


def _person_scores(frames: list[np.ndarray]) -> list[float]:
    return [score_frame_person(frame).confidence for frame in frames]


def _longest_contiguous_run(scores: list[float], threshold: float) -> tuple[int, int] | None:
    best_start = best_end = -1
    best_len = 0
    run_start = 0
    run_len = 0

    for i, score in enumerate(scores):
        if score >= threshold:
            if run_len == 0:
                run_start = i
            run_len += 1
            if run_len > best_len:
                best_len = run_len
                best_start = run_start
                best_end = i
        else:
            run_len = 0

    if best_len <= 0:
        return None
    return best_start, best_end


def detect_swing_window(
    frames: list[np.ndarray],
    *,
    fps: float,
    sample_every_n: int = 2,
) -> SwingWindow:
    """
    Find the longest contiguous segment where a person is likely visible.
    Rejects clips with too little swing footage or heavy scenery tails.
    """
    if len(frames) < 5:
        raise SwingWindowError("Video too short for swing analysis (need at least 5 sampled frames)")

    scores = _person_scores(frames)
    person_coverage = sum(1 for s in scores if s >= PERSON_THRESHOLD) / len(scores)
    if person_coverage < MIN_PERSON_COVERAGE:
        raise SwingWindowError(
            "Could not find enough of your swing on film. Film one clean rep with your full body in frame."
        )

    run = _longest_contiguous_run(scores, PERSON_THRESHOLD)
    if run is None:
        raise SwingWindowError(
            "Could not find a continuous swing on film. Keep the camera steady on one full swing."
        )

    start, end = run
    window_len = end - start + 1
    if window_len < MIN_WINDOW_FRAMES:
        raise SwingWindowError(
            "Swing footage was too short. Film one full swing from setup through finish."
        )

    effective_fps = fps / max(sample_every_n, 1)
    duration_sec = window_len / max(effective_fps, 1.0)
    if duration_sec < MIN_WINDOW_SECONDS:
        raise SwingWindowError(
            "Swing footage was too short. Film one full swing from setup through finish."
        )

    window_scores = scores[start : end + 1]
    window_coverage = sum(1 for s in window_scores if s >= PERSON_THRESHOLD) / len(window_scores)

    return SwingWindow(
        start_frame=start,
        end_frame=end,
        duration_sec=duration_sec,
        person_coverage_pct=window_coverage,
        fps=fps,
    )
