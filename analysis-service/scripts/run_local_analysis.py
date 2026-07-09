#!/usr/bin/env python3
"""Local analysis test script — no Supabase required."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.frame_extractor import extract_frames
from app.gemini_coach import generate_coaching_report
from app.gemini_video import build_phase_evidence_packet
from app.mode_resolver import resolve_report_mode
from app.pipeline import SAMPLE_EVERY_N, _phases_for_mode
from app.pose_extractor import extract_pose_sequence
from app.report_audit import audit_report_quality
from app.swing_window import SwingWindowError, detect_swing_window


def main():
    parser = argparse.ArgumentParser(description="Run local swing analysis on a video file")
    parser.add_argument("video_path", type=Path, help="Path to mp4/mov file")
    parser.add_argument(
        "--pose-only",
        action="store_true",
        help="Run MediaPipe pose extraction only (skip Gemini)",
    )
    args = parser.parse_args()

    if not args.video_path.exists():
        print(f"File not found: {args.video_path}", file=sys.stderr)
        sys.exit(1)

    print(f"Extracting frames from {args.video_path}...")
    frames, fps, duration = extract_frames(args.video_path, sample_every_n=SAMPLE_EVERY_N)
    print(f"  {len(frames)} frames, {fps:.1f} fps, ~{duration}s duration")

    print("Running MediaPipe Pose...")
    pose_sequence = extract_pose_sequence(frames)
    print(
        f"  provider={pose_sequence.provider} model={pose_sequence.model} "
        f"avg_confidence={pose_sequence.average_confidence:.3f} "
        f"camera={pose_sequence.camera_angle_estimate}"
    )
    if pose_sequence.limitations:
        print(f"  limitations: {'; '.join(pose_sequence.limitations)}")

    try:
        swing_window = detect_swing_window(
            frames,
            fps=fps,
            sample_every_n=SAMPLE_EVERY_N,
            pose_sequence=pose_sequence,
        )
    except SwingWindowError as exc:
        print(f"Swing window rejected: {exc}", file=sys.stderr)
        sys.exit(2)

    print(f"Swing window: {swing_window.to_dict()}")
    phase_result = _phases_for_mode(frames, swing_window, "full_swing", pose_sequence)
    if phase_result is None:
        print("Phase detection failed", file=sys.stderr)
        sys.exit(2)

    print(f"Phase map: {json.dumps(phase_result.phase_map, indent=2)}")
    print(f"Detection method: {phase_result.detection_method}")
    if phase_result.validation:
        print(f"Phase validation: {json.dumps(phase_result.validation, indent=2)}")
    pose_landmarks = pose_sequence.to_persist_dict(
        phase_result.keyframe_indices,
        validation=phase_result.validation,
        timeline=phase_result.timeline,
    )
    print(f"Pose landmarks (keyframes): {json.dumps(pose_landmarks, indent=2)}")
    print(
        "Pose evidence packet excerpt:\n"
        + build_phase_evidence_packet(phase_result, swing_window.to_dict(), pose_sequence)[:2000]
    )
    if phase_result.limitation_notes():
        print("Limitations:", "; ".join(phase_result.limitation_notes()))

    if args.pose_only:
        print("\nPose-only run complete (--pose-only).")
        return

    print("\nGenerating Gemini video coaching report...")
    report, ai_ok, gemini_meta = generate_coaching_report(
        video_path=args.video_path,
        frames=frames,
        phase_result=phase_result,
        swing_window=swing_window.to_dict(),
        pose_sequence=pose_sequence,
        history_summary=None,
    )
    print(f"AI narrative available: {ai_ok}")
    if gemini_meta:
        print(f"Gemini meta: {json.dumps(gemini_meta)}")
    if not ai_ok:
        print("Report audit: FAIL — AI analysis unavailable")
        print(f"\nCoaching Report:\n{json.dumps(report.model_dump(), indent=2)}")
        sys.exit(2)
    try:
        report = resolve_report_mode(report)
        audit_report_quality(
            report,
            swing_mode="full_swing",
            player_context=None,
            history_summary=None,
            phase_map=phase_result.phase_map,
        )
        print("Report audit: PASS")
    except Exception as exc:
        print(f"Report audit: FAIL — {exc}")
        print(f"\nCoaching Report:\n{json.dumps(report.model_dump(), indent=2)}")
        sys.exit(3)
    print(f"\nCoaching Report:\n{json.dumps(report.model_dump(), indent=2)}")


if __name__ == "__main__":
    main()
