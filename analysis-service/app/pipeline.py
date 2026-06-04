from __future__ import annotations

import logging
from pathlib import Path

from app.frame_extractor import download_video, extract_frames
from app.frame_sampler import sample_keyframe_indices
from app.gemini_coach import generate_coaching_report
from app.persistence import mark_analysis_failed, persist_analysis_result, upload_key_frames
from app.schemas import AnalyzeRequest, CoachingReportSchema

logger = logging.getLogger(__name__)


def run_analysis(request: AnalyzeRequest) -> CoachingReportSchema:
    video_path: Path | None = None
    try:
        video_path = download_video(request.video_url)
        frames, fps, duration = extract_frames(video_path)

        if len(frames) < 5:
            raise ValueError("Video too short for swing analysis (need at least 5 sampled frames)")

        keyframe_indices = sample_keyframe_indices(len(frames))
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
            history_summary=request.history_summary,
            player_name=request.player_name,
            swing_number=request.swing_number,
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
        )

        return report
    except Exception as exc:
        logger.exception("Analysis failed for %s: %s", request.analysis_id, exc)
        mark_analysis_failed(request.analysis_id, request.video_id, str(exc))
        raise
    finally:
        if video_path and video_path.exists():
            video_path.unlink(missing_ok=True)
