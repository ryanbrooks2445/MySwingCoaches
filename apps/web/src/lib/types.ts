export type UserRole = "user" | "coach" | "admin";
export type SubscriptionPlan = "free" | "player" | "serious";
export type VideoStatus = "uploaded" | "processing" | "ready" | "failed";
export type ReportStatus = "processing" | "ready" | "failed";
export type IssueSeverity = "low" | "medium" | "high";

export interface Profile {
  id: string;
  display_name: string | null;
  role: UserRole;
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
  diagnostic: DiagnosticTruth;
  blueprint: KinestheticBlueprint;
  roadmap: AccountabilityPlan;
  next_upload_focus: string;
  disclaimer: string;
}

export interface SwingReport {
  id: string;
  user_id: string;
  video_id: string;
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

export const PLAN_LIMITS: Record<SubscriptionPlan, number> = {
  free: 5,
  player: 10,
  serious: -1,
};

export const PLAN_PRICES: Record<SubscriptionPlan, { name: string; price: string; features: string[] }> = {
  free: {
    name: "Free",
    price: "$0",
    features: ["5 swing analyses", "Full coaching blueprint", "Key frame reference"],
  },
  player: {
    name: "Player",
    price: "$19/mo",
    features: ["10 analyses per month", "Milestone tracking", "7-day practice plans"],
  },
  serious: {
    name: "Serious Golfer",
    price: "$49/mo",
    features: ["Unlimited AI analyses", "Training history", "Priority processing"],
  },
};
