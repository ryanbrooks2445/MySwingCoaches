from __future__ import annotations

import logging
import time
from pathlib import Path

from app.diagnosis_engine import analyze_swing_sequence
from app.frame_extractor import download_video, extract_frames
from app.frame_sampler import checkpoints_for_mode, sample_keyframe_indices
from app.gemini_coach import generate_coaching_report
from app.persistence import mark_analysis_failed, persist_analysis_result, upload_key_frames
from app.schemas import AnalyzeRequest, CoachingReportSchema
from app.vision_fusion import build_hybrid_vision_evidence

logger = logging.getLogger(__name__)


def _trace_log(event: str, *, swing_id: str, trace_id: str, error: str | None = None, **extra) -> None:
    logger.info(
        "%s swing_id=%s trace_id=%s error_message=%s extra=%s",
        event,
        swing_id,
        trace_id,
        error or "",
        extra,
    )


def _clamp_score(value: float) -> int:
    return max(0, min(100, round(value)))


def _phase_metrics(metric_payload: dict, phase: str) -> dict:
    for item in metric_payload.get("checkpoints", []):
        if item.get("checkpoint") == phase:
            return item.get("metrics", {})
    return {}


def _computed_progress_score(metric_payload: dict, prior_progress: dict | None) -> dict:
    setup = _phase_metrics(metric_payload, "setup_address")
    top = _phase_metrics(metric_payload, "top_of_backswing")
    transition = _phase_metrics(metric_payload, "transition")
    impact = _phase_metrics(metric_payload, "impact")
    finish = _phase_metrics(metric_payload, "finish")
    checkpoints = metric_payload.get("checkpoints", [])
    avg_confidence = (
        sum(float(item.get("confidence", 0)) for item in checkpoints) / len(checkpoints)
        if checkpoints
        else 0
    )

    scores = {
        "Head stability": _clamp_score(100 - abs(float(top.get("head_position_x_movement", 0))) * 3 - abs(float(top.get("head_position_y_movement", 0))) * 2),
        "Balance": _clamp_score(float(finish.get("balance_score", setup.get("balance_score", 50)))),
        "Posture retention": _clamp_score(100 - abs(float(transition.get("spine_angle", 38)) - float(setup.get("spine_angle", 38))) * 2.4),
        "Hip depth": _clamp_score(100 - max(0, float(impact.get("pelvis_depth_early_extension_proxy", 0))) * 4),
        "Sequencing": _clamp_score(100 - abs(float(transition.get("center_of_mass_shift_proxy", 0))) * 2.5 - max(0, float(transition.get("trail_elbow_position", 0)) - 8) * 2),
        "Consistency": _clamp_score(avg_confidence * 100),
    }

    prior_metrics = {
        item.get("name"): item
        for item in ((prior_progress or {}).get("progress_score") or {}).get("metrics", [])
        if isinstance(item, dict)
    }
    metrics = []
    for name, current in scores.items():
        previous = prior_metrics.get(name, {}).get("current_score")
        metrics.append(
            {
                "name": name,
                "current_score": current,
                "previous_score": previous,
                "change": current - previous if isinstance(previous, int) else None,
            }
        )

    overall = _clamp_score(sum(scores.values()) / max(len(scores), 1))
    previous_overall = ((prior_progress or {}).get("progress_score") or {}).get("overall")
    if not isinstance(previous_overall, int):
        trend = "first_upload"
    elif overall >= previous_overall + 5:
        trend = "improved"
    elif overall <= previous_overall - 5:
        trend = "regressed"
    else:
        trend = "same"

    return {
        "overall": overall,
        "previous_overall": previous_overall if isinstance(previous_overall, int) else None,
        "trend": trend,
        "metrics": metrics,
        "note": "Scores compare this golfer to their own prior uploads and are directional, not PGA Tour benchmarks.",
    }


