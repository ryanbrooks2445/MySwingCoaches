from __future__ import annotations

import logging
from pathlib import Path

from app.frame_extractor import download_video, extract_frames
from app.gemini_coach import generate_coaching_report
from app.metrics import compute_metrics
from app.persistence import mark_analysis_failed, persist_analysis_result, upload_checkpoint_frames
from app.phase_detector import checkpoint_confidence, detect_checkpoints
from app.pose_processor import process_video_frames
from app.rules_engine import evaluate_rules
from app.schemas import AnalyzeRequest, CoachingReportSchema

logger = logging.getLogger(__name__)


def run_analysis(request: AnalyzeRequest) -> CoachingReportSchema:
    video_path: Path | None = None
    try:
        video_path = download_video(request.video_url)
        frames, fps, duration = extract_frames(video_path)

        if len(frames) < 5:
            raise ValueError("Video too short for swing analysis (need at least 5 sampled frames)")

        pose_sequence = process_video_frames(frames)
        checkpoints = detect_checkpoints(pose_sequence, request.handedness)
        phase_confidence = {
            phase: checkpoint_confidence(pose_sequence, idx)
            for phase, idx in checkpoints.items()
        }

        metrics = compute_metrics(pose_sequence, checkpoints, request.handedness)
        rules_issues = evaluate_rules(metrics)

        checkpoint_frames = upload_checkpoint_frames(
            request.user_id,
            request.video_id,
            frames,
            checkpoints,
            pose_sequence,
            phase_confidence,
        )

        report, ai_ok = generate_coaching_report(
            skill_level=request.skill_level,
            handedness=request.handedness,
            camera_angle=request.camera_angle,
            metrics=metrics,
            detected_issues=rules_issues,
            checkpoint_frames=checkpoint_frames,
            history_summary=request.history_summary,
        )

        persist_analysis_result(
            analysis_id=request.analysis_id,
            video_id=request.video_id,
            user_id=request.user_id,
            report=report,
            metrics=metrics,
            rules_issues=rules_issues,
            checkpoint_frames=checkpoint_frames,
            ai_narrative_available=ai_ok,
        )

        return report
    except Exception as exc:
        logger.exception("Analysis failed for %s: %s", request.analysis_id, exc)
        mark_analysis_failed(request.analysis_id, request.video_id, str(exc))
        raise
    finally:
        if video_path and video_path.exists():
            video_path.unlink(missing_ok=True)
