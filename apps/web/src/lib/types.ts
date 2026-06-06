export type UserRole = "user" | "coach" | "admin";
export type SubscriptionPlan = "free" | "player" | "serious";
export type { SwingMode } from "@/lib/pricing";
export type VideoStatus = "uploaded" | "processing" | "ready" | "failed";
export type ReportStatus = "processing" | "ready" | "failed";
export type IssueSeverity = "low" | "medium" | "high";

export interface Profile {
  id: string;
  display_name: string | null;
  role: UserRole;
  age?: number | null;
  years_playing?: number | null;
  physical_limitations?: string | null;
}

export interface Subscription {
  id: string;
  user_id: string;
  plan: SubscriptionPlan;
  status: string;
  analyses_used: number;
  analyses_limit: number;
  coach_review_addon: boolean;
}

export interface SwingVideo {
  id: string;
  user_id: string;
  storage_path: string;
  original_filename: string | null;
  mime_type: string;
  size_bytes: number;
  duration_sec: number | null;
  swing_mode?: import("@/lib/pricing").SwingMode;
  camera_angle?: "face-on" | "down-the-line" | "unknown" | null;
  status: VideoStatus;
  created_at: string;
}

export interface SwingStrength {
  title: string;
  detail: string;
}

export interface BlueprintStep {
  title: string;
  step_type: "setup" | "visual_cue" | "constraint_drill";
  adjustment?: string | null;
  action?: string | null;
  feel: string;
  success_condition?: string | null;
  video_slug?: string | null;
  video_url?: string | null;
  video_title?: string | null;
}

export interface MilestoneBlock {
  days: string;
  title: string;
  detail: string;
}

export interface AnalysisBullet {
  title: string;
  detail: string;
}

export interface ProFix {
  title: string;
  detail: string;
}

export interface SwingMetricEvidence {
  checkpoint: string;
  metric: string;
  observed: string;
  expected: string;
  interpretation?: string | null;
  confidence: number;
}

export interface DrillPrescription {
  name: string;
  instructions: string;
  sets_reps: string;
  success_metric: string;
}

export interface PgaDrill {
  name: string;
  why_it_helps: string;
  how_to_do_it: string;
}

export interface PgaCoachAnalysis {
  pga_analysis: string;
  main_fix: string;
  tips_and_feels: string[];
  drills: PgaDrill[];
  next_upload_focus: string;
  confidence_note: string;
}

export interface FixItDrill {
  name: string;
  steps: string[];
  dose: string;
  success_check: string;
}

export interface AdvancedDetails {
  first_breakdown_checkpoint: string;
  root_cause: string;
  symptom: string;
  confidence_note: string;
  camera_angle_limitations: string;
  evidence_plain_english: string[];
  raw_metrics: Record<string, unknown>;
}

export interface CoachSummaryReport {
  coach_summary: string;
  whats_working: string[];
  main_swing_leak: string;
  why_it_matters: string;
  feel_this_week: string;
  what_to_feel: string[];
  fix_it_drill: FixItDrill;
  practice_plan_7_day: string[];
  next_upload_goal: string;
  advanced_details: AdvancedDetails;
}

export type ImpactLevel = "low" | "medium" | "high";
export type ConfidenceLevel = "high" | "medium" | "low";

export interface EstimatedScoreImpact {
  level: ImpactLevel;
  shots_at_risk: string;
  explanation: string;
}

export interface ImprovementFixPriority {
  fix_first: string;
  fix_second: string;
  ignore_for_now: string[];
  why_this_order: string;
}

export interface ImprovementPracticePlan {
  practice_goal: string;
  tomorrow_plan: string[];
  primary_drill: PgaDrill;
  feels: string[];
  dosage: string;
  success_check: string;
}

export interface ImprovementBenchmark {
  metric: string;
  current_state: string;
  target_next_upload: string;
  upload_instruction: string;
}

export interface ProgressMetric {
  name: string;
  current_score: number;
  previous_score?: number | null;
  change?: number | null;
  interpretation: string;
}

export interface ProgressScore {
  overall: number;
  previous_overall?: number | null;
  trend: "first_upload" | "improved" | "same" | "regressed" | "unknown";
  summary: string;
  metrics: ProgressMetric[];
}

export interface ImprovementConfidence {
  level: ConfidenceLevel;
  why: string;
  limiting_factors: string[];
  evidence_used: string[];
}

export interface PracticeValueScore {
  contact: ImpactLevel;
  direction: ImpactLevel;
  consistency: ImpactLevel;
  distance: ImpactLevel;
  summary: string;
}

