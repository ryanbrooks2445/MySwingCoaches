from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import cv2
import mediapipe as mp
import numpy as np
from mediapipe.tasks.python import vision

logger = logging.getLogger(__name__)

MODELS_DIR = Path(__file__).resolve().parent.parent / "models"
DEFAULT_MODEL = MODELS_DIR / "pose_landmarker_lite.task"
FALLBACK_MODEL = MODELS_DIR / "pose_landmarker_full.task"

# MediaPipe Pose landmark indices (33-point body model).
NOSE = 0
LEFT_SHOULDER, RIGHT_SHOULDER = 11, 12
LEFT_ELBOW, RIGHT_ELBOW = 13, 14
LEFT_WRIST, RIGHT_WRIST = 15, 16
LEFT_HIP, RIGHT_HIP = 23, 24
LEFT_KNEE, RIGHT_KNEE = 25, 26
LEFT_ANKLE, RIGHT_ANKLE = 27, 28

CORE_LANDMARKS = (
    LEFT_SHOULDER,
    RIGHT_SHOULDER,
    LEFT_HIP,
    RIGHT_HIP,
    LEFT_WRIST,
    RIGHT_WRIST,
    LEFT_KNEE,
    RIGHT_KNEE,
)

_landmarker: vision.PoseLandmarker | None = None
_active_model_path: Path | None = None


@dataclass
class PoseLandmark:
    x: float
    y: float
    z: float
    visibility: float

    def to_dict(self) -> dict[str, float]:
        return {
            "x": round(self.x, 4),
            "y": round(self.y, 4),
            "z": round(self.z, 4),
            "visibility": round(self.visibility, 3),
        }


@dataclass
class FramePose:
    frame_index: int
    confidence: float
    landmarks: list[PoseLandmark] | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "frame_index": self.frame_index,
            "confidence": round(self.confidence, 3),
            "landmarks": [lm.to_dict() for lm in self.landmarks] if self.landmarks else None,
        }


