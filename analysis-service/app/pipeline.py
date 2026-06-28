from __future__ import annotations

import json
import logging
from pathlib import Path

from app.frame_extractor import download_video, extract_frames
from app.gemini_coach import generate_coaching_report
from app.mode_resolver import resolve_report_mode
from app.persistence import persist_analysis_result, upload_key_frames
from app.phase_detector import PhaseDetectionResult, detect_swing_phases
from app.report_audit import audit_report_quality
from app.media_validation import validate_and_normalize_video
from app.schemas import AnalyzeRequest, CoachingReportSchema
from app.swing_window import SwingWindowError, detect_swing_window
from app.frame_sampler import sample_keyframe_indices
from app.trace_log import log_trace

logger = logging.getLogger(__name__)

SAMPLE_EVERY_N = 2


def _phases_for_mode(
    frames: list,
    window,
    swing_mode: str,
) -> PhaseDetectionResult | None:
    if swing_mode == "full_swing":
        return detect_swing_phases(frames, window)

    span = window.end_frame - window.start_frame
    if span <= 0:
        indices = sample_keyframe_indices(len(frames), swing_mode)
    else:
        window_len = span + 1
        local = sample_keyframe_indices(window_len, swing_mode)
        indices = {phase: window.start_frame + idx for phase, idx in local.items()}

    from app.phase_detector import PhaseFrame

    phases = []
    for phase, idx in indices.items():
        phases.append(
            PhaseFrame(
                phase=phase,
                frame_index=idx,
                confidence=0.5,
                person_visible=True,
                notes="Even sampling within swing window.",
            )
        )
    return PhaseDetectionResult(phases=phases, keyframe_indices=indices)


def run_analysis(request: AnalyzeRequest) -> CoachingReportSchema:
    video_path: Path | None = None
    trace_id = request.trace_id
    report_id = request.analysis_id
    user_id = request.user_id
    try:
        video_path = download_video(request.video_url)
        validate_and_normalize_video(video_path)
        log_trace(
            "video_loaded",
            trace_id=trace_id,
            user_id=user_id,
            report_id=report_id,
            status="ok",
        )

        frames, fps, duration = extract_frames(video_path, sample_every_n=SAMPLE_EVERY_N)

        if len(frames) < 5:
            raise ValueError("Video too short for swing analysis (need at least 5 sampled frames)")

        swing_window = detect_swing_window(frames, fps=fps, sample_every_n=SAMPLE_EVERY_N)
        phase_result = _phases_for_mode(frames, swing_window, request.swing_mode)
        if phase_result is None:
            raise ValueError("Could not detect swing phases")

        log_trace(
            "frames_extracted",
            trace_id=trace_id,
            user_id=user_id,
            report_id=report_id,
            status="ok",
            frame_count=len(frames),
            fps=fps,
            duration_sec=duration,
            swing_window=swing_window.to_dict(),
        )

        key_frames = upload_key_frames(
            request.user_id,
            request.video_id,
            frames,
            phase_result.keyframe_indices,
        )

        report, ai_ok, gemini_meta = generate_coaching_report(
            video_path=video_path,
            frames=frames,
            phase_result=phase_result,
            swing_window=swing_window.to_dict(),
            swing_mode=request.swing_mode,
            history_summary=request.history_summary,
            player_name=request.player_name,
            swing_number=request.swing_number,
            player_context=request.player_context,
            player_age=request.player_age,
            years_playing=request.years_playing,
            physical_limitations=request.physical_limitations,
            trace_id=trace_id,
            report_id=report_id,
            user_id=user_id,
        )

        if ai_ok:
            report = resolve_report_mode(report)

            audit_report_quality(
                report,
                swing_mode=request.swing_mode,
                player_context=request.player_context,
                history_summary=request.history_summary,
                phase_map=phase_result.phase_map,
            )

        persist_analysis_result(
            analysis_id=request.analysis_id,
            video_id=request.video_id,
            user_id=request.user_id,
            report=report,
            key_frames=key_frames,
            ai_narrative_available=ai_ok,
            gemini_meta=gemini_meta,
            trace_id=trace_id,
            phase_map=phase_result.phase_map,
            swing_window=swing_window.to_dict(),
        )

        return report
    except SwingWindowError as exc:
        logger.warning("Swing window rejected for %s: %s", request.analysis_id, exc)
        raise ValueError(str(exc)) from exc
    except Exception as exc:
        logger.exception("Analysis failed for %s: %s", request.analysis_id, exc)
        log_trace(
            "report_saved",
            trace_id=trace_id,
            user_id=user_id,
            report_id=report_id,
            status="failed",
            error=str(exc)[:500],
        )
        raise
    finally:
        if video_path and video_path.exists():
            video_path.unlink(missing_ok=True)