export interface ImprovementEngine {
  main_diagnosis: string;
  expected_ball_flight_consequence: string;
  estimated_score_impact: EstimatedScoreImpact;
  fix_priority: ImprovementFixPriority;
  practice_plan: ImprovementPracticePlan;
  improvement_benchmark: ImprovementBenchmark;
  progress_score: ProgressScore;
  confidence: ImprovementConfidence;
  practice_value_score: PracticeValueScore;
}

export interface SwingDiagnosisIssue {
  symptom: string;
  root_cause: string;
  first_breakdown_checkpoint: string;
  evidence: SwingMetricEvidence[];
  chain_reaction: string;
  fix_priority: 1 | 2 | 3;
  why_this_comes_first: string;
  recommended_feel: string;
  drill: DrillPrescription;
  next_video_focus: string;
}

export interface SwingDiagnosisEngine {
  main_diagnosis: string;
  skill_level_note: string;
  first_breakdown_checkpoint: string;
  root_cause: string;
  symptom: string;
  chain_reaction: string;
  fix_priority: {
    primary: string;
    secondary: string;
    optional: string;
  };
  evidence: SwingMetricEvidence[];
  what_to_feel: string;
  one_drill: DrillPrescription;
  next_upload_focus: string;
  coach_warning: string;
  issues?: SwingDiagnosisIssue[];
}

export interface FeelBlueprintDiagnostic {
  opening_narrative: string;
  headline: string;
  strengths: AnalysisBullet[];
  flaws: AnalysisBullet[];
  current_ceiling: string;
  potential_ceiling: string;
  pro_fixes: ProFix[];
  body_part_cue: string;
  spatial_cue: string;
  /** @deprecated Compact format — migrated in UI */
  posture_check?: string;
  real_culprit?: string;
  kinetic_reaction?: string;
}

/** @deprecated Legacy reports only */
export interface DiagnosticTruth {
  headline: string;
  what_your_eye_sees: string;
  mechanical_cause: string;
  kinetic_chain: string;
}

export interface KinestheticBlueprint {
  headline: string;
  intro: string;
  steps: BlueprintStep[];
}

export interface AccountabilityPlan {
  weekly_focus: string;
  milestones: MilestoneBlock[];
  day_7_test: string;
}

export interface CoachingContent {
  personalized_greeting: string;
  feel_blueprint?: FeelBlueprintDiagnostic;
  /** @deprecated Legacy reports only */
  diagnostic?: DiagnosticTruth;
  blueprint: KinestheticBlueprint;
  roadmap: AccountabilityPlan;
  pga_coach_analysis?: PgaCoachAnalysis | null;
  coach_summary_report?: CoachSummaryReport | null;
  improvement_engine?: ImprovementEngine | null;
  diagnosis_engine?: SwingDiagnosisEngine | null;
  next_upload_focus: string;
  disclaimer: string;
}

export interface SwingReport {
  id: string;
  user_id: string;
  video_id: string;
  swing_mode?: import("@/lib/pricing").SwingMode;
  status: ReportStatus;
  /** @deprecated Legacy score fields — no longer populated */
  overall_score: number | null;
  setup_score: number | null;
  backswing_score: number | null;
  downswing_score: number | null;
  impact_score: number | null;
  finish_score: number | null;
  main_diagnosis: string | null;
  coaching_content: CoachingContent | null;
  gemini_raw: Record<string, unknown> | null;
  swing_strengths: SwingStrength[];
  practice_plan: string | null;
  next_upload_focus: string | null;
  disclaimer: string | null;
  key_frame_urls: KeyFrameUrl[];
  pose_landmarks: Record<string, unknown>;
  ai_narrative_available: boolean;
  error_message: string | null;
  created_at: string;
}

export interface KeyFrameUrl {
  phase: string;
  url: string;
  storage_path?: string;
  confidence?: number;
}

export interface SwingIssue {
  id: string;
  issue_code: string;
  issue: string;
  severity: IssueSeverity;
  why_it_matters: string | null;
  fix: string | null;
  drill: string | null;
  source: "rules" | "gemini";
}

export interface DrillRecommendation {
  id: string;
  title: string;
  description: string | null;
  focus_area: string | null;
}

export interface CoachReview {
  id: string;
  report_id: string;
  video_id: string;
  user_id: string;
  reviewer_id: string | null;
  requested: boolean;
  status: "pending" | "in_progress" | "completed";
  notes: string | null;
  completed_at: string | null;
}

/** Dev / legacy: -1 = unlimited analyses */
export const PLAN_LIMITS: Record<SubscriptionPlan, number> = {
  free: 0,
  player: 0,
  serious: -1,
};

export { PRICE_PER_ANALYSIS, PRICE_PER_ANALYSIS_DISPLAY } from "@/lib/pricing";
