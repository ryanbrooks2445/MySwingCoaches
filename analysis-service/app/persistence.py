from __future__ import annotations

import logging
import tempfile
from pathlib import Path

from supabase import create_client

from app.config import get_settings
from app.frame_extractor import save_frame_jpeg
from app.schemas import CoachingReportSchema, KeyFrame
from app.report_converter import filter_phase_map
from app.trace_log import log_trace

logger = logging.getLogger(__name__)


def get_supabase_client():
    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_service_role_key:
        raise ValueError("Supabase credentials not configured")
    return create_client(settings.supabase_url, settings.supabase_service_role_key)


def upload_key_frames(
    user_id: str,
    video_id: str,
    frames: list,
    keyframe_indices: dict[str, int],
) -> list[KeyFrame]:
    client = get_supabase_client()
    results: list[KeyFrame] = []

    with tempfile.TemporaryDirectory() as tmpdir:
        for phase, idx in keyframe_indices.items():
            frame = frames[idx]
            local_path = Path(tmpdir) / f"{phase}.jpg"
            save_frame_jpeg(frame, local_path)

            storage_path = f"{user_id}/{video_id}/{phase}.jpg"
            with open(local_path, "rb") as f:
                client.storage.from_("swing-frames").upload(
                    storage_path,
                    f.read(),
                    file_options={"content-type": "image/jpeg", "upsert": "true"},
                )

            signed = client.storage.from_("swing-frames").create_signed_url(storage_path, 86400)
            url = signed.get("signedURL") or signed.get("signedUrl") or ""

            results.append(
                KeyFrame(
                    phase=phase,
                    frame_index=idx,
                    storage_path=storage_path,
                    url=url,
                )
            )

    return results


def persist_analysis_result(
    *,
    analysis_id: str,
    video_id: str,
    user_id: str,
    report: CoachingReportSchema,
    key_frames: list[KeyFrame],
    ai_narrative_available: bool,
    gemini_meta: dict | None = None,
    trace_id: str | None = None,
    phase_map: list[dict] | None = None,
    swing_window: dict | None = None,
    pose_landmarks: dict | None = None,
) -> None:
    client = get_supabase_client()
    visible_phase_map = filter_phase_map(phase_map)
    if not visible_phase_map:
        report = report.model_copy(
            update={
                "advanced_details": report.advanced_details.model_copy(
                    update={"diagnostic_checkpoints": []}
                )
            }
        )

    key_frame_urls = [
        {"phase": f.phase, "storage_path": f.storage_path}
        for f in key_frames
        if f.storage_path
    ]
    coaching_content = report.model_dump()

    gemini_raw = {
        "provider": "gemini",
        "raw_responses": (gemini_meta or {}).get("raw_responses", []),
        "meta": {k: v for k, v in (gemini_meta or {}).items() if k != "raw_responses"},
        "final_report_preview": {
            "pga_analysis": report.pga_analysis,
            "main_fix": report.main_fix,
            "advanced_details": report.advanced_details.model_dump(),
        },
        "debug_context": {
            "key_frames": key_frame_urls,
            "phase_map": visible_phase_map,
            "swing_window": swing_window,
            "pose_landmarks": pose_landmarks or {},
        },
    }

    client.table("swing_reports").update({
        "status": "ready",
        "overall_score": None,
        "setup_score": None,
        "backswing_score": None,
        "downswing_score": None,
        "impact_score": None,
        "finish_score": None,
        "main_diagnosis": report.pga_analysis[:500],
        "swing_strengths": [],
        "practice_plan": report.main_fix[:500],
        "next_upload_focus": report.next_swing_check or report.next_upload_focus,
        "disclaimer": report.disclaimer,
        "coaching_content": coaching_content,
        "key_frame_urls": key_frame_urls,
        "phase_map": visible_phase_map,
        "swing_window": swing_window,
        "pose_landmarks": pose_landmarks or {},
        "gemini_raw": gemini_raw,
        "ai_narrative_available": ai_narrative_available,
        "error_message": (gemini_meta or {}).get("error") if not ai_narrative_available else None,
    }).eq("id", analysis_id).execute()

    client.table("swing_videos").update({"status": "ready"}).eq("id", video_id).execute()

    client.table("swing_issues").delete().eq("report_id", analysis_id).execute()
    client.table("drill_recommendations").delete().eq("report_id", analysis_id).execute()

    log_trace(
        "report_saved",
        trace_id=trace_id,
        user_id=user_id,
        report_id=analysis_id,
        status="ready",
        ai_narrative_available=ai_narrative_available,
    )


def mark_analysis_failed(analysis_id: str, video_id: str, error: str) -> None:
    client = get_supabase_client()
    client.table("swing_reports").update({
        "status": "failed",
        "error_message": error[:500],
        "ai_narrative_available": False,
    }).eq("id", analysis_id).execute()
    client.table("swing_videos").update({"status": "failed"}).eq("id", video_id).execute()
