from __future__ import annotations

import logging
import socket
from datetime import datetime, timedelta, timezone

from app.persistence import get_supabase_client
from app.pipeline import run_analysis
from app.schemas import AnalyzeRequest

logger = logging.getLogger(__name__)


def retry_delay_seconds(attempt: int) -> int:
    return 30 * (4 ** max(0, attempt - 1))


def run_maintenance(client) -> dict[str, int]:
    now = datetime.now(timezone.utc)
    expired = (
        client.table("upload_sessions")
        .select("id,report_id,storage_path")
        .in_("status", ["pending", "uploaded"])
        .lt("expires_at", now.isoformat())
        .execute()
    )
    expired_count = 0
    for session in expired.data or []:
        client.storage.from_("swing-videos").remove([session["storage_path"]])
        client.table("upload_sessions").update({"status": "expired"}).eq(
            "id", session["id"]
        ).execute()
        client.rpc(
            "service_restore_analysis_credit",
            {"p_report_id": session["report_id"], "p_reason": "upload_expired"},
        ).execute()
        expired_count += 1

    stale_cutoff = now - timedelta(minutes=15)
    stale = (
        client.table("analysis_jobs")
        .select("id,report_id,attempts")
        .eq("status", "running")
        .lt("locked_at", stale_cutoff.isoformat())
        .execute()
    )
    stale_count = 0
    for job in stale.data or []:
        if int(job.get("attempts") or 0) >= 3:
            client.table("analysis_jobs").update(
                {"status": "failed", "locked_at": None, "locked_by": None}
            ).eq("id", job["id"]).execute()
            client.rpc(
                "service_restore_analysis_credit",
                {"p_report_id": job["report_id"], "p_reason": "worker_timeout"},
            ).execute()
        else:
            client.table("analysis_jobs").update(
                {
                    "status": "retry",
                    "available_at": now.isoformat(),
                    "locked_at": None,
                    "locked_by": None,
                }
            ).eq("id", job["id"]).execute()
        stale_count += 1

    retention_cutoff = now - timedelta(days=30)
    old_videos = (
        client.table("swing_videos")
        .select("id,storage_path,swing_reports!inner(id,source_video_deleted_at,status)")
        .lt("created_at", retention_cutoff.isoformat())
        .execute()
    )
    retained_count = 0
    for video in old_videos.data or []:
        reports = video.get("swing_reports") or []
        report = reports[0] if isinstance(reports, list) and reports else reports
        if not report or report.get("source_video_deleted_at"):
            continue
        if report.get("status") not in ("ready", "failed"):
            continue
        client.storage.from_("swing-videos").remove([video["storage_path"]])
        client.table("swing_reports").update(
            {"source_video_deleted_at": now.isoformat()}
        ).eq("id", report["id"]).execute()
        retained_count += 1

    return {
        "expired_uploads": expired_count,
        "stale_jobs": stale_count,
        "retained_videos_removed": retained_count,
    }


def _safe_error(exc: Exception) -> tuple[str, str]:
    text = str(exc).lower()
    if "valid video" in text or "30 seconds" in text or "too short" in text:
        return "invalid_video", "We could not read this video. Your credit was restored so you can upload a new clip."
    if "usable golf swing" in text or "non-golf" in text:
        return "unusable_swing", "We could not verify a usable golf swing. Your credit was restored."
    return "analysis_unavailable", "We could not complete the analysis. Your credit was restored so you can try again."


def _build_request(client, job: dict) -> AnalyzeRequest:
    report_result = (
        client.table("swing_reports")
        .select("id,user_id,video_id,swing_mode,swing_videos(storage_path)")
        .eq("id", job["report_id"])
        .single()
        .execute()
    )
    report = report_result.data
    if not report:
        raise ValueError("Report not found")

    video = report.get("swing_videos") or {}
    signed = client.storage.from_("swing-videos").create_signed_url(video["storage_path"], 3600)
    video_url = signed.get("signedURL") or signed.get("signedUrl")
    if not video_url:
        raise ValueError("Could not sign video URL")

    profile_result = (
        client.table("profiles")
        .select(
            "display_name,age,years_playing,physical_limitations,"
            "average_9_score,typical_miss,primary_goal"
        )
        .eq("id", report["user_id"])
        .single()
        .execute()
    )
    profile = profile_result.data or {}
    first_name = (profile.get("display_name") or "").split(" ")[0] or None
    context_parts = [
        f"Average 9-hole score: {profile.get('average_9_score')}."
        if profile.get("average_9_score")
        else "",
        f"Typical miss: {profile.get('typical_miss')}."
        if profile.get("typical_miss")
        else "",
        f"Main goal: {profile.get('primary_goal')}."
        if profile.get("primary_goal")
        else "",
    ]

    return AnalyzeRequest(
        analysis_id=report["id"],
        video_id=report["video_id"],
        user_id=report["user_id"],
        video_url=video_url,
        swing_mode=report.get("swing_mode") or "full_swing",
        player_name=first_name,
        player_context=" ".join(part for part in context_parts if part),
        player_age=profile.get("age"),
        years_playing=profile.get("years_playing"),
        physical_limitations=profile.get("physical_limitations"),
    )


def drain_jobs(limit: int = 1) -> dict[str, int]:
    client = get_supabase_client()
    maintenance = run_maintenance(client)
    worker_id = socket.gethostname()
    claimed = client.rpc(
        "service_claim_analysis_jobs",
        {"p_worker_id": worker_id, "p_limit": max(1, min(limit, 10))},
    ).execute()
    jobs = claimed.data or []
    completed = 0
    retried = 0
    failed = 0

    for job in jobs:
        report_id = job["report_id"]
        attempt = int(job.get("attempts") or 1)
        try:
            request = _build_request(client, job)
            run_analysis(request)
            client.table("analysis_jobs").update(
                {"status": "completed", "locked_at": None, "locked_by": None}
            ).eq("id", job["id"]).execute()
            client.rpc(
                "service_complete_analysis", {"p_report_id": report_id}
            ).execute()
            completed += 1
        except Exception as exc:
            logger.exception("Analysis job %s failed on attempt %s", job["id"], attempt)
            error_code, customer_message = _safe_error(exc)
            if attempt < 3:
                available_at = datetime.now(timezone.utc) + timedelta(
                    seconds=retry_delay_seconds(attempt)
                )
                client.table("analysis_jobs").update(
                    {
                        "status": "retry",
                        "available_at": available_at.isoformat(),
                        "locked_at": None,
                        "locked_by": None,
                        "last_error": str(exc)[:500],
                    }
                ).eq("id", job["id"]).execute()
                client.table("swing_reports").update(
                    {
                        "status": "processing",
                        "error_code": None,
                        "error_message": None,
                        "attempt_count": attempt,
                    }
                ).eq("id", report_id).execute()
                retried += 1
            else:
                client.table("analysis_jobs").update(
                    {
                        "status": "failed",
                        "locked_at": None,
                        "locked_by": None,
                        "last_error": str(exc)[:500],
                    }
                ).eq("id", job["id"]).execute()
                client.table("swing_reports").update(
                    {
                        "status": "failed",
                        "error_code": error_code,
                        "error_message": customer_message,
                        "attempt_count": attempt,
                        "ai_narrative_available": False,
                    }
                ).eq("id", report_id).execute()
                client.rpc(
                    "service_restore_analysis_credit",
                    {"p_report_id": report_id, "p_reason": error_code},
                ).execute()
                failed += 1

    return {
        "claimed": len(jobs),
        "completed": completed,
        "retried": retried,
        "failed": failed,
        **maintenance,
    }
