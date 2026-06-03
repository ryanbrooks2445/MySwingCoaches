from typing import Literal

from pydantic import BaseModel, Field

DISCLAIMER = (
    "AI-generated swing analysis inspired by common coaching principles. "
    "This does not replace in-person instruction from a certified golf professional."
)

CHECKPOINTS = [
    "address",
    "takeaway",
    "top",
    "downswing",
    "impact",
    "finish",
]


class TopIssue(BaseModel):
    issue: str
    severity: Literal["low", "medium", "high"]
    why_it_matters: str
    fix: str
    drill: str


class CoachingReportSchema(BaseModel):
    overall_score: int = Field(ge=0, le=100)
    setup_score: int = Field(ge=0, le=100)
    backswing_score: int = Field(ge=0, le=100)
    downswing_score: int = Field(ge=0, le=100)
    impact_score: int = Field(ge=0, le=100)
    finish_score: int = Field(ge=0, le=100)
    main_diagnosis: str
    top_issues: list[TopIssue]
    practice_plan: str
    next_upload_focus: str
    disclaimer: str


class AnalyzeRequest(BaseModel):
    analysis_id: str
    video_id: str
    user_id: str
    video_url: str
    handedness: Literal["right", "left"] = "right"
    skill_level: Literal["beginner", "intermediate", "advanced"] = "intermediate"
    camera_angle: Literal["face-on", "down-the-line", "unknown"] = "unknown"
    history_summary: str | None = None


class CheckpointFrame(BaseModel):
    phase: str
    frame_index: int
    storage_path: str | None = None
    url: str | None = None
    landmarks: dict | None = None
    confidence: float = 0.5


class DetectedIssue(BaseModel):
    issue_code: str
    issue: str
    severity: Literal["low", "medium", "high"]
    why_it_matters: str
    fix: str
    drill: str
    metric_evidence: dict = Field(default_factory=dict)


class SwingMetrics(BaseModel):
    head_movement: float
    spine_angle_address: float
    spine_angle_impact: float
    spine_angle_change: float
    hip_rotation_address_to_top: float
    hip_rotation_top_to_impact: float
    shoulder_tilt_top: float
    lead_arm_angle_top: float
    lead_arm_angle_impact: float
    trail_elbow_flex_top: float
    knee_bend_address: float
    knee_bend_impact: float
    finish_balance: float
    tempo_ratio: float
    raw_metrics: dict = Field(default_factory=dict)
