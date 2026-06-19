from __future__ import annotations

import logging
from pathlib import Path

from app.frame_extractor import download_video, extract_frames
from app.frame_sampler import sample_keyframe_indices
from app.gemini_coach import generate_coaching_report
from app.persistence import mark_analysis_failed, persist_analysis_result, upload_key_frames
from app.report_audit import audit_report_quality
from app.media_validation import validate_and_normalize_video
from app.schemas import AnalyzeRequest, CoachingReportSchema
from app.trace_log import log_trace

logger = logging.getLogger(__name__)


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

        frames, fps, duration = extract_frames(video_path)

        if len(frames) < 5:
            raise ValueError("Video too short for swing analysis (need at least 5 sampled frames)")

        log_trace(
            "frames_extracted",
            trace_id=trace_id,
            user_id=user_id,
            report_id=report_id,
            status="ok",
            frame_count=len(frames),
            fps=fps,
            duration_sec=duration,
        )

        keyframe_indices = sample_keyframe_indices(len(frames), request.swing_mode)
        key_frames = upload_key_frames(
            request.user_id,
            request.video_id,
            frames,
            keyframe_indices,
        )

        report, ai_ok, gemini_meta = generate_coaching_report(
            video_path=video_path,
            frames=frames,
            keyframe_indices=keyframe_indices,
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

        if not ai_ok:
            raise ValueError(gemini_meta.get("error") or "AI analysis unavailable")

        audit_report_quality(
            report,
            swing_mode=request.swing_mode,
            player_context=request.player_context,
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
        )

        return report
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
        mark_analysis_failed(request.analysis_id, request.video_id, str(exc))
        raise
    finally:
        if video_path and video_path.exists():
            video_path.unlink(missing_ok=True)
