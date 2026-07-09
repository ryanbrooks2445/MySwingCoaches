import numpy as np

from app.pose_extractor import (
    FramePose,
    PoseLandmark,
    PoseSequence,
    build_pose_evidence,
    compute_frame_metrics,
    compute_phase_metrics,
    extract_pose_sequence,
    overlay_pose_skeleton,
)


def _landmarks(
    *,
    nose=(0.5, 0.2),
    left_shoulder=(0.45, 0.3),
    right_shoulder=(0.55, 0.3),
    left_hip=(0.46, 0.55),
    right_hip=(0.54, 0.55),
) -> list[PoseLandmark]:
    points: list[PoseLandmark | None] = [None] * 33
    for idx, (x, y) in (
        (0, nose),
        (11, left_shoulder),
        (12, right_shoulder),
        (13, (0.43, 0.42)),
        (14, (0.57, 0.42)),
        (15, (0.42, 0.5)),
        (16, (0.58, 0.5)),
        (23, left_hip),
        (24, right_hip),
        (25, (0.46, 0.72)),
        (26, (0.54, 0.72)),
        (27, (0.46, 0.9)),
        (28, (0.54, 0.9)),
    ):
        points[idx] = PoseLandmark(x=x, y=y, z=0.0, visibility=0.95)

    return [point if point is not None else PoseLandmark(0, 0, 0, 0) for point in points]


def test_compute_frame_metrics_includes_spine_and_knee_angles() -> None:
    metrics = compute_frame_metrics(
        _landmarks(
            left_shoulder=(0.42, 0.28),
            right_shoulder=(0.58, 0.28),
            left_hip=(0.48, 0.58),
            right_hip=(0.56, 0.58),
        )
    )
    assert metrics["spine_angle_deg"] > 0
    assert metrics["left_knee_flex_deg"] > 0
    assert metrics["right_knee_flex_deg"] > 0


def test_compute_frame_metrics_tracks_head_drift_from_address() -> None:
    address = _landmarks(nose=(0.5, 0.2))
    impact = _landmarks(nose=(0.56, 0.24))
    metrics = compute_frame_metrics(impact, reference=address)
    assert metrics["head_drift_x_norm"] > 0
    assert metrics["head_drift_y_norm"] > 0


def test_compute_phase_metrics_builds_deltas() -> None:
    sequence = PoseSequence(
        frames=[
            FramePose(frame_index=0, confidence=0.8, landmarks=_landmarks()),
            FramePose(
                frame_index=10,
                confidence=0.8,
                landmarks=_landmarks(
                    left_hip=(0.40, 0.55),
                    right_hip=(0.60, 0.55),
                ),
            ),
        ],
        average_confidence=0.8,
    )

    metrics = compute_phase_metrics(sequence, {"address": 0, "top": 1})
    assert "address" in metrics
    assert "top" in metrics
    assert "deltas" in metrics
    assert "hip_rotation_address_to_top_deg" in metrics["deltas"]


def test_build_pose_evidence_includes_rules() -> None:
    sequence = PoseSequence(
        frames=[],
        average_confidence=0.7,
        camera_angle_estimate="down_the_line",
    )
    evidence = build_pose_evidence(sequence, {"address": 0})
    assert evidence["provider"] == "mediapipe_pose"
    assert evidence["camera_angle_estimate"] == "down_the_line"
    assert evidence["rules"]


def test_extract_pose_sequence_gracefully_handles_missing_model(monkeypatch) -> None:
    from app.pose_extractor import DEFAULT_MODEL

    monkeypatch.setattr(
        "app.pose_extractor._run_pose_on_frames",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(FileNotFoundError("missing model")),
    )
    monkeypatch.setattr(
        "app.pose_extractor._resolve_model_path",
        lambda: DEFAULT_MODEL,
    )

    frames = [np.zeros((240, 320, 3), dtype=np.uint8) for _ in range(3)]
    sequence = extract_pose_sequence(frames)
    assert len(sequence.frames) == 3
    assert sequence.limitations


def test_overlay_pose_skeleton_returns_copy_with_landmarks() -> None:
    frame = np.zeros((120, 160, 3), dtype=np.uint8)
    output = overlay_pose_skeleton(frame, _landmarks())
    assert output.shape == frame.shape
    assert not np.array_equal(output, frame)
