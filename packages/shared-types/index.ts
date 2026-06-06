export type UserRole = "user" | "coach" | "admin";
export type SubscriptionPlan = "free" | "player" | "serious";
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
  status: VideoStatus;
  created_at: string;
}

export interface SwingReport {
  id: string;
  user_id: string;
  video_id: string;
  status: ReportStatus;
  overall_score: number | null;
  setup_score: number | null;
  backswing_score: number | null;
  downswing_score: number | null;
  impact_score: number | null;
  finish_score: number | null;
  main_diagnosis: string | null;
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

export const PRICE_PER_ANALYSIS = 19.99;
export const PRICE_PER_ANALYSIS_DISPLAY = "$19.99";

export type SwingMode = "full_swing" | "chipping" | "putting";

export const PLAN_LIMITS: Record<SubscriptionPlan, number> = {
  free: 0,
  player: 0,
  serious: -1,
};
