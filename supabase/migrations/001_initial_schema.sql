-- MySwingCoaches initial schema + RLS + storage policies

-- Enums
CREATE TYPE user_role AS ENUM ('user', 'coach', 'admin');
CREATE TYPE subscription_plan AS ENUM ('free', 'player', 'serious');
CREATE TYPE subscription_status AS ENUM ('active', 'canceled', 'past_due', 'trialing');
CREATE TYPE video_status AS ENUM ('uploaded', 'processing', 'ready', 'failed');
CREATE TYPE report_status AS ENUM ('processing', 'ready', 'failed');
CREATE TYPE issue_severity AS ENUM ('low', 'medium', 'high');
CREATE TYPE issue_source AS ENUM ('rules', 'gemini');
CREATE TYPE coach_review_status AS ENUM ('pending', 'in_progress', 'completed');
CREATE TYPE handedness AS ENUM ('right', 'left');
CREATE TYPE skill_level AS ENUM ('beginner', 'intermediate', 'advanced');
CREATE TYPE camera_angle AS ENUM ('face-on', 'down-the-line', 'unknown');

-- Profiles
CREATE TABLE profiles (
  id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  display_name TEXT,
  handedness handedness DEFAULT 'right',
  skill_level skill_level DEFAULT 'intermediate',
  camera_angle_pref camera_angle DEFAULT 'unknown',
  role user_role NOT NULL DEFAULT 'user',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Subscriptions (Stripe-ready stub)
CREATE TABLE subscriptions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE UNIQUE,
  plan subscription_plan NOT NULL DEFAULT 'free',
  status subscription_status NOT NULL DEFAULT 'active',
  analyses_used INTEGER NOT NULL DEFAULT 0,
  analyses_limit INTEGER NOT NULL DEFAULT 1,
  period_start TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  stripe_customer_id TEXT,
  stripe_subscription_id TEXT,
  coach_review_addon BOOLEAN NOT NULL DEFAULT FALSE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Swing videos
CREATE TABLE swing_videos (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  storage_path TEXT NOT NULL,
  original_filename TEXT,
  mime_type TEXT NOT NULL,
  size_bytes BIGINT NOT NULL,
  duration_sec NUMERIC,
  status video_status NOT NULL DEFAULT 'uploaded',
  camera_angle camera_angle DEFAULT 'unknown',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Swing reports
CREATE TABLE swing_reports (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  video_id UUID NOT NULL REFERENCES swing_videos(id) ON DELETE CASCADE,
  status report_status NOT NULL DEFAULT 'processing',
  overall_score INTEGER,
  setup_score INTEGER,
  backswing_score INTEGER,
  downswing_score INTEGER,
  impact_score INTEGER,
  finish_score INTEGER,
  main_diagnosis TEXT,
  practice_plan TEXT,
  next_upload_focus TEXT,
  disclaimer TEXT,
  key_frame_urls JSONB DEFAULT '[]'::jsonb,
  pose_landmarks JSONB DEFAULT '{}'::jsonb,
  gemini_raw JSONB,
  ai_narrative_available BOOLEAN NOT NULL DEFAULT TRUE,
  error_message TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Swing metrics
CREATE TABLE swing_metrics (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  report_id UUID NOT NULL REFERENCES swing_reports(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  head_movement NUMERIC,
  spine_angle_address NUMERIC,
  spine_angle_impact NUMERIC,
  spine_angle_change NUMERIC,
  hip_rotation_address_to_top NUMERIC,
  hip_rotation_top_to_impact NUMERIC,
  shoulder_tilt_top NUMERIC,
  lead_arm_angle_top NUMERIC,
  lead_arm_angle_impact NUMERIC,
  trail_elbow_flex_top NUMERIC,
  knee_bend_address NUMERIC,
  knee_bend_impact NUMERIC,
  finish_balance NUMERIC,
  tempo_ratio NUMERIC,
  raw_metrics JSONB DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Swing issues
CREATE TABLE swing_issues (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  report_id UUID NOT NULL REFERENCES swing_reports(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  issue_code TEXT NOT NULL,
  issue TEXT NOT NULL,
  severity issue_severity NOT NULL,
  why_it_matters TEXT,
  fix TEXT,
  drill TEXT,
  source issue_source NOT NULL DEFAULT 'rules',
  metric_evidence JSONB DEFAULT '{}'::jsonb,
  sort_order INTEGER DEFAULT 0,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Drill recommendations
CREATE TABLE drill_recommendations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  report_id UUID NOT NULL REFERENCES swing_reports(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  title TEXT NOT NULL,
  description TEXT,
  focus_area TEXT,
  sort_order INTEGER DEFAULT 0,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Coach reviews
CREATE TABLE coach_reviews (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  report_id UUID NOT NULL REFERENCES swing_reports(id) ON DELETE CASCADE,
  video_id UUID NOT NULL REFERENCES swing_videos(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  reviewer_id UUID REFERENCES profiles(id),
  requested BOOLEAN NOT NULL DEFAULT FALSE,
  status coach_review_status NOT NULL DEFAULT 'pending',
  notes TEXT,
  completed_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_swing_videos_user_id ON swing_videos(user_id);
CREATE INDEX idx_swing_reports_user_id ON swing_reports(user_id);
CREATE INDEX idx_swing_reports_video_id ON swing_reports(video_id);
CREATE INDEX idx_swing_reports_created_at ON swing_reports(created_at DESC);
CREATE INDEX idx_swing_issues_report_id ON swing_issues(report_id);
CREATE INDEX idx_coach_reviews_status ON coach_reviews(status);

-- Updated_at trigger
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER profiles_updated_at BEFORE UPDATE ON profiles
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER subscriptions_updated_at BEFORE UPDATE ON subscriptions
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER swing_videos_updated_at BEFORE UPDATE ON swing_videos
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER swing_reports_updated_at BEFORE UPDATE ON swing_reports
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER coach_reviews_updated_at BEFORE UPDATE ON coach_reviews
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- Auto-create profile + subscription on signup
CREATE OR REPLACE FUNCTION handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO profiles (id, display_name)
  VALUES (NEW.id, COALESCE(NEW.raw_user_meta_data->>'display_name', split_part(NEW.email, '@', 1)));
  INSERT INTO subscriptions (user_id, plan, analyses_limit)
  VALUES (NEW.id, 'free', 1);
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public;

CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION handle_new_user();

-- Helper: check if user is coach/admin
CREATE OR REPLACE FUNCTION is_coach_or_admin()
RETURNS BOOLEAN AS $$
  SELECT EXISTS (
    SELECT 1 FROM profiles
    WHERE id = auth.uid() AND role IN ('coach', 'admin')
  );
$$ LANGUAGE sql SECURITY DEFINER STABLE SET search_path = public;

-- RLS
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE swing_videos ENABLE ROW LEVEL SECURITY;
ALTER TABLE swing_reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE swing_metrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE swing_issues ENABLE ROW LEVEL SECURITY;
ALTER TABLE drill_recommendations ENABLE ROW LEVEL SECURITY;
ALTER TABLE coach_reviews ENABLE ROW LEVEL SECURITY;

-- Profiles policies
CREATE POLICY "Users read own profile" ON profiles FOR SELECT USING (auth.uid() = id);
CREATE POLICY "Users update own profile" ON profiles FOR UPDATE USING (auth.uid() = id);
CREATE POLICY "Coaches read all profiles" ON profiles FOR SELECT USING (is_coach_or_admin());

-- Subscriptions policies
CREATE POLICY "Users read own subscription" ON subscriptions FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users update own subscription" ON subscriptions FOR UPDATE USING (auth.uid() = user_id);

-- Swing videos policies
CREATE POLICY "Users read own videos" ON swing_videos FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users insert own videos" ON swing_videos FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users update own videos" ON swing_videos FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Coaches read all videos" ON swing_videos FOR SELECT USING (is_coach_or_admin());

-- Swing reports policies
CREATE POLICY "Users read own reports" ON swing_reports FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users insert own reports" ON swing_reports FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Coaches read all reports" ON swing_reports FOR SELECT USING (is_coach_or_admin());

-- Swing metrics policies
CREATE POLICY "Users read own metrics" ON swing_metrics FOR SELECT USING (auth.uid() = user_id);

-- Swing issues policies
CREATE POLICY "Users read own issues" ON swing_issues FOR SELECT USING (auth.uid() = user_id);

-- Drill recommendations policies
CREATE POLICY "Users read own drills" ON drill_recommendations FOR SELECT USING (auth.uid() = user_id);

-- Coach reviews policies
CREATE POLICY "Users read own coach reviews" ON coach_reviews FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users request coach review" ON coach_reviews FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Coaches manage reviews" ON coach_reviews FOR ALL USING (is_coach_or_admin());

-- Storage buckets
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES
  ('swing-videos', 'swing-videos', false, 104857600, ARRAY['video/mp4', 'video/quicktime', 'video/x-msvideo']),
  ('swing-frames', 'swing-frames', false, 10485760, ARRAY['image/jpeg', 'image/png', 'image/webp'])
ON CONFLICT (id) DO NOTHING;

-- Storage policies: swing-videos
CREATE POLICY "Users upload own swing videos"
  ON storage.objects FOR INSERT
  WITH CHECK (
    bucket_id = 'swing-videos'
    AND auth.uid()::text = (storage.foldername(name))[1]
  );

CREATE POLICY "Users read own swing videos"
  ON storage.objects FOR SELECT
  USING (
    bucket_id = 'swing-videos'
    AND auth.uid()::text = (storage.foldername(name))[1]
  );

CREATE POLICY "Users update own swing videos"
  ON storage.objects FOR UPDATE
  USING (
    bucket_id = 'swing-videos'
    AND auth.uid()::text = (storage.foldername(name))[1]
  );

CREATE POLICY "Coaches read swing videos"
  ON storage.objects FOR SELECT
  USING (bucket_id = 'swing-videos' AND is_coach_or_admin());

-- Storage policies: swing-frames
CREATE POLICY "Users read own swing frames"
  ON storage.objects FOR SELECT
  USING (
    bucket_id = 'swing-frames'
    AND auth.uid()::text = (storage.foldername(name))[1]
  );

CREATE POLICY "Coaches read swing frames"
  ON storage.objects FOR SELECT
  USING (bucket_id = 'swing-frames' AND is_coach_or_admin());
