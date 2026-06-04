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


class DiagnosticTruth(BaseModel):
    headline: str = Field(description="Pattern name, max 6 words e.g. 'The Over-the-Top Cut'")
    what_your_eye_sees: str = Field(description="Ball flight. Max 2 short sentences.")
    mechanical_cause: str = Field(description="Root cause only. Max 2 sentences. **Bold** one key term.")
    kinetic_chain: str = Field(
        description="Max 2 bullets: fault → compensation → flight. One analogy max."
    )


class BlueprintStep(BaseModel):
    title: str = Field(description="Max 5 words")
    step_type: Literal["setup", "visual_cue", "constraint_drill"]
    adjustment: str | None = Field(default=None, description="One line setup change")
    action: str | None = Field(default=None, description="One line what to do")
    feel: str = Field(description="THE money line — max 15 words, what the body feels")
    success_condition: str | None = Field(default=None, description="One line pass/fail check")
    video_slug: str | None = Field(
        default=None,
        description="From catalog. Required for constraint_drill.",
    )
    video_url: str | None = Field(default=None, description="Leave null")
    video_title: str | None = Field(default=None, description="Leave null")


class KinestheticBlueprint(BaseModel):
    headline: str = Field(description="Max 5 words")
    intro: str = Field(description="One sentence max — changing boundaries, not rebuilding")
    steps: list[BlueprintStep] = Field(min_length=2, max_length=3)


class MilestoneBlock(BaseModel):
    days: str = Field(description="e.g. 'Day 1-3'")
    title: str = Field(description="Max 4 words")
    detail: str = Field(description="Max 2 short sentences — reps + what to ignore")


class AccountabilityPlan(BaseModel):
    weekly_focus: str = Field(description="1-3 words e.g. 'Rotation'")
    milestones: list[MilestoneBlock] = Field(min_length=3, max_length=3)
    day_7_test: str = Field(description="One sentence pass/fail before next upload")


class CoachingReportSchema(BaseModel):
    personalized_greeting: str = Field(
        description=(
            "1-2 short sentences. Use player's first name. Reference their swing history "
            "(first upload vs returning, prior focus if any). Hook them to open the app again. Max 35 words."
        )
    )
    diagnostic: DiagnosticTruth
    blueprint: KinestheticBlueprint
    roadmap: AccountabilityPlan
    next_upload_focus: str = Field(description="One filming tip, max 20 words")
    disclaimer: str


class KeyFrame(BaseModel):
    phase: str
    frame_index: int
    storage_path: str | None = None
    url: str | None = None


class AnalyzeRequest(BaseModel):
    analysis_id: str
    video_id: str
    user_id: str
    video_url: str
    history_summary: str | None = None
    player_name: str | None = None
    swing_number: int | None = None
    player_context: str | None = None
