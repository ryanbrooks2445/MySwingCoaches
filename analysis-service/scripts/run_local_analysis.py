#!/usr/bin/env python3
"""Local analysis test script — no Supabase required."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.frame_extractor import extract_frames
from app.frame_sampler import sample_keyframe_indices
from app.gemini_coach import generate_coaching_report


def main():
    parser = argparse.ArgumentParser(description="Run local swing analysis on a video file")
    parser.add_argument("video_path", type=Path, help="Path to mp4/mov file")
    args = parser.parse_args()

    if not args.video_path.exists():
        print(f"File not found: {args.video_path}", file=sys.stderr)
        sys.exit(1)

    print(f"Extracting frames from {args.video_path}...")
    frames, fps, duration = extract_frames(args.video_path)
    print(f"  {len(frames)} frames, {fps:.1f} fps, ~{duration}s duration")

    keyframe_indices = sample_keyframe_indices(len(frames))
    print(f"Key frame indices (evenly sampled): {keyframe_indices}")

    print("\nGenerating Gemini video coaching report...")
    report, ai_ok, gemini_meta = generate_coaching_report(
        video_path=args.video_path,
        frames=frames,
        keyframe_indices=keyframe_indices,
        history_summary=None,
    )
    print(f"AI narrative available: {ai_ok}")
    if gemini_meta:
        print(f"Gemini meta: {json.dumps(gemini_meta)}")
    print(f"\nCoaching Report:\n{json.dumps(report.model_dump(), indent=2)}")


if __name__ == "__main__":
    main()
