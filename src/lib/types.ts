export type UserRole = "user" | "coach" | "admin";
export type SubscriptionPlan = "free" | "player" | "serious" | "unlimited_annual";
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
  average_9_score?: number | null;
  typical_miss?: string | null;
  primary_goal?: string | null;
}

export interface Subscription {
  id: string;
  user_id: string;
  plan: SubscriptionPlan;
  status: string;
  analyses_used: number;
  analyses_limit: number;
  period_start?: string | null;
  period_end?: string | null;
  stripe_customer_id?: string | null;
  stripe_subscription_id?: string | null;
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
  camera_angle?: string | null;
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

export interface DrillSummary {
  name: string;
  why_it_helps: string;
  how_to_do_it: string;
}

export interface DiagnosticCheckpointGrade {
  checkpoint: string;
  grade: "optimal" | "compensation" | "constraint" | "not_visible";
  observation: string;
}

export interface AdvancedDetails {
  report_mode?: "development" | "maintenance";
  foundational_missing_piece?: string;
  profile_constraints_applied?: string;
  diagnostic_checkpoints?: DiagnosticCheckpointGrade[];
  root_cause: string;
  symptom: string;
  evidence_metrics: string[];
  secondary_fix: string;
  optional_fix: string;
  chain_reaction: string;
  why_it_caused_the_miss: string;
  confidence_score: number;
  next_checkpoint?: string;
}

export interface CategoryRating {
  label: string;
  rating: string;
}

export interface CoachVerdict {
  overall_rating: string;
  biggest_positive: string;
  main_issue: string;
  best_fix: string;
  category_ratings: CategoryRating[];
}

export interface SimplifiedSwingReport {
  pga_analysis: string;
  main_fix: string;
  tips_and_feels: string[];
  drills: DrillSummary[];
  practice_plan?: string[];
  next_swing_check: string;
  advanced_details: AdvancedDetails;
  coach_verdict?: CoachVerdict | null;
}

export interface CoachingContent {
  personalized_greeting: string;
  pga_analysis?: string;
  main_fix?: string;
  tips_and_feels?: string[];
  drills?: DrillSummary[];
  next_swing_check?: string;
  coach_verdict?: CoachVerdict | null;
  advanced_details?: AdvancedDetails;
  feel_blueprint?: FeelBlueprintDiagnostic;
  /** @deprecated Legacy reports only */
  diagnostic?: DiagnosticTruth;
  blueprint?: KinestheticBlueprint;
  roadmap?: AccountabilityPlan;
  diagnosis_engine?: SwingDiagnosisEngine | null;
  /** @deprecated Dev / legacy reports */
  improvement_engine?: Record<string, unknown> | null;
  /** @deprecated Dev / legacy reports */
  pga_coach_analysis?: Record<string, unknown> | null;
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
  phase_map?: PhaseFrame[];
  swing_window?: SwingWindowMeta | null;
  pose_landmarks: Record<string, unknown>;
  ai_narrative_available: boolean;
  error_message: string | null;
  created_at: string;
}

export interface KeyFrameUrl {
  phase: string;
  url?: string;
  storage_path?: string;
  confidence?: number;
  person_visible?: boolean;
  notes?: string;
}

export interface PhaseFrame {
  phase: string;
  frame_index: number;
  confidence: number;
  person_visible: boolean;
  notes?: string;
}

export interface SwingWindowMeta {
  start_frame: number;
  end_frame: number;
  duration_sec: number;
  person_coverage_pct: number;
  fps: number;
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
  unlimited_annual: -1,
};

export {
  PRICE_PER_ANALYSIS,
  PRICE_PER_ANALYSIS_DISPLAY,
  PRICE_PER_ANALYSIS_CENTS,
  getNextAnalysisPrice,
  getNextAnalysisPriceDisplay,
} from "@/lib/pricing";
