from __future__ import annotations

import logging
import tempfile
from pathlib import Path

from supabase import create_client

from app.config import get_settings
from app.frame_extractor import save_frame_jpeg
from app.schemas import CheckpointFrame, CoachingReportSchema, DetectedIssue, SwingMetrics

logger = logging.getLogger(__name__)


def get_supabase_client():
    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_service_role_key:
        raise ValueError("Supabase credentials not configured")
    return create_client(settings.supabase_url, settings.supabase_service_role_key)


def upload_checkpoint_frames(
    user_id: str,
    video_id: str,
    frames: list,
    checkpoints: dict[str, int],
    pose_sequence: list,
    phase_confidence: dict[str, float],
) -> list[CheckpointFrame]:
    client = get_supabase_client()
    results: list[CheckpointFrame] = []

    with tempfile.TemporaryDirectory() as tmpdir:
        for phase, idx in checkpoints.items():
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

            landmarks = pose_sequence[idx] if idx < len(pose_sequence) else None
            results.append(
                CheckpointFrame(
                    phase=phase,
                    frame_index=idx,
                    storage_path=storage_path,
                    url=url,
                    landmarks=landmarks,
                    confidence=phase_confidence.get(phase, 0.5),
                )
            )

    return results


def persist_analysis_result(
    *,
    analysis_id: str,
    video_id: str,
    user_id: str,
    report: CoachingReportSchema,
    metrics: SwingMetrics,
    rules_issues: list[DetectedIssue],
    checkpoint_frames: list[CheckpointFrame],
    ai_narrative_available: bool,
) -> None:
    client = get_supabase_client()

    key_frame_urls = [
        {"phase": f.phase, "url": f.url, "confidence": f.confidence}
        for f in checkpoint_frames
    ]
    pose_landmarks = {
        f.phase: f.landmarks for f in checkpoint_frames if f.landmarks
    }

    client.table("swing_reports").update({
        "status": "ready",
        "overall_score": report.overall_score,
        "setup_score": report.setup_score,
        "backswing_score": report.backswing_score,
        "downswing_score": report.downswing_score,
        "impact_score": report.impact_score,
        "finish_score": report.finish_score,
        "main_diagnosis": report.main_diagnosis,
        "practice_plan": report.practice_plan,
        "next_upload_focus": report.next_upload_focus,
        "disclaimer": report.disclaimer,
        "key_frame_urls": key_frame_urls,
        "pose_landmarks": pose_landmarks,
        "gemini_raw": report.model_dump(),
        "ai_narrative_available": ai_narrative_available,
    }).eq("id", analysis_id).execute()

    client.table("swing_videos").update({"status": "ready"}).eq("id", video_id).execute()

    client.table("swing_metrics").insert({
        "report_id": analysis_id,
        "user_id": user_id,
        **{k: v for k, v in metrics.model_dump().items() if k != "raw_metrics"},
        "raw_metrics": metrics.raw_metrics,
    }).execute()

    # Merge Gemini top issues with rules issues
    client.table("swing_issues").delete().eq("report_id", analysis_id).execute()

    gemini_issues = report.top_issues
    for i, gi in enumerate(gemini_issues):
        client.table("swing_issues").insert({
            "report_id": analysis_id,
            "user_id": user_id,
            "issue_code": gi.issue.lower().replace(" ", "_")[:50],
            "issue": gi.issue,
            "severity": gi.severity,
            "why_it_matters": gi.why_it_matters,
            "fix": gi.fix,
            "drill": gi.drill,
            "source": "gemini",
            "sort_order": i,
        }).execute()

    for i, ri in enumerate(rules_issues):
        if not any(gi.issue == ri.issue for gi in gemini_issues):
            client.table("swing_issues").insert({
                "report_id": analysis_id,
                "user_id": user_id,
                "issue_code": ri.issue_code,
                "issue": ri.issue,
                "severity": ri.severity,
                "why_it_matters": ri.why_it_matters,
                "fix": ri.fix,
                "drill": ri.drill,
                "source": "rules",
                "metric_evidence": ri.metric_evidence,
                "sort_order": 10 + i,
            }).execute()

    client.table("drill_recommendations").delete().eq("report_id", analysis_id).execute()
    for i, gi in enumerate(gemini_issues):
        client.table("drill_recommendations").insert({
            "report_id": analysis_id,
            "user_id": user_id,
            "title": gi.drill,
            "description": gi.fix,
            "focus_area": gi.issue,
            "sort_order": i,
        }).execute()

    # Increment analyses_used
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
