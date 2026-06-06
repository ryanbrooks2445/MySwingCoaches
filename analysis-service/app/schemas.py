from typing import Literal

from pydantic import BaseModel, Field

SwingMode = Literal["full_swing", "chipping", "putting"]

DISCLAIMER = (
    "AI-generated swing analysis inspired by common coaching principles. "
    "This does not replace in-person instruction from a certified golf professional."
)

CHECKPOINTS = [
    "setup_address",
    "takeaway",
    "club_parallel_back",
    "lead_arm_parallel_back",
    "top_of_backswing",
    "transition",
    "lead_arm_parallel_down",
    "shaft_parallel_down",
    "impact",
    "release",
    "finish",
]

CHECKPOINTS_BY_MODE: dict[SwingMode, list[str]] = {
    "full_swing": CHECKPOINTS,
    "chipping": ["address", "takeaway", "top", "downswing", "impact", "finish"],
    "putting": ["address", "backstroke", "forward", "impact", "follow_through", "finish"],
}


class AnalysisBullet(BaseModel):
    title: str = Field(description="Bold label e.g. 'Excellent Lower Body Action' or 'The Setup: The Sitting Stance'")
    detail: str = Field(description="2-4 sentences. Specific to THIS swing video. Plain English.")


class SwingMetricEvidence(BaseModel):
    checkpoint: str
    metric: str
    observed: str
    expected: str
    interpretation: str | None = None
    confidence: float = Field(ge=0, le=1)


class DrillPrescription(BaseModel):
    name: str
    instructions: str
    sets_reps: str
    success_metric: str


class PgaDrill(BaseModel):
    name: str
    why_it_helps: str
    how_to_do_it: str


class PgaCoachAnalysis(BaseModel):
    pga_analysis: str
    main_fix: str
    tips_and_feels: list[str] = Field(min_length=3, max_length=3)
    drills: list[PgaDrill] = Field(min_length=2, max_length=2)
    next_upload_focus: str
    confidence_note: str


class FixItDrill(BaseModel):
    name: str
    steps: list[str] = Field(min_length=3, max_length=5)
    dose: str
    success_check: str


class AdvancedDetails(BaseModel):
    first_breakdown_checkpoint: str
    root_cause: str
    symptom: str
    confidence_note: str
    camera_angle_limitations: str
    evidence_plain_english: list[str] = Field(default_factory=list)
    raw_metrics: dict = Field(default_factory=dict)


class CoachSummaryReport(BaseModel):
    coach_summary: str
    whats_working: list[str] = Field(min_length=1, max_length=3)
    main_swing_leak: str
    why_it_matters: str
    feel_this_week: str
    what_to_feel: list[str] = Field(min_length=1, max_length=3)
    fix_it_drill: FixItDrill
    practice_plan_7_day: list[str] = Field(min_length=3, max_length=4)
    next_upload_goal: str
    advanced_details: AdvancedDetails


ImpactLevel = Literal["low", "medium", "high"]
ConfidenceLevel = Literal["high", "medium", "low"]


class EstimatedScoreImpact(BaseModel):
    level: ImpactLevel
    shots_at_risk: str = Field(description="Plain-English estimate, not fake precision.")
    explanation: str


class ImprovementFixPriority(BaseModel):
    fix_first: str
    fix_second: str
    ignore_for_now: list[str] = Field(min_length=1, max_length=3)
    why_this_order: str


class ImprovementPracticePlan(BaseModel):
    practice_goal: str
    tomorrow_plan: list[str] = Field(min_length=3, max_length=5)
    primary_drill: PgaDrill
    feels: list[str] = Field(min_length=2, max_length=3)
    dosage: str
    success_check: str


class ImprovementBenchmark(BaseModel):
    metric: str
    current_state: str
    target_next_upload: str
    upload_instruction: str


class ProgressMetric(BaseModel):
    name: str
    current_score: int = Field(ge=0, le=100)
    previous_score: int | None = Field(default=None, ge=0, le=100)
    change: int | None = None
    interpretation: str


