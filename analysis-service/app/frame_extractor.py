from __future__ import annotations

import tempfile
from pathlib import Path

import cv2
import httpx
import numpy as np


def download_video(video_url: str) -> Path:
    tmp = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
    tmp.close()
    path = Path(tmp.name)
    with httpx.Client(timeout=120.0) as client:
        response = client.get(video_url)
        response.raise_for_status()
        path.write_bytes(response.content)
    return path


def extract_frames(video_path: Path, sample_every_n: int = 2) -> tuple[list[np.ndarray], float, int]:
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise ValueError("Could not open video file")

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
    return frames, fps, int(duration)


def save_frame_jpeg(frame: np.ndarray, path: Path) -> None:
    bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
    cv2.imwrite(str(path), bgr, [cv2.IMWRITE_JPEG_QUALITY, 85])
