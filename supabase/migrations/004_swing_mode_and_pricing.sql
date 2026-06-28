-- Swing mode (full swing, chipping, putting) + pay-per-upload credits (default 0 on signup)

CREATE TYPE swing_mode AS ENUM ('full_swing', 'chipping', 'putting');

ALTER TABLE swing_videos
  ADD COLUMN IF NOT EXISTS swing_mode swing_mode NOT NULL DEFAULT 'full_swing';

ALTER TABLE swing_reports
  ADD COLUMN IF NOT EXISTS swing_mode swing_mode NOT NULL DEFAULT 'full_swing';

CREATE INDEX IF NOT EXISTS idx_swing_videos_swing_mode ON swing_videos(swing_mode);
CREATE INDEX IF NOT EXISTS idx_swing_reports_swing_mode ON swing_reports(swing_mode);

-- New signups start with 0 prepaid analyses; swing uploads are purchased one at a time.
CREATE OR REPLACE FUNCTION handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO profiles (id, display_name)
  VALUES (NEW.id, COALESCE(NEW.raw_user_meta_data->>'display_name', split_part(NEW.email, '@', 1)));
  INSERT INTO subscriptions (user_id, plan, analyses_limit, analyses_used)
  VALUES (NEW.id, 'free', 0, 0);
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public;
