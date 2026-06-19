from typing import Literal

from pydantic import BaseModel, Field

SwingMode = Literal["full_swing", "chipping", "putting"]

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

CHECKPOINTS_BY_MODE: dict[SwingMode, list[str]] = {
    "full_swing": CHECKPOINTS,
    "chipping": ["setup", "backswing", "downswing", "impact", "finish"],
    "putting": ["address", "backstroke", "forward", "impact", "follow_through", "finish"],
}


class AnalysisBullet(BaseModel):
    title: str = Field(description="Bold label e.g. 'Excellent Lower Body Action' or 'The Setup: The Sitting Stance'")
    detail: str = Field(description="2-4 sentences. Specific to THIS swing video. Plain English.")


class ProFix(BaseModel):
    title: str = Field(description="Fix name e.g. 'Stand Up and Tilt'")
    detail: str = Field(description="What to do and why it unlocks their path. 2-3 sentences.")


class FeelBlueprintDiagnostic(BaseModel):
    opening_narrative: str = Field(
        description=(
            "2-3 sentences. Unfiltered PGA tone. Reference age/years/athleticism from profile if known. "
            "Name the setup-to-backswing fight — not a generic label. No 'Standard Slice' boxes."
        )
    )
    headline: str = Field(
        description="Unique pattern name for the report title. Max 8 words. e.g. 'The Sitting Stance Loop'"
    )
    strengths: list[AnalysisBullet] = Field(
        min_length=2,
        max_length=4,
        description="THE STRENGTHS (The Good Stuff) — real positives seen in the video.",
    )
    flaws: list[AnalysisBullet] = Field(
        min_length=2,
        max_length=4,
        description=(
            "THE MISSING PIECE chain (never say flaw/fault) — setup link → takeaway → downswing. "
            "Titles use unlocked-potential language; details empower, not shame."
        ),
    )
    current_ceiling: str = Field(
        description=(
            "WHAT IS THEIR CEILING (current): Honest handicap/outcome range if mechanics stay. "
            "Mention timing-dependent miss (push-slice, chunk, etc.). 2-3 sentences."
        )
    )
    potential_ceiling: str = Field(
        description=(
            "Ceiling IF they fix the root setup/flaw — achievable range. Tie to existing athleticism. "
            "Pain-free, not tour textbook. 2-3 sentences."
        )
    )
    pro_fixes: list[ProFix] = Field(
        min_length=2,
        max_length=3,
        description="THE PRO FIXES — prioritized setup/takeaway feels that clear the path.",
    )
    body_part_cue: str = Field(description="Primary tactile feel. No jargon. Max 20 words.")
    spatial_cue: str = Field(description="Spatial awareness feel. No jargon. Max 20 words.")


class DiagnosticTruth(BaseModel):
    """Legacy format — kept for older reports only."""

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


class DrillSummary(BaseModel):
    name: str = Field(description="Drill name — specific to this swing, not generic")
    why_it_helps: str = Field(description="1-2 sentences tied to pga_analysis and main_fix")
    how_to_do_it: str = Field(description="1-2 sentences — reps, setup, pass/fail")


class DiagnosticCheckpointGrade(BaseModel):
    checkpoint: str = Field(
        description="Short label e.g. 'Setup: weight on heels' or 'Backswing: arm lift'"
    )
    grade: Literal["optimal", "compensation", "constraint", "not_visible"] = Field(
        description="Internal grade only — never show raw grade labels in user-facing fields"
    )
    observation: str = Field(
        description="One line evidence from THIS video. Internal/coach view."
    )


class AdvancedDetails(BaseModel):
    report_mode: Literal["development", "maintenance"] = Field(
        default="development",
        description="maintenance = elite baseline, no forced flaw; development = real unlock needed",
    )
    foundational_missing_piece: str = Field(
        description=(
            "Development: earliest breakdown. Maintenance: 'None — maintain current elite baseline'."
        )
    )
    profile_constraints_applied: str = Field(
        default="",
        description="How Human Blueprint (age, injuries, mobility, years playing) shaped the plan.",
    )
    diagnostic_checkpoints: list[DiagnosticCheckpointGrade] = Field(
        default_factory=list,
        max_length=20,
        description="8-20 key graded checkpoints when video analysis succeeds. Internal only.",
    )
    root_cause: str = Field(description="Technical root — aligns with foundational_missing_piece")
    symptom: str = Field(description="What the golfer sees (ball flight, contact)")
    evidence_metrics: list[str] = Field(
        default_factory=list,
        max_length=8,
        description="Short checkpoint observations e.g. 'Address: weight on heels'",
    )
    secondary_fix: str = Field(description="Alternate fix — hidden from main UI")
    optional_fix: str = Field(description="Nice-to-have — hidden from main UI")
    chain_reaction: str = Field(description="Hidden technical: missing link → compensation → miss")
    why_it_caused_the_miss: str = Field(description="Plain-English miss explanation")
    confidence_score: float = Field(
        ge=0.0,
        le=1.0,
        description="0-1 model confidence in the diagnosis",
    )
    next_checkpoint: str = Field(
        default="",
        description="Phase to evaluate on next upload (e.g. takeaway, impact)",
    )


class CoachingReportSchema(BaseModel):
    personalized_greeting: str = Field(
        description=(
            "First name if known, one genuine visible positive, then the priority. "
            "No hype, handicap prediction, or unsupported praise. Max 25 words."
        )
    )
    pga_analysis: str = Field(
        description=(
            "USER-FACING deep dive in plain English. Four sections with plain-text titles on their own line "
            "(NO markdown #): What's working, Setup to finish, then either "
            "The missing piece + What changes when you unlock it (development) OR "
            "What to keep doing + Your ceiling at this level (maintenance). "
            "Clear, supportive, evidence-led tone. Use **bold** only for phase labels in Setup to finish."
        )
    )
    main_fix: str = Field(
        description=(
            "USER-FACING: ONE primary unlock — what to add or hand off (hips, chest, path). "
            "2-3 sentences. Breakthrough energy, not corrective shame."
        )
    )
    tips_and_feels: list[str] = Field(
        min_length=2,
        max_length=4,
        description=(
            "USER-FACING: Tactile feels/tricks to execute the fix. "
            "Start with 'Feel...' when natural. No jargon. No repeated ideas."
        ),
    )
    drills: list[DrillSummary] = Field(
        max_length=3,
        description="USER-FACING: 0-3 drills. Empty OK in maintenance mode.",
    )
    next_swing_check: str = Field(
        description="USER-FACING: One clear thing to film or look for on next upload."
    )
    advanced_details: AdvancedDetails
    feel_blueprint: FeelBlueprintDiagnostic | None = Field(
        default=None,
        description="Optional deep narrative storage — leave null; use advanced_details instead.",
    )
    blueprint: KinestheticBlueprint
    roadmap: AccountabilityPlan
    next_upload_focus: str = Field(description="Same as next_swing_check or filming tip, max 25 words")
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
    trace_id: str | None = None
    swing_mode: SwingMode = "full_swing"
    history_summary: str | None = None
    player_name: str | None = None
    swing_number: int | None = None
    player_context: str | None = None
    player_age: int | None = None
    years_playing: int | None = None
    physical_limitations: str | None = None
