from __future__ import annotations

from app.pose_processor import hip_line_angle, spine_angle, wrist_height


def detect_checkpoints(
    pose_sequence: list[dict | None],
    handedness: str = "right",
) -> dict[str, int]:
    """MVP heuristic checkpoint detection from pose sequence."""
    n = len(pose_sequence)
    if n == 0:
        return {k: 0 for k in ["address", "takeaway", "top", "downswing", "impact", "finish"]}

    valid_indices = [i for i, p in enumerate(pose_sequence) if p is not None]
    if not valid_indices:
        return {k: 0 for k in ["address", "takeaway", "top", "downswing", "impact", "finish"]}

    wrist_heights = []
    for i, pose in enumerate(pose_sequence):
        if pose:
            wrist_heights.append((i, wrist_height(pose, handedness)))
        else:
            wrist_heights.append((i, 0.0))

    address = valid_indices[0]
    finish = valid_indices[-1]

    # Top of backswing: max wrist height (hands highest)
    top = max(wrist_heights, key=lambda x: x[1])[0]

    # Takeaway: ~15% into swing before top
    takeaway = address + max(1, int((top - address) * 0.25))

    # Impact: after top, min wrist height before finish
    post_top = [(i, h) for i, h in wrist_heights if top < i < finish]
    impact = min(post_top, key=lambda x: x[1])[0] if post_top else top + max(1, (finish - top) // 2)

    # Downswing: midpoint top -> impact
    downswing = top + max(1, (impact - top) // 2)

    return {
        "address": address,
        "takeaway": min(takeaway, top),
        "top": top,
        "downswing": downswing,
        "impact": impact,
        "finish": finish,
    }


def checkpoint_confidence(pose_sequence: list[dict | None], index: int) -> float:
    pose = pose_sequence[index] if 0 <= index < len(pose_sequence) else None
    if not pose:
        return 0.2
    visibilities = [v.get("visibility", 0) for v in pose.values() if isinstance(v, dict)]
    if not visibilities:
        return 0.3
    avg = sum(visibilities) / len(visibilities)
    return round(min(0.95, max(0.35, avg)), 2)
