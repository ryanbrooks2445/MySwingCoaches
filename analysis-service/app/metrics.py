from __future__ import annotations

import math

from app.pose_processor import angle_between, get_point, hip_line_angle, spine_angle, wrist_height
from app.schemas import SwingMetrics


def _dist(p1: tuple[float, float], p2: tuple[float, float]) -> float:
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])


def compute_metrics(
    pose_sequence: list[dict | None],
    checkpoints: dict[str, int],
    handedness: str = "right",
) -> SwingMetrics:
    lead = "left" if handedness == "right" else "right"
    trail = "right" if handedness == "right" else "left"

    def pose_at(phase: str) -> dict | None:
        idx = checkpoints.get(phase, 0)
        if 0 <= idx < len(pose_sequence):
            return pose_sequence[idx]
        return None

    address = pose_at("address") or {}
    top = pose_at("top") or {}
    impact = pose_at("impact") or {}
    finish = pose_at("finish") or {}

    nose_addr = get_point(address, "nose") if address else (0, 0)
    max_head_move = 0.0
    for pose in pose_sequence:
        if pose:
            nose = get_point(pose, "nose")
            max_head_move = max(max_head_move, _dist(nose_addr, nose))

    spine_addr = spine_angle(address) if address else 0.0
    spine_imp = spine_angle(impact) if impact else 0.0

    hip_addr = hip_line_angle(address) if address else 0.0
    hip_top = hip_line_angle(top) if top else 0.0
    hip_imp = hip_line_angle(impact) if impact else 0.0

    ls, rs = get_point(top, f"{lead}_shoulder"), get_point(top, f"{trail}_shoulder")
    shoulder_tilt = abs(math.degrees(math.atan2(rs[1] - ls[1], rs[0] - ls[0]))) if top else 0.0

    def arm_angle(pose: dict, side: str) -> float:
        if not pose:
            return 0.0
        return angle_between(
            get_point(pose, f"{side}_wrist"),
            get_point(pose, f"{side}_shoulder"),
            get_point(pose, f"{side}_elbow"),
        )

    trail_elbow_top = arm_angle(top, trail) if top else 0.0

    def knee_angle(pose: dict, side: str) -> float:
        if not pose:
            return 0.0
        return angle_between(
            get_point(pose, f"{side}_hip"),
            get_point(pose, f"{side}_knee"),
            get_point(pose, f"{side}_ankle"),
        )

    finish_poses = [p for p in pose_sequence[-5:] if p]
    finish_variance = 0.0
    if len(finish_poses) >= 2:
        nose_positions = [get_point(p, "nose") for p in finish_poses]
        cx = sum(p[0] for p in nose_positions) / len(nose_positions)
        cy = sum(p[1] for p in nose_positions) / len(nose_positions)
        finish_variance = sum(_dist(p, (cx, cy)) for p in nose_positions) / len(nose_positions)

    addr_to_top = max(1, checkpoints["top"] - checkpoints["address"])
    top_to_imp = max(1, checkpoints["impact"] - checkpoints["top"])
    tempo = round(addr_to_top / top_to_imp, 2)

    return SwingMetrics(
        head_movement=round(max_head_move * 100, 2),
        spine_angle_address=round(spine_addr, 2),
        spine_angle_impact=round(spine_imp, 2),
        spine_angle_change=round(abs(spine_imp - spine_addr), 2),
        hip_rotation_address_to_top=round(abs(hip_top - hip_addr), 2),
        hip_rotation_top_to_impact=round(abs(hip_imp - hip_top), 2),
        shoulder_tilt_top=round(shoulder_tilt, 2),
        lead_arm_angle_top=round(arm_angle(top, lead), 2),
        lead_arm_angle_impact=round(arm_angle(impact, lead), 2),
        trail_elbow_flex_top=round(trail_elbow_top, 2),
        knee_bend_address=round(knee_angle(address, lead), 2),
        knee_bend_impact=round(knee_angle(impact, lead), 2),
        finish_balance=round(max(0, 1 - finish_variance * 10) * 100, 2),
        tempo_ratio=tempo,
        raw_metrics={
            "checkpoints": checkpoints,
            "handedness": handedness,
        },
    )