@dataclass
class PoseSequence:
    frames: list[FramePose]
    provider: str = "mediapipe_pose"
    model: str = "pose_landmarker_lite"
    camera_angle_estimate: str = "unknown"
    average_confidence: float = 0.0
    limitations: list[str] = field(default_factory=list)

    def confidence_at(self, index: int) -> float:
        if 0 <= index < len(self.frames):
            return self.frames[index].confidence
        return 0.0

    def landmarks_at(self, index: int) -> list[PoseLandmark] | None:
        if 0 <= index < len(self.frames):
            return self.frames[index].landmarks
        return None

    def person_scores(self) -> list[float]:
        return [frame.confidence for frame in self.frames]

    def to_persist_dict(
        self,
        phase_indices: dict[str, int],
        *,
        validation: dict[str, dict[str, Any]] | None = None,
        timeline: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        payload = self.to_persist_dict_legacy(phase_indices)
        if validation:
            payload["phase_validation"] = validation
        if timeline:
            payload["pose_timeline"] = timeline
        return payload

    def to_persist_dict_legacy(self, phase_indices: dict[str, int]) -> dict[str, Any]:
        keyframes: dict[str, Any] = {}
        for phase, idx in phase_indices.items():
            if idx < 0 or idx >= len(self.frames):
                continue
            frame = self.frames[idx]
            keyframes[phase] = {
                "frame_index": idx,
                "confidence": round(frame.confidence, 3),
                "landmarks": [lm.to_dict() for lm in frame.landmarks] if frame.landmarks else None,
                "metrics": compute_frame_metrics(frame.landmarks, reference=self.landmarks_at(phase_indices.get("address", idx))),
            }
        return {
            "provider": self.provider,
            "model": self.model,
            "camera_angle_estimate": self.camera_angle_estimate,
            "average_confidence": round(self.average_confidence, 3),
            "limitations": self.limitations,
            "keyframes": keyframes,
        }


def _resolve_model_path() -> Path:
    if DEFAULT_MODEL.exists():
        return DEFAULT_MODEL
    if FALLBACK_MODEL.exists():
        return FALLBACK_MODEL
    raise FileNotFoundError(
        f"MediaPipe pose model not found. Expected {DEFAULT_MODEL} or {FALLBACK_MODEL}."
    )


def _get_landmarker(model_path: Path | None = None) -> vision.PoseLandmarker:
    global _landmarker, _active_model_path
    resolved = model_path or _resolve_model_path()
    if _landmarker is not None and _active_model_path == resolved:
        return _landmarker

    options = vision.PoseLandmarkerOptions(
        base_options=mp.tasks.BaseOptions(model_asset_path=str(resolved)),
        running_mode=vision.RunningMode.IMAGE,
        num_poses=1,
        min_pose_detection_confidence=0.5,
        min_pose_presence_confidence=0.5,
        min_tracking_confidence=0.5,
    )
    _landmarker = vision.PoseLandmarker.create_from_options(options)
    _active_model_path = resolved
    return _landmarker


def _round(value: float, places: int = 1) -> float:
    if math.isnan(value) or math.isinf(value):
        return 0.0
    return round(value, places)


def _midpoint(a: PoseLandmark, b: PoseLandmark) -> tuple[float, float]:
    return ((a.x + b.x) / 2, (a.y + b.y) / 2)


def _angle_from_vertical(dx: float, dy: float) -> float:
    """Degrees from vertical; 0 = upright, larger = more forward bend in image space."""
    return abs(math.degrees(math.atan2(abs(dx), max(abs(dy), 1e-6))))


def _line_angle(a: PoseLandmark, b: PoseLandmark) -> float:
    return math.degrees(math.atan2(b.y - a.y, b.x - a.x))


def _joint_angle(a: PoseLandmark, b: PoseLandmark, c: PoseLandmark) -> float:
    """Angle at point b formed by segments ba and bc."""
    v1 = (a.x - b.x, a.y - b.y)
    v2 = (c.x - b.x, c.y - b.y)
    dot = v1[0] * v2[0] + v1[1] * v2[1]
    mag1 = math.hypot(*v1)
    mag2 = math.hypot(*v2)
    if mag1 < 1e-6 or mag2 < 1e-6:
        return 0.0
    cos_angle = max(-1.0, min(1.0, dot / (mag1 * mag2)))
    return math.degrees(math.acos(cos_angle))


def _landmark_confidence(landmarks: list[PoseLandmark]) -> float:
    if not landmarks:
        return 0.0
    visibilities = [landmarks[i].visibility for i in CORE_LANDMARKS if i < len(landmarks)]
    if not visibilities:
        return 0.0
    return sum(visibilities) / len(visibilities)


def _estimate_camera_angle(frames: list[FramePose]) -> str:
    samples = [frame for frame in frames if frame.landmarks and frame.confidence >= 0.45][:12]
    if len(samples) < 3:
        return "unknown"

    depth_ratios: list[float] = []
    for frame in samples:
        lm = frame.landmarks
        assert lm is not None
        shoulder_width = abs(lm[LEFT_SHOULDER].x - lm[RIGHT_SHOULDER].x)
        hip_width = abs(lm[LEFT_HIP].x - lm[RIGHT_HIP].x)
        if shoulder_width < 1e-4:
            continue
        depth_ratios.append(hip_width / shoulder_width)

    if not depth_ratios:
        return "unknown"

    avg_ratio = sum(depth_ratios) / len(depth_ratios)
    if avg_ratio > 0.82:
        return "face_on"
    if avg_ratio < 0.62:
        return "down_the_line"
    return "three_quarter"


def compute_frame_metrics(
    landmarks: list[PoseLandmark] | None,
    *,
    reference: list[PoseLandmark] | None = None,
) -> dict[str, float | str]:
    if not landmarks or len(landmarks) < 29:
        return {}

    ls, rs = landmarks[LEFT_SHOULDER], landmarks[RIGHT_SHOULDER]
    lh, rh = landmarks[LEFT_HIP], landmarks[RIGHT_HIP]
    shoulder_mid = _midpoint(ls, rs)
    hip_mid = _midpoint(lh, rh)
    spine_dx = shoulder_mid[0] - hip_mid[0]
    spine_dy = shoulder_mid[1] - hip_mid[1]

    left_knee = _joint_angle(landmarks[LEFT_HIP], landmarks[LEFT_KNEE], landmarks[LEFT_ANKLE])
    right_knee = _joint_angle(landmarks[RIGHT_HIP], landmarks[RIGHT_KNEE], landmarks[RIGHT_ANKLE])
    left_arm = _joint_angle(ls, landmarks[LEFT_ELBOW], landmarks[LEFT_WRIST])
    right_arm = _joint_angle(rs, landmarks[RIGHT_ELBOW], landmarks[RIGHT_WRIST])

    metrics: dict[str, float | str] = {
        "spine_angle_deg": _round(_angle_from_vertical(spine_dx, spine_dy)),
        "shoulder_tilt_deg": _round(abs(_line_angle(ls, rs))),
        "hip_line_angle_deg": _round(_line_angle(lh, rh)),
        "left_knee_flex_deg": _round(left_knee),
        "right_knee_flex_deg": _round(right_knee),
        "left_arm_angle_deg": _round(left_arm),
        "right_arm_angle_deg": _round(right_arm),
        "lead_wrist_height_norm": _round(min(landmarks[LEFT_WRIST].y, landmarks[RIGHT_WRIST].y), 3),
    }

    if reference and len(reference) >= 29:
        ref_nose = reference[NOSE]
        nose = landmarks[NOSE]
        metrics["head_drift_x_norm"] = _round(abs(nose.x - ref_nose.x), 3)
        metrics["head_drift_y_norm"] = _round(abs(nose.y - ref_nose.y), 3)

    return metrics


def compute_phase_metrics(
    pose_sequence: PoseSequence,
    phase_indices: dict[str, int],
    *,
    validation: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    address_idx = phase_indices.get("address")
    reference = pose_sequence.landmarks_at(address_idx) if address_idx is not None else None

    phase_metrics: dict[str, Any] = {}
    for phase, idx in phase_indices.items():
        if validation is not None and not validation.get(phase, {}).get("validated", False):
            continue
        landmarks = pose_sequence.landmarks_at(idx)
        metrics = compute_frame_metrics(landmarks, reference=reference)
        if metrics:
            phase_metrics[phase] = metrics

    if len(phase_metrics) >= 2:
        address = phase_metrics.get("address", {})
        top = phase_metrics.get("top", {})
        impact = phase_metrics.get("impact") or phase_metrics.get("impact_window_estimate", {})
        if address and top:
            phase_metrics.setdefault("deltas", {})
            if "hip_line_angle_deg" in address and "hip_line_angle_deg" in top:
                phase_metrics["deltas"]["hip_rotation_address_to_top_deg"] = _round(
                    abs(float(top["hip_line_angle_deg"]) - float(address["hip_line_angle_deg"]))
                )
            if "spine_angle_deg" in address and "spine_angle_deg" in top:
                phase_metrics["deltas"]["spine_change_address_to_top_deg"] = _round(
                    abs(float(top["spine_angle_deg"]) - float(address["spine_angle_deg"]))
                )
        if address and impact:
            phase_metrics.setdefault("deltas", {})
            if "head_drift_x_norm" in impact:
                phase_metrics["deltas"]["head_drift_at_impact_norm"] = impact["head_drift_x_norm"]

    return phase_metrics


def build_pose_evidence(
    pose_sequence: PoseSequence,
    phase_indices: dict[str, int],
    *,
    validation: dict[str, dict[str, Any]] | None = None,
    timeline: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "provider": pose_sequence.provider,
        "model": pose_sequence.model,
        "camera_angle_estimate": pose_sequence.camera_angle_estimate,
        "average_pose_confidence": round(pose_sequence.average_confidence, 3),
        "limitations": pose_sequence.limitations,
        "pose_timeline": timeline or {},
        "phase_validation": validation or {},
        "phase_metrics": compute_phase_metrics(
            pose_sequence,
            phase_indices,
            validation=validation,
        ),
        "rules": [
            "Full video is the primary truth for club motion and timing.",
            "pose_timeline shows body geometry over time inside the swing window.",
            "phase_metrics are only attached for pose-validated phase frames.",
            "If a keyframe still conflicts with the video, trust the video and note the mismatch.",
            "If average_pose_confidence < 0.45, prefer full-video observations over numeric metrics.",
            "Do not claim precise impact geometry when impact phase is impact_window_estimate.",
        ],
    }


def _frame_pose_from_result(frame_index: int, result: vision.PoseLandmarkerResult) -> FramePose:
    if not result.pose_landmarks:
        return FramePose(frame_index=frame_index, confidence=0.0, landmarks=None)

    raw = result.pose_landmarks[0]
    landmarks = [
        PoseLandmark(
            x=point.x,
            y=point.y,
            z=point.z,
            visibility=point.visibility if point.visibility is not None else 0.0,
        )
        for point in raw
    ]
    confidence = _landmark_confidence(landmarks)
    return FramePose(frame_index=frame_index, confidence=confidence, landmarks=landmarks)


def _run_pose_on_frames(frames: list[np.ndarray], model_path: Path) -> PoseSequence:
    landmarker = _get_landmarker(model_path)
    frame_poses: list[FramePose] = []

    for index, frame in enumerate(frames):
        if not isinstance(frame, np.ndarray) or frame.ndim != 3:
            frame_poses.append(FramePose(frame_index=index, confidence=0.0, landmarks=None))
            continue
        rgb = np.ascontiguousarray(frame)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        result = landmarker.detect(mp_image)
        frame_poses.append(_frame_pose_from_result(index, result))

    confidences = [frame.confidence for frame in frame_poses]
    average_confidence = sum(confidences) / len(confidences) if confidences else 0.0
    limitations: list[str] = []
    if average_confidence < 0.45:
        limitations.append("Pose tracking confidence is low; metrics are approximate.")
    low_wrist_frames = sum(
        1
        for frame in frame_poses
        if frame.landmarks
        and min(frame.landmarks[LEFT_WRIST].visibility, frame.landmarks[RIGHT_WRIST].visibility) < 0.35
    )
    if low_wrist_frames > len(frame_poses) * 0.4:
        limitations.append("Wrist landmarks were often occluded; arm-path metrics may be unreliable.")

    return PoseSequence(
        frames=frame_poses,
        model=model_path.stem,
        camera_angle_estimate=_estimate_camera_angle(frame_poses),
        average_confidence=average_confidence,
        limitations=limitations,
    )


def extract_pose_sequence(frames: list[np.ndarray]) -> PoseSequence:
    """Run MediaPipe Pose on sampled RGB frames; retry with full model if lite is weak."""
    if not frames:
        return PoseSequence(frames=[], limitations=["No frames available for pose extraction."])

    try:
        lite_path = DEFAULT_MODEL if DEFAULT_MODEL.exists() else _resolve_model_path()
    except FileNotFoundError as exc:
        logger.warning("MediaPipe model unavailable: %s", exc)
        return PoseSequence(
            frames=[FramePose(frame_index=i, confidence=0.0, landmarks=None) for i in range(len(frames))],
            limitations=[str(exc)],
        )

    try:
        sequence = _run_pose_on_frames(frames, lite_path)
    except (FileNotFoundError, TypeError, ValueError) as exc:
        logger.warning("MediaPipe extraction failed: %s", exc)
        return PoseSequence(
            frames=[FramePose(frame_index=i, confidence=0.0, landmarks=None) for i in range(len(frames))],
            limitations=[str(exc)],
        )

    if (
        sequence.average_confidence < 0.45
        and FALLBACK_MODEL.exists()
        and lite_path != FALLBACK_MODEL
    ):
        logger.info(
            "Pose lite confidence %.3f — retrying with full model",
            sequence.average_confidence,
        )
        try:
            full_sequence = _run_pose_on_frames(frames, FALLBACK_MODEL)
        except FileNotFoundError:
            return sequence
        if full_sequence.average_confidence > sequence.average_confidence:
            return full_sequence

    return sequence


def hip_line_angle_for_frame(pose_sequence: PoseSequence, index: int) -> float | None:
    landmarks = pose_sequence.landmarks_at(index)
    if not landmarks or pose_sequence.confidence_at(index) < 0.4:
        return None
    return _line_angle(landmarks[LEFT_HIP], landmarks[RIGHT_HIP])


def wrist_height_proxy(pose_sequence: PoseSequence, index: int) -> float:
    """Lower normalized y = higher hands in frame."""
    landmarks = pose_sequence.landmarks_at(index)
    if not landmarks:
        return 1.0
    return min(landmarks[LEFT_WRIST].y, landmarks[RIGHT_WRIST].y)


def hip_rotation_proxy(pose_sequence: PoseSequence, index: int, setup_angle: float) -> float:
    landmarks = pose_sequence.landmarks_at(index)
    if not landmarks:
        return 0.0
    angle = _line_angle(landmarks[LEFT_HIP], landmarks[RIGHT_HIP])
    return abs(angle - setup_angle) / 90.0


def overlay_pose_skeleton(frame: np.ndarray, landmarks: list[PoseLandmark] | None) -> np.ndarray:
    """Draw pose connections on a copy of the frame for Gemini keyframe context."""
    if not landmarks or len(landmarks) < 29:
        return frame

    output = frame.copy()
    height, width = output.shape[:2]

    connections = (
        (LEFT_SHOULDER, RIGHT_SHOULDER),
        (LEFT_SHOULDER, LEFT_ELBOW),
        (LEFT_ELBOW, LEFT_WRIST),
        (RIGHT_SHOULDER, RIGHT_ELBOW),
        (RIGHT_ELBOW, RIGHT_WRIST),
        (LEFT_SHOULDER, LEFT_HIP),
        (RIGHT_SHOULDER, RIGHT_HIP),
        (LEFT_HIP, RIGHT_HIP),
        (LEFT_HIP, LEFT_KNEE),
        (LEFT_KNEE, LEFT_ANKLE),
        (RIGHT_HIP, RIGHT_KNEE),
        (RIGHT_KNEE, RIGHT_ANKLE),
    )

    for start, end in connections:
        a, b = landmarks[start], landmarks[end]
        if a.visibility < 0.35 or b.visibility < 0.35:
            continue
        p1 = (int(a.x * width), int(a.y * height))
        p2 = (int(b.x * width), int(b.y * height))
        cv2.line(output, p1, p2, (74, 222, 128), 2, cv2.LINE_AA)

    for idx in (NOSE, LEFT_SHOULDER, RIGHT_SHOULDER, LEFT_WRIST, RIGHT_WRIST, LEFT_HIP, RIGHT_HIP):
        lm = landmarks[idx]
        if lm.visibility < 0.35:
            continue
        center = (int(lm.x * width), int(lm.y * height))
        cv2.circle(output, center, 4, (16, 163, 74), -1, cv2.LINE_AA)

    return output
