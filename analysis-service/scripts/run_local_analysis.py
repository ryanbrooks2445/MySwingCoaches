#!/usr/bin/env python3
"""Local analysis test script — no Supabase required unless --write-db is passed."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.frame_extractor import extract_frames
from app.gemini_coach import generate_coaching_report
from app.metrics import compute_metrics
from app.phase_detector import checkpoint_confidence, detect_checkpoints
from app.pose_processor import process_video_frames
from app.rules_engine import evaluate_rules
from app.schemas import CheckpointFrame


def main():
    parser = argparse.ArgumentParser(description="Run local swing analysis on a video file")
    parser.add_argument("video_path", type=Path, help="Path to mp4/mov file")
    parser.add_argument("--handedness", default="right", choices=["right", "left"])
    parser.add_argument("--skill-level", default="intermediate")
    parser.add_argument("--camera-angle", default="unknown")
    args = parser.parse_args()

    if not args.video_path.exists():
        print(f"File not found: {args.video_path}", file=sys.stderr)
        sys.exit(1)

    print(f"Extracting frames from {args.video_path}...")
    frames, fps, duration = extract_frames(args.video_path)
    print(f"  {len(frames)} frames, {fps:.1f} fps, ~{duration}s duration")

    print("Running MediaPipe pose...")
    pose_sequence = process_video_frames(frames)

    checkpoints = detect_checkpoints(pose_sequence, args.handedness)
    print(f"Checkpoints (MVP heuristics): {checkpoints}")

    metrics = compute_metrics(pose_sequence, checkpoints, args.handedness)
    print(f"\nMetrics:\n{json.dumps(metrics.model_dump(), indent=2)}")

    issues = evaluate_rules(metrics)
    print(f"\nRules engine detected {len(issues)} issue(s):")
    for issue in issues:
        print(f"  [{issue.severity}] {issue.issue}")

    checkpoint_frames = [
        CheckpointFrame(
            phase=phase,
            frame_index=idx,
            url=f"local://frame/{idx}",
            landmarks=pose_sequence[idx] if idx < len(pose_sequence) else None,
            confidence=checkpoint_confidence(pose_sequence, idx),
        )
        for phase, idx in checkpoints.items()
    ]

    print("\nGenerating Gemini coaching report...")
    report, ai_ok = generate_coaching_report(
        skill_level=args.skill_level,
        handedness=args.handedness,
        camera_angle=args.camera_angle,
        metrics=metrics,
        detected_issues=issues,
        checkpoint_frames=checkpoint_frames,
        history_summary=None,
    )
    print(f"AI narrative available: {ai_ok}")
    print(f"\nCoaching Report:\n{json.dumps(report.model_dump(), indent=2)}")


if __name__ == "__main__":
    main()