class ProgressScore(BaseModel):
    overall: int = Field(ge=0, le=100)
    previous_overall: int | None = Field(default=None, ge=0, le=100)
    trend: Literal["first_upload", "improved", "same", "regressed", "unknown"]
    summary: str
    metrics: list[ProgressMetric] = Field(min_length=3, max_length=6)


class ImprovementConfidence(BaseModel):
    level: ConfidenceLevel
    why: str
    limiting_factors: list[str] = Field(default_factory=list)
    evidence_used: list[str] = Field(default_factory=list)


class PracticeValueScore(BaseModel):
    contact: ImpactLevel
    direction: ImpactLevel
    consistency: ImpactLevel
    distance: ImpactLevel
    summary: str


class ImprovementEngine(BaseModel):
    main_diagnosis: str
    expected_ball_flight_consequence: str
    estimated_score_impact: EstimatedScoreImpact
    fix_priority: ImprovementFixPriority
    practice_plan: ImprovementPracticePlan
    improvement_benchmark: ImprovementBenchmark
    progress_score: ProgressScore
    confidence: ImprovementConfidence
    practice_value_score: PracticeValueScore


class SwingIssueDiagnosis(BaseModel):
    symptom: str
    root_cause: str
    first_breakdown_checkpoint: str
    evidence: list[SwingMetricEvidence] = Field(default_factory=list)
    chain_reaction: str
    fix_priority: int = Field(ge=1, le=3)
    why_this_comes_first: str
    recommended_feel: str
    drill: DrillPrescription
    next_video_focus: str


class FixPriorityBlock(BaseModel):
    primary: str
    secondary: str
    optional: str


class SwingDiagnosisEngine(BaseModel):
    main_diagnosis: str
    skill_level_note: str
    first_breakdown_checkpoint: str
    root_cause: str
    symptom: str
    chain_reaction: str
    fix_priority: FixPriorityBlock
    evidence: list[SwingMetricEvidence] = Field(default_factory=list)
    what_to_feel: str
    one_drill: DrillPrescription
    next_upload_focus: str
    coach_warning: str
    issues: list[SwingIssueDiagnosis] = Field(default_factory=list)


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
            "THE WEAKNESSES (The Flaws) — numbered chain: setup flaw → takeaway compensation → "
            "downswing rescue. Each title can include a nickname in quotes."
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


class CoachingReportSchema(BaseModel):
    personalized_greeting: str = Field(
        description=(
            "1-2 short sentences. Use player's first name. Reference their swing history "
            "(first upload vs returning, prior focus if any). Hook them to open the app again. Max 35 words."
        )
    )
    feel_blueprint: FeelBlueprintDiagnostic
    blueprint: KinestheticBlueprint
    roadmap: AccountabilityPlan
    pga_coach_analysis: PgaCoachAnalysis | None = Field(
        default=None,
        description="Skimmable PGA-coach read in the requested user-facing JSON structure.",
    )
    coach_summary_report: CoachSummaryReport | None = Field(
        default=None,
        description="Short paid-coach report for the public UI. Technical evidence belongs in advanced_details only.",
    )
    improvement_engine: ImprovementEngine
    diagnosis_engine: SwingDiagnosisEngine | None = Field(
        default=None,
        description="Cause-and-effect swing diagnosis with first-breakdown evidence and one prioritized prescription.",
    )
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
    video_mime_type: str | None = None
    swing_mode: SwingMode = "full_swing"
    history_summary: str | None = None
    player_name: str | None = None
    swing_number: int | None = None
    player_context: str | None = None
    player_age: int | None = None
    years_playing: int | None = None
    physical_limitations: str | None = None
    camera_angle: str | None = None
    handedness: str | None = None
    skill_level: str | None = None
    ball_flight: str | None = None
    user_goal: str | None = None
    club_used: str | None = None
    practice_availability: str | None = None
    handicap: str | None = None
    prior_progress: dict | None = None
