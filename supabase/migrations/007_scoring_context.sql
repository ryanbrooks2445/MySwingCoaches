-- Structured player context so analysis tone and priorities match the golfer.

ALTER TABLE profiles
  ADD COLUMN IF NOT EXISTS average_9_score INTEGER CHECK (
    average_9_score IS NULL OR (average_9_score >= 25 AND average_9_score <= 90)
  ),
  ADD COLUMN IF NOT EXISTS typical_miss TEXT,
  ADD COLUMN IF NOT EXISTS primary_goal TEXT;
