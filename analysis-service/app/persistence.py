from __future__ import annotations

import logging
import tempfile
from pathlib import Path

from supabase import create_client

from app.config import get_settings
from app.frame_extractor import save_frame_jpeg
from app.schemas import CoachingReportSchema, KeyFrame

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
    metric_payload: dict | None = None,
    gemini_meta: dict | None = None,
) -> None:
    client = get_supabase_client()

    key_frame_urls = [
        {"phase": f.phase, "url": f.url, "storage_path": f.storage_path}
        for f in key_frames
    ]
    coaching_content = report.model_dump()
    pose_payload = metric_payload or {}

    gemini_raw = {
        **coaching_content,
        "_meta": gemini_meta or {},
        "_debug": {
            "gemini_input": {
                "prompt": (gemini_meta or {}).get("prompt"),
                "frame_count": (gemini_meta or {}).get("frame_count"),
                "frame_timestamps": (gemini_meta or {}).get("frame_timestamps"),
                "frame_labels": (gemini_meta or {}).get("frame_labels"),
                "frames": (gemini_meta or {}).get("frames"),
                "full_video_sent": (gemini_meta or {}).get("full_video_sent"),
                "video_attached": (gemini_meta or {}).get("video_attached"),
                "model_name": (gemini_meta or {}).get("model_used"),
                "input_parts": (gemini_meta or {}).get("input_parts"),
                "camera_angle_detected": (gemini_meta or {}).get("camera_angle_detected"),
            },
            "gemini_raw_response": (gemini_meta or {}).get("gemini_raw_response"),
            "frontend_display_source": coaching_content,
            "processing_time_ms": (gemini_meta or {}).get("processing_time_ms"),
            "processing_time_sec": (gemini_meta or {}).get("processing_time_sec"),
            "camera_angle_detection": (gemini_meta or {}).get("camera_angle_detected"),
            "confidence_scores": (gemini_meta or {}).get("confidence_scores"),
            "hybrid_vision_evidence": (gemini_meta or {}).get("hybrid_vision_evidence"),
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
        "main_diagnosis": report.improvement_engine.main_diagnosis,
        "swing_strengths": [],
        "practice_plan": report.improvement_engine.practice_plan.practice_goal,
        "next_upload_focus": report.improvement_engine.improvement_benchmark.target_next_upload,
        "disclaimer": report.disclaimer,
        "coaching_content": coaching_content,
        "key_frame_urls": key_frame_urls,
        "pose_landmarks": pose_payload,
        "gemini_raw": gemini_raw,
        "ai_narrative_available": ai_narrative_available,
        "error_message": (gemini_meta or {}).get("error") if not ai_narrative_available else None,
    }).eq("id", analysis_id).execute()

    client.table("swing_videos").update({"status": "ready"}).eq("id", video_id).execute()

    client.table("swing_issues").delete().eq("report_id", analysis_id).execute()
    client.table("drill_recommendations").delete().eq("report_id", analysis_id).execute()

    sub = client.table("subscriptions").select("analyses_used").eq("user_id", user_id).single().execute()
    if sub.data:
        used = sub.data.get("analyses_used", 0) + 1
        client.table("subscriptions").update({"analyses_used": used}).eq("user_id", user_id).execute()


def mark_analysis_failed(analysis_id: str, video_id: str, error: str) -> None:
    client = get_supabase_client()
    client.table("swing_reports").update({
        "status": "failed",
        "error_message": error[:500],
        "ai_narrative_available": False,
    }).eq("id", analysis_id).execute()
    client.table("swing_videos").update({"status": "failed"}).eq("id", video_id).execute()
