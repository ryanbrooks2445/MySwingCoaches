from __future__ import annotations

import math
import urllib.request
from pathlib import Path

import mediapipe as mp
import numpy as np
from mediapipe.tasks.python import vision

MODEL_DIR = Path(__file__).resolve().parent.parent / "models"
MODEL_PATH = MODEL_DIR / "pose_landmarker_lite.task"
MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/pose_landmarker/"
    "pose_landmarker_lite/float16/1/pose_landmarker_lite.task"
)

# MediaPipe PoseLandmark enum index -> name mapping (33 landmarks)
LANDMARK_NAMES = [
    "nose", "left_eye_inner", "left_eye", "left_eye_outer",
    "right_eye_inner", "right_eye", "right_eye_outer",
    "left_ear", "right_ear", "mouth_left", "mouth_right",
    "left_shoulder", "right_shoulder", "left_elbow", "right_elbow",
    "left_wrist", "right_wrist", "left_pinky", "right_pinky",
    "left_index", "right_index", "left_thumb", "right_thumb",
    "left_hip", "right_hip", "left_knee", "right_knee",
    "left_ankle", "right_ankle", "left_heel", "right_heel",
    "left_foot_index", "right_foot_index",
]

_landmarker: vision.PoseLandmarker | None = None


def _ensure_model() -> Path:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    if not MODEL_PATH.exists():
        urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
    return MODEL_PATH


def _get_landmarker() -> vision.PoseLandmarker:
    global _landmarker
    if _landmarker is None:
        model_path = _ensure_model()
        options = vision.PoseLandmarkerOptions(
            base_options=mp.tasks.BaseOptions(model_asset_path=str(model_path)),
            running_mode=vision.RunningMode.IMAGE,
            num_poses=1,
            min_pose_detection_confidence=0.5,
            min_pose_presence_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        _landmarker = vision.PoseLandmarker.create_from_options(options)
    return _landmarker


def process_frame(frame: np.ndarray) -> dict | None:
    landmarker = _get_landmarker()
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)
    result = landmarker.detect(mp_image)

    if not result.pose_landmarks:
        return None

    landmarks = {}
    for i, lm in enumerate(result.pose_landmarks[0]):
        name = LANDMARK_NAMES[i] if i < len(LANDMARK_NAMES) else f"landmark_{i}"
        landmarks[name] = {
            "x": lm.x,
            "y": lm.y,
            "z": lm.z,
            "visibility": lm.visibility if lm.visibility is not None else 0.5,
        }
    return landmarks


def process_video_frames(frames: list[np.ndarray]) -> list[dict | None]:
    return [process_frame(f) for f in frames]


def get_point(landmarks: dict, name: str) -> tuple[float, float]:
    lm = landmarks.get(name)
    if not lm:
        return 0.0, 0.0
    return lm["x"], lm["y"]


def angle_between(p1: tuple[float, float], vertex: tuple[float, float], p2: tuple[float, float]) -> float:
    v1 = (p1[0] - vertex[0], p1[1] - vertex[1])
    v2 = (p2[0] - vertex[0], p2[1] - vertex[1])
    dot = v1[0] * v2[0] + v1[1] * v2[1]
    mag1 = math.hypot(v1[0], v1[1])
    mag2 = math.hypot(v2[0], v2[1])
    if mag1 == 0 or mag2 == 0:
        return 0.0
    cos_angle = max(-1.0, min(1.0, dot / (mag1 * mag2)))
    return math.degrees(math.acos(cos_angle))


def spine_angle(landmarks: dict) -> float:
    ls = get_point(landmarks, "left_shoulder")
    rs = get_point(landmarks, "right_shoulder")
    lh = get_point(landmarks, "left_hip")
    rh = get_point(landmarks, "right_hip")
    mid_shoulder = ((ls[0] + rs[0]) / 2, (ls[1] + rs[1]) / 2)
    mid_hip = ((lh[0] + rh[0]) / 2, (lh[1] + rh[1]) / 2)
    vertical = (mid_hip[0], mid_hip[1] - 0.1)
    return angle_between(vertical, mid_hip, mid_shoulder)


def hip_line_angle(landmarks: dict) -> float:
    lh = get_point(landmarks, "left_hip")
    rh = get_point(landmarks, "right_hip")
    return math.degrees(math.atan2(rh[1] - lh[1], rh[0] - lh[0]))


def wrist_height(landmarks: dict, handedness: str = "right") -> float:
    wrist = get_point(landmarks, "right_wrist" if handedness == "right" else "left_wrist")
    shoulder = get_point(landmarks, "right_shoulder" if handedness == "right" else "left_shoulder")
    return shoulder[1] - wrist[1]
