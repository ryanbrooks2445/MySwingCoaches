export type UserRole = "user" | "coach" | "admin";
export type SubscriptionPlan = "free" | "player" | "serious";
export type VideoStatus = "uploaded" | "processing" | "ready" | "failed";
export type ReportStatus = "processing" | "ready" | "failed";
export type IssueSeverity = "low" | "medium" | "high";

export interface Profile {
  id: string;
  display_name: string | null;
  handedness: "right" | "left";
  skill_level: "beginner" | "intermediate" | "advanced";
  camera_angle_pref: "face-on" | "down-the-line" | "unknown";
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
  camera_angle: string;
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
  free: 1,
  player: 10,
  serious: -1,
};

export const PLAN_PRICES: Record<SubscriptionPlan, { name: string; price: string; features: string[] }> = {
  free: {
    name: "Free",
    price: "$0",
    features: ["1 swing analysis", "Basic AI report", "Key frame breakdown"],
  },
  player: {
    name: "Player",
    price: "$19/mo",
    features: ["10 analyses per month", "Progress tracking", "Drill library"],
  },
  serious: {
    name: "Serious Golfer",
    price: "$49/mo",
    features: ["Unlimited AI analyses", "Progress tracking", "Priority processing"],
  },
};
