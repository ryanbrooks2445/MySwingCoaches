from app import persistence, pipeline
from app.gemini_coach import _fallback_report
from app.pose_extractor import PoseSequence
from app.schemas import AnalyzeRequest


def test_run_analysis_leaves_failure_state_to_job_runner(monkeypatch) -> None:
    marked_failed: list[tuple[str, str, str]] = []

    monkeypatch.setattr(
        pipeline,
        "download_video",
        lambda _url: (_ for _ in ()).throw(RuntimeError("provider temporarily unavailable")),
    )
    monkeypatch.setattr(persistence, "mark_analysis_failed", lambda *args: marked_failed.append(args))

    request = AnalyzeRequest(
        analysis_id="report-1",
        video_id="video-1",
        user_id="user-1",
        video_url="https://example.test/video.mp4",
    )

    try:
        pipeline.run_analysis(request)
    except RuntimeError:
        pass

    assert marked_failed == []


def test_run_analysis_persists_fallback_report_when_ai_is_unavailable(monkeypatch, tmp_path) -> None:
    video_path = tmp_path / "swing.mp4"
    video_path.write_bytes(b"video")
    persisted: list[dict] = []
    audited: list[object] = []

    class PhaseResult:
        keyframe_indices = {"setup": 0}
        phase_map = [{"phase": "setup", "frame_index": 0, "confidence": 0.8}]
        validation = {}
        timeline = {}

    monkeypatch.setattr(pipeline, "download_video", lambda _url: video_path)
    monkeypatch.setattr(pipeline, "validate_and_normalize_video", lambda _path: None)
    monkeypatch.setattr(pipeline, "extract_frames", lambda _path, sample_every_n: ([object()] * 5, 30.0, 1))
    monkeypatch.setattr(
        pipeline,
        "extract_pose_sequence",
        lambda _frames: PoseSequence(frames=[], average_confidence=0.0),
    )
    monkeypatch.setattr(
        pipeline,
        "detect_swing_window",
        lambda _frames, fps, sample_every_n, pose_sequence=None: type(
            "Window",
            (),
            {"to_dict": lambda self: {"start_frame": 0, "end_frame": 0}},
        )(),
    )
    monkeypatch.setattr(
        pipeline,
        "_phases_for_mode",
        lambda _frames, _window, _mode, _pose_sequence=None: PhaseResult(),
    )
    monkeypatch.setattr(pipeline, "upload_key_frames", lambda *_args: [])
    monkeypatch.setattr(
        pipeline,
        "generate_coaching_report",
        lambda **_kwargs: (
            _fallback_report("provider temporarily unavailable", "Ryan", "full_swing"),
            False,
            {"error": "provider temporarily unavailable"},
        ),
    )
    monkeypatch.setattr(pipeline, "resolve_report_mode", lambda report: report)
    monkeypatch.setattr(pipeline, "audit_report_quality", lambda *args, **kwargs: audited.append(args))
    monkeypatch.setattr(pipeline, "persist_analysis_result", lambda **kwargs: persisted.append(kwargs))

    request = AnalyzeRequest(
        analysis_id="report-1",
        video_id="video-1",
        user_id="user-1",
        video_url="https://example.test/video.mp4",
    )

    report = pipeline.run_analysis(request)

    assert report.main_fix
    assert persisted[0]["analysis_id"] == "report-1"
    assert persisted[0]["ai_narrative_available"] is False
    assert persisted[0]["gemini_meta"]["error"] == "provider temporarily unavailable"
    assert audited == []