def run_analysis(request: AnalyzeRequest) -> CoachingReportSchema:
    video_path: Path | None = None
    started_at = time.perf_counter()
    swing_id = request.video_id
    trace_id = request.analysis_id
    try:
        _trace_log("analysis_started", swing_id=swing_id, trace_id=trace_id)
        _trace_log(
            "video_reference_received",
            swing_id=swing_id,
            trace_id=trace_id,
            has_video_url=bool(request.video_url),
            swing_mode=request.swing_mode,
        )
        video_path = download_video(
            request.video_url,
            mime_type=request.video_mime_type,
            swing_id=swing_id,
            trace_id=trace_id,
        )
        frames, fps, duration = extract_frames(video_path, swing_id=swing_id, trace_id=trace_id)

        if len(frames) < 5:
            raise ValueError("Video too short for swing analysis (need at least 5 sampled frames)")

        keyframe_indices = sample_keyframe_indices(len(frames), request.swing_mode)
        key_frames = upload_key_frames(
            request.user_id,
            request.video_id,
            frames,
            keyframe_indices,
        )

        diagnosis_engine, metric_payload = analyze_swing_sequence(
            frames=frames,
            keyframe_indices=keyframe_indices,
            swing_mode=request.swing_mode,
        )
        hybrid_evidence = build_hybrid_vision_evidence(
            frames=frames,
            keyframe_indices=keyframe_indices,
            metric_payload=metric_payload,
            expected_order=checkpoints_for_mode(request.swing_mode),
        )
        metric_payload = {
            **metric_payload,
            "hybrid_vision_evidence": hybrid_evidence,
            "computed_progress_score": _computed_progress_score(metric_payload, request.prior_progress),
            "intake_context": {
                "camera_angle": request.camera_angle,
                "handedness": request.handedness,
                "skill_level": request.skill_level,
                "ball_flight": request.ball_flight,
                "user_goal": request.user_goal,
                "club_used": request.club_used,
                "practice_availability": request.practice_availability,
                "handicap": request.handicap,
            },
        }

        report, ai_ok, gemini_meta = generate_coaching_report(
            swing_id=swing_id,
            trace_id=trace_id,
            video_path=video_path,
            video_mime_type=request.video_mime_type,
            frames=frames,
            keyframe_indices=keyframe_indices,
            fps=fps,
            swing_mode=request.swing_mode,
            diagnosis_engine=diagnosis_engine,
            metric_payload=metric_payload,
            history_summary=request.history_summary,
            player_name=request.player_name,
            swing_number=request.swing_number,
            player_context=request.player_context,
            player_age=request.player_age,
            years_playing=request.years_playing,
            physical_limitations=request.physical_limitations,
            camera_angle=request.camera_angle,
            handedness=request.handedness,
            skill_level=request.skill_level,
            ball_flight=request.ball_flight,
            user_goal=request.user_goal,
            club_used=request.club_used,
            practice_availability=request.practice_availability,
            handicap=request.handicap,
            prior_progress=request.prior_progress,
        )
        if not ai_ok:
            raise RuntimeError(
                f"Gemini analysis unavailable: {gemini_meta.get('error') or 'no AI narrative returned'}"
            )
        processing_time_ms = round((time.perf_counter() - started_at) * 1000)
        gemini_meta["processing_time_ms"] = processing_time_ms
        gemini_meta["processing_time_sec"] = round(processing_time_ms / 1000, 2)
        gemini_meta["camera_angle_detected"] = metric_payload.get("camera_angle")
        gemini_meta["hybrid_vision_evidence"] = metric_payload.get("hybrid_vision_evidence")
        gemini_meta["confidence_scores"] = {
            "diagnosis_evidence": [
                item.model_dump() for item in (report.diagnosis_engine.evidence if report.diagnosis_engine else [])
            ],
            "metric_checkpoints": metric_payload.get("checkpoints", []),
            "hybrid_vision_evidence": metric_payload.get("hybrid_vision_evidence"),
        }

        _trace_log("report_save_started", swing_id=swing_id, trace_id=trace_id)
        persist_analysis_result(
            analysis_id=request.analysis_id,
            video_id=request.video_id,
            user_id=request.user_id,
            report=report,
            key_frames=key_frames,
            metric_payload=metric_payload,
            ai_narrative_available=ai_ok,
            gemini_meta=gemini_meta,
        )
        _trace_log("report_save_success", swing_id=swing_id, trace_id=trace_id)
        _trace_log("analysis_completed", swing_id=swing_id, trace_id=trace_id)

        return report
    except Exception as exc:
        _trace_log("analysis_completed", swing_id=swing_id, trace_id=trace_id, error=str(exc))
        logger.exception("Analysis failed for %s: %s", request.analysis_id, exc)
        mark_analysis_failed(request.analysis_id, request.video_id, str(exc))
        raise
    finally:
        if video_path and video_path.exists():
            video_path.unlink(missing_ok=True)
